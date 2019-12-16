#!usr/bin/env python3
#-*- coding:utf-8 -*-
"""
@author: yanqiong
@file: guihelper.py
@create_on: 2019/11/7
@description: 
"""
import os
import sys
import argparse
import simplejson
import asyncio
from datetime import datetime
from aiohttp import web
import socket
import websockets
import tqsdk

class TqWebHelper(object):
    async def _run(self, api, api_send_chan, api_recv_chan, web_send_chan, web_recv_chan):
        self._api = api
        self._logger = self._api._logger.getChild("TqWebHelper")  # 调试信息输出
        if not self._api._web_gui:
            # 没有开启 web_gui 功能
            _data_handler_without_web_task = self._api.create_task(
                self._data_handler_without_web(api_recv_chan, web_recv_chan))
            try:
                async for pack in api_send_chan:
                    # api 发送的包，过滤出 set_chart_data, set_web_chart_data, 其余的原样转发
                    if pack['aid'] != 'set_chart_data' and pack['aid'] != 'set_web_chart_data':
                        await web_send_chan.send(pack)
            finally:
                _data_handler_without_web_task.cancel()
        else:
            # 解析命令行参数
            parser = argparse.ArgumentParser()
            # 天勤连接基本参数
            parser.add_argument('--_http_server_port', type=int, required=False)
            args, unknown = parser.parse_known_args()
            # 可选参数，tqwebhelper 中 http server 的 port
            if args._http_server_port is not None:
                self._http_server_port = args._http_server_port
            else:
                self._http_server_port = 0

            self._web_dir = os.path.join(os.path.dirname(__file__), 'web')
            file_path = os.path.abspath(sys.argv[0])
            file_name = os.path.basename(file_path)
            # 初始化数据截面
            self._data = {
                "action": {
                    "mode": "run",
                    "md_url_status": '-',
                    "td_url_status": True if isinstance(self._api._account, tqsdk.api.TqSim) else '-',
                    "account_id": self._api._account._account_id,
                    "broker_id": self._api._account._broker_id if isinstance(self._api._account, tqsdk.api.TqAccount) else 'TQSIM',
                    "file_path": file_path[0].upper() + file_path[1:],
                    "file_name": file_name
                },
                "trade": {},
                "subscribed": [],
                "draw_chart_datas": {},
                "snapshots": {}
            }
            self._order_symbols = set()
            self._diffs = []
            self._conn_diff_chans = set()
            self.web_port_chan = tqsdk.api.TqChan(self._api)  # 记录到 ws port 的channel
            _data_task = self._api.create_task(self._data_handler(api_recv_chan, web_recv_chan))
            _wsserver_task = self._api.create_task(self.link_wsserver())
            _httpserver_task = self._api.create_task(self.link_httpserver())

            try:
                # api 发送的包，过滤出需要的包记录在 self._data
                async for pack in api_send_chan:
                    if pack['aid'] == 'set_chart_data' or pack['aid'] == 'set_web_chart_data':
                        # 发送的是绘图数据
                        # 旧版 tqhelper aid=set_chart_data，发送除 KSERIAL/SERIAL 之外的序列，因为其 KSERIAL/SERIAL 序列不符合 diff 协议
                        # 新版 tqwebhelper aid=set_web_chart_data 中发送的 KSERIAL/SERIAL 数据
                        diff_data = {}  # 存储 pack 中的 diff 数据的对象
                        for series_id, series in pack['datas'].items():
                            if (pack['aid'] == 'set_chart_data' and series["type"] != "KSERIAL" and series["type"] != "SERIAL") or\
                                    pack['aid'] == 'set_web_chart_data' :
                                diff_data[series_id] = series
                        if diff_data != {}:
                            web_diff = {'draw_chart_datas': {}}
                            web_diff['draw_chart_datas'][pack['symbol']] = {}
                            web_diff['draw_chart_datas'][pack['symbol']][pack['dur_nano']] = diff_data
                            TqWebHelper.merge_diff(self._data, web_diff)
                            for chan in self._conn_diff_chans:
                                self.send_to_conn_chan(chan, [web_diff])
                    else:
                        if pack["aid"] == "insert_order":
                            self._order_symbols.add(pack["exchange_id"] + "." + pack["instrument_id"])
                        if pack['aid'] == 'subscribe_quote' or pack["aid"] == "set_chart" or pack["aid"] == 'insert_order':
                            web_diff = {'subscribed': []}
                            for item in self._api._requests["klines"].keys():
                                web_diff['subscribed'].append({"symbol": item[0], "dur_nano": item[1] * 1000000000})
                            for item in self._api._requests["ticks"].keys():
                                web_diff['subscribed'].append({"symbol": item[0], "dur_nano": 0})
                            for symbol in self._api._requests["quotes"]:
                                web_diff['subscribed'].append({"symbol": symbol})
                            for symbol in self._order_symbols:
                                web_diff['subscribed'].append({"symbol": symbol})
                            if web_diff['subscribed'] != self._data['subscribed']:
                                self._data['subscribed'] = web_diff['subscribed']
                            for chan in self._conn_diff_chans:
                                self.send_to_conn_chan(chan, [web_diff])
                        # 发送的转发给上游
                        await web_send_chan.send(pack)
            finally:
                _data_task.cancel()
                _wsserver_task.cancel()
                _httpserver_task.cancel()

    async def _data_handler_without_web(self, api_recv_chan, web_recv_chan):
        # 没有 web_gui, 接受全部数据转发给下游 api_recv_chan
        async for pack in web_recv_chan:
            await api_recv_chan.send(pack)

    async def _data_handler(self, api_recv_chan, web_recv_chan):
        async for pack in web_recv_chan:
            if pack['aid'] == 'rtn_data':
                web_diffs = []
                account_changed = False
                for d in pack['data']:
                    # 把 d 处理成需要的数据
                    # 处理 trade
                    trade = d.get("trade")
                    if trade is not None:
                        TqWebHelper.merge_diff(self._data["trade"], trade)
                        web_diffs.append({"trade": trade})
                        # 账户是否有变化
                        static_balance_changed = d.get("trade", {}).get(self._api._account._account_id, {}).\
                            get("accounts", {}).get("CNY", {}).get('static_balance')
                        trades_changed = d.get("trade", {}).get(self._api._account._account_id, {}).get("trades", {})
                        orders_changed = d.get("trade", {}).get(self._api._account._account_id, {}).get("orders", {})
                        if static_balance_changed is not None or trades_changed != {} or orders_changed != {}:
                            account_changed = True
                    # 处理 backtest
                    tqsdk_backtest = d.get("_tqsdk_backtest")
                    if tqsdk_backtest is not None:
                        TqWebHelper.merge_diff(self._data, d)
                        web_diffs.append(d)
                        if self._data["action"]["mode"] != "backtest":
                            TqWebHelper.merge_diff(self._data, {"action": {"mode": "backtest"}})
                            web_diffs.append({"action": {"mode": "backtest"}})
                    # 处理通知，行情和交易连接的状态
                    notify_diffs = self._notify_handler(d.get("notify", {}))
                    for diff in notify_diffs:
                        TqWebHelper.merge_diff(self._data, diff)
                    web_diffs.extend(notify_diffs)
                if account_changed:
                    dt, snapshot = self.get_snapshot()
                    _snapshots = {"snapshots": {}}
                    _snapshots["snapshots"][dt] = snapshot
                    web_diffs.append(_snapshots)
                    TqWebHelper.merge_diff(self._data, _snapshots)
                for chan in self._conn_diff_chans:
                    self.send_to_conn_chan(chan, web_diffs)
            # 接收的数据转发给下游 api
            await api_recv_chan.send(pack)

    def _notify_handler(self, notifies):
        """将连接状态的通知转成 diff 协议"""
        diffs = []
        for _, notify in notifies.items():
            if notify["code"] == 2019112901 or notify["code"] == 2019112902:
                # 连接建立的通知 第一次建立 或者 重连建立
                if notify["url"] == self._api._md_url:
                    diffs.append({
                        "action": {
                            "md_url_status": True
                        }
                    })
                elif notify["url"] == self._api._td_url:
                    diffs.append({
                        "action": {
                            "td_url_status": True
                        }
                    })
            elif notify["code"] == 2019112911:
                # 连接断开的通知
                if notify["url"] == self._api._md_url:
                    diffs.append({
                        "action": {
                            "md_url_status": False
                        }
                    })
                elif notify["url"] == self._api._td_url:
                    diffs.append({
                        "action": {
                            "td_url_status": False
                        }
                    })
        return diffs

    def send_to_conn_chan(self, chan, diffs):
        last_diff = chan.recv_latest({})
        for d in diffs:
            TqWebHelper.merge_diff(last_diff, d, reduce_diff = False)
        if last_diff != {}:
            chan.send_nowait(last_diff)

    def dt_func (self):
        if '_tqsdk_backtest' in self._data:
            return self._data['_tqsdk_backtest']['current_dt']
        else:
            return int(datetime.now().timestamp() * 1e9)

    def get_snapshot(self):
        account = self._data.get("trade", {}).get(self._api._account._account_id, {}).get("accounts", {}).get("CNY", {})
        positions = self._data.get("trade", {}).get(self._api._account._account_id, {}).get("positions", {})
        dt = self.dt_func()
        return dt, {
            'accounts': {'CNY': {k: v for k, v in account.items() if not k.startswith("_")}},
            'positions': {k: {pk: pv for pk, pv in v.items() if not pk.startswith("_")} for k, v in
                          positions.items() if
                          not k.startswith("_")}
        }

    @staticmethod
    def get_obj(root, path, default=None):
        """获取业务数据"""
        d = root
        for i in range(len(path)):
            if path[i] not in d:
                dv = {} if i != len(path) - 1 or default is None else default
                d[path[i]] = dv
            d = d[path[i]]
        return d

    @staticmethod
    def merge_diff(result, diff, reduce_diff = True):
        """
        更新业务数据
        :param result: 更新结果
        :param diff: diff pack 
        :param reduce_diff: 表示是否修改 diff 对象本身，因为如果 merge_diff 的 result 是 conn_chan 内部的 last_diff，那么 diff 会在循环中多次使用，这时候一定不能修改 diff 本身
        :return: 
        """
        for key in list(diff.keys()):
            if diff[key] is None:
                result.pop(key, None)
            elif isinstance(diff[key], dict):
                target = TqWebHelper.get_obj(result, [key])
                TqWebHelper.merge_diff(target, diff[key], reduce_diff = reduce_diff)
                if len(diff[key]) == 0:
                    del diff[key]
            elif reduce_diff and key in result and result[key] == diff[key]:
                del diff[key]
            else:
                result[key] = diff[key]

    async def link_wsserver(self):
        async def lambda_connection_handler(conn, path): await self.connection_handler(conn)
        async with websockets.serve(lambda_connection_handler, host='127.0.0.1', port=0) as server:
            port = server.server.sockets[0].getsockname()[1]
            await self.web_port_chan.send({'port': port})
            await asyncio.sleep(100000000000)

    def get_send_msg(self, data=None):
        return simplejson.dumps({
            'aid': 'rtn_data',
            'data': [self._data if data is None else data]
        }, ignore_nan=True)

    async def connection_handler(self, conn):
        send_msg = self.get_send_msg(self._data)
        await conn.send(send_msg)
        conn_chan = tqsdk.api.TqChan(self._api, last_only=True)
        self._conn_diff_chans.add(conn_chan)
        try:
            async for msg in conn:
                pack = simplejson.loads(msg)
                if pack["aid"] == 'peek_message':
                    last_diff = await conn_chan.recv()
                    send_msg = self.get_send_msg(last_diff)
                    await conn.send(send_msg)
        except Exception as e:
            await conn_chan.close()
            self._conn_diff_chans.remove(conn_chan)

    async def link_httpserver(self):

        ws_port = await self.web_port_chan.recv()
        # init http server handlers
        ins_url = self._api._ins_url
        md_url = self._api._md_url
        ws_url = 'ws://127.0.0.1:' + str(ws_port['port'])
        app = web.Application()
        app.router.add_get(path='/url',
                           handler=lambda request: TqWebHelper.httpserver_url_handler(ins_url, md_url, ws_url))
        app.router.add_get(path='/', handler=lambda request: TqWebHelper.httpserver_index_handler(self._web_dir))
        app.router.add_static('/', self._web_dir, show_index=True)
        runner = web.AppRunner(app)
        await runner.setup()
        server_socket = socket.socket()
        server_socket.bind(('127.0.0.1', self._http_server_port))
        address = server_socket.getsockname()
        site = web.SockSite(runner, server_socket)
        await site.start()
        self._logger.info("您可以访问 http://{ip}:{port} 查看策略绘制出的 K 线图形。".format(ip=address[0], port=address[1]))
        await asyncio.sleep(100000000000)

    @staticmethod
    def httpserver_url_handler(ins_url, md_url, ws_url):
        return web.json_response({
                'ins_url': ins_url,
                'md_url': md_url,
                'ws_url': ws_url
            })

    @staticmethod
    def httpserver_index_handler(web_dir):
        return web.FileResponse(path=web_dir + '/index.html')
