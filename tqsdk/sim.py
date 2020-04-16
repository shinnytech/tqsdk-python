#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import asyncio
import datetime
import statistics
import time

from tqsdk.datetime import _get_trading_day_end_time, _get_trading_day_from_timestamp, _get_trading_day_start_time


class TqSim(object):
    """
    天勤模拟交易类

    该类实现了一个本地的模拟账户，并且在内部完成撮合交易，在回测和复盘模式下，只能使用 TqSim 账户来交易。

    限价单要求报单价格达到或超过对手盘价格才能成交, 成交价为报单价格, 如果没有对手盘(涨跌停)则无法成交

    市价单使用对手盘价格成交, 如果没有对手盘(涨跌停)则自动撤单

    模拟交易不会有部分成交的情况, 要成交就是全部成交
    """

    def __init__(self, init_balance: float = 10000000.0, account_id: str = "TQSIM") -> None:
        """
        Args:
            init_balance (float): [可选]初始资金, 默认为一千万

            account_id (str): [可选]帐号, 默认为 "TQSIM"

        Example::

            # 修改TqSim模拟帐号的初始资金为100000
            from tqsdk import TqApi, TqSim
            api = TqApi(TqSim(init_balance=100000))

        """
        self.trade_log = {}  # 日期->交易记录及收盘时的权益及持仓
        self._account_id = account_id
        self._init_balance = float(init_balance)
        if self._init_balance <= 0:
            raise Exception("初始资金(init_balance) %s 错误, 请检查 init_balance 是否填写正确" % (init_balance))
        self._current_datetime = "1990-01-01 00:00:00.000000"  # 当前行情时间（最新的 quote 时间）
        self._trading_day_end = "1990-01-01 18:00:00.000000"
        self._local_time_record = float("nan")  # 记录获取最新行情时的本地时间

    async def _run(self, api, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan):
        """模拟交易task"""
        self._api = api
        self._tqsdk_backtest = {}  # 储存可能的回测信息
        self._tqsdk_stat = {}  # 回测结束后储存回测报告信息
        self._logger = api._logger.getChild("TqSim")  # 调试信息输出
        self._api_send_chan = api_send_chan
        self._api_recv_chan = api_recv_chan
        self._md_send_chan = md_send_chan
        self._md_recv_chan = md_recv_chan
        self._pending_peek = False
        self._diffs = []
        self._account = {
            "currency": "CNY",
            "pre_balance": self._init_balance,
            "static_balance": self._init_balance,
            "balance": self._init_balance,
            "available": self._init_balance,
            "float_profit": 0.0,
            "position_profit": 0.0,  # 期权没有持仓盈亏
            "close_profit": 0.0,
            "frozen_margin": 0.0,
            "margin": 0.0,
            "frozen_commission": 0.0,
            "commission": 0.0,
            "frozen_premium": 0.0,
            "premium": 0.0,
            "deposit": 0.0,
            "withdraw": 0.0,
            "risk_ratio": 0.0,
            "market_value": 0.0,
            "ctp_balance": float("nan"),
            "ctp_available": float("nan"),
        }
        self._positions = {}
        self._orders = {}
        self._quotes = {}  # 记下最新行情
        self._client_subscribe = set()  # 客户端订阅的合约集合
        self._all_subscribe = set()  # 客户端+模拟交易模块订阅的合约集合
        # 是否已经发送初始账户信息
        self._has_send_init_account = False
        md_task = self._api.create_task(self._md_handler())  # 将所有 md_recv_chan 上收到的包投递到 api_send_chan 上
        try:
            async for pack in self._api_send_chan:
                self._logger.debug("TqSim message received: %s", pack)
                if "_md_recv" in pack:
                    if pack["aid"] == "rtn_data":
                        self._md_recv(pack)
                        await self._send_diff()
                elif pack["aid"] == "subscribe_quote":
                    self._client_subscribe = set(pack["ins_list"].split(","))
                    await self._subscribe_quote()
                elif pack["aid"] == "peek_message":
                    self._pending_peek = True
                    await self._send_diff()
                    if self._pending_peek:  # 控制"peek_message"发送: 当没有新的事件需要用户处理时才推进到下一个行情
                        await self._md_send_chan.send(pack)
                elif pack["aid"] == "insert_order":
                    self._insert_order(pack)
                    symbol = pack["exchange_id"] + "." + pack["instrument_id"]
                    if symbol not in self._all_subscribe or (
                            self._quotes[symbol]["ins_class"] in ["OPTION", "FUTURE_OPTION"] and self._quotes[symbol][
                        "underlying_symbol"] not in self._all_subscribe):
                        await self._subscribe_quote()
                    await self._send_diff()
                elif pack["aid"] == "cancel_order":
                    self._cancel_order(pack)
                    await self._send_diff()
                else:
                    await self._md_send_chan.send(pack)
                if self._tqsdk_backtest != {} and self._tqsdk_backtest["current_dt"] >= self._tqsdk_backtest["end_dt"] \
                        and not self._tqsdk_stat:
                    # 回测情况下，把 _send_stat_report 在循环中回测结束时执行
                    await self._send_stat_report()
        finally:
            if not self._tqsdk_stat:
                await self._send_stat_report()
            md_task.cancel()
            await asyncio.gather(md_task, return_exceptions=True)

    async def _md_handler(self):
        async for pack in self._md_recv_chan:
            pack["_md_recv"] = True
            await self._api_send_chan.send(pack)

    async def _send_diff(self):
        if self._pending_peek and self._diffs:
            rtn_data = {
                "aid": "rtn_data",
                "data": self._diffs,
            }
            self._diffs = []
            self._pending_peek = False
            self._logger.debug("TqSim message send: %s", rtn_data)
            await self._api_recv_chan.send(rtn_data)

    async def _subscribe_quote(self):
        underlying_symbol_list = set()
        for o in self._orders.values():
            if self._quotes[o["exchange_id"] + "." + o["instrument_id"]]["ins_class"] in ["OPTION", "FUTURE_OPTION"]:
                underlying_symbol_list.add(
                    self._quotes[o["exchange_id"] + "." + o["instrument_id"]]["underlying_symbol"])
        self._all_subscribe = self._client_subscribe | {o["exchange_id"] + "." + o["instrument_id"] for o in
                                                        self._orders.values()} | self._positions.keys() | underlying_symbol_list
        await self._md_send_chan.send({
            "aid": "subscribe_quote",
            "ins_list": ",".join(self._all_subscribe)
        })

    async def _send_stat_report(self):
        self._settle()
        self._report()
        await self._api_recv_chan.send({
            "aid": "rtn_data",
            "data": [{
                "trade": {
                    self._account_id: {
                        "accounts": {
                            "CNY": {
                                "_tqsdk_stat": self._tqsdk_stat
                            }
                        }
                    }
                }
            }]
        })

    def _md_recv(self, pack):
        for d in pack["data"]:
            d.pop("trade", None)
            self._diffs.append(d)

            # 在第一次收到 mdhis_more_data 为 False 的时候，发送账户初始截面信息，这样回测模式下，往后的模块才有正确的时间顺序
            if not self._has_send_init_account and not d.get("mdhis_more_data", True):
                self._send_account()
                self._diffs.append({
                    "trade": {
                        self._account_id: {
                            "orders": {},
                            "positions": {},
                            "trade_more_data": False
                        }
                    }
                })
                self._has_send_init_account = True
            _tqsdk_backtest = d.get("_tqsdk_backtest", {})
            if _tqsdk_backtest:
                # 回测时，用 _tqsdk_backtest 对象中 current_dt 作为 TqSim 的 _current_datetime
                self._tqsdk_backtest.update(_tqsdk_backtest)
                self._current_datetime = datetime.datetime.fromtimestamp(
                    self._tqsdk_backtest["current_dt"] / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f")
                self._local_time_record = float("nan")
                # 1. 回测时不使用时间差来模拟交易所时间的原因(_local_time_record始终为初始值nan)：
                #   在sim收到行情后记录_local_time_record，然后下发行情到api进行merge_diff(),api需要处理完k线和quote才能结束wait_update(),
                #   若处理时间过长，此时下单则在判断下单时间时与测试用例中的预期时间相差较大，导致测试用例无法通过。
                # 2. 回测不使用时间差的方法来判断下单时间仍是可行的: 与使用了时间差的方法相比, 只对在每个交易时间段最后一笔行情时的下单时间判断有差异,
                #   若不使用时间差, 则在最后一笔行情时下单仍判断为在可交易时间段内, 且可成交.
            for symbol, quote_diff in d.get("quotes", {}).items():
                if quote_diff is None:
                    continue
                quote = self._ensure_quote(symbol)

                # 在第一次接收到期权的标的行情后，对此期权合约match_orders()，避免因下一笔行情一直未收到而无法处理其order信息
                quote_list = []  # 记录以本quote为标的的期权合约
                if not quote["datetime"] and quote_diff.get("datetime"):  # 第一次收到行情
                    for q in self._quotes.values():
                        if q["datetime"] != "" and q["underlying_symbol"] == symbol and q["ins_class"] in ["OPTION",
                                                                                                           "FUTURE_OPTION"]:
                            quote_list.append(q)
                quote["datetime"] = quote_diff.get("datetime", quote["datetime"])
                # 若直接使用本地时间来判断下单时间是否在可交易时间段内 可能有较大误差,因此判断的方案为:(在接收到下单指令时判断 估计的交易所时间 是否在交易时间段内)
                # 在更新最新行情时间(即self._current_datetime)时，记录当前本地时间(self._local_time_record)，
                # 在这之后若收到下单指令，则获取当前本地时间,判 "最新行情时间 + (当前本地时间 - 记录的本地时间)" 是否在交易时间段内。
                # 另外, 若在盘后下单且下单前未订阅此合约：
                # 因为从_md_recv()中获取数据后立即判断下单时间则速度过快(两次time.time()的时间差小于最后一笔行情(14:59:9995)到15点的时间差),
                # 则会立即成交,为处理此情况则将当前时间减去5毫秒（模拟发生5毫秒网络延迟，则两次time.time()的时间差增加了5毫秒）。
                # todo: 按交易所来存储 _current_datetime(issue： #277)
                if quote["datetime"] > self._current_datetime and not self._tqsdk_backtest:
                    self._current_datetime = quote["datetime"]  # 最新行情时间
                    self._local_time_record = time.time() - 0.005  # 更新最新行情时间时的本地时间

                if self._current_datetime > self._trading_day_end:  # 结算
                    self._settle()
                    # 若当前行情时间大于交易日的结束时间(切换交易日)，则根据此行情时间更新交易日及交易日结束时间
                    trading_day = _get_trading_day_from_timestamp(self._get_current_timestamp())
                    self._trading_day_end = datetime.datetime.fromtimestamp(
                        (_get_trading_day_end_time(trading_day) - 999) / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f")
                if "ask_price1" in quote_diff:
                    quote["ask_price1"] = float("nan") if type(quote_diff["ask_price1"]) is str else quote_diff[
                        "ask_price1"]
                if "bid_price1" in quote_diff:
                    quote["bid_price1"] = float("nan") if type(quote_diff["bid_price1"]) is str else quote_diff[
                        "bid_price1"]
                if "last_price" in quote_diff:
                    quote["last_price"] = float("nan") if type(quote_diff["last_price"]) is str else quote_diff[
                        "last_price"]
                quote["volume_multiple"] = quote_diff.get("volume_multiple", quote["volume_multiple"])
                quote["commission"] = quote_diff.get("commission", quote["commission"])
                quote["margin"] = quote_diff.get("margin", quote["margin"])
                quote["trading_time"] = quote_diff.get("trading_time", quote["trading_time"])
                quote["ins_class"] = quote_diff.get("ins_class", quote["ins_class"])
                quote["option_class"] = quote_diff.get("option_class", quote["option_class"])
                quote["underlying_symbol"] = quote_diff.get("underlying_symbol", quote["underlying_symbol"])
                quote["strike_price"] = quote_diff.get("strike_price", quote["strike_price"])
                self._match_orders(quote)
                for q in quote_list:
                    self._match_orders(q)
                if symbol in self._positions:
                    self._adjust_position(symbol, price=quote["last_price"])

    @staticmethod
    def _get_trading_timestamp(quote, current_datetime: str):
        """ 将 quote 在 current_datetime 所在交易日的所有可交易时间段转换为纳秒时间戳(tqsdk内部使用的时间戳统一为纳秒)并返回 """
        # 获取当前交易日时间戳
        current_trading_day_timestamp = _get_trading_day_from_timestamp(
            int(datetime.datetime.strptime(current_datetime, "%Y-%m-%d %H:%M:%S.%f").timestamp() * 1e6) * 1000)
        # 获取上一交易日时间戳
        last_trading_day_timestamp = _get_trading_day_from_timestamp(
            _get_trading_day_start_time(current_trading_day_timestamp) - 1)
        trading_timestamp = {
            "day": TqSim._get_period_timestamp(current_trading_day_timestamp, quote["trading_time"].get("day", [])),
            "night": TqSim._get_period_timestamp(last_trading_day_timestamp, quote["trading_time"].get("night", []))
        }
        return trading_timestamp

    @staticmethod
    def _get_period_timestamp(real_date_timestamp, period_str):
        """
        real_date_timestamp：period_str 所在真实日期的纳秒时间戳（如 period_str 为周一(周二)的夜盘,则real_date_timestamp为上周五(周一)的日期; period_str 为周一的白盘,则real_date_timestamp为周一的日期）
        period_str: quote["trading_time"]["day"] or quote["trading_time"]["night"]
        """
        period_timestamp = []
        for duration in period_str:  # 对于白盘（或夜盘）中的每一个可交易时间段
            start = [int(i) for i in duration[0].split(":")]  # 交易时间段起始点
            end = [int(i) for i in duration[1].split(":")]  # 交易时间段结束点
            period_timestamp.append([real_date_timestamp + (start[0] * 3600 + start[1] * 60 + start[2]) * 1000000000,
                                     real_date_timestamp + (end[0] * 3600 + end[1] * 60 + end[2]) * 1000000000])
        return period_timestamp

    def _insert_order(self, order):
        symbol = order["exchange_id"] + "." + order["instrument_id"]
        order["exchange_order_id"] = order["order_id"]
        order["volume_orign"] = order["volume"]
        order["volume_left"] = order["volume"]
        order["frozen_margin"] = 0.0
        order["frozen_premium"] = 0.0
        order["last_msg"] = "报单成功"
        order["status"] = "ALIVE"
        # order 的 insert_date_time 携带flag信息, <0:未收到行情但需要撤单，==0:未收到行情需撮合，>0:收到行情需撮合
        order["insert_date_time"] = 0  # 初始化为0：保持 order 的结构不变(所有字段都有，只是值不同)
        del order["aid"]
        del order["volume"]
        quote = self._ensure_quote(symbol)
        quote["orders"][order["order_id"]] = order  # 将挂单存入 self._quote 中对应 symbol 下 (挂单处理结束则从中删除)
        self._orders[order["order_id"]] = order
        self._match_order(quote, order)

    @staticmethod
    def _is_in_trading_time(quote, current_datetime, local_time_record):
        """ 判断是否在可交易时间段内，需在quote已收到行情后调用本函数"""
        # 只在需要用到可交易时间段时(即本函数中)才调用_get_trading_timestamp()
        trading_timestamp = TqSim._get_trading_timestamp(quote, current_datetime)
        now_ns_timestamp = TqSim._get_trade_timestamp(current_datetime, local_time_record)  # 当前预估交易所纳秒时间戳
        # 判断当前交易所时间（估计值）是否在交易时间段内
        for v in trading_timestamp.values():
            for period in v:
                if now_ns_timestamp >= period[0] and now_ns_timestamp < period[1]:
                    return True
        return False

    def _cancel_order(self, pack):
        if self._orders[pack["order_id"]]["insert_date_time"] <= 0:  # 如果未收到行情或已经发过撤单指令
            self._orders[pack["order_id"]]["insert_date_time"] = -1
            return
        if pack["order_id"] in self._orders:
            self._del_order(self._orders[pack["order_id"]], "已撤单")

    def _del_order(self, order, msg):
        symbol = order["exchange_id"] + "." + order["instrument_id"]
        self._logger.info("模拟交易委托单 %s: %s", order["order_id"], msg)
        if order["offset"].startswith("CLOSE"):
            volume_long_frozen = 0 if order["direction"] == "BUY" else -order["volume_left"]
            volume_short_frozen = 0 if order["direction"] == "SELL" else -order["volume_left"]
            if order["exchange_id"] == "SHFE" or order["exchange_id"] == "INE":
                priority = "H" if order["offset"] == "CLOSE" else "T"
            else:
                priority = "HT"
            self._adjust_position(symbol, volume_long_frozen=volume_long_frozen,
                                  volume_short_frozen=volume_short_frozen, priority=priority)
        else:
            self._adjust_account(frozen_margin=-order["frozen_margin"], frozen_premium=-order["frozen_premium"])
            order["frozen_margin"] = 0.0
            order["frozen_premium"] = 0.0
        order["last_msg"] = msg
        order["status"] = "FINISHED"
        self._send_order(order)
        del self._orders[order["order_id"]]
        del self._quotes[symbol]["orders"][order["order_id"]]  # 挂单处理结束，将其删除

    def _match_orders(self, quote):
        for order in list(quote["orders"].values()):
            self._match_order(quote, order)

    def _match_order(self, quote, order):
        underlying_quote = self._ensure_quote(quote["underlying_symbol"])
        # 如果未收到行情，不处理
        if quote["datetime"] == "" or (
                quote["ins_class"] in ["OPTION", "FUTURE_OPTION"] and underlying_quote["datetime"] == ""):
            return
        symbol = order["exchange_id"] + "." + order["instrument_id"]

        cancel_order_flag = False  # 是否需要在不能成交的时候撤掉该委托单，适用于连着发下单和撤单指令时
        if order["insert_date_time"] <= 0:  # 此字段已在_insert_order()初始化为0，或在cancel_order置为-1
            # order初始化时计算期权的frozen_margin需要使用行情数据，因此等待收到行情后再调整初始化字段的方案：
            # 在_insert_order()只把order存在quote下的orders字典中，然后在match_order()判断收到行情后从根据insert_order_time来判断此委托单是否已初始化.
            if order["offset"].startswith("CLOSE"):
                volume_long_frozen = 0 if order["direction"] == "BUY" else order["volume_left"]
                volume_short_frozen = 0 if order["direction"] == "SELL" else order["volume_left"]
                if order["exchange_id"] == "SHFE" or order["exchange_id"] == "INE":
                    priority = "H" if order["offset"] == "CLOSE" else "T"
                else:
                    priority = "TH"
                if not self._adjust_position(symbol, volume_long_frozen=volume_long_frozen,
                                             volume_short_frozen=volume_short_frozen, priority=priority):
                    self._del_order(order, "平仓手数不足")
                    return
            else:
                if (quote["commission"] is None or quote["margin"] is None) and quote["ins_class"] not in ["OPTION",
                                                                                                           "FUTURE_OPTION"]:
                    self._del_order(order, "合约不存在")  # 除了期权外，主连、指数和组合没有这两个字段
                    return
                if quote["ins_class"] in ["OPTION", "FUTURE_OPTION"]:
                    if order["price_type"] == "ANY" and order["exchange_id"] != "CZCE":
                        self._del_order(order, "此交易所（" + order["exchange_id"] + ")不支持期权市价单")
                        return
                    elif order["direction"] == "SELL":  # 期权的SELL义务仓
                        if quote["option_class"] == "CALL":
                            # 认购期权义务仓开仓保证金＝[合约最新价 + Max（12% × 合约标的最新价 - 认购期权虚值， 7% × 合约标的前收盘价）] × 合约单位
                            # 认购期权虚值＝Max（行权价 - 合约标的前收盘价，0）；
                            order["frozen_margin"] = (quote["last_price"] + max(
                                0.12 * underlying_quote["last_price"] - max(
                                    quote["strike_price"] - underlying_quote["last_price"], 0),
                                0.07 * underlying_quote["last_price"])) * quote["volume_multiple"]
                        else:
                            # 认沽期权义务仓开仓保证金＝Min[合约最新价+ Max（12% × 合约标的前收盘价 - 认沽期权虚值，7%×行权价），行权价] × 合约单位
                            # 认沽期权虚值＝Max（合约标的前收盘价 - 行权价，0）
                            order["frozen_margin"] = min(quote["last_price"] + max(
                                0.12 * underlying_quote["last_price"] - max(
                                    underlying_quote["last_price"] - quote["strike_price"], 0),
                                0.07 * quote["strike_price"]), quote["strike_price"]) * quote["volume_multiple"]
                    elif order["price_type"] != "ANY":  # 期权的BUY权利仓（市价单立即成交且没有limit_price字段,frozen_premium默认为0）
                        order["frozen_premium"] = order["volume_orign"] * quote["volume_multiple"] * order[
                            "limit_price"]
                else:  # 期货
                    # 市价单立即成交或不成, 对api来说普通市价单没有 冻结_xxx 数据存在的状态
                    order["frozen_margin"] = quote["margin"] * order["volume_orign"]
                if not self._adjust_account(frozen_margin=order["frozen_margin"],
                                            frozen_premium=order["frozen_premium"]):
                    self._del_order(order, "开仓资金不足")
                    return

            # 需在收到quote行情时, 才将其order的diff下发并将“模拟交易下单”logger发出（即可保证order的insert_date_time为正确的行情时间）
            # 方案为：通过在 match_order() 中判断 “inster_datetime” 来处理：
            # 则能判断收到了行情，又根据 “inster_datetime” 判断了是下单后还未处理（即diff下发和生成logger info）过的order.
            if order["insert_date_time"] == -1:  # 如果等待撤单
                cancel_order_flag = True
            order["insert_date_time"] = TqSim._get_trade_timestamp(self._current_datetime, self._local_time_record)
            self._send_order(order)
            self._logger.info("模拟交易下单 %s: 时间:%s,合约:%s,开平:%s,方向:%s,手数:%s,价格:%s", order["order_id"],
                              datetime.datetime.fromtimestamp(order["insert_date_time"] / 1e9).strftime(
                                  "%Y-%m-%d %H:%M:%S.%f"), symbol, order["offset"], order["direction"],
                              order["volume_left"], order.get("limit_price", "市价"))
            if not TqSim._is_in_trading_time(quote, self._current_datetime, self._local_time_record):
                self._del_order(order, "下单失败, 不在可交易时间段内")
                return

        ask_price = quote["ask_price1"]
        bid_price = quote["bid_price1"]
        if "limit_price" not in order:
            price = ask_price if order["direction"] == "BUY" else bid_price
            if price != price:
                self._del_order(order, "市价指令剩余撤销")
                return
        elif order["direction"] == "BUY" and order["limit_price"] >= ask_price:
            price = order["limit_price"]
        elif order["direction"] == "SELL" and order["limit_price"] <= bid_price:
            price = order["limit_price"]
        elif cancel_order_flag:
            self._del_order(order, "已撤单")
            return
        else:
            return
        trade = {
            "user_id": order["user_id"],
            "order_id": order["order_id"],
            "trade_id": order["order_id"] + "|" + str(order["volume_left"]),
            "exchange_trade_id": order["order_id"] + "|" + str(order["volume_left"]),
            "exchange_id": order["exchange_id"],
            "instrument_id": order["instrument_id"],
            "direction": order["direction"],
            "offset": order["offset"],
            "price": price,
            "volume": order["volume_left"],
            # todo: 可能导致测试结果不确定
            "trade_date_time": TqSim._get_trade_timestamp(self._current_datetime, self._local_time_record),
            # 期权quote没有commission字段, 设为固定10元一张
            "commission": (quote["commission"] if quote["ins_class"] not in ["OPTION", "FUTURE_OPTION"] else 10) *
                          order["volume_left"],
        }
        trade_log = self._ensure_trade_log()
        trade_log["trades"].append(trade)
        self._diffs.append({
            "trade": {
                self._account_id: {
                    "trades": {
                        trade["trade_id"]: trade.copy()
                    }
                }
            }
        })
        if order["exchange_id"] == "SHFE" or order["exchange_id"] == "INE":
            priority = "H" if order["offset"] == "CLOSE" else "T"
        else:
            priority = "TH"
        if order["offset"].startswith("CLOSE"):
            volume_long = 0 if order["direction"] == "BUY" else -order["volume_left"]
            volume_short = 0 if order["direction"] == "SELL" else -order["volume_left"]
            self._adjust_position(symbol, volume_long_frozen=volume_long, volume_short_frozen=volume_short,
                                  priority=priority)
        else:
            volume_long = 0 if order["direction"] == "SELL" else order["volume_left"]
            volume_short = 0 if order["direction"] == "BUY" else order["volume_left"]
        self._adjust_position(symbol, volume_long=volume_long, volume_short=volume_short, price=price,
                              priority=priority)
        premium = -order["frozen_premium"] if order["direction"] == "BUY" else order["frozen_premium"]
        self._adjust_account(commission=trade["commission"], premium=premium)
        order["volume_left"] = 0
        self._del_order(order, "全部成交")

    def _settle(self):
        if self._trading_day_end[:10] == "1990-01-01":
            return
        trade_log = self._ensure_trade_log()
        # 撤销所有委托单
        for order in list(self._orders.values()):
            # 在结算时只删除已有行情的order(它们已下单成功);
            # 因为调用settle()一定是某合约的行情已经到了第二个交易日; 在settle()后才收到第一笔行情的 order 再判断是否在可交易时间段或成交/撤单
            if order["insert_date_time"] > 0:
                self._del_order(order, "交易日结束，自动撤销当日有效的委托单（GFD）")
        # 记录账户截面
        trade_log["account"] = self._account.copy()
        trade_log["positions"] = {k: v.copy() for k, v in self._positions.items()}
        # 为下一交易日调整账户
        self._account["pre_balance"] = self._account["balance"]
        self._account["static_balance"] = self._account["balance"]
        self._account["position_profit"] = 0
        self._account["close_profit"] = 0
        self._account["commission"] = 0
        self._account["premium"] = 0
        self._send_account()
        self._adjust_account()
        for symbol, position in self._positions.items():
            position["pos_long_his"] = position["volume_long"]
            position["pos_long_today"] = 0
            position["pos_short_his"] = position["volume_short"]
            position["pos_short_today"] = 0
            position["volume_long_today"] = 0
            position["volume_long_his"] = position["volume_long"]
            position["volume_short_today"] = 0
            position["volume_short_his"] = position["volume_short"]
            position["position_price_long"] = position["last_price"]
            position["position_price_short"] = position["last_price"]
            position["position_cost_long"] = position["open_cost_long"] + position["float_profit_long"]
            position["position_cost_short"] = position["open_cost_short"] + position["float_profit_short"]
            position["position_profit_long"] = 0
            position["position_profit_short"] = 0
            position["position_profit"] = 0
            self._send_position(position)

    def _report(self):
        if not self.trade_log:
            return
        self._tqsdk_stat["init_balance"] = self._init_balance  # 起始资金
        self._tqsdk_stat["balance"] = self._account["balance"]  # 结束资金
        self._tqsdk_stat["max_drawdown"] = 0  # 最大回撤
        max_balance = 0
        daily_yield = []
        self._logger.warning("模拟交易成交记录")
        # 胜率 盈亏额比例
        trades_logs = {}
        profit_logs = []  # 盈利记录
        loss_logs = []  # 亏损记录
        for d in sorted(self.trade_log.keys()):
            balance = self.trade_log[d]["account"]["balance"]
            if balance > max_balance:
                max_balance = balance
            drawdown = (max_balance - balance) / max_balance
            if drawdown > self._tqsdk_stat["max_drawdown"]:
                self._tqsdk_stat["max_drawdown"] = drawdown
            daily_yield.append(
                self.trade_log[d]["account"]["balance"] / self.trade_log[d]["account"]["pre_balance"] - 1)
            for t in self.trade_log[d]["trades"]:
                symbol = t["exchange_id"] + "." + t["instrument_id"]
                self._logger.warning("时间:%s,合约:%s,开平:%s,方向:%s,手数:%d,价格:%.3f,手续费:%.2f",
                                     datetime.datetime.fromtimestamp(t["trade_date_time"] / 1e9).strftime(
                                         "%Y-%m-%d %H:%M:%S.%f"), symbol, t["offset"], t["direction"], t["volume"],
                                     t["price"], t["commission"])
                if symbol not in trades_logs:
                    trades_logs[symbol] = {
                        "BUY": [],
                        "SELL": [],
                    }
                if t["offset"] == "OPEN":
                    trades_logs[symbol][t["direction"]].append({
                        "volume": t["volume"],
                        "price": t["price"]
                    })
                else:
                    opposite_dir = "BUY" if t["direction"] == "SELL" else "SELL"
                    opposite_list = trades_logs[symbol][opposite_dir]
                    cur_close_volume = t["volume"]
                    cur_close_price = t["price"]
                    cur_close_dir = 1 if t["direction"] == "SELL" else -1
                    while cur_close_volume > 0 and opposite_list[0]:
                        volume = min(cur_close_volume, opposite_list[0]["volume"])
                        profit = (cur_close_price - opposite_list[0]["price"]) * cur_close_dir
                        if profit >= 0:
                            profit_logs.append({
                                "symbol": symbol,
                                "profit": profit,
                                "volume": volume
                            })
                        else:
                            loss_logs.append({
                                "symbol": symbol,
                                "profit": profit,
                                "volume": volume
                            })
                        cur_close_volume -= volume
                        opposite_list[0]["volume"] -= volume
                        if opposite_list[0]["volume"] == 0:
                            opposite_list.pop(0)

        self._tqsdk_stat["profit_volumes"] = sum(p["volume"] for p in profit_logs)  # 盈利手数
        self._tqsdk_stat["loss_volumes"] = sum(l["volume"] for l in loss_logs)  # 亏损手数
        self._tqsdk_stat["profit_value"] = sum(
            p["profit"] * p["volume"] * self._quotes[p["symbol"]]["volume_multiple"] for p in profit_logs)  # 盈利额
        self._tqsdk_stat["loss_value"] = sum(
            l["profit"] * l["volume"] * self._quotes[l["symbol"]]["volume_multiple"] for l in loss_logs)  # 亏损额

        mean = statistics.mean(daily_yield)
        rf = 0.0001
        stddev = statistics.pstdev(daily_yield, mu=mean)
        self._tqsdk_stat["sharpe_ratio"] = 250 ** (1 / 2) * (mean - rf) / stddev if stddev else float("inf")  # 年化夏普率

        _ror = self._tqsdk_stat["balance"] / self._tqsdk_stat["init_balance"]
        self._tqsdk_stat["ror"] = _ror - 1  # 收益率
        self._tqsdk_stat["annual_yield"] = _ror ** (250 / len(self.trade_log)) - 1  # 年化收益率

        self._logger.warning("模拟交易账户资金")
        for d in sorted(self.trade_log.keys()):
            account = self.trade_log[d]["account"]
            self._logger.warning(
                "日期:%s,账户权益:%.2f,可用资金:%.2f,浮动盈亏:%.2f,持仓盈亏:%.2f,平仓盈亏:%.2f,市值:%.2f,保证金:%.2f,手续费:%.2f,风险度:%.2f%%",
                d, account["balance"], account["available"], account["float_profit"], account["position_profit"],
                account["close_profit"], account["market_value"], account["margin"], account["commission"],
                account["risk_ratio"] * 100)

        self._tqsdk_stat["winning_rate"] = (self._tqsdk_stat["profit_volumes"] / (
                self._tqsdk_stat["profit_volumes"] + self._tqsdk_stat["loss_volumes"])) \
            if self._tqsdk_stat["profit_volumes"] + self._tqsdk_stat["loss_volumes"] else 0
        profit_pre_volume = self._tqsdk_stat["profit_value"] / self._tqsdk_stat["profit_volumes"] if self._tqsdk_stat[
            "profit_volumes"] else 0
        loss_pre_volume = self._tqsdk_stat["loss_value"] / self._tqsdk_stat["loss_volumes"] if self._tqsdk_stat[
            "loss_volumes"] else 0
        self._tqsdk_stat["profit_loss_ratio"] = abs(profit_pre_volume / loss_pre_volume) if loss_pre_volume else float(
            "inf")
        self._logger.warning("胜率:%.2f%%,盈亏额比例:%.2f,收益率:%.2f%%,年化收益率:%.2f%%,最大回撤:%.2f%%,年化夏普率:%.4f",
                             self._tqsdk_stat["winning_rate"] * 100,
                             self._tqsdk_stat["profit_loss_ratio"],
                             self._tqsdk_stat["ror"] * 100,
                             self._tqsdk_stat["annual_yield"] * 100,
                             self._tqsdk_stat["max_drawdown"] * 100,
                             self._tqsdk_stat["sharpe_ratio"])

    def _ensure_trade_log(self):
        return self.trade_log.setdefault(self._trading_day_end[:10], {
            "trades": []
        })

    def _adjust_position(self, symbol, volume_long_frozen=0, volume_short_frozen=0, volume_long=0, volume_short=0,
                         price=None, priority=None):
        quote = self._quotes[symbol]
        underlying_quote = self._quotes[quote["underlying_symbol"]]
        position = self._ensure_position(symbol)
        volume_multiple = self._quotes[symbol]["volume_multiple"]
        if volume_long_frozen:
            position["volume_long_frozen"] += volume_long_frozen
            if priority[0] == "T":
                position["volume_long_frozen_today"] += volume_long_frozen
                if len(priority) > 1:
                    if position["volume_long_frozen_today"] < 0:
                        position["volume_long_frozen_his"] += position["volume_long_frozen_today"]
                        position["volume_long_frozen_today"] = 0
                    elif position["volume_long_today"] < position["volume_long_frozen_today"]:
                        position["volume_long_frozen_his"] += position["volume_long_frozen_today"] - position[
                            "volume_long_today"]
                        position["volume_long_frozen_today"] = position["volume_long_today"]
            else:
                position["volume_long_frozen_his"] += volume_long_frozen
                if len(priority) > 1:
                    if position["volume_long_frozen_his"] < 0:
                        position["volume_long_frozen_today"] += position["volume_long_frozen_his"]
                        position["volume_long_frozen_his"] = 0
                    elif position["volume_long_his"] < position["volume_long_frozen_his"]:
                        position["volume_long_frozen_today"] += position["volume_long_frozen_his"] - position[
                            "volume_long_his"]
                        position["volume_long_frozen_his"] = position["volume_long_his"]
        if volume_short_frozen:
            position["volume_short_frozen"] += volume_short_frozen
            if priority[0] == "T":
                position["volume_short_frozen_today"] += volume_short_frozen
                if len(priority) > 1:
                    if position["volume_short_frozen_today"] < 0:
                        position["volume_short_frozen_his"] += position["volume_short_frozen_today"]
                        position["volume_short_frozen_today"] = 0
                    elif position["volume_short_today"] < position["volume_short_frozen_today"]:
                        position["volume_short_frozen_his"] += position["volume_short_frozen_today"] - position[
                            "volume_short_today"]
                        position["volume_short_frozen_today"] = position["volume_short_today"]
            else:
                position["volume_short_frozen_his"] += volume_short_frozen
                if len(priority) > 1:
                    if position["volume_short_frozen_his"] < 0:
                        position["volume_short_frozen_today"] += position["volume_short_frozen_his"]
                        position["volume_short_frozen_his"] = 0
                    elif position["volume_short_his"] < position["volume_short_frozen_his"]:
                        position["volume_short_frozen_today"] += position["volume_short_frozen_his"] - position[
                            "volume_short_his"]
                        position["volume_short_frozen_his"] = position["volume_short_his"]
        if price is not None and price == price:
            if position["last_price"] is not None:
                float_profit_long = (price - position["last_price"]) * position["volume_long"] * volume_multiple
                float_profit_short = (position["last_price"] - price) * position["volume_short"] * volume_multiple
                float_profit = float_profit_long + float_profit_short
                position["float_profit_long"] += float_profit_long
                position["float_profit_short"] += float_profit_short
                position["float_profit"] += float_profit
                if quote["ins_class"] in ["OPTION", "FUTURE_OPTION"]:  # 期权市值 = 权利金 + 期权持仓盈亏
                    position["market_value_long"] += float_profit_long  # 权利方市值(始终 >= 0)
                    position["market_value_short"] += float_profit_short  # 义务方市值(始终 <= 0)
                    position["market_value"] += float_profit
                    self._adjust_account(float_profit=float_profit, market_value=float_profit)
                else:  # 期权没有持仓盈亏
                    position["position_profit_long"] += float_profit_long
                    position["position_profit_short"] += float_profit_short
                    position["position_profit"] += float_profit
                    self._adjust_account(float_profit=float_profit, position_profit=float_profit)
            position["last_price"] = price
        if volume_long:  # volume_long > 0:买开,  < 0:卖平
            close_profit = 0 if volume_long > 0 else (position["last_price"] - position[
                "position_price_long"]) * -volume_long * volume_multiple
            float_profit = 0 if volume_long > 0 else position["float_profit_long"] / position[
                "volume_long"] * volume_long
            position["open_cost_long"] += volume_long * position["last_price"] * volume_multiple if volume_long > 0 else \
                position["open_cost_long"] / position["volume_long"] * volume_long
            position["position_cost_long"] += volume_long * position[
                "last_price"] * volume_multiple if volume_long > 0 else position["position_cost_long"] / position[
                "volume_long"] * volume_long
            market_value = 0
            margin = 0.0
            if quote["ins_class"] in ["OPTION", "FUTURE_OPTION"]:
                # 期权市值 = 权利金 + 期权持仓盈亏
                market_value = position["last_price"] * volume_long * volume_multiple
                position["market_value_long"] += market_value
                position["market_value"] += market_value
            else:
                margin = volume_long * self._quotes[symbol]["margin"]
                position["position_profit_long"] -= close_profit
                position["position_profit"] -= close_profit
            position["volume_long"] += volume_long
            position["open_price_long"] = position["open_cost_long"] / volume_multiple / position["volume_long"] if \
                position["volume_long"] else float("nan")
            position["position_price_long"] = position["position_cost_long"] / volume_multiple / position[
                "volume_long"] if position["volume_long"] else float("nan")
            position["float_profit_long"] += float_profit
            position["float_profit"] += float_profit
            position["margin_long"] += margin
            position["margin"] += margin
            if priority[0] == "T":
                position["volume_long_today"] += volume_long
                if len(priority) > 1:
                    if position["volume_long_today"] < 0:
                        position["volume_long_his"] += position["volume_long_today"]
                        position["volume_long_today"] = 0
            else:
                position["volume_long_his"] += volume_long
                if len(priority) > 1:
                    if position["volume_long_his"] < 0:
                        position["volume_long_today"] += position["volume_long_his"]
                        position["volume_long_his"] = 0

            if priority[0] == "T":
                position["pos_long_today"] += volume_long
                if len(priority) > 1:
                    if position["pos_long_today"] < 0:
                        position["pos_long_his"] += position["pos_long_today"]
                        position["pos_long_today"] = 0
            else:
                position["pos_long_his"] += volume_long
                if len(priority) > 1:
                    if position["pos_long_his"] < 0:
                        position["pos_long_today"] += position["pos_long_his"]
                        position["pos_long_his"] = 0

            self._adjust_account(float_profit=float_profit,
                                 position_profit=-close_profit if quote["ins_class"] not in ["OPTION",
                                                                                             "FUTURE_OPTION"] else 0,
                                 close_profit=close_profit, margin=margin, market_value=market_value)
        if volume_short:  # volume_short > 0: 卖开,  < 0:买平
            close_profit = 0 if volume_short > 0 else (position["position_price_short"] - position[
                "last_price"]) * -volume_short * volume_multiple
            float_profit = 0 if volume_short > 0 else position["float_profit_short"] / position[
                "volume_short"] * volume_short
            # 期权: open_cost_short > 0, open_cost_long > 0
            position["open_cost_short"] += volume_short * position[
                "last_price"] * volume_multiple if volume_short > 0 else position["open_cost_short"] / position[
                "volume_short"] * volume_short
            position["position_cost_short"] += volume_short * position[
                "last_price"] * volume_multiple if volume_short > 0 else position["position_cost_short"] / position[
                "volume_short"] * volume_short
            market_value = 0
            margin = 0
            if quote["ins_class"] in ["OPTION", "FUTURE_OPTION"]:
                market_value = -(position["last_price"] * volume_short * volume_multiple)
                position["market_value_short"] += market_value
                position["market_value"] += market_value
                if volume_short > 0:
                    if quote["option_class"] == "CALL":
                        margin = (quote["last_price"] + max(0.12 * underlying_quote["last_price"] - max(
                            quote["strike_price"] - underlying_quote["last_price"], 0),
                                                            0.07 * underlying_quote["last_price"])) * quote[
                                     "volume_multiple"]
                    else:
                        margin = min(quote["last_price"] + max(0.12 * underlying_quote["last_price"] - max(
                            underlying_quote["last_price"] - quote["strike_price"], 0), 0.07 * quote["strike_price"]),
                                     quote["strike_price"]) * quote["volume_multiple"]
            else:
                margin = volume_short * self._quotes[symbol]["margin"]
                position["position_profit_short"] -= close_profit
                position["position_profit"] -= close_profit
            position["volume_short"] += volume_short
            position["open_price_short"] = position["open_cost_short"] / volume_multiple / position["volume_short"] if \
                position["volume_short"] else float("nan")
            position["position_price_short"] = position["position_cost_short"] / volume_multiple / position[
                "volume_short"] if position["volume_short"] else float("nan")
            position["float_profit_short"] += float_profit
            position["float_profit"] += float_profit
            position["margin_short"] += margin
            position["margin"] += margin
            if priority[0] == "T":
                position["volume_short_today"] += volume_short
                if len(priority) > 1:
                    if position["volume_short_today"] < 0:
                        position["volume_short_his"] += position["volume_short_today"]
                        position["volume_short_today"] = 0
            else:
                position["volume_short_his"] += volume_short
                if len(priority) > 1:
                    if position["volume_short_his"] < 0:
                        position["volume_short_today"] += position["volume_short_his"]
                        position["volume_short_his"] = 0

            if priority[0] == "T":
                position["pos_short_today"] += volume_short
                if len(priority) > 1:
                    if position["pos_short_today"] < 0:
                        position["pos_short_his"] += position["pos_short_today"]
                        position["pos_short_today"] = 0
            else:
                position["pos_short_his"] += volume_short
                if len(priority) > 1:
                    if position["pos_short_his"] < 0:
                        position["pos_short_today"] += position["pos_short_his"]
                        position["pos_short_his"] = 0
            self._adjust_account(float_profit=float_profit,
                                 position_profit=-close_profit if quote["ins_class"] not in ["OPTION",
                                                                                             "FUTURE_OPTION"] else 0,
                                 close_profit=close_profit,
                                 margin=margin, market_value=market_value)
        self._send_position(position)
        return position["volume_long_his"] - position["volume_long_frozen_his"] >= 0 and position["volume_long_today"] - \
               position["volume_long_frozen_today"] >= 0 and \
               position["volume_short_his"] - position["volume_short_frozen_his"] >= 0 and position[
                   "volume_short_today"] - position["volume_short_frozen_today"] >= 0

    def _adjust_account(self, commission=0.0, frozen_margin=0.0, frozen_premium=0.0, float_profit=0.0,
                        position_profit=0.0, close_profit=0.0, margin=0.0, premium=0.0, market_value=0.0):
        # 权益 += 持仓盈亏 + 平仓盈亏 - 手续费 + 权利金(收入为负值,支出为正值) + 市值
        self._account["balance"] += position_profit + close_profit - commission + premium + market_value
        # 可用资金 += 权益 - 冻结保证金 - 保证金 - 冻结权利金 - 市值
        self._account[
            "available"] += position_profit + close_profit - commission + premium - frozen_margin - margin - frozen_premium
        self._account["float_profit"] += float_profit
        self._account["position_profit"] += position_profit
        self._account["close_profit"] += close_profit
        self._account["frozen_margin"] += frozen_margin
        self._account["frozen_premium"] += frozen_premium
        self._account["margin"] += margin
        # premium变量的值有正负，正数表示收入的权利金，负数表示付出的权利金；account["premium"]为累计值
        self._account["premium"] += premium
        self._account["market_value"] += market_value
        self._account["commission"] += commission
        self._account["risk_ratio"] = self._account["margin"] / self._account[
            "balance"] if self._account["balance"] else 0.0
        self._send_account()
        return self._account["available"] >= 0

    def _ensure_position(self, symbol):
        if symbol not in self._positions:
            self._positions[symbol] = {
                "exchange_id": symbol.split(".", maxsplit=1)[0],
                "instrument_id": symbol.split(".", maxsplit=1)[1],
                "pos_long_his": 0,
                "pos_long_today": 0,
                "pos_short_his": 0,
                "pos_short_today": 0,
                "volume_long_today": 0,
                "volume_long_his": 0,
                "volume_long": 0,
                "volume_long_frozen_today": 0,
                "volume_long_frozen_his": 0,
                "volume_long_frozen": 0,
                "volume_short_today": 0,
                "volume_short_his": 0,
                "volume_short": 0,
                "volume_short_frozen_today": 0,
                "volume_short_frozen_his": 0,
                "volume_short_frozen": 0,
                "open_price_long": float("nan"),
                "open_price_short": float("nan"),
                "open_cost_long": 0.0,
                "open_cost_short": 0.0,
                "position_price_long": float("nan"),
                "position_price_short": float("nan"),
                "position_cost_long": 0.0,
                "position_cost_short": 0.0,
                "float_profit_long": 0.0,
                "float_profit_short": 0.0,
                "float_profit": 0.0,
                "position_profit_long": 0.0,
                "position_profit_short": 0.0,
                "position_profit": 0.0,
                "margin_long": 0.0,
                "margin_short": 0.0,
                "margin": 0.0,
                "last_price": None,
                "market_value_long": 0.0,  # 权利方市值(始终 >= 0)
                "market_value_short": 0.0,  # 义务方市值(始终 <= 0)
                "market_value": 0.0,
            }
        return self._positions[symbol]

    def _ensure_quote(self, symbol):
        if symbol not in self._quotes:
            self._quotes[symbol] = {
                "ins_class": None,  # 合约信息初始化为None
                "option_class": None,
                "symbol": symbol,
                "underlying_symbol": "",
                "orders": {},
                "datetime": "",
                "trading_time": {},
                "ask_price1": float("nan"),
                "bid_price1": float("nan"),
                "last_price": float("nan"),
                "volume_multiple": None,
                "strike_price": float("nan"),
                "margin": None,
                "commission": None,
            }
        return self._quotes[symbol]

    def _send_order(self, order):
        self._diffs.append({
            "trade": {
                self._account_id: {
                    "orders": {
                        order["order_id"]: order.copy()
                    }
                }
            }
        })

    def _send_position(self, position):
        self._diffs.append({
            "trade": {
                self._account_id: {
                    "positions": {
                        position["exchange_id"] + "." + position["instrument_id"]: position.copy()
                    }
                }
            }
        })

    def _send_account(self):
        self._diffs.append({
            "trade": {
                self._account_id: {
                    "accounts": {
                        "CNY": self._account.copy()
                    }
                }
            }
        })

    def _get_current_timestamp(self):
        return int(datetime.datetime.strptime(self._current_datetime, "%Y-%m-%d %H:%M:%S.%f").timestamp() * 1e6) * 1000

    @staticmethod
    def _get_trade_timestamp(current_datetime, local_time_record):
        # 根据最新行情时间获取模拟的(预估的)当前交易所纳秒时间戳（tqsdk内部使用的时间戳统一为纳秒）
        # 如果local_time_record为nan，則不加时间差
        return int((datetime.datetime.strptime(current_datetime,
                                               "%Y-%m-%d %H:%M:%S.%f").timestamp() + (
                        0 if local_time_record != local_time_record else (
                                time.time() - local_time_record))) * 1e6) * 1000
