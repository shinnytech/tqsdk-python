#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'

import asyncio
import os
import socket
import sys
from datetime import datetime
from urllib.parse import urlparse

import numpy as np
import simplejson
from aiohttp import web
from tqsdk.tradeable.sim.basesim import BaseSim

from tqsdk.auth import TqAuth
from tqsdk.backtest import TqBacktest, TqReplay
from tqsdk.channel import TqChan
from tqsdk.datetime import _get_trading_day_start_time
from tqsdk.diff import _simple_merge_diff
from tqsdk.tradeable import TqAccount, TqKq, TqSim


class TqWebHelper(object):

    def __init__(self, api):
        """初始化，检查参数"""
        self._api = api
        ip, port = TqWebHelper.parse_url(self._api._web_gui)
        self._http_server_host = ip if ip else "0.0.0.0"
        self._http_server_port = int(port) if port else 0
        args = TqWebHelper.parser_env_arguments()

        if args["_action"] == "run":
            # 运行模式下，账户参数冲突需要抛错，提示用户
            if args["_broker_id"] == "TQ_KQ":
                if type(self._api._account) is TqAccount:
                    raise Exception("策略代码与插件设置中的账户参数冲突。可尝试删去代码中的账户参数 TqAccount，以插件设置的账户参数运行。")
                self._api._account = TqKq()
            elif args["_broker_id"] and args["_account_id"] and args["_password"]:
                if isinstance(self._api._account, TqKq):
                    raise Exception("策略代码与插件设置中的账户参数冲突。可尝试删去代码中的账户参数 TqKq，以插件设置的账户参数运行。")
                if isinstance(self._api._account, TqAccount) and \
                        (self._api._account._account_id != args["_account_id"] or self._api._account._broker_id !=
                         args["_broker_id"]):
                    raise Exception("策略代码与插件设置中的账户参数冲突。可尝试删去代码中的账户参数 TqAccount，以插件设置的账户参数运行。")
                self._api._account = TqAccount(args["_broker_id"], args["_account_id"], args["_password"])
            else:
                self._api._account = TqSim(args["_init_balance"])
            self._api._backtest = None
            self._api._print(f"正在使用账户 {args['_broker_id']}, {args['_account_id']} 运行策略。")
        elif args["_action"] is not None:
            self._api._account = TqSim(args["_init_balance"])
            if args["_action"] == "backtest":
                self._api._backtest = TqBacktest(start_dt=datetime.strptime(args["_start_dt"], '%Y%m%d'),
                                                 end_dt=datetime.strptime(args["_end_dt"], '%Y%m%d'))
                self._api._print(f"当前回测区间 {args['_start_dt']} - {args['_end_dt']}。")
            elif args["_action"] == "replay":
                self._api._backtest = TqReplay(datetime.strptime(args["_replay_dt"], '%Y%m%d'))
                self._api._print(f"当前复盘日期 {args['_replay_dt']}。")
        if args["_auth"]:
            comma_index = args["_auth"].find(',')
            user_name, pwd = args["_auth"][:comma_index], args["_auth"][comma_index + 1:]
            if self._api._auth is not None and (user_name != self._api._auth._user_name or pwd != self._api._auth._password):
                raise Exception("策略代码与插件设置中的 auth 参数冲突。可尝试删去代码中的 auth 参数，以插件设置的参数运行。")
            self._api._auth = TqAuth(user_name, pwd)
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
                    if pack['aid'] not in ['set_chart_data', 'set_report_data']:
                        await web_send_chan.send(pack)
            finally:
                _data_handler_without_web_task.cancel()
                await asyncio.gather(_data_handler_without_web_task, return_exceptions=True)
        else:
            self._web_dir = os.path.join(os.path.dirname(__file__), 'web')
            file_path = os.path.abspath(sys.argv[0])
            file_name = os.path.basename(file_path)
            # 初始化数据截面
            accounts_info = {
                acc._account_key: {"td_url_status": True if isinstance(acc, BaseSim) else '-'}
                for acc in self._api._account._account_list
            }
            for acc in self._api._account._account_list:
                accounts_info[acc._account_key].update(acc._account_info)
            self._data = {
                "action": {
                    "mode": "replay" if isinstance(self._api._backtest, TqReplay) else "backtest" if isinstance(self._api._backtest, TqBacktest) else "run",
                    "md_url_status": '-',
                    "user_name": self._api._auth._user_name,
                    "file_path": file_path[0].upper() + file_path[1:],
                    "file_name": file_name,
                    "accounts": accounts_info
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
                            _simple_merge_diff(self._data, web_diff)
                            for chan in self._conn_diff_chans:
                                self.send_to_conn_chan(chan, [web_diff])
                    elif pack['aid'] == 'set_report_data':
                        # 发送的是绘图报告数据
                        web_diff = {'draw_report_datas': {}}
                        for data in pack['report_datas']:
                            _simple_merge_diff(web_diff['draw_report_datas'], data)
                        _simple_merge_diff(self._data, web_diff)
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
                await asyncio.gather(_data_task, _httpserver_task, return_exceptions=True)

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
                        _simple_merge_diff(self._data["trade"], trade)
                        web_diffs.append({"trade": trade})
                        # 账户是否有变化
                        static_balance_changed = d.get("trade", {}).get(self._api._account._get_account_key(account=None), {}).\
                            get("accounts", {}).get("CNY", {}).get('static_balance')
                        trades_changed = d.get("trade", {}).get(self._api._account._get_account_key(account=None), {}).get("trades", {})
                        orders_changed = d.get("trade", {}).get(self._api._account._get_account_key(account=None), {}).get("orders", {})
                        if static_balance_changed is not None or trades_changed != {} or orders_changed != {}:
                            account_changed = True
                    # 处理 backtest replay
                    if d.get("_tqsdk_backtest") or d.get("_tqsdk_replay"):
                        _simple_merge_diff(self._data, d)
                        web_diffs.append(d)
                    # 处理通知，行情和交易连接的状态
                    notify_diffs = self._notify_handler(d.get("notify", {}))
                    for diff in notify_diffs:
                        _simple_merge_diff(self._data, diff)
                    web_diffs.extend(notify_diffs)
                if account_changed:
                    dt, snapshot = self.get_snapshot()
                    _snapshots = {"snapshots": {}}
                    _snapshots["snapshots"][dt] = snapshot
                    web_diffs.append(_snapshots)
                    _simple_merge_diff(self._data, _snapshots)
                for chan in self._conn_diff_chans:
                    self.send_to_conn_chan(chan, web_diffs)
            # 接收的数据转发给下游 api
            await api_recv_chan.send(pack)

    def _notify_handler(self, notifies):
        """将连接状态的通知转成 diff 协议"""
        diffs = []
        for _, notify in notifies.items():
            if notify["code"] == 2019112901 or notify["code"] == 2019112902:
                url_status = True  # 连接建立的通知 第一次建立 或者 重连建立
            elif notify["code"] == 2019112911:
                url_status = False  # 连接断开的通知
            else:
                continue
            if notify["url"] == self._api._md_url:
                diffs.append({
                    "action": {"md_url_status": url_status}
                })
            elif notify["conn_id"] in self._api._account._map_conn_id:
                acc = self._api._account._map_conn_id[notify["conn_id"]]
                diffs.append({
                    "action": {
                        "accounts": {acc._account_key: {"td_url_status": url_status}}
                    }
                })
        return diffs

    def send_to_conn_chan(self, chan, diffs):
        last_diff = chan.recv_latest({})
        for d in diffs:
            _simple_merge_diff(last_diff, d, reduce_diff = False)
        if last_diff != {}:
            chan.send_nowait(last_diff)

    def dt_func (self):
        # 回测和复盘模式，用 _api._account 一定是 TqSim, 使用 TqSim _get_current_timestamp() 提供的时间
        # todo: 使用 TqSim.EPOCH
        if self._data["action"]["mode"] == "backtest":
            return self._data['_tqsdk_backtest']['current_dt']
        elif self._data["action"]["mode"] == "replay":
            tqsim_current_timestamp = self._api._account._account_list[0]._get_current_timestamp()
            if tqsim_current_timestamp == 631123200000000000:
                # 未收到任何行情, TqSim 时间没有更新
                return _get_trading_day_start_time(self._data['_tqsdk_replay']['replay_dt'])
            else:
                return tqsim_current_timestamp
        else:
            return int(datetime.now().timestamp() * 1e9)

    def get_snapshot(self):
        account = self._data.get("trade", {}).get(self._api._account._get_account_key(account=None), {}).get("accounts", {}).get("CNY", {})
        positions = self._data.get("trade", {}).get(self._api._account._get_account_key(account=None), {}).get("positions", {})
        dt = self.dt_func()
        return dt, {
            'accounts': {'CNY': {k: v for k, v in account.items() if not k.startswith("_")}},
            'positions': {k: {pk: pv for pk, pv in v.items() if not pk.startswith("_")} for k, v in
                          positions.items() if
                          not k.startswith("_")}
        }

    def get_send_msg(self, data=None):
        return simplejson.dumps({
            'aid': 'rtn_data',
            'data': [self._data if data is None else data]
        }, ignore_nan=True, default=TqWebHelper._convert)

    async def connection_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        send_msg = self.get_send_msg(self._data)
        await ws.send_str(send_msg)
        conn_chan = TqChan(self._api, last_only=True)
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
        try:
            url_response = {
                "ins_url": self._api._ins_url,
                "md_url": self._api._md_url,
            }
            # TODO：在复盘模式下发送 replay_dt 给 web 端，服务器改完后可以去掉
            if isinstance(self._api._backtest, TqReplay):
                url_response["replay_dt"] = int(datetime.combine(self._api._backtest._replay_dt, datetime.min.time()).timestamp() * 1e9)
            app = web.Application()
            app.router.add_get(path='/url', handler=lambda request: TqWebHelper.httpserver_url_handler(url_response))
            app.router.add_get(path='/', handler=self.httpserver_index_handler)
            app.router.add_get(path='/index.html', handler=self.httpserver_index_handler)
            app.router.add_static('/web', self._web_dir, show_index=True)
            app.add_routes([web.get('/ws', self.connection_handler)])
            runner = web.AppRunner(app)
            await runner.setup()
            server_socket = socket.socket()
            if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self._http_server_host, self._http_server_port))
            address = server_socket.getsockname()
            site = web.SockSite(runner, server_socket)
            await site.start()
            ip = "127.0.0.1" if address[0] == "0.0.0.0" else address[0]
            self._api._print("您可以访问 http://{ip}:{port} 查看策略绘制出的 K 线图形。".format(ip=ip, port=address[1]))
            await asyncio.sleep(100000000000)
        finally:
            await runner.shutdown()
            await runner.cleanup()

    def httpserver_index_handler(self, request):
        return web.FileResponse(self._web_dir + '/index.html')

    @staticmethod
    def _convert(o):
        """对于 numpy 类型的数据，返回可以序列化的值"""
        if isinstance(o, np.generic):
            return o.item()
        raise TypeError

    @staticmethod
    def parse_url(url):
        if isinstance(url, str):
            parse_result = urlparse(url, scheme='')
            addr = parse_result.netloc if parse_result.scheme == "http" else url
            return addr.split(':')
        else:
            return '0.0.0.0', '0'

    @staticmethod
    def httpserver_url_handler(response):
        return web.json_response(response)

    @staticmethod
    def parser_env_arguments():
        action = {
            "_action": os.getenv("TQ_ACTION"),
            "_http_server_address": os.getenv("TQ_HTTP_SERVER_ADDRESS"),
            "_auth": os.getenv("TQ_AUTH")
        }
        try:
            action["_init_balance"] = 10000000.0 if os.getenv("TQ_INIT_BALANCE") is None else float(
                os.getenv("TQ_INIT_BALANCE"))
        except ValueError:
            action["_init_balance"] = 10000000.0
        if action["_action"] == "run":
            action["_broker_id"] = os.getenv("TQ_BROKER_ID")
            action["_account_id"] = os.getenv("TQ_ACCOUNT_ID")
            action["_password"] = os.getenv("TQ_PASSWORD")
            if not action["_broker_id"]:
                action["_action"] = None
        elif action["_action"] == "backtest":
            action["_start_dt"] = os.getenv("TQ_START_DT")
            action["_end_dt"] = os.getenv("TQ_END_DT")
            if not action["_start_dt"] or not action["_end_dt"]:
                action["_action"] = None
        elif action["_action"] == "replay":
            action["_replay_dt"] = os.getenv("TQ_REPLAY_DT")
            if not action["_replay_dt"]:
                action["_action"] = None
        return action
