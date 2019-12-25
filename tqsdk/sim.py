#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from datetime import datetime
import statistics


class TqSim(object):
    """
    天勤模拟交易类

    该类只针对天勤外部IDE编写使用, 在天勤内部如要使用模拟账号测试, 推荐用模拟账号登录天勤终端之后配合 api = TqApi() 使用

    限价单要求报单价格达到或超过对手盘价格才能成交, 成交价为报单价格, 如果没有对手盘(涨跌停)则无法成交

    市价单使用对手盘价格成交, 如果没有对手盘(涨跌停)则自动撤单

    模拟交易不会有部分成交的情况, 要成交就是全部成交
    """

    def __init__(self, init_balance: float = 10000000.0, account_id: str = "TQSIM") -> None:
        """
        Args:
            init_balance (float): [可选]初始资金, 默认为一千万

            account_id (str): [可选]帐号, 默认为 "TQSIM"
        """
        self._account_id = account_id
        self._init_balance = float(init_balance)
        if self._init_balance <= 0:
            raise Exception("初始资金(init_balance) %s 错误, 请检查 init_balance 是否填写正确" % (init_balance))
        self._current_datetime = "1990-01-01 00:00:00.000000"
        self._trading_day_end = "1990-01-01 18:00:00.000000"

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
            "position_profit": 0.0,
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
        }
        self._positions = {}
        self._orders = {}
        self._quotes = {}  # 记下最新行情
        self._trade_log = {}  # 日期->交易记录及收盘时的权益及持仓
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
                    if self._pending_peek:
                        await self._md_send_chan.send(pack)
                elif pack["aid"] == "insert_order":
                    self._insert_order(pack)
                    if pack["symbol"] not in self._all_subscribe:
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
        self._all_subscribe = self._client_subscribe | {o["symbol"] for o in self._orders.values()} | {p["symbol"] for p
                                                                                                       in
                                                                                                       self._positions.values()}
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
            self._tqsdk_backtest.update(d.get("_tqsdk_backtest", {}))
            for symbol, quote_diff in d.get("quotes", {}).items():
                if quote_diff is None:
                    continue
                quote = self._ensure_quote(symbol)
                quote["datetime"] = quote_diff.get("datetime", quote["datetime"])
                if self._tqsdk_backtest == {}:
                    self._current_datetime = max(quote["datetime"], self._current_datetime)
                else:
                    self._current_datetime = datetime.fromtimestamp(self._tqsdk_backtest["current_dt"] / 1e9).strftime(
                        "%Y-%m-%d %H:%M:%S.%f")
                if self._current_datetime > self._trading_day_end:  # 结算
                    self._settle()
                    trading_day = self._api._get_trading_day_from_timestamp(self._get_current_timestamp())
                    self._trading_day_end = datetime.fromtimestamp(
                        (self._api._get_trading_day_end_time(trading_day) - 1000) / 1e9).strftime(
                        "%Y-%m-%d %H:%M:%S.%f")
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
                self._match_orders(quote)
                if symbol in self._positions:
                    self._adjust_position(symbol, price=quote["last_price"])

    def _insert_order(self, order):
        order["symbol"] = order["exchange_id"] + "." + order["instrument_id"]
        order["exchange_order_id"] = order["order_id"]
        order["volume_orign"] = order["volume"]
        order["volume_left"] = order["volume"]
        order["frozen_margin"] = 0.0
        order["insert_date_time"] = self._get_current_timestamp()
        order["last_msg"] = "报单成功"
        order["status"] = "ALIVE"
        del order["aid"]
        del order["volume"]
        self._logger.info("模拟交易下单 %s: 时间:%s,合约:%s,开平:%s,方向:%s,手数:%s,价格:%s", order["order_id"], self._current_datetime,
                          order["symbol"], order["offset"], order["direction"], order["volume_left"],
                          order.get("limit_price", "市价"))
        quote = self._ensure_quote(order["symbol"])
        quote["orders"][order["order_id"]] = order
        self._orders[order["order_id"]] = order
        if order["offset"].startswith("CLOSE"):
            volume_long_frozen = 0 if order["direction"] == "BUY" else order["volume_left"]
            volume_short_frozen = 0 if order["direction"] == "SELL" else order["volume_left"]
            if order["exchange_id"] == "SHFE" or order["exchange_id"] == "INE":
                priority = "H" if order["offset"] == "CLOSE" else "T"
            else:
                priority = "TH"
            if not self._adjust_position(order["symbol"], volume_long_frozen=volume_long_frozen,
                                         volume_short_frozen=volume_short_frozen, priority=priority):
                self._del_order(order, "平仓手数不足")
                return
        else:
            if quote["commission"] is None or quote["margin"] is None:
                self._del_order(order, "合约不存在")
                return
            order["frozen_margin"] = quote["margin"] * order["volume_orign"]
            if not self._adjust_account(frozen_margin=order["frozen_margin"]):
                self._del_order(order, "开仓资金不足")
                return
        self._send_order(order)
        self._match_order(quote, order)

    def _cancel_order(self, pack):
        if pack["order_id"] in self._orders:
            self._del_order(self._orders[pack["order_id"]], "已撤单")

    def _del_order(self, order, msg):
        self._logger.info("模拟交易委托单 %s: %s", order["order_id"], msg)
        if order["offset"].startswith("CLOSE"):
            volume_long_frozen = 0 if order["direction"] == "BUY" else -order["volume_left"]
            volume_short_frozen = 0 if order["direction"] == "SELL" else -order["volume_left"]
            if order["exchange_id"] == "SHFE" or order["exchange_id"] == "INE":
                priority = "H" if order["offset"] == "CLOSE" else "T"
            else:
                priority = "HT"
            self._adjust_position(order["symbol"], volume_long_frozen=volume_long_frozen,
                                  volume_short_frozen=volume_short_frozen, priority=priority)
        else:
            self._adjust_account(frozen_margin=-order["frozen_margin"])
            order["frozen_margin"] = 0.0
        order["last_msg"] = msg
        order["status"] = "FINISHED"
        self._send_order(order)
        del self._orders[order["order_id"]]
        del self._quotes[order["symbol"]]["orders"][order["order_id"]]

    def _match_orders(self, quote):
        for order in list(quote["orders"].values()):
            self._match_order(quote, order)

    def _match_order(self, quote, order):
        ask_price = quote["ask_price1"]
        bid_price = quote["bid_price1"]
        if quote["datetime"] == "":
            return
        if "limit_price" not in order:
            price = ask_price if order["direction"] == "BUY" else bid_price
            if price != price:
                self._del_order(order, "市价指令剩余撤销")
                return
        elif order["direction"] == "BUY" and order["limit_price"] >= ask_price:
            price = order["limit_price"]
        elif order["direction"] == "SELL" and order["limit_price"] <= bid_price:
            price = order["limit_price"]
        else:
            return
        trade = {
            "symbol": order["symbol"],
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
            "trade_date_time": self._get_current_timestamp(),
            "commission": quote["commission"] * order["volume_left"],
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
            self._adjust_position(order["symbol"], volume_long_frozen=volume_long, volume_short_frozen=volume_short,
                                  priority=priority)
        else:
            volume_long = 0 if order["direction"] == "SELL" else order["volume_left"]
            volume_short = 0 if order["direction"] == "BUY" else order["volume_left"]
        self._adjust_position(order["symbol"], volume_long=volume_long, volume_short=volume_short, price=price,
                              priority=priority)
        self._adjust_account(commission=trade["commission"])
        order["volume_left"] = 0
        self._del_order(order, "全部成交")

    def _settle(self):
        if self._trading_day_end[:10] == "1990-01-01":
            return
        trade_log = self._ensure_trade_log()
        # 撤销所有委托单
        for order in list(self._orders.values()):
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
        if not self._trade_log:
            return
        self._tqsdk_stat["init_balance"] = self._init_balance  # 起始资金
        self._tqsdk_stat["balance"] = self._account["balance"]  # 结束资金
        self._tqsdk_stat["max_drawdown"] = 0  # 最大回撤
        max_balance = 0
        daily_yield = []
        self._logger.warning("模拟交易成交记录")
        # 胜率 盈亏额比例
        trades_logs = {}
        profit_logs = [] # 盈利记录
        loss_logs = [] # 亏损记录
        for d in sorted(self._trade_log.keys()):
            balance = self._trade_log[d]["account"]["balance"]
            if balance > max_balance:
                max_balance = balance
            drawdown = (max_balance - balance) / max_balance
            if drawdown > self._tqsdk_stat["max_drawdown"]:
                self._tqsdk_stat["max_drawdown"] = drawdown
            daily_yield.append(
                self._trade_log[d]["account"]["balance"] / self._trade_log[d]["account"]["pre_balance"] - 1)
            for t in self._trade_log[d]["trades"]:
                self._logger.warning("时间:%s,合约:%s,开平:%s,方向:%s,手数:%d,价格:%.3f,手续费:%.2f",
                                     datetime.fromtimestamp(t["trade_date_time"] / 1e9).strftime(
                                         "%Y-%m-%d %H:%M:%S.%f"), t["symbol"], t["offset"], t["direction"], t["volume"],
                                     t["price"], t["commission"])
                if t["symbol"] not in trades_logs:
                    trades_logs[t["symbol"]] = {
                        "BUY": [],
                        "SELL": [],
                    }
                if t["offset"] == "OPEN":
                    trades_logs[t["symbol"]][t["direction"]].append({"volume": t["volume"], "price": t["price"]})
                else:
                    opposite_dir = "BUY" if t["direction"] == "SELL" else "SELL"
                    opposite_list = trades_logs[t["symbol"]][opposite_dir]
                    cur_close_volume = t["volume"]
                    cur_close_price = t["price"]
                    cur_close_dir = 1 if t["direction"] == "SELL" else -1
                    while cur_close_volume > 0 and opposite_list[0]:
                        volume = min(cur_close_volume, opposite_list[0]["volume"])
                        profit = (cur_close_price - opposite_list[0]["price"]) * cur_close_dir
                        if profit >= 0:
                            profit_logs.append({"symbol": t["symbol"], "profit": profit, "volume": volume})
                        else:
                            loss_logs.append({"symbol": t["symbol"], "profit": profit, "volume": volume})
                        cur_close_volume -= volume
                        opposite_list[0]["volume"] -= volume
                        if opposite_list[0]["volume"] == 0:
                            opposite_list.pop()

        self._tqsdk_stat["profit_volumes"] = sum(p["volume"] for p in profit_logs)  # 盈利手数
        self._tqsdk_stat["loss_volumes"] = sum(l["volume"] for l in loss_logs)  # 亏损手数
        self._tqsdk_stat["profit_value"] = sum(p["profit"] * p["volume"] * self._quotes[p["symbol"]]["volume_multiple"] for p in profit_logs)  # 盈利额
        self._tqsdk_stat["loss_value"] = sum(l["profit"] * l["volume"] * self._quotes[l["symbol"]]["volume_multiple"] for l in loss_logs)  # 亏损额

        mean = statistics.mean(daily_yield)
        rf = 0.0001
        stddev = statistics.pstdev(daily_yield, mu=mean)
        self._tqsdk_stat["sharpe_ratio"] = 250 ** (1 / 2) * (mean - rf) / stddev if stddev else float("inf")  # 年化夏普率

        _ror = self._tqsdk_stat["balance"] / self._tqsdk_stat["init_balance"]
        self._tqsdk_stat["ror"] = _ror - 1 # 收益率
        self._tqsdk_stat["annual_yield"] = _ror ** (250 / len(self._trade_log)) - 1 # 年化收益率

        self._logger.warning("模拟交易账户资金")
        for d in sorted(self._trade_log.keys()):
            account = self._trade_log[d]["account"]
            self._logger.warning("日期:%s,账户权益:%.2f,可用资金:%.2f,浮动盈亏:%.2f,持仓盈亏:%.2f,平仓盈亏:%.2f,保证金:%.2f,手续费:%.2f,风险度:%.2f%%",
                                d, account["balance"], account["available"], account["float_profit"],
                                account["position_profit"],
                                account["close_profit"], account["margin"], account["commission"],
                                account["risk_ratio"] * 100)

        self._tqsdk_stat["winning_rate"] = (self._tqsdk_stat["profit_volumes"] / (self._tqsdk_stat["profit_volumes"] + self._tqsdk_stat["loss_volumes"])) \
            if self._tqsdk_stat["profit_volumes"] + self._tqsdk_stat["loss_volumes"] else 0
        profit_pre_volume = self._tqsdk_stat["profit_value"] / self._tqsdk_stat["profit_volumes"] if self._tqsdk_stat["profit_volumes"] else 0
        loss_pre_volume = self._tqsdk_stat["loss_value"] / self._tqsdk_stat["loss_volumes"] if self._tqsdk_stat["loss_volumes"] else 0
        self._tqsdk_stat["profit_loss_ratio"] = profit_pre_volume / loss_pre_volume if loss_pre_volume else float("inf")
        self._logger.warning("胜率:%.2f,每手盈亏额比例:%.2f,收益率:%.2f%%,年化收益率:%.2f%%,最大回撤:%.2f%%,年化夏普率:%.4f",
                             self._tqsdk_stat["winning_rate"],
                             self._tqsdk_stat["profit_loss_ratio"],
                             self._tqsdk_stat["ror"] * 100,
                             self._tqsdk_stat["annual_yield"] * 100,
                             self._tqsdk_stat["max_drawdown"] * 100,
                             self._tqsdk_stat["sharpe_ratio"])

    def _ensure_trade_log(self):
        return self._trade_log.setdefault(self._trading_day_end[:10], {
            "trades": []
        })

    def _adjust_position(self, symbol, volume_long_frozen=0, volume_short_frozen=0, volume_long=0, volume_short=0,
                         price=None, priority=None):
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
                position["position_profit_long"] += float_profit_long
                position["position_profit_short"] += float_profit_short
                position["position_profit"] += float_profit
                self._adjust_account(float_profit=float_profit, position_profit=float_profit)
            position["last_price"] = price
        if volume_long:
            margin = volume_long * self._quotes[symbol]["margin"]
            close_profit = 0 if volume_long > 0 else (position["last_price"] - position[
                "position_price_long"]) * -volume_long * volume_multiple
            float_profit = 0 if volume_long > 0 else position["float_profit_long"] / position[
                "volume_long"] * volume_long
            position["open_cost_long"] += volume_long * position["last_price"] * volume_multiple if volume_long > 0 else \
                position["open_cost_long"] / position["volume_long"] * volume_long
            position["position_cost_long"] += volume_long * position[
                "last_price"] * volume_multiple if volume_long > 0 else position["position_cost_long"] / position[
                "volume_long"] * volume_long
            position["volume_long"] += volume_long
            position["open_price_long"] = position["open_cost_long"] / volume_multiple / position["volume_long"] if \
                position["volume_long"] else float("nan")
            position["position_price_long"] = position["position_cost_long"] / volume_multiple / position[
                "volume_long"] if position["volume_long"] else float("nan")
            position["float_profit_long"] += float_profit
            position["float_profit"] += float_profit
            position["position_profit_long"] -= close_profit
            position["position_profit"] -= close_profit
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

            self._adjust_account(float_profit=float_profit, position_profit=-close_profit, close_profit=close_profit,
                                 margin=margin)
        if volume_short:
            margin = volume_short * self._quotes[symbol]["margin"]
            close_profit = 0 if volume_short > 0 else (position["position_price_short"] - position[
                "last_price"]) * -volume_short * volume_multiple
            float_profit = 0 if volume_short > 0 else position["float_profit_short"] / position[
                "volume_short"] * volume_short
            position["open_cost_short"] += volume_short * position[
                "last_price"] * volume_multiple if volume_short > 0 else position["open_cost_short"] / position[
                "volume_short"] * volume_short
            position["position_cost_short"] += volume_short * position[
                "last_price"] * volume_multiple if volume_short > 0 else position["position_cost_short"] / position[
                "volume_short"] * volume_short
            position["volume_short"] += volume_short
            position["open_price_short"] = position["open_cost_short"] / volume_multiple / position["volume_short"] if \
                position["volume_short"] else float("nan")
            position["position_price_short"] = position["position_cost_short"] / volume_multiple / position[
                "volume_short"] if position["volume_short"] else float("nan")
            position["float_profit_short"] += float_profit
            position["float_profit"] += float_profit
            position["position_profit_short"] -= close_profit
            position["position_profit"] -= close_profit
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
            self._adjust_account(float_profit=float_profit, position_profit=-close_profit, close_profit=close_profit,
                                 margin=margin)
        self._send_position(position)
        return position["volume_long_his"] - position["volume_long_frozen_his"] >= 0 and position["volume_long_today"] - \
               position["volume_long_frozen_today"] >= 0 and \
               position["volume_short_his"] - position["volume_short_frozen_his"] >= 0 and position[
                   "volume_short_today"] - position["volume_short_frozen_today"] >= 0

    def _adjust_account(self, commission=0.0, frozen_margin=0.0, float_profit=0.0, position_profit=0.0,
                        close_profit=0.0, margin=0.0):
        self._account["balance"] += position_profit + close_profit - commission
        self._account["available"] += position_profit + close_profit - commission - frozen_margin - margin
        self._account["float_profit"] += float_profit
        self._account["position_profit"] += position_profit
        self._account["close_profit"] += close_profit
        self._account["frozen_margin"] += frozen_margin
        self._account["margin"] += margin
        self._account["commission"] += commission
        self._account["risk_ratio"] = (self._account["frozen_margin"] + self._account["margin"]) / self._account[
            "balance"] if self._account["balance"] else 0.0
        self._send_account()
        return self._account["available"] >= 0

    def _ensure_position(self, symbol):
        if symbol not in self._positions:
            self._positions[symbol] = {
                "symbol": symbol,
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
            }
        return self._positions[symbol]

    def _ensure_quote(self, symbol):
        if symbol not in self._quotes:
            self._quotes[symbol] = {
                "symbol": symbol,
                "orders": {},
                "datetime": "",
                "ask_price1": float("nan"),
                "bid_price1": float("nan"),
                "last_price": float("nan"),
                "volume_multiple": None,
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
        return int(datetime.strptime(self._current_datetime, "%Y-%m-%d %H:%M:%S.%f").timestamp() * 1e6) * 1000
