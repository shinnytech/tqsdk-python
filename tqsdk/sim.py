#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from datetime import datetime
import statistics

class TqSim(object):
    """
    天勤模拟交易类

    限价单要求报单价格达到或超过对手盘价格才能成交, 成交价为报单价格, 如果没有对手盘(涨跌停)则无法成交

    市价单使用对手盘价格成交, 如果没有对手盘(涨跌停)则自动撤单

    模拟交易不会有部分成交的情况, 要成交就是全部成交
    """
    def __init__(self, init_balance=1000000.0, account_id="TQSIM"):
        """
        创建天勤模拟交易类

        Args:
            init_balance (float): [可选]初始资金, 默认为一百万

            account_id (str): [可选]帐号, 默认为 "TQSIM"
        """
        self.account_id = account_id
        self.init_balance = init_balance
        self.current_datetime = "1990-01-01 00:00:00.000000"
        self.trading_day_end = "1990-01-01 18:00:00.000000"

    async def _run(self, api, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan):
        """模拟交易task"""
        self.api = api
        self.logger = api.logger.getChild("TqSim")  # 调试信息输出
        self.api_send_chan = api_send_chan
        self.api_recv_chan = api_recv_chan
        self.md_send_chan = md_send_chan
        self.md_recv_chan = md_recv_chan
        self.pending_peek = False
        self.diffs = []
        self.account = {
            "currency": "CNY",
            "pre_balance": self.init_balance,
            "static_balance": self.init_balance,
            "balance": self.init_balance,
            "available": self.init_balance,
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
        self.positions = {}
        self.orders = {}
        self.quotes = {}  # 记下最新行情
        self.trade_log = {}  # 日期->交易记录及收盘时的权益及持仓
        self.client_subscribe = set()  # 客户端订阅的合约集合
        self.all_subscribe = set()  # 客户端+模拟交易模块订阅的合约集合
        self._send_account()  # 发送初始账户信息
        self.diffs.append({"trade":{self.account_id:{"orders":{},"positions":{},"trade_more_data": False}}})
        md_task = self.api.create_task(self._md_handler())  # 将所有 md_recv_chan 上收到的包投递到 api_send_chan 上
        try:
            async for pack in self.api_send_chan:
                self.logger.debug("TqSim message received: %s", pack)
                if "_md_recv" in pack:
                    if pack["aid"] == "rtn_data":
                        self._md_recv(pack)
                        await self._send_diff()
                elif pack["aid"] == "subscribe_quote":
                    self.client_subscribe = set(pack["ins_list"].split(","))
                    await self._subscribe_quote()
                elif pack["aid"] == "peek_message":
                    self.pending_peek = True
                    await self._send_diff()
                    if self.pending_peek:
                        await self.md_send_chan.send(pack)
                elif pack["aid"] == "insert_order":
                    self._insert_order(pack)
                    if pack["symbol"] not in self.all_subscribe:
                        await self._subscribe_quote()
                    await self._send_diff()
                elif pack["aid"] == "cancel_order":
                    self._cancel_order(pack)
                    await self._send_diff()
                else:
                    await self.md_send_chan.send(pack)
        finally:
            self._settle()
            self._report()
            md_task.cancel()

    async def _md_handler(self):
        async for pack in self.md_recv_chan:
            pack["_md_recv"] = True
            await self.api_send_chan.send(pack)

    async def _send_diff(self):
        if self.pending_peek and self.diffs:
            rtn_data = {
                "aid": "rtn_data",
                "data": self.diffs,
            }
            self.diffs = []
            self.pending_peek = False
            self.logger.debug("TqSim message send: %s", rtn_data)
            await self.api_recv_chan.send(rtn_data)

    async def _subscribe_quote(self):
        self.all_subscribe = self.client_subscribe | {o["symbol"] for o in self.orders.values()} | {p["symbol"] for p in self.positions.values()}
        await self.md_send_chan.send({
            "aid":"subscribe_quote",
            "ins_list":",".join(self.all_subscribe)
        })

    def _md_recv(self, pack):
        for d in pack["data"]:
            d.pop("trade", None)
            self.diffs.append(d)
            for symbol, quote_diff in d.get("quotes", {}).items():
                if quote_diff is None:
                    continue
                quote = self._ensure_quote(symbol)
                quote["datetime"] = quote_diff.get("datetime", quote["datetime"])
                self.current_datetime = max(quote["datetime"], self.current_datetime)
                if self.current_datetime > self.trading_day_end:  # 结算
                    self._settle()
                    trading_day = self.api._get_trading_day_from_timestamp(self._get_current_timestamp())
                    self.trading_day_end = datetime.fromtimestamp((self.api._get_trading_day_end_time(trading_day)-1000) / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f")
                if "ask_price1" in quote_diff:
                    quote["ask_price1"] = float("nan") if type(quote_diff["ask_price1"]) is str else quote_diff["ask_price1"]
                if "bid_price1" in quote_diff:
                    quote["bid_price1"] = float("nan") if type(quote_diff["bid_price1"]) is str else quote_diff["bid_price1"]
                if "last_price" in quote_diff:
                    quote["last_price"] = float("nan") if type(quote_diff["last_price"]) is str else quote_diff["last_price"]
                quote["volume_multiple"] = quote_diff.get("volume_multiple", quote["volume_multiple"])
                quote["commission"] = quote_diff.get("commission", quote["commission"])
                quote["margin"] = quote_diff.get("margin", quote["margin"])
                self._match_orders(quote)
                if symbol in self.positions:
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
        self.logger.info("模拟交易下单 %s: 时间:%s,合约:%s,开平:%s,方向:%s,手数:%s,价格:%s", order["order_id"], self.current_datetime,
                         order["symbol"], order["offset"], order["direction"], order["volume_left"], order.get("limit_price", "市价"))
        quote = self._ensure_quote(order["symbol"])
        quote["orders"][order["order_id"]] = order
        self.orders[order["order_id"]] = order
        if order["offset"].startswith("CLOSE"):
            volume_long_frozen = 0 if order["direction"] == "BUY" else order["volume_left"]
            volume_short_frozen = 0 if order["direction"] == "SELL" else order["volume_left"]
            if order["exchange_id"] == "SHFE" or order["exchange_id"] == "INE":
                priority = "H" if order["offset"] == "CLOSE" else "T"
            else:
                priority = "TH"
            if not self._adjust_position(order["symbol"], volume_long_frozen=volume_long_frozen, volume_short_frozen=volume_short_frozen, priority=priority):
                self._del_order(order, "平仓手数不足")
                return
        else:
            if quote["commission"] is None or quote["margin"] is None:
                self._del_order(order, "合约不存在")
                return
            order["frozen_margin"] = quote["margin"] * order["volume_orign"]
            if not self._adjust_account(frozen_margin = order["frozen_margin"]):
                self._del_order(order, "开仓资金不足")
                return
        self._send_order(order)
        self._match_order(quote, order)

    def _cancel_order(self, pack):
        if pack["order_id"] in self.orders:
            self._del_order(self.orders[pack["order_id"]], "已撤单")

    def _del_order(self, order, msg):
        self.logger.info("模拟交易委托单 %s: %s", order["order_id"], msg)
        if order["offset"].startswith("CLOSE"):
            volume_long_frozen = 0 if order["direction"] == "BUY" else -order["volume_left"]
            volume_short_frozen = 0 if order["direction"] == "SELL" else -order["volume_left"]
            if order["exchange_id"] == "SHFE" or order["exchange_id"] == "INE":
                priority = "H" if order["offset"] == "CLOSE" else "T"
            else:
                priority = "HT"
            self._adjust_position(order["symbol"], volume_long_frozen=volume_long_frozen, volume_short_frozen=volume_short_frozen, priority=priority)
        else:
            self._adjust_account(frozen_margin=-order["frozen_margin"])
            order["frozen_margin"] = 0.0
        order["last_msg"] = msg
        order["status"] = "FINISHED"
        self._send_order(order)
        del self.orders[order["order_id"]]
        del self.quotes[order["symbol"]]["orders"][order["order_id"]]

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
        self.diffs.append({"trade":{self.account_id:{"trades":{trade["trade_id"]:trade.copy()}}}})
        if order["exchange_id"] == "SHFE" or order["exchange_id"] == "INE":
            priority = "H" if order["offset"] == "CLOSE" else "T"
        else:
            priority = "TH"
        if order["offset"].startswith("CLOSE"):
            volume_long = 0 if order["direction"] == "BUY" else -order["volume_left"]
            volume_short = 0 if order["direction"] == "SELL" else -order["volume_left"]
            self._adjust_position(order["symbol"], volume_long_frozen=volume_long, volume_short_frozen=volume_short, priority=priority)
        else:
            volume_long = 0 if order["direction"] == "SELL" else order["volume_left"]
            volume_short = 0 if order["direction"] == "BUY" else order["volume_left"]
        self._adjust_position(order["symbol"], volume_long=volume_long, volume_short=volume_short, price=price, priority=priority)
        self._adjust_account(commission=trade["commission"])
        order["volume_left"] = 0
        self._del_order(order, "全部成交")

    def _settle(self):
        if self.trading_day_end[:10] == "1990-01-01":
            return
        trade_log = self._ensure_trade_log()
        # 撤销所有委托单
        for order in list(self.orders.values()):
            self._del_order(order, "交易日结束撤单")
        # 记录账户截面
        trade_log["account"] = self.account.copy()
        trade_log["positions"] = { k:v.copy() for k, v in self.positions.items()}
        # 为下一交易日调整账户
        self.account["pre_balance"] = self.account["balance"]
        self.account["static_balance"] = self.account["balance"]
        self.account["position_profit"] = 0
        self.account["close_profit"] = 0
        self.account["commission"] = 0
        self._send_account()
        self._adjust_account()
        for symbol, position in self.positions.items():
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
        max_balance = 0
        max_drawdown = 0
        daily_yield = []
        self.logger.warning("模拟交易成交记录")
        for d in sorted(self.trade_log.keys()):
            balance = self.trade_log[d]["account"]["balance"]
            if balance > max_balance:
                max_balance = balance
            drawdown = (max_balance - balance) / max_balance
            if drawdown > max_drawdown:
                max_drawdown = drawdown
            daily_yield.append(self.trade_log[d]["account"]["balance"] / self.trade_log[d]["account"]["pre_balance"] - 1)
            for t in self.trade_log[d]["trades"]:
                self.logger.warning("时间:%s,合约:%s,开平:%s,方向:%s,手数:%d,价格:%.3f,手续费:%.2f",
                                    datetime.fromtimestamp(t["trade_date_time"] / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f"),
                                    t["symbol"], t["offset"], t["direction"], t["volume"], t["price"], t["commission"])
        mean = statistics.mean(daily_yield)
        rf = 0.0001
        stddev = statistics.pstdev(daily_yield, mu=mean)
        sharpe_ratio = 250**(1/2) * (mean - rf) / stddev if stddev else float("inf")
        ror = self.account["balance"] / self.init_balance
        annual_yield = ror**(250/len(self.trade_log))
        self.logger.warning("模拟交易账户资金")
        for d in sorted(self.trade_log.keys()):
            account = self.trade_log[d]["account"]
            self.logger.warning("日期:%s,账户权益:%.2f,可用资金:%.2f,浮动盈亏:%.2f,持仓盈亏:%.2f,平仓盈亏:%.2f,保证金:%.2f,手续费:%.2f,风险度:%.2f%%",
                                d, account["balance"], account["available"], account["float_profit"], account["position_profit"],
                                account["close_profit"], account["margin"], account["commission"], account["risk_ratio"] * 100)
        self.logger.warning("收益率:%.2f%%,年化收益率:%.2f%%,最大回撤:%.2f%%,年化夏普率:%.4f",
                            (ror - 1) * 100, (annual_yield - 1) * 100, max_drawdown * 100, sharpe_ratio)

    def _ensure_trade_log(self):
        return self.trade_log.setdefault(self.trading_day_end[:10], {"trades":[]})

    def _adjust_position(self, symbol, volume_long_frozen=0, volume_short_frozen=0, volume_long=0, volume_short=0, price=None, priority=None):
        position = self._ensure_position(symbol)
        volume_multiple = self.quotes[symbol]["volume_multiple"]
        if volume_long_frozen:
            position["volume_long_frozen"] += volume_long_frozen
            if priority[0] == "T":
                position["volume_long_frozen_today"] += volume_long_frozen
                if len(priority) > 1:
                    if position["volume_long_frozen_today"] < 0:
                        position["volume_long_frozen_his"] += position["volume_long_frozen_today"]
                        position["volume_long_frozen_today"] = 0
                    elif position["volume_long_today"] < position["volume_long_frozen_today"]:
                        position["volume_long_frozen_his"] += position["volume_long_frozen_today"] - position["volume_long_today"]
                        position["volume_long_frozen_today"] = position["volume_long_today"]
            else:
                position["volume_long_frozen_his"] += volume_long_frozen
                if len(priority) > 1:
                    if position["volume_long_frozen_his"] < 0:
                        position["volume_long_frozen_today"] += position["volume_long_frozen_his"]
                        position["volume_long_frozen_his"] = 0
                    elif position["volume_long_his"] < position["volume_long_frozen_his"]:
                        position["volume_long_frozen_today"] += position["volume_long_frozen_his"] - position["volume_long_his"]
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
                        position["volume_short_frozen_his"] += position["volume_short_frozen_today"] - position["volume_short_today"]
                        position["volume_short_frozen_today"] = position["volume_short_today"]
            else:
                position["volume_short_frozen_his"] += volume_short_frozen
                if len(priority) > 1:
                    if position["volume_short_frozen_his"] < 0:
                        position["volume_short_frozen_today"] += position["volume_short_frozen_his"]
                        position["volume_short_frozen_his"] = 0
                    elif position["volume_short_his"] < position["volume_short_frozen_his"]:
                        position["volume_short_frozen_today"] += position["volume_short_frozen_his"] - position["volume_short_his"]
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
            margin = volume_long * self.quotes[symbol]["margin"]
            close_profit = 0 if volume_long > 0 else (position["last_price"] - position["position_price_long"]) * -volume_long * volume_multiple
            float_profit = 0 if volume_long > 0 else position["float_profit_long"] / position["volume_long"] * volume_long
            position["open_cost_long"] += volume_long * position["last_price"] * volume_multiple if volume_long > 0 else position["open_cost_long"] / position["volume_long"] * volume_long
            position["position_cost_long"] += volume_long * position["last_price"] * volume_multiple if volume_long > 0 else position["position_cost_long"] / position["volume_long"] * volume_long
            position["volume_long"] += volume_long
            position["open_price_long"] = position["open_cost_long"] / volume_multiple / position["volume_long"] if position["volume_long"] else float("nan")
            position["position_price_long"] = position["position_cost_long"] / volume_multiple / position["volume_long"] if position["volume_long"] else float("nan")
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
            self._adjust_account(float_profit=float_profit, position_profit=-close_profit, close_profit=close_profit, margin=margin)
        if volume_short:
            margin = volume_short * self.quotes[symbol]["margin"]
            close_profit = 0 if volume_short > 0 else (position["position_price_short"] - position["last_price"]) * -volume_short * volume_multiple
            float_profit = 0 if volume_short > 0 else position["float_profit_short"] / position["volume_short"] * volume_short
            position["open_cost_short"] += volume_short * position["last_price"] * volume_multiple if volume_short > 0 else position["open_cost_short"] / position["volume_short"] * volume_short
            position["position_cost_short"] += volume_short * position["last_price"] * volume_multiple if volume_short > 0 else position["position_cost_short"] / position["volume_short"] * volume_short
            position["volume_short"] += volume_short
            position["open_price_short"] = position["open_cost_short"] / volume_multiple / position["volume_short"] if position["volume_short"] else float("nan")
            position["position_price_short"] = position["position_cost_short"] / volume_multiple / position["volume_short"] if position["volume_short"] else float("nan")
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
            self._adjust_account(float_profit=float_profit, position_profit=-close_profit, close_profit=close_profit, margin=margin)
        self._send_position(position)
        return position["volume_long_his"] - position["volume_long_frozen_his"] >= 0 and position["volume_long_today"] - position["volume_long_frozen_today"] >= 0 and\
               position["volume_short_his"] - position["volume_short_frozen_his"] >= 0 and position["volume_short_today"] - position["volume_short_frozen_today"] >= 0

    def _adjust_account(self, commission=0.0, frozen_margin=0.0, float_profit=0.0, position_profit=0.0, close_profit=0.0, margin=0.0):
        self.account["balance"] += position_profit + close_profit - commission
        self.account["available"] += position_profit + close_profit - commission - frozen_margin - margin
        self.account["float_profit"] += float_profit
        self.account["position_profit"] += position_profit
        self.account["close_profit"] += close_profit
        self.account["frozen_margin"] += frozen_margin
        self.account["margin"] += margin
        self.account["commission"] += commission
        self.account["risk_ratio"] = (self.account["frozen_margin"] + self.account["margin"]) / self.account["balance"] if self.account["balance"] else 0.0
        self._send_account()
        return self.account["available"] >= 0

    def _ensure_position(self, symbol):
        if symbol not in self.positions:
            self.positions[symbol] = {
                "symbol": symbol,
                "exchange_id": symbol.split(".", maxsplit=1)[0],
                "instrument_id": symbol.split(".", maxsplit=1)[1],
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
        return self.positions[symbol]

    def _ensure_quote(self, symbol):
        if symbol not in self.quotes:
            self.quotes[symbol] = {
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
        return self.quotes[symbol]

    def _send_order(self, order):
        self.diffs.append({"trade":{self.account_id:{"orders":{order["order_id"]:order.copy()}}}})

    def _send_position(self, position):
        self.diffs.append({"trade":{self.account_id:{"positions":{position["exchange_id"] + "." + position["instrument_id"]:position.copy()}}}})

    def _send_account(self):
        self.diffs.append({"trade":{self.account_id:{"accounts":{"CNY":self.account.copy()}}}})

    def _get_current_timestamp(self):
        return int(datetime.strptime(self.current_datetime, "%Y-%m-%d %H:%M:%S.%f").timestamp() * 1e6)*1000
