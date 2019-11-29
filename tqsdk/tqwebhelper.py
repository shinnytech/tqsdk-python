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
import simplejson
import asyncio
import datetime
from aiohttp import web
import socket
import websockets
import tqsdk

class TqWebHelper(object):
    def __init__(self):
        self.web_dir = os.path.join(os.path.dirname(__file__), 'web')
        file_path = os.path.abspath(sys.argv[0])
        self._data = {
            "action": {
                "mode": "run",
                "md_url_status": '-',
                "td_url_status": '-',
            },
            "full_path": file_path[0].upper() + file_path[1:],
            "trade": {},
            "subscribed": [],
            "draw_chart_datas": {},
            "snapshots": {}
        }
        self.order_symbols = set()
        self._diffs = []
        self.conn_diff_chans = set()

    async def _run(self, api, api_send_chan, api_recv_chan, web_send_chan, web_recv_chan):
        self.api = api
        self.logger = api._logger.getChild("TqWebHelper")
        # 发送给 web 账户信息，用作显示
        self._data["action"]["account_id"] = self.api._account.account_id
        self._data["action"]["broker_id"] = self.api._account.broker_id if isinstance(self.api._account,
                                                                                      tqsdk.api.TqAccount) else 'TQSIM'
        if self.api._backtest:
            # 回测模式下，发送 start_dt, end_dt
            self._data["action"]["mode"] = "backtest"
            self._data["action"]["start_dt"] = self.api._backtest.current_dt
            self._data["action"]["end_dt"] = self.api._backtest.end_dt

        self.web_port_chan = tqsdk.api.TqChan(self.api)  # 记录到 ws port 的channel
        self.dt_func = lambda: int(datetime.datetime.now().timestamp() * 1e9)
        if isinstance(api._backtest, tqsdk.backtest.TqBacktest):
            self.dt_func = lambda: api._account._get_current_timestamp()

        _data_task = self.api.create_task(self._data_handler(api_recv_chan, web_recv_chan))
        _wsserver_task = self.api.create_task(self.link_wsserver())
        _httpserver_task = self.api.create_task(self.link_httpserver())

        try:
            # api 发送的包，过滤出需要的包记录在 self._data
            async for pack in api_send_chan:
                if pack['aid'] == 'set_chart_data':
                    diff_data = {} # 存储 pack 中的 diff 数据的对象
                    for series_id, series in pack['datas'].items():
                        if (series["type"] != "KSERIAL" and series["type"] != "SERIAL") \
                                or ("data" in series and isinstance(series["data"], dict)):
                            # 过滤出不符合 diff 协议的数据，旧版 tqhelper 中 KSERIAL/SERIAL 中的 data 对象是 list，不符合 diff 协议
                            diff_data[series_id] = series
                    if diff_data != {}:
                        web_diff = {'draw_chart_datas': {}}
                        web_diff['draw_chart_datas'][pack['symbol']] = {}
                        web_diff['draw_chart_datas'][pack['symbol']][pack['dur_nano']] = diff_data
                        TqWebHelper.merge_diff(self._data, web_diff)
                        for chan in self.conn_diff_chans:
                            self.send_to_conn_chan(chan, [web_diff])
                else:
                    if pack["aid"] == "insert_order":
                        self.order_symbols.add(pack["exchange_id"] + "." + pack["instrument_id"])
                    if pack['aid'] == 'subscribe_quote' or pack["aid"] == "set_chart" or pack["aid"] == 'insert_order':
                        web_diff = {'subscribed': []}
                        for item in self.api._requests["klines"].keys():
                            web_diff['subscribed'].append({"symbol": item[0], "dur_nano": item[1] * 1000000000})
                        for item in self.api._requests["ticks"].keys():
                            web_diff['subscribed'].append({"symbol": item[0], "dur_nano": 0})
                        for symbol in self.api._requests["quotes"]:
                            web_diff['subscribed'].append({"symbol": symbol})
                        for symbol in self.order_symbols:
                            web_diff['subscribed'].append({"symbol": symbol})
                        if web_diff['subscribed'] != self._data['subscribed']:
                            self._data['subscribed'] = web_diff['subscribed']
                        for chan in self.conn_diff_chans:
                            self.send_to_conn_chan(chan, [web_diff])
                    # 发送的转发给上游
                    await web_send_chan.send(pack)
        finally:
            _data_task.cancel()
            _wsserver_task.cancel()
            _httpserver_task.cancel()

    async def _data_handler(self, api_recv_chan, web_recv_chan):
        async for pack in web_recv_chan:
            if pack['aid'] == 'rtn_data':
                web_diffs = []
                account_changed = False
                for d in pack['data']:
                    ## 把 d 处理成需要的数据
                    trade = d.get("trade")
                    if trade is not None:
                        TqWebHelper.merge_diff(self._data["trade"], trade)
                        web_diffs.append({"trade": trade})
                        # 账户是否有变化
                        static_balance_changed = d.get("trade", {}).get(self.api._account.account_id, {}).\
                            get("accounts", {}).get("CNY", {}).get('static_balance')
                        trades_changed = d.get("trade", {}).get(self.api._account.account_id, {}).get("trades", {})
                        orders_changed = d.get("trade", {}).get(self.api._account.account_id, {}).get("orders", {})
                        if static_balance_changed is not None or trades_changed != {} or orders_changed != {}:
                            account_changed = True
                    # 处理通知，行情和交易连接的状态
                    notifies = d.get("notify")
                    if notifies is not None:
                        notify_diffs = self._notify_handler(notifies)
                        if len(notify_diffs) > 0:
                            TqWebHelper.merge_diff(self._data, notify_diffs[0])
                            web_diffs.extend(notify_diffs)
                if account_changed:
                    dt, snapshot = self.get_snapshot()
                    _snapshots = {"snapshots": {}}
                    _snapshots["snapshots"][dt] = snapshot
                    web_diffs.append(_snapshots)
                    TqWebHelper.merge_diff(self._data, _snapshots)
                for chan in self.conn_diff_chans:
                    self.send_to_conn_chan(chan, web_diffs)
            # 接收的数据转发给下游 api
            await api_recv_chan.send(pack)

    def _notify_handler(self, notifies):
        """将连接状态的通知转成 diff 协议"""
        diffs = []
        for _, notify in notifies.items():
            if notify["code"] == 2019112901:
                # 连接建立的通知
                if notify["url"] == self.api._md_url:
                    diffs.append({
                        "action": {
                            "md_url_status": True,
                            "td_url_status": True if isinstance(self.api._account, tqsdk.sim.TqSim) \
                                else self._data["action"]["td_url_status"]
                        }
                    })
                elif notify["url"] == self.api._td_url:
                    diffs.append({
                        "action": {
                            "td_url_status": True
                        }
                    })
            elif notify["code"] == 2019112902:
                # 连接断开的通知
                if notify["url"] == self.api._md_url:
                    diffs.append({
                        "action": {
                            "md_url_status": False,
                            "td_url_status": True if isinstance(self.api._account, tqsdk.sim.TqSim) \
                                else self._data["action"]["td_url_status"]
                        }
                    })
                elif notify["url"] == self.api._td_url:
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

    def get_snapshot(self):
        account = self._data.get("trade", {}).get(self.api._account.account_id, {}).get("accounts", {}).get("CNY", {})
        positions = self._data.get("trade", {}).get(self.api._account.account_id, {}).get("positions", {})
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
        conn_chan = tqsdk.api.TqChan(self.api, last_only=True)
        self.conn_diff_chans.add(conn_chan)
        try:
            async for msg in conn:
                if simplejson.loads(msg)["aid"] == 'peek_message':
                    last_diff = await conn_chan.recv()
                    send_msg = self.get_send_msg(last_diff)
                    await conn.send(send_msg)
        except Exception as e:
            await conn_chan.close()
            self.conn_diff_chans.remove(conn_chan)

    async def link_httpserver(self):
        ws_port = await self.web_port_chan.recv()
        # init http server handlers
        ins_url = self.api._ins_url
        md_url = self.api._md_url
        ws_url = 'ws://127.0.0.1:' + str(ws_port['port'])
        app = web.Application()
        app.router.add_get(path='/url',
                           handler=lambda request: TqWebHelper.httpserver_url_handler(ins_url, md_url, ws_url))
        app.router.add_get(path='/', handler=lambda request: TqWebHelper.httpserver_index_handler(self.web_dir))
        app.router.add_static('/', self.web_dir, show_index=True)
        runner = web.AppRunner(app)
        await runner.setup()
        server_socket = socket.socket()
        server_socket.bind(('127.0.0.1', 0 if self._http_server_port is None else self._http_server_port))
        address = server_socket.getsockname()
        site = web.SockSite(runner, server_socket)
        await site.start()
        self.logger.info("您可以访问 http://{ip}:{port} 查看策略绘制出的 K 线图形。".format(ip=address[0], port=address[1]))
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
