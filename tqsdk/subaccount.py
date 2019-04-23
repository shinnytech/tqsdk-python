#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'


class TqSubAccount(object):
    """
    天勤子账户类

    账户信息和主账户相同, 委托和成交按子帐号筛选, 持仓从0开始计算

    以上行为可能会在以后版本调整
    """
    def __init__(self, account_id):
        """
        创建天勤子账户类

        Args:
            account_id (str): 子帐号
        """
        self.account_id = account_id
        self.main_account_id = account_id.rsplit(".", 1)[0]

    async def _run(self, api, api_send_chan, api_recv_chan, main_send_chan, main_recv_chan):
        """子账户task"""
        self.api = api
        self.logger = api.logger.getChild("TqSubAccount")  # 调试信息输出
        self.api_send_chan = api_send_chan
        self.api_recv_chan = api_recv_chan
        self.main_send_chan = main_send_chan
        self.main_recv_chan = main_recv_chan
        self.pending_peek = False
        self.diffs = []
        self.positions = {}
        self.quotes = {}
        self.orders = {}
        self.trades = {}
        main_task = self.api.create_task(self._main_handler())  # 将所有 main_recv_chan 上收到的包投递到 api_send_chan 上
        try:
            async for pack in self.api_send_chan:
                self.logger.debug("TqSubAccount message received: %s", pack)
                if "_main_recv" in pack:
                    if pack["aid"] == "rtn_data":
                        self._main_recv(pack)
                        await self._send_diff()
                elif pack["aid"] == "peek_message":
                    self.pending_peek = True
                    await self._send_diff()
                    if self.pending_peek:
                        await self.main_recv_chan.send(pack)
                else:
                    await self.main_send_chan.send(pack)
        finally:
            main_task.cancel()

    async def _main_handler(self):
        async for pack in self.main_recv_chan:
            pack["_main_recv"] = True
            await self.api_send_chan.send(pack)

    async def _send_diff(self):
        if self.pending_peek and self.diffs:
            rtn_data = {
                "aid": "rtn_data",
                "data": self.diffs,
            }
            self.diffs = []
            self.pending_peek = False
            self.logger.debug("TqSubAccount message send: %s", rtn_data)
            await self.api_recv_chan.send(rtn_data)

    def _main_recv(self, pack):
        self.diffs.extend(pack["data"])
        self._porcess_quote(pack["data"])
        self._porcess_trade(pack["data"])
        self._porcess_order(pack["data"])
        self._porcess_account(pack["data"])
        self._porcess_trade_more_data(pack["data"])

    def _porcess_quote(self, diff):
        for d in diff:
            for symbol, quote_diff in d.get("quotes", {}).items():
                if quote_diff is None:
                    continue
                quote = self._ensure_quote(symbol)
                quote["volume_multiple"] = quote_diff.get("volume_multiple", quote["volume_multiple"])
                quote["margin"] = quote_diff.get("margin", quote["margin"])
                if "last_price" in quote_diff and type(quote_diff["last_price"]) is not str and quote_diff["last_price"] == quote_diff["last_price"]:
                    quote["last_price"] = quote_diff["last_price"]
                    if symbol in self.positions:
                        self._adjust_position(symbol, price=quote["last_price"])

    def _porcess_trade(self, diff):
        old = {}
        for d in diff:
            for tid, t in d.get("trade", {}).get(self.main_account_id, {}).get("trades", {}).items():
                if tid not in old:
                    old[tid] = self.trades.get(tid, {}).copy()
                self.trades.setdefault(tid, {}).update(t)
        for tid in sorted(old.keys(), key=lambda tid: int(self.trades[tid]["exchange_trade_id"])):
            ot = old[tid]
            if self.trades[tid]["user_id"] != self.account_id:
                continue
            vol = self.trades[tid]["volume"] - ot.get("volume", 0)
            price = self.trades[tid]["price"]
            dir = self.trades[tid]["direction"]
            offset = self.trades[tid]["offset"]
            symbol = self.trades[tid]["exchange_id"] + "." + self.trades[tid]["instrument_id"]
            if self.trades[tid]["exchange_id"] == "SHFE" or self.trades[tid]["exchange_id"] == "INE":
                priority = "H" if offset == "CLOSE" else "T"
            else:
                priority = "TH"
            if offset.startswith("CLOSE"):
                volume_long = 0 if dir == "BUY" else -vol
                volume_short = 0 if dir == "SELL" else -vol
            else:
                volume_long = 0 if dir == "SELL" else vol
                volume_short = 0 if dir == "BUY" else vol
            self._adjust_position(symbol, volume_long=volume_long, volume_short=volume_short, price=price,
                                  priority=priority)
            self._send_trade(tid)

    def _porcess_order(self, diff):
        oids = []
        symbols = set()
        for d in diff:
            for oid, o in d.get("trade", {}).get(self.main_account_id, {}).get("orders", {}).items():
                o["symbol"] = o["exchange_id"] + "." + o["instrument_id"]
                self.orders.setdefault(oid, {}).update(o)
                oids.append(oid)
        for oid in oids:
            o = self.orders[oid]
            if o["user_id"] != self.account_id:
                continue
            symbols.add(o["symbol"])
            self._send_order(oid)
        for s in symbols:
            self._adjust_position(s, frozen_volume=True)

    def _porcess_account(self, diff):
        for d in diff:
            accounts = d.get("trade", {}).get(self.main_account_id, {}).get("accounts", {})
            self.diffs.append({"trade": {self.account_id: {"accounts":accounts}}})

    def _porcess_trade_more_data(self, diff):
        for d in diff:
            trade_more_data = d.get("trade", {}).get(self.main_account_id, {}).get("trade_more_data", None)
            if trade_more_data is not None:
                self.diffs.append({"trade": {self.account_id: {"trade_more_data":trade_more_data}}})

    def _adjust_position(self, symbol, volume_long=0, volume_short=0, price=None, priority=None, frozen_volume=False):
        position = self._ensure_position(symbol)
        volume_multiple = self.quotes[symbol]["volume_multiple"]
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
            position["last_price"] = price
        if volume_long:
            frozen_volume = True
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
        if volume_short:
            frozen_volume = True
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
        if frozen_volume:
            position["volume_long_frozen"] = 0
            position["volume_long_frozen_today"] = 0
            position["volume_long_frozen_his"] = 0
            position["volume_short_frozen"] = 0
            position["volume_short_frozen_today"] = 0
            position["volume_short_frozen_his"] = 0
            for oid, o in self.orders.items():
                if o["user_id"] != self.account_id or o["symbol"] != symbol or not o["offset"].startswith("CLOSE"):
                    continue
                if o["direction"] == "SELL":
                    position["volume_long_frozen"] += o["volume_left"]
                    if o["exchange_id"] == "SHFE" or o["exchange_id"] == "INE":
                        if o["offset"] == "CLOSE":
                            position["volume_long_frozen_his"] += o["volume_left"]
                        else:
                            position["volume_long_frozen_today"] += o["volume_left"]
                    else:
                        position["volume_long_frozen_today"] += o["volume_left"]
                        if position["volume_long_frozen_today"] > position["volume_long_today"]:
                            position["volume_long_frozen_his"] += position["volume_long_frozen_today"] - position["volume_long_today"]
                            position["volume_long_frozen_today"] = position["volume_long_today"]
                else:
                    position["volume_short_frozen"] += o["volume_left"]
                    if o["exchange_id"] == "SHFE" or o["exchange_id"] == "INE":
                        if o["offset"] == "CLOSE":
                            position["volume_short_frozen_his"] += o["volume_left"]
                        else:
                            position["volume_short_frozen_today"] += o["volume_left"]
                    else:
                        position["volume_short_frozen_today"] += o["volume_left"]
                        if position["volume_short_frozen_today"] > position["volume_short_today"]:
                            position["volume_short_frozen_his"] += position["volume_short_frozen_today"] - position["volume_short_today"]
                            position["volume_short_frozen_today"] = position["volume_short_today"]
        self._send_position(symbol)

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
                "last_price": float("nan"),
                "volume_multiple": None,
                "margin": None,
            }
        return self.quotes[symbol]

    def _send_trade(self, tid):
        self.diffs.append({"trade":{self.account_id:{"trades":{tid:self.trades[tid].copy()}}}})

    def _send_order(self, oid):
        self.diffs.append({"trade":{self.account_id:{"orders":{oid:self.orders[oid].copy()}}}})

    def _send_position(self, symbol):
        self.diffs.append({"trade":{self.account_id:{"positions":{symbol:self.positions[symbol].copy()}}}})
