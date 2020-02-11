#!usr/bin/env python3
#-*- coding:utf-8 -*-
"""
@author: yanqiong
@file: guihelper.py
@create_on: 2019/11/7
@description: 
"""
import os
import re
import sys
import argparse
import simplejson
import asyncio
from urllib.parse import urlparse
from datetime import datetime
from aiohttp import web
import socket
import tqsdk

class TqWebHelper(object):

    def __init__(self, api):
        """初始化，检查参数"""
        self._api = api
        self._logger = self._api._logger.getChild("TqWebHelper")  # 调试信息输出
        ip, port = TqWebHelper.parse_url(self._api._web_gui)
        self._http_server_host = ip if ip else "0.0.0.0"
        self._http_server_port = int(port) if port else 0

        args = TqWebHelper.parser_arguments()
        if args:
            if args["_action"] == "run":
                # 运行模式下，账户参数冲突需要抛错，提示用户
                if isinstance(self._api._account, tqsdk.api.TqAccount) and \
                        (self._api._account._account_id != args["_account_id"] or self._api._account._broker_id != args["_broker_id"]):
                    raise Exception("策略代码与设置中的账户参数冲突。可尝试删去代码中的账户参数 TqAccount，以终端或者插件设置的账户参数运行。")
                self._api._account = tqsdk.api.TqAccount(args["_broker_id"], args["_account_id"], args["_password"])
                self._api._backtest = None
            elif args["_action"] == "backtest":
                self._api._account = tqsdk.api.TqSim(args["_init_balance"])
                self._api._backtest = tqsdk.api.TqBacktest(start_dt=datetime.strptime(args["_start_dt"], '%Y%m%d'),
                                            end_dt=datetime.strptime(args["_end_dt"], '%Y%m%d'))
            elif args["_action"] == "replay":
                self._api._backtest = tqsdk.api.TqReplay(datetime.strptime(args["_replay_dt"], '%Y%m%d'))

            if args["_http_server_address"]:
                self._api._web_gui = True  # 命令行 _http_server_address, 一定打开 _web_gui
                ip, port = TqWebHelper.parse_url(args["_http_server_address"])
                self._http_server_host = ip if ip else "0.0.0.0"
                self._http_server_port = int(port) if port else 0

    async def _run(self, api_send_chan, api_recv_chan, web_send_chan, web_recv_chan):
        if not self._api._web_gui:
            # 没有开启 web_gui 功能
            _data_handler_without_web_task = self._api.create_task(
                self._data_handler_without_web(api_recv_chan, web_recv_chan))
            try:
                async for pack in api_send_chan:
                    # api 发送的包，过滤出 set_chart_data, 其余的原样转发
                    if pack['aid'] != 'set_chart_data':
                        await web_send_chan.send(pack)
            finally:
                _data_handler_without_web_task.cancel()
        else:
            self._web_dir = os.path.join(os.path.dirname(__file__), 'web')
            file_path = os.path.abspath(sys.argv[0])
            file_name = os.path.basename(file_path)
            # 初始化数据截面
            self._data = {
                "action": {
                    "mode": "replay" if isinstance(self._api._backtest, tqsdk.api.TqReplay) else "backtest" if isinstance(self._api._backtest, tqsdk.api.TqBacktest) else "run",
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
            _data_task = self._api.create_task(self._data_handler(api_recv_chan, web_recv_chan))
            _httpserver_task = self._api.create_task(self.link_httpserver())

            try:
                # api 发送的包，过滤出需要的包记录在 self._data
                async for pack in api_send_chan:
                    if pack['aid'] == 'set_chart_data':
                        # 发送的是绘图数据
                        diff_data = {}  # 存储 pack 中的 diff 数据的对象
                        for series_id, series in pack['datas'].items():
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
                    # 处理 backtest replay
                    if d.get("_tqsdk_backtest") or d.get("_tqsdk_replay"):
                        TqWebHelper.merge_diff(self._data, d)
                        web_diffs.append(d)
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
        # 回测和复盘模式，用 _api._account 一定是 TqSim, 使用 TqSim _get_current_timestamp() 提供的时间
        # todo: 使用 TqSim.EPOCH
        if self._data["action"]["mode"] == "backtest":
            return self._data['_tqsdk_backtest']['current_dt']
        elif self._data["action"]["mode"] == "replay":
            tqsim_current_timestamp = self._api._account._get_current_timestamp()
            if tqsim_current_timestamp == 631123200000000000:
                # 未收到任何行情, TqSim 时间没有更新
                return tqsdk.TqApi._get_trading_day_start_time(self._data['_tqsdk_replay']['replay_dt'])
            else:
                return tqsim_current_timestamp
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

    def get_send_msg(self, data=None):
        return simplejson.dumps({
            'aid': 'rtn_data',
            'data': [self._data if data is None else data]
        }, ignore_nan=True)

    async def connection_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        send_msg = self.get_send_msg(self._data)
        await ws.send_str(send_msg)
        conn_chan = tqsdk.api.TqChan(self._api, last_only=True)
        self._conn_diff_chans.add(conn_chan)
        try:
            async for msg in ws:
                pack = simplejson.loads(msg.data)
                if pack["aid"] == 'peek_message':
                    last_diff = await conn_chan.recv()
                    send_msg = self.get_send_msg(last_diff)
                    await ws.send_str(send_msg)
        except Exception as e:
            await conn_chan.close()
            self._conn_diff_chans.remove(conn_chan)

    async def link_httpserver(self):
        # init http server handlers
        url_response = {
            "ins_url": self._api._ins_url,
            "md_url": self._api._md_url,
        }
        # TODO：在复盘模式下发送 replay_dt 给 web 端，服务器改完后可以去掉
        if isinstance(self._api._backtest, tqsdk.api.TqReplay):
            url_response["replay_dt"] = int(datetime.combine(self._api._backtest._replay_dt, datetime.min.time()).timestamp() * 1e9)
        app = web.Application()
        app.router.add_get(path='/url',
                           handler=lambda request: TqWebHelper.httpserver_url_handler(url_response))
        app.router.add_get(path='/', handler=lambda request: TqWebHelper.httpserver_index_handler(self._web_dir))
        app.add_routes([web.get('/ws', self.connection_handler)])
        app.router.add_static('/web', self._web_dir, show_index=True)
        runner = web.AppRunner(app)
        await runner.setup()
        server_socket = socket.socket()
        server_socket.bind((self._http_server_host, self._http_server_port))
        address = server_socket.getsockname()
        site = web.SockSite(runner, server_socket)
        await site.start()
        self._logger.info("您可以访问 http://{ip}:{port} 查看策略绘制出的 K 线图形。".format(ip=address[0], port=address[1]))
        await asyncio.sleep(100000000000)

    @staticmethod
    def parse_url(url):
        if isinstance(url, str):
            parse_result = urlparse(url, scheme='')
            ip, _, port = parse_result.path.partition(":")
            if not port:
                ip, _, port = parse_result.netloc.partition(":")
            return ip, port
        else:
            return '0.0.0.0', '0'

    @staticmethod
    def httpserver_url_handler(response):
        return web.json_response(response)

    @staticmethod
    def httpserver_index_handler(web_dir):
        return web.FileResponse(path=web_dir + '/index.html')

    @staticmethod
    def parser_arguments():
        """解析命令行参数"""
        parser = argparse.ArgumentParser()
        # 天勤连接基本参数
        parser.add_argument('--_action', type=str, required=False)
        # action==run
        parser.add_argument('--_broker_id', type=str, required=False)
        parser.add_argument('--_account_id', type=str, required=False)
        parser.add_argument('--_password', type=str, required=False)
        # action==backtest
        parser.add_argument('--_start_dt', type=str, required=False)
        parser.add_argument('--_end_dt', type=str, required=False)
        parser.add_argument('--_init_balance', type=str, required=False)
        # action==replay
        parser.add_argument('--_replay_dt', type=str, required=False)
        # others
        parser.add_argument('--_http_server_address', type=str, required=False)
        args, unknown = parser.parse_known_args()
        action = {}
        action["_action"] = args._action
        if action["_action"] == "run":
            if not args._broker_id or not args._account_id or not args._password:
                raise Exception("run 必要参数缺失")
            else:
                action["_broker_id"] = args._broker_id
                action["_account_id"] = args._account_id
                action["_password"] = args._password
        elif action["_action"] == "backtest":
            if not args._start_dt or not args._end_dt:
                raise Exception("backtest 必要参数缺失")
            else:
                try:
                    init_balance = 10000000.0 if args._init_balance is None else float(args._init_balance)
                    action["_start_dt"] = args._start_dt
                    action["_end_dt"] = args._end_dt
                    action["_init_balance"] = init_balance
                except ValueError:
                    raise Exception("backtest 参数错误, _init_balance = " + args._init_balance + " 不是数字")
        elif action["_action"] == "replay":
            if not args._replay_dt:
                raise Exception("replay 必要参数缺失")
            else:
                action["_replay_dt"] = args._replay_dt

        action["_http_server_address"] = args._http_server_address
        return action
