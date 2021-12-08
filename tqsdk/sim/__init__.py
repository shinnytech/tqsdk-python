#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import asyncio
import statistics
import time
from datetime import datetime

from tqsdk.channel import TqChan
from tqsdk.datetime import _get_trading_day_from_timestamp, _get_trading_day_end_time, _get_trade_timestamp, \
    _is_in_trading_time, _format_from_timestamp_nano
from tqsdk.diff import _get_obj, _register_update_chan, _merge_diff
from tqsdk.entity import Entity
from tqsdk.objs import Quote
from tqsdk.report import TqReport
from tqsdk.sim.trade import SimTrade
from tqsdk.sim.utils import _get_future_margin, _get_commission
from tqsdk.utils import _query_for_quote



class TqSim(object):
    """
    天勤模拟交易类

    该类实现了一个本地的模拟账户，并且在内部完成撮合交易，在回测和复盘模式下，只能使用 TqSim 账户来交易。

    限价单要求报单价格达到或超过对手盘价格才能成交, 成交价为报单价格, 如果没有对手盘(涨跌停)则无法成交

    市价单使用对手盘价格成交, 如果没有对手盘(涨跌停)则自动撤单

    模拟交易不会有部分成交的情况, 要成交就是全部成交
    """

    def __init__(self, init_balance: float = 10000000.0, account_id: str = None) -> None:
        """
        Args:
            init_balance (float): [可选]初始资金, 默认为一千万

            account_id (str): [可选]帐号, 默认为 TQSIM

        Example::

            # 修改TqSim模拟帐号的初始资金为100000
            from tqsdk import TqApi, TqSim, TqAuth
            api = TqApi(TqSim(init_balance=100000), auth=TqAuth("信易账户", "账户密码"))

        """
        self.trade_log = {}  # 日期->交易记录及收盘时的权益及持仓
        self.tqsdk_stat = {}  # 回测结束后储存回测报告信息
        self._account_id = "TQSIM" if account_id is None else account_id
        self._account_type = "FUTURE"
        self._broker_id = "TQSIM" if self._account_type == "FUTURE" else "TQSIM_STOCK"
        self._account_key = str(id(self))
        self._init_balance = float(init_balance)
        if self._init_balance <= 0:
            raise Exception("初始资金(init_balance) %s 错误, 请检查 init_balance 是否填写正确" % (init_balance))
        self._current_datetime = "1990-01-01 00:00:00.000000"  # 当前行情时间（最新的 quote 时间）
        self._trading_day_end = "1990-01-01 18:00:00.000000"
        self._local_time_record = float("nan")  # 记录获取最新行情时的本地时间
        self._sim_trade = SimTrade(account_key=self._account_key, init_balance=self._init_balance,
                                     get_trade_timestamp=self._get_trade_timestamp,
                                     is_in_trading_time=self._is_in_trading_time)
        self._data = Entity()
        self._data._instance_entity([])
        self._prototype = {
            "quotes": {
                "#": Quote(self),  # 行情的数据原型
            }
        }
        self._quote_tasks = {}

    def set_commission(self, symbol: str, commission: float=float('nan')):
        """
        设置指定合约模拟交易的每手手续费。

        Args:
            symbol (str): 合约代码

            commission (float): 每手手续费

        Returns:
            float: 设置的每手手续费

        Example::

            from tqsdk import TqSim, TqApi, TqAuth

            sim = TqSim()
            api = TqApi(sim, auth=TqAuth("信易账户", "账户密码"))

            sim.set_commission("SHFE.cu2112", 50)

            print(sim.get_commission("SHFE.cu2112"))
        """
        if commission != commission:
            raise Exception("合约手续费不可以设置为 float('nan')")
        quote = _get_obj(self._data, ["quotes", symbol], Quote(self._api if hasattr(self, "_api") else None))
        quote["user_commission"] = commission
        if self._quote_tasks.get(symbol):
            self._quote_tasks[symbol]["quote_chan"].send_nowait({
                "quotes": {symbol: {"user_commission": commission}}
            })
        return commission

    def set_margin(self, symbol: str, margin: float=float('nan')):
        """
        设置指定合约模拟交易的每手保证金。

        Args:
            symbol (str): 合约代码 (只支持期货合约)

            margin (float): 每手保证金

        Returns:
            float: 设置的每手保证金

        Example::

            from tqsdk import TqSim, TqApi, TqAuth

            sim = TqSim()
            api = TqApi(sim, auth=TqAuth("信易账户", "账户密码"))

            sim.set_margin("SHFE.cu2112", 26000)

            print(sim.get_margin("SHFE.cu2112"))
        """
        if margin != margin:
            raise Exception("合约手续费不可以设置为 float('nan')")
        quote = _get_obj(self._data, ["quotes", symbol], Quote(self._api if hasattr(self, "_api") else None))
        quote["user_margin"] = margin
        if self._quote_tasks.get(symbol):
            self._quote_tasks[symbol]["quote_chan"].send_nowait({
                "quotes": {symbol: {"user_margin": margin}}
            })
            # 当用户设置保证金时，用户应该得到的效果是：
            # 在调用 sim.set_margin() 之后，立即调用 api.get_position(symbol)，得到的 margin 字段应该按照新设置的保证金调整过，而且中间没有收到过行情更新包
            # 以下代码可以保证这个效果，说明：
            # 1. 持仓已经调整过:
            #   sim_trade 中持仓的 future_margin 字段更新，margin 会同时调整，那么 api 中持仓的 future_margin 更新时，margin 一定也已经更新
            # 2. 中间没有收到过行情更新包:
            #   前提1：根据 diff 协议，sim 收到 peek_message 时，会将缓存的 diffs 发给用户，当缓存的 diffs 为空，会转发 peek_message；
            #   前提2：api.wait_update() 会等到所有 task 都执行到 pending 状态，然后发送 peek_message 给 sim
            #   当用户代码执行到 sim.set_margin()，立即向 quote_chan 中发送一个数据包，quote_task 就会到 ready 状态，此时调用 wait_update()，
            #   到所有 task 执行到 pending 状态时，sim 的 diffs 中有数据了，此时收到 api 发来 peek_message 不会转发给上游，用户会先收到 sim 本身的账户数据，
            #   在下一次 wait_update，sim 的 diffs 为空，才会收到行情数据
            # 在回测时，以下代码应该只经历一次 wait_update
            while margin != self._api.get_position(symbol).get("future_margin"):
                self._api.wait_update()
        return margin

    def get_margin(self, symbol: str):
        """
        获取指定合约模拟交易的每手保证金。

        Args:
            symbol (str): 合约代码

        Returns:
            float: 返回合约模拟交易的每手保证金

        Example::

            from tqsdk import TqSim, TqApi, TqAuth

            sim = TqSim()
            api = TqApi(sim, auth=TqAuth("信易账户", "账户密码"))

            quote = api.get_quote("SHFE.cu2112")
            print(sim.get_margin("SHFE.cu2112"))
        """
        return _get_future_margin(self._data.get("quotes", {}).get(symbol, {}))

    def get_commission(self, symbol: str):
        """
        获取指定合约模拟交易的每手手续费

        Args:
            symbol (str): 合约代码

        Returns:
            float: 返回合约模拟交易的每手手续费

        Example::

            from tqsdk import TqSim, TqApi, TqAuth

            sim = TqSim()
            api = TqApi(sim, auth=TqAuth("信易账户", "账户密码"))

            quote = api.get_quote("SHFE.cu2112")
            print(sim.get_commission("SHFE.cu2112"))
        """
        return _get_commission(self._data.get("quotes", {}).get(symbol, {}))

    async def _run(self, api, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan):
        """模拟交易task"""
        self._api = api
        self._tqsdk_backtest = {}  # 储存可能的回测信息
        self._logger = api._logger.getChild("TqSim")  # 调试信息输出
        self._api_send_chan = api_send_chan
        self._api_recv_chan = api_recv_chan
        self._md_send_chan = md_send_chan
        self._md_recv_chan = md_recv_chan
        self._pending_peek = False
        # True 下游发过 subscribe，但是没有转发给上游；False 表示下游发的 subscribe 都转发给上游
        self._pending_subscribe_downstream = False
        # True 发给上游 subscribe，但是没有收到过回复；False 如果行情不变，上游不会回任何包
        self._pending_subscribe_upstream = False
        self._diffs = []
        self._all_subscribe = set()  # 客户端+模拟交易模块订阅的合约集合
        # 是否已经发送初始账户信息
        self._has_send_init_account = False
        md_task = self._api.create_task(self._md_handler())  # 将所有 md_recv_chan 上收到的包投递到 api_send_chan 上
        try:
            async for pack in self._api_send_chan:
                if "_md_recv" in pack:
                    if pack["aid"] == "rtn_data":
                        self._md_recv(pack)  # md_recv 中会发送 wait_count 个 quotes 包给各个 quote_chan
                        await asyncio.gather(*[quote_task["quote_chan"].join() for quote_task in self._quote_tasks.values()])
                        await self._send_diff()
                elif pack["aid"] == "subscribe_quote":
                    await self._subscribe_quote(set(pack["ins_list"].split(",")))
                elif pack["aid"] == "peek_message":
                    self._pending_peek = True
                    await self._send_diff()
                    if self._pending_peek:  # 控制"peek_message"发送: 当没有新的事件需要用户处理时才推进到下一个行情
                        await self._md_send_chan.send(pack)
                elif pack["aid"] == "insert_order":
                    # 非该账户的消息包发送至下一个账户
                    if pack["account_key"] != self._account_key:
                        await self._md_send_chan.send(pack)
                    else:
                        symbol = pack["exchange_id"] + "." + pack["instrument_id"]
                        if symbol not in self._quote_tasks:
                            quote_chan = TqChan(self._api)
                            order_chan = TqChan(self._api)
                            self._quote_tasks[symbol] = {
                                "quote_chan": quote_chan,
                                "order_chan": order_chan,
                                "task": self._api.create_task(self._quote_handler(symbol, quote_chan, order_chan))
                            }
                        if "account_key" in pack:
                            pack.pop("account_key", None)
                        await self._quote_tasks[symbol]["order_chan"].send(pack)
                elif pack["aid"] == "cancel_order":
                    # 非该账户的消息包发送至下一个账户
                    if pack["account_key"] != self._account_key:
                        await self._md_send_chan.send(pack)
                    else:
                        # 发送至服务器的包需要去除 account_key 信息
                        if "account_key" in pack:
                            pack.pop("account_key", None)
                        # pack 里只有 order_id 信息，发送到每一个合约的 order_chan, 交由 quote_task 判断是不是当前合约下的委托单
                        for symbol in self._quote_tasks:
                            await self._quote_tasks[symbol]["order_chan"].send(pack)
                else:
                    await self._md_send_chan.send(pack)
                if self._tqsdk_backtest != {} and self._tqsdk_backtest["current_dt"] >= self._tqsdk_backtest["end_dt"] \
                        and not self.tqsdk_stat:
                    # 回测情况下，把 _send_stat_report 在循环中回测结束时执行
                    await self._send_stat_report()
        finally:
            if not self.tqsdk_stat:
                await self._send_stat_report()
            md_task.cancel()
            tasks = [md_task]
            for symbol in self._quote_tasks:
                self._quote_tasks[symbol]["task"].cancel()
                tasks.append(self._quote_tasks[symbol]["task"])
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _md_handler(self):
        async for pack in self._md_recv_chan:
            pack["_md_recv"] = True
            self._pending_subscribe_upstream = False
            await self._api_send_chan.send(pack)

    async def _send_diff(self):
        if self._pending_peek:
            if self._diffs:
                rtn_data = {
                    "aid": "rtn_data",
                    "data": self._diffs,
                }
                self._diffs = []
                self._pending_peek = False
                await self._api_recv_chan.send(rtn_data)
            if self._pending_subscribe_downstream:
                self._pending_subscribe_upstream = True
                self._pending_subscribe_downstream = False
                await self._md_send_chan.send({
                    "aid": "subscribe_quote",
                    "ins_list": ",".join(self._all_subscribe)
                })

    async def _subscribe_quote(self, symbols: [set, str]):
        """这里只会增加订阅合约，不会退订合约"""
        symbols = symbols if isinstance(symbols, set) else {symbols}
        if symbols - self._all_subscribe:
            self._all_subscribe |= symbols
            if self._pending_peek and not self._pending_subscribe_upstream:
                self._pending_subscribe_upstream = True
                self._pending_subscribe_downstream = False
                await self._md_send_chan.send({
                    "aid": "subscribe_quote",
                    "ins_list": ",".join(self._all_subscribe)
                })
            else:
                self._pending_subscribe_downstream = True

    async def _send_stat_report(self):
        self._settle()
        self._report()
        await self._api_recv_chan.send({
            "aid": "rtn_data",
            "data": [{
                "trade": {
                    self._account_key: {
                        "accounts": {
                            "CNY": {
                                "_tqsdk_stat": self.tqsdk_stat
                            }
                        }
                    }
                }
            }]
        })

    async def _ensure_quote_info(self, symbol, quote_chan):
        """quote收到合约信息后返回"""
        quote = _get_obj(self._data, ["quotes", symbol], Quote(self._api))
        if quote.get("price_tick") == quote.get("price_tick"):
            return quote.copy()
        if quote.get("price_tick") != quote.get("price_tick"):
            await self._md_send_chan.send(_query_for_quote(symbol))
        async for _ in quote_chan:
            quote_chan.task_done()
            if quote.get("price_tick") == quote.get("price_tick"):
                return quote.copy()

    async def _ensure_quote(self, symbol, quote_chan):
        """quote收到行情以及合约信息后返回"""
        quote = _get_obj(self._data, ["quotes", symbol], Quote(self._api))
        _register_update_chan(quote, quote_chan)
        if quote.get("datetime", "") and quote.get("price_tick") == quote.get("price_tick"):
            return quote.copy()
        if quote.get("price_tick") != quote.get("price_tick"):
            # 对于没有合约信息的 quote，发送查询合约信息的请求
            await self._md_send_chan.send(_query_for_quote(symbol))
        async for _ in quote_chan:
            quote_chan.task_done()
            if quote.get("datetime", "") and quote.get("price_tick") == quote.get("price_tick"):
                return quote.copy()

    async def _quote_handler(self, symbol, quote_chan, order_chan):
        try:
            await self._subscribe_quote(symbol)
            quote = await self._ensure_quote(symbol, quote_chan)
            if quote["ins_class"].endswith("INDEX") and quote["exchange_id"] == "KQ":
                # 指数可以交易，需要补充 margin commission
                if "margin" not in quote:
                    quote_m = await self._ensure_quote_info(symbol.replace("KQ.i", "KQ.m"), quote_chan)
                    quote_underlying = await self._ensure_quote_info(quote_m["underlying_symbol"], quote_chan)
                    self._data["quotes"][symbol]["margin"] = quote_underlying["margin"]
                    self._data["quotes"][symbol]["commission"] = quote_underlying["commission"]
                    quote.update(self._data["quotes"][symbol])
            underlying_quote = None
            if quote["ins_class"].endswith("OPTION"):
                # 如果是期权，订阅标的合约行情，确定收到期权标的合约行情
                underlying_symbol = quote["underlying_symbol"]
                await self._subscribe_quote(underlying_symbol)
                underlying_quote = await self._ensure_quote(underlying_symbol, quote_chan)  # 订阅合约
            # 在等待标的行情的过程中，quote_chan 可能有期权行情，把 quote_chan 清空，并用最新行情更新 quote
            while not quote_chan.empty():
                quote_chan.recv_nowait()
                quote_chan.task_done()

            # 用最新行情更新 quote
            quote.update(self._data["quotes"][symbol])
            if underlying_quote:
                underlying_quote.update(self._data["quotes"][underlying_symbol])
            task = self._api.create_task(self._forward_chan_handler(order_chan, quote_chan))
            quotes = {symbol: quote}
            if underlying_quote:
                quotes[underlying_symbol] = underlying_quote
            self._sim_trade.update_quotes(symbol, {"quotes": quotes})
            async for pack in quote_chan:
                if "aid" not in pack:
                    diffs, orders_events = self._sim_trade.update_quotes(symbol, pack)
                    self._handle_diffs(diffs, orders_events, "match order")
                elif pack["aid"] == "insert_order":
                    diffs, orders_events = self._sim_trade.insert_order(symbol, pack)
                    self._handle_diffs(diffs, orders_events, "insert order")
                    await self._send_diff()
                elif pack["aid"] == "cancel_order":
                    diffs, orders_events = self._sim_trade.cancel_order(symbol, pack)
                    self._handle_diffs(diffs, orders_events, "cancel order")
                    await self._send_diff()
                quote_chan.task_done()
        finally:
            await quote_chan.close()
            await order_chan.close()
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def _forward_chan_handler(self, chan_from, chan_to):
        async for pack in chan_from:
            await chan_to.send(pack)

    def _md_recv(self, pack):
        for d in pack["data"]:
            self._diffs.append(d)
            # 在第一次收到 mdhis_more_data 为 False 的时候，发送账户初始截面信息，这样回测模式下，往后的模块才有正确的时间顺序
            if not self._has_send_init_account and not d.get("mdhis_more_data", True):
                self._diffs.append(self._sim_trade.init_snapshot())
                self._diffs.append({
                    "trade": {
                        self._account_key: {
                            "trade_more_data": False
                        }
                    }
                })
                self._has_send_init_account = True
            _tqsdk_backtest = d.get("_tqsdk_backtest", {})
            if _tqsdk_backtest:
                # 回测时，用 _tqsdk_backtest 对象中 current_dt 作为 TqSim 的 _current_datetime
                self._tqsdk_backtest.update(_tqsdk_backtest)
                self._current_datetime = datetime.fromtimestamp(
                    self._tqsdk_backtest["current_dt"] / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f")
                self._local_time_record = float("nan")
                # 1. 回测时不使用时间差来模拟交易所时间的原因(_local_time_record始终为初始值nan)：
                #   在sim收到行情后记录_local_time_record，然后下发行情到api进行merge_diff(),api需要处理完k线和quote才能结束wait_update(),
                #   若处理时间过长，此时下单则在判断下单时间时与测试用例中的预期时间相差较大，导致测试用例无法通过。
                # 2. 回测不使用时间差的方法来判断下单时间仍是可行的: 与使用了时间差的方法相比, 只对在每个交易时间段最后一笔行情时的下单时间判断有差异,
                #   若不使用时间差, 则在最后一笔行情时下单仍判断为在可交易时间段内, 且可成交.
            quotes_diff = d.get("quotes", {})
            # 先根据 quotes_diff 里的 datetime, 确定出 _current_datetime，再 _merge_diff(同时会发送行情到 quote_chan)
            for symbol, quote_diff in quotes_diff.items():
                if quote_diff is None:
                    continue
                # 若直接使用本地时间来判断下单时间是否在可交易时间段内 可能有较大误差,因此判断的方案为:(在接收到下单指令时判断 估计的交易所时间 是否在交易时间段内)
                # 在更新最新行情时间(即self._current_datetime)时，记录当前本地时间(self._local_time_record)，
                # 在这之后若收到下单指令，则获取当前本地时间,判 "最新行情时间 + (当前本地时间 - 记录的本地时间)" 是否在交易时间段内。
                # 另外, 若在盘后下单且下单前未订阅此合约：
                # 因为从_md_recv()中获取数据后立即判断下单时间则速度过快(两次time.time()的时间差小于最后一笔行情(14:59:9995)到15点的时间差),
                # 则会立即成交,为处理此情况则将当前时间减去5毫秒（模拟发生5毫秒网络延迟，则两次time.time()的时间差增加了5毫秒）。
                # todo: 按交易所来存储 _current_datetime(issue： #277)
                if quote_diff.get("datetime", "") > self._current_datetime:
                    # 回测时，当前时间更新即可以由 quote 行情更新，也可以由 _tqsdk_backtest.current_dt 更新，
                    # 在最外层的循环里，_tqsdk_backtest.current_dt 是在 rtn_data.data 中数组位置中的最后一个，会在循环最后一个才更新 self.current_datetime
                    # 导致前面处理 order 时的 _current_datetime 还是旧的行情时间
                    self._current_datetime = quote_diff["datetime"]  # 最新行情时间
                    # 更新最新行情时间时的本地时间，回测时不使用时间差
                    self._local_time_record = (time.time() - 0.005) if not self._tqsdk_backtest else float("nan")
                if self._current_datetime > self._trading_day_end:  # 结算
                    self._settle()
                    # 若当前行情时间大于交易日的结束时间(切换交易日)，则根据此行情时间更新交易日及交易日结束时间
                    trading_day = _get_trading_day_from_timestamp(self._get_current_timestamp())
                    self._trading_day_end = datetime.fromtimestamp(
                        (_get_trading_day_end_time(trading_day) - 999) / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f")
            if quotes_diff:
                _merge_diff(self._data, {"quotes": quotes_diff}, self._prototype, False, True)

    def _handle_diffs(self, diffs, orders_events, msg):
        """
        处理 sim_trade 返回的 diffs
        orders_events 为持仓变更事件，依次屏幕输出信息，打印日志
        """
        self._diffs += diffs
        for order in orders_events:
            if order["status"] == "FINISHED":
                self._handle_on_finished(msg, order)
            else:
                assert order["status"] == "ALIVE"
                self._handle_on_alive(msg, order)

    def _handle_on_alive(self, msg, order):
        """
        在 order 状态变为 ALIVE 调用，屏幕输出信息，打印日志
        """
        symbol = f"{order['exchange_id']}.{order['instrument_id']}"
        self._api._print(
            f"模拟交易下单 {order['order_id']}: 时间: {_format_from_timestamp_nano(order['insert_date_time'])}, "
            f"合约: {symbol}, 开平: {order['offset']}, 方向: {order['direction']}, 手数: {order['volume_left']}, "
            f"价格: {order.get('limit_price', '市价')}")
        self._logger.debug(msg, order_id=order["order_id"], datetime=order["insert_date_time"],
                           symbol=symbol, offset=order["offset"], direction=order["direction"],
                           volume_left=order["volume_left"], limit_price=order.get("limit_price", "市价"))

    def _handle_on_finished(self, msg, order):
        """
        在 order 状态变为 FINISHED 调用，屏幕输出信息，打印日志
        """
        self._api._print(f"模拟交易委托单 {order['order_id']}: {order['last_msg']}")
        self._logger.debug(msg, order_id=order["order_id"], last_msg=order["last_msg"], status=order["status"],
                           volume_orign=order["volume_orign"], volume_left=order["volume_left"])

    def _settle(self):
        if self._trading_day_end[:10] == "1990-01-01":
            return
        # 结算并记录账户截面
        diffs, orders_events, trade_log = self._sim_trade.settle()
        self._handle_diffs(diffs, orders_events, "settle")
        self.trade_log[self._trading_day_end[:10]] = trade_log

    def _report(self):
        if not self.trade_log:
            return
        date_keys = sorted(self.trade_log.keys())
        self._api._print("模拟交易成交记录")
        for d in date_keys:
            for t in self.trade_log[d]["trades"]:
                symbol = t["exchange_id"] + "." + t["instrument_id"]
                self._api._print(f"时间: {_format_from_timestamp_nano(t['trade_date_time'])}, 合约: {symbol}, "
                                 f"开平: {t['offset']}, 方向: {t['direction']}, 手数: {t['volume']}, 价格: {t['price']:.3f},"
                                 f"手续费: {t['commission']:.2f}")

        self._api._print("模拟交易账户资金")
        for d in date_keys:
            account = self.trade_log[d]["account"]
            self._api._print(
                f"日期: {d}, 账户权益: {account['balance']:.2f}, 可用资金: {account['available']:.2f}, "
                f"浮动盈亏: {account['float_profit']:.2f}, 持仓盈亏: {account['position_profit']:.2f}, "
                f"平仓盈亏: {account['close_profit']:.2f}, 市值: {account['market_value']:.2f}, "
                f"保证金: {account['margin']:.2f}, 手续费: {account['commission']:.2f}, "
                f"风险度: {account['risk_ratio'] * 100:.2f}%")

        # TqReport 模块计算交易统计信息
        report = TqReport(report_id=self._account_id, trade_log=self.trade_log, quotes=self._data['quotes'])
        self.tqsdk_stat = report.default_metrics
        self._api._print(
            f"胜率: {self.tqsdk_stat['winning_rate'] * 100:.2f}%, 盈亏额比例: {self.tqsdk_stat['profit_loss_ratio']:.2f}, "
            f"收益率: {self.tqsdk_stat['ror'] * 100:.2f}%, 年化收益率: {self.tqsdk_stat['annual_yield'] * 100:.2f}%, "
            f"最大回撤: {self.tqsdk_stat['max_drawdown'] * 100:.2f}%, 年化夏普率: {self.tqsdk_stat['sharpe_ratio']:.4f},"
            f"年化索提诺比率: {self.tqsdk_stat['sortino_ratio']:.4f}")

        # 回测情况下，在计算报告之后，还会发送绘制图表请求，
        # 这样处理，用户不要修改代码，就能够看到报告图表
        if self._tqsdk_backtest:
            self._api.draw_report(report.full())

    def _get_current_timestamp(self):
        return int(datetime.strptime(self._current_datetime, "%Y-%m-%d %H:%M:%S.%f").timestamp() * 1e6) * 1000

    def _get_trade_timestamp(self):
        return _get_trade_timestamp(self._current_datetime, self._local_time_record)

    def _is_in_trading_time(self, quote):
        return _is_in_trading_time(quote, self._current_datetime, self._local_time_record)
