#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import statistics
from datetime import datetime
from tqsdk.api import TqApi, TqChan

class TqBacktest(object):
    """
    天勤回测类

    将该类传入 TqApi 的构造函数, 则策略就会进入回测模式

    回测模式下 k线会在刚创建出来时和结束时分别更新一次, 在这之间 k线是不会更新的

    回测模式下 quote 的更新频率由所订阅的 tick 和 k线周期确定:
        * 只要订阅了 tick, 则对应合约的 quote 就会使用 tick 生成, 更新频率也和 tick 一致, 但是会缺失部分字段:
              open/close/settlement/lower_limit/upper_limit/pre_open_interest/pre_settlement/pre_close/change/change_percent/expired
        * 如果没有订阅 tick, 但是订阅了 k线, 则对应合约的 quote 会使用 k线生成, 更新频率和 k线的周期一致， 如果订阅了某个合约的多个周期的 k线,
          则任一个周期的 k线有更新时, quote 都会更新. 使用 k线生成的 quote 的盘口由收盘价分别加/减一个最小变动单位, 并且 highest/lowest/average/amount
          始终为 nan, volume 始终为0
        * 如果即没有订阅 tick, 也没有订阅 k线, 则 TqBacktest 会自动订阅分钟线来生成 quote

    回测模式下的模拟交易要求报单价格大于等于对手盘价格才会成交, 例如下买单, 要求价格大于等于卖一价才会成交, 如果不能立即成交则会等到下次行情更新再重新判断

    回测模式下 wait_update 每次最多推进一个行情时间

    回测结束后会抛出 BacktestFinished 例外
    """
    def __init__(self, start_dt, end_dt, init_balance = 1000000.0):
        """
        创建天勤天勤回测类

        Args:
            start_dt (datetime): 回测起始时间

            end_dt (datetime): 回测结束时间

            init_balance (float): [可选]初始资金, 默认为一百万
        """
        self.current_dt = int(start_dt.timestamp()*1e9)
        self.end_dt = int(end_dt.timestamp()*1e9)
        self.init_balance = init_balance

    async def _run(self, api, send_chan, recv_chan, ws_send_chan, ws_recv_chan):
        self.api = api
        self.logger = api.logger.getChild("TqBacktest")  # 调试信息输出
        self.send_chan = send_chan
        self.recv_chan = recv_chan
        self.ws_send_chan = ws_send_chan
        self.ws_recv_chan = ws_recv_chan
        self.pending_peek = False
        self.data = {"_path": [], "_listener": set()}  # 数据存储
        self.serials = {}  # 所有原始数据序列
        self.quotes = {}  # 由于需要处理模拟交易，因此需要额外记下最新行情及所有挂单
        self.diffs = []
        self.statistics = {
            "last_balance": self.init_balance,
            "next_time": self.current_dt + 7 * 24 * 3600 * 1000000000,
            "weekly_yield": [],
            "sharpe_ratio": float("nan"),
            "max_balance": self.init_balance,
            "max_balance_time": None,
            "max_drawdown": 0,
            "longest_drawdown_period": 0,
        }
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
        ws_task = self.api.create_task(self._ws_handler())
        try:
            await self._send_snapshot()
            async for pack in self.send_chan:
                self.logger.debug("backtest message received: %s", pack)
                if pack["aid"] == "subscribe_quote":
                    self.diffs.append({"ins_list":pack["ins_list"]})
                    for ins in pack["ins_list"].split(","):
                        await self._ensure_quote(ins)
                    await self._send_diff()
                elif pack["aid"] == "set_chart":
                    self.diffs.append({"charts": {pack["chart_id"]: {"state": pack}}})
                    await self._ensure_serial(pack["ins_list"], pack["duration"])
                    await self._send_diff()
                elif pack["aid"] == "peek_message":
                    self.pending_peek = True
                    await self._send_diff()
                elif pack["aid"] == "insert_order":
                    symbol = pack["exchange_id"] + "." + pack["instrument_id"]
                    await self._ensure_quote(symbol)
                    quote = self.quotes[symbol]
                    if self._init_order(quote, pack):
                        await self._match_order(quote, pack)
                    await self._send_diff()
                elif pack["aid"] == "cancel_order":
                    for quote in self.quotes.values():
                        if "orders" in quote and pack["order_id"] in quote["orders"]:
                            self._del_order(quote, quote["orders"][pack["order_id"]], "已撤单")
                            await self._send_diff()
                            break
        finally:
            # 关闭所有serials
            for s in self.serials.values():
                await s["generator"].aclose()
            await self.send_chan.close()
            await self.recv_chan.close()
            await self.ws_recv_chan.close()
            await ws_task

    async def _ws_handler(self):
        async for pack in self.ws_recv_chan:
            for d in pack.get("data", []):
                TqApi._merge_diff(self.data, d, self.api.prototype)

    async def _send_snapshot(self):
        async with TqChan(self.api, last_only=True) as update_chan:
            self.data["_listener"].add(update_chan)
            while self.data.get("mdhis_more_data", True):
                await update_chan.recv()
        # 发送合约信息截面
        quotes = {}
        for ins, quote in self.data["quotes"].items():
            if not ins.startswith("_"):
                quotes[ins] = {
                    "datetime": "",
                    "ask_price1": float("nan"),
                    "ask_volume1": 0,
                    "bid_price1": float("nan"),
                    "bid_volume1": 0,
                    "last_price": float("nan"),
                    "highest": float("nan"),
                    "lowest": float("nan"),
                    "open": None,
                    "close": None,
                    "average": float("nan"),
                    "volume": 0,
                    "amount": float("nan"),
                    "open_interest": 0,
                    "settlement": None,
                    "lower_limit": None,
                    "upper_limit": None,
                    "pre_open_interest": None,
                    "pre_settlement": None,
                    "pre_close": None,
                    "price_tick": quote["price_tick"],
                    "price_decs": quote["price_decs"],
                    "volume_multiple": quote["volume_multiple"],
                    "max_limit_order_volume": quote["max_limit_order_volume"],
                    "max_market_order_volume": quote["max_market_order_volume"],
                    "min_limit_order_volume": quote["min_limit_order_volume"],
                    "min_market_order_volume": quote["min_market_order_volume"],
                    "underlying_symbol": quote["underlying_symbol"],
                    "strike_price": quote["strike_price"],
                    "change": None,
                    "change_percent": None,
                    "expired": None,
                }
        self.diffs.append({
            "quotes": quotes,
            "ins_list": "",
            "mdhis_more_data": False,
        })

    async def _send_diff(self):
        if self.pending_peek:
            if not self.diffs:
                while self.serials:
                    min_serial = min(self.serials.keys(), key=lambda serial: self.serials[serial]["timestamp"])
                    timestamp = self.serials[min_serial]["timestamp"]
                    last_quote = self.serials[min_serial]["last_quote"]
                    # 推进时间，一次只会推进最多一个(补数据时有可能是0个)行情时间，并确保<=该行情时间的行情都被发出
                    if timestamp > self.current_dt:
                        if self.diffs:
                            break
                        else:
                            self.current_dt = timestamp
                    self.diffs.append(self.serials[min_serial]["diff"])
                    quote = self.quotes[min_serial[0]]
                    if last_quote and (quote["min_duration"] != 0 or min_serial[1] == 0):
                        self.diffs.append({"quotes": {min_serial[0]: last_quote}})
                        quote.update(last_quote)
                    await self._fetch_serial(min_serial)
                    if self.current_dt >= self.statistics["next_time"]:
                        while self.current_dt >= self.statistics["next_time"]:
                            self.statistics["next_time"] += 7 * 24 * 3600 * 1000000000
                        self.statistics["weekly_yield"].append(self.account["balance"]/self.statistics["last_balance"] - 1)
                        self.statistics["last_balance"] = self.account["balance"]
                        mean = statistics.mean(self.statistics["weekly_yield"])
                        rf = 0.0004
                        stddev = statistics.pstdev(self.statistics["weekly_yield"], mu=mean)
                        self.statistics["sharpe_ratio"] = (mean - rf) / stddev if stddev else float("inf")
                    if timestamp == self.current_dt:
                        await self._match_orders(quote)
                        self._adjust_position(min_serial[0], price=quote.get("last_price"))
            if self.diffs:
                rtn_data = {
                    "aid": "rtn_data",
                    "data": self.diffs,
                }
                self.diffs = []
                self.pending_peek = False
                self.logger.debug("backtest message send: %s", rtn_data)
                await self.recv_chan.send(rtn_data)

    async def _ensure_serial(self, ins, dur):
        if (ins, dur) not in self.serials:
            quote = self.quotes.setdefault(ins, {"symbol": ins, "orders": {}, "min_duration": dur})
            quote["min_duration"] = min(quote["min_duration"], dur)
            self.serials[(ins, dur)] = {
                "generator": self._gen_serial(ins, dur),
            }
            await self._fetch_serial((ins, dur))

    async def _ensure_quote(self, ins):
        if ins not in self.quotes:
            await self._ensure_serial(ins, 60000000000)

    async def _fetch_serial(self, serial):
        s = self.serials[serial]
        try:
            s["timestamp"], s["diff"], s["last_quote"] = await s["generator"].__anext__()
        except StopAsyncIteration:
            del self.serials[serial]
            if not self.serials:
                self.statistics["yield"] = self.account["balance"] / self.init_balance - 1
                raise BacktestFinished(self.statistics) from None

    async def _gen_serial(self, ins, dur):
        # 先定位左端点, focus_datetime 是 lower_bound ,这里需要的是 upper_bound
        # 因此将 view_width 和 focus_position 设置成一样，这样 focus_datetime 所对应的 k线刚好位于屏幕外
        chart_info = {
            "aid": "set_chart",
            "chart_id": TqApi._generate_chart_id("backtest", ins, dur//1000000000),
            "ins_list": ins,
            "duration": dur,
            "view_width": 8964,
            "focus_datetime": int(self.current_dt),
            "focus_position": 8964,
        }
        chart = TqApi._get_obj(self.data, ["charts", chart_info["chart_id"]])
        current_id = None  # 当前数据指针
        serial = TqApi._get_obj(self.data, ["klines", ins, str(dur)] if dur != 0 else ["ticks", ins])
        async with TqChan(self.api, last_only=True) as update_chan:
            serial["_listener"].add(update_chan)
            chart["_listener"].add(update_chan)
            await self.ws_send_chan.send(chart_info.copy())
            try:
                async for _ in update_chan:
                    if not (chart_info.items() <= TqApi._get_obj(chart, ["state"]).items()):
                        # 当前请求还没收齐回应, 不应继续处理
                        continue
                    left_id = chart.get("left_id", -1)
                    right_id = chart.get("right_id", -1)
                    last_id = serial.get("last_id", -1)
                    if (left_id == -1 and right_id == -1) or last_id == -1:
                        # 定位信息还没收到, 或数据序列还没收到
                        continue
                    if self.data.get("mdhis_more_data", True):
                        self.data["_listener"].add(update_chan)
                        continue
                    else:
                        self.data["_listener"].discard(update_chan)
                    if current_id is None:
                        current_id = max(left_id, 0)
                    while True:
                        if current_id - chart_info.get("left_kline_id", left_id) > 5000:
                            # 当前 id 已超出订阅范围, 需重新订阅后续数据
                            chart_info["left_kline_id"] = current_id
                            chart_info.pop("focus_datetime", None)
                            chart_info.pop("focus_position", None)
                            await self.ws_send_chan.send(chart_info.copy())
                        if current_id > right_id:
                            break
                        item = serial["data"].get(str(current_id), {}).copy()
                        del item["_path"]
                        del item["_listener"]
                        if current_id == last_id or item["datetime"] + dur > self.end_dt:
                            # 当前 id 已达到 last_id
                            return
                        if dur == 0:
                            diff = {
                                "ticks": {
                                    ins: {
                                        "last_id": current_id,
                                        "data": {
                                            str(current_id): item,
                                            str(current_id-8964): None,
                                        }
                                    }
                                }
                            }
                            yield item["datetime"], diff, self._get_quote_from_tick(item)
                        else:
                            diff = {
                                "klines": {
                                    ins: {
                                        str(dur): {
                                            "last_id": current_id,
                                            "data": {
                                                str(current_id): {
                                                    "datetime": item["datetime"],
                                                    "open": item["open"],
                                                    "high": item["open"],
                                                    "low": item["open"],
                                                    "close": item["open"],
                                                    "volume": 0,
                                                    "open_oi": item["open_oi"],
                                                    "close_oi": item["open_oi"],
                                                },
                                                str(current_id-8964): None,
                                            }
                                        }
                                    }
                                }
                            }
                            timestamp = item["datetime"] if dur < 86400000000000 else self._get_trading_day_start_time(item["datetime"])
                            yield timestamp, diff, None
                            diff = {
                                "klines": {
                                    ins: {
                                        str(dur): {
                                            "data": {
                                                str(current_id): item,
                                            }
                                        }
                                    }
                                }
                            }
                            timestamp = item["datetime"] + dur - 1 if dur < 86400000000000 else self._get_trading_day_end_time(item["datetime"])
                            yield timestamp, diff, self._get_quote_from_kline(self.data["quotes"][ins], item)
                        current_id += 1
            finally:
                # 释放chart资源
                chart_info["ins_list"] = ""
                await self.ws_send_chan.send(chart_info.copy())

    async def _match_orders(self, quote):
        for order in list(quote.get("orders", {}).values()):
            await self._match_order(quote, order)

    async def _match_order(self, quote, order):
        ask_price = quote.get("ask_price1")
        bid_price = quote.get("bid_price1")
        if ask_price is None or bid_price is None:
            return
        if "limit_price" not in order:
            price = ask_price if order["direction"] == "BUY" else bid_price
            if price != price:
                self._del_order(quote, order, "市价指令剩余撤销")
                return
        elif order["direction"] == "BUY" and order["limit_price"] >= ask_price:
            price = order["limit_price"]
        elif order["direction"] == "SELL" and order["limit_price"] <= bid_price:
            price = order["limit_price"]
        else:
            return
        trade = {
            "order_id": order["order_id"],
            "trade_id": order["order_id"] + "|" + str(order["volume_left"]),
            "exchange_trade_id": order["order_id"] + "|" + str(order["volume_left"]),
            "exchange_id": order["exchange_id"],
            "instrument_id": order["instrument_id"],
            "direction": order["direction"],
            "offset": order["offset"],
            "price": price,
            "volume": order["volume_left"],
            "trade_date_time": self.current_dt,
        }
        self.diffs.append({"trade":{self.api.account_id:{"trades":{trade["trade_id"]:trade}}}})
        if order["offset"].startswith("CLOSE"):
            volume_long = 0 if order["direction"] == "BUY" else -order["volume_left"]
            volume_short = 0 if order["direction"] == "SELL" else -order["volume_left"]
            self._adjust_position(quote["symbol"], volume_long_frozen=volume_long, volume_short_frozen=volume_short)
        else:
            volume_long = 0 if order["direction"] == "SELL" else order["volume_left"]
            volume_short = 0 if order["direction"] == "BUY" else order["volume_left"]
        self._adjust_position(quote["symbol"], volume_long=volume_long, volume_short=volume_short, price=price)
        self._adjust_account(commission=self.data["quotes"][quote["symbol"]]["commission"] * order["volume_left"])
        order["volume_left"] = 0
        self._del_order(quote, order, "全部成交")

    def _init_order(self, quote, order):
        quote["orders"][order["order_id"]] = order
        order["exchange_order_id"] = order["order_id"]
        order["volume_orign"] = order["volume"]
        order["volume_left"] = order["volume"]
        order["frozen_margin"] = 0.0
        order["insert_date_time"] = self.current_dt
        order["last_msg"] = "报单成功"
        order["status"] = "ALIVE"
        del order["aid"]
        del order["volume"]
        if order["offset"].startswith("CLOSE"):
            volume_long_frozen = 0 if order["direction"] == "BUY" else order["volume_left"]
            volume_short_frozen = 0 if order["direction"] == "SELL" else order["volume_left"]
            if not self._adjust_position(quote["symbol"], volume_long_frozen=volume_long_frozen, volume_short_frozen=volume_short_frozen):
                self._del_order(quote, order, "平仓手数不足")
                return False
        else:
            if quote["symbol"] not in self.data["quotes"]:
                self._del_order(quote, order, "合约不存在")
                return False
            order["frozen_margin"] = self.data["quotes"][quote["symbol"]]["margin"] * order["volume_orign"]
            if not self._adjust_account(frozen_margin = order["frozen_margin"]):
                self._del_order(quote, order, "开仓资金不足")
                return False
        self._send_order(order)
        return True

    def _del_order(self, quote, order, msg):
        if order["offset"].startswith("CLOSE"):
            volume_long_frozen = 0 if order["direction"] == "BUY" else -order["volume_left"]
            volume_short_frozen = 0 if order["direction"] == "SELL" else -order["volume_left"]
            self._adjust_position(quote["symbol"], volume_long_frozen=volume_long_frozen, volume_short_frozen=volume_short_frozen)
        else:
            self._adjust_account(frozen_margin=-order["frozen_margin"])
            order["frozen_margin"] = 0.0
        order["last_msg"] = msg
        order["status"] = "FINISHED"
        self._send_order(order)
        del quote["orders"][order["order_id"]]

    def _adjust_position(self, symbol, volume_long_frozen=0, volume_short_frozen=0, volume_long=0, volume_short=0, price=None):
        position = self._ensure_position(symbol)
        volume_multiple = self.data["quotes"][symbol]["volume_multiple"]
        if volume_long_frozen:
            position["volume_long_frozen"] += volume_long_frozen
            position["volume_long_frozen_today"] += volume_long_frozen
        if volume_short_frozen:
            position["volume_short_frozen"] += volume_short_frozen
            position["volume_short_frozen_today"] += volume_short_frozen
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
                self._adjust_account(float_profit=float_profit)
            position["last_price"] = price
        if volume_long:
            margin = volume_long * self.data["quotes"][symbol]["margin"]
            close_profit = 0 if volume_long > 0 else (position["last_price"] - position["open_price_long"]) * -volume_long * volume_multiple
            float_profit = -close_profit
            position["open_cost_long"] += volume_long * position["last_price"] * volume_multiple if volume_long > 0 else position["open_cost_long"] / position["volume_long"] * volume_long
            position["position_cost_long"] = position["open_cost_long"]
            position["volume_long_today"] += volume_long
            position["volume_long"] += volume_long
            position["open_price_long"] = position["open_cost_long"] / volume_multiple / position["volume_long"] if position["volume_long"] else float("nan")
            position["position_price_long"] = position["open_price_long"]
            position["float_profit_long"] += float_profit
            position["float_profit"] += float_profit
            position["position_profit_long"] += float_profit
            position["position_profit"] += float_profit
            position["margin_long"] += margin
            position["margin"] += margin
            self._adjust_account(close_profit=close_profit, margin = margin)
        if volume_short:
            margin = volume_short * self.data["quotes"][symbol]["margin"]
            close_profit = 0 if volume_short > 0 else (position["open_price_short"] - position["last_price"]) * -volume_short * volume_multiple
            float_profit = -close_profit
            position["open_cost_short"] += volume_short * position["last_price"] * volume_multiple if volume_short > 0 else position["open_cost_short"] / position["volume_short"] * volume_short
            position["position_cost_short"] = position["open_cost_short"]
            position["volume_short_today"] += volume_short
            position["volume_short"] += volume_short
            position["open_price_short"] = position["open_cost_short"] / volume_multiple / position["volume_short"] if position["volume_short"] else float("nan")
            position["position_price_short"] = position["open_price_short"]
            position["float_profit_short"] += float_profit
            position["float_profit"] += float_profit
            position["position_profit_short"] += float_profit
            position["position_profit"] += float_profit
            position["margin_short"] += margin
            position["margin"] += margin
            self._adjust_account(close_profit=close_profit, margin = margin)
        self._send_position(position)
        return position["volume_long"] - position["volume_long_frozen"] >= 0 and position["volume_short"] - position["volume_short_frozen"] >= 0


    def _adjust_account(self, commission=0.0, frozen_margin=0.0, float_profit=0.0,close_profit=0.0, margin=0.0):
        self.account["balance"] += float_profit + close_profit - commission
        self.account["available"] += float_profit + close_profit - commission - frozen_margin - margin
        self.account["float_profit"] += float_profit
        self.account["position_profit"] += float_profit
        self.account["close_profit"] += close_profit
        self.account["frozen_margin"] += frozen_margin
        self.account["margin"] += margin
        self.account["commission"] += commission
        self.account["risk_ratio"] = (self.account["frozen_margin"] + self.account["margin"]) / self.account["balance"] if self.account["balance"] else 0.0
        self._send_account()
        if self.account["balance"] >= self.statistics["max_balance"]:
            self.statistics["max_balance"] = self.account["balance"]
            self.statistics["max_balance_time"] = self.current_dt
        if self.account["balance"] < self.statistics["max_balance"]:
            drawdown = 1 - self.account["balance"] / self.statistics["max_balance"]
            drawdown_period = self.current_dt - self.statistics["max_balance_time"]
            if drawdown > self.statistics["max_drawdown"]:
                self.statistics["max_drawdown"] = drawdown
            if drawdown_period > self.statistics["longest_drawdown_period"]:
                self.statistics["longest_drawdown_period"] = drawdown_period
        return self.account["available"] >= 0

    def _ensure_position(self, symbol):
        if symbol not in self.positions:
            self.positions[symbol] = {
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

    def _send_order(self, order):
        self.diffs.append({"trade":{self.api.account_id:{"orders":{order["order_id"]:order.copy()}}}})

    def _send_position(self, position):
        self.diffs.append({"trade":{self.api.account_id:{"positions":{position["exchange_id"] + "." + position["instrument_id"]:position.copy()}}}})

    def _send_account(self):
        self.diffs.append({"trade":{self.api.account_id:{"accounts":{"CNY":self.account.copy()}}}})

    @staticmethod
    def _get_quote_from_tick(tick):
        quote = tick.copy()
        quote["datetime"] = datetime.fromtimestamp(tick["datetime"] / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f")
        return quote

    @staticmethod
    def _get_quote_from_kline(info, kline):
        quote = {
            "datetime": datetime.fromtimestamp(kline["datetime"] / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f"),
            "ask_price1":  kline["close"] + info["price_tick"],
            "ask_volume1": 1,
            "bid_price1": kline["close"] - info["price_tick"],
            "bid_volume1": 1,
            "last_price": kline["close"],
            "highest": float("nan"),
            "lowest": float("nan"),
            "average": float("nan"),
            "volume": 0,
            "amount": float("nan"),
            "open_interest": kline["close_oi"],
        }
        return quote

    @staticmethod
    def _get_trading_day_start_time(trading_day):
        begin_mark = 631123200000000000  # 1990-01-01
        start_time = trading_day - 21600000000000  # 6小时
        week_day = (start_time - begin_mark) // 86400000000000 % 7
        if week_day >= 5:
            start_time -= 86400000000000 * (week_day-4)
        return start_time

    @staticmethod
    def _get_trading_day_end_time(trading_day):
        return trading_day + 64799999999999  # 18小时

class BacktestFinished(Exception):
    def __init__(self, statistics):
        self.statistics = statistics
        message = "回测结束: 收益率 %.2f%% 夏普比率 %.3f 最大回撤 %.2f%%" % (statistics["yield"]*100, statistics["sharpe_ratio"], statistics["max_drawdown"] * 100)
        super().__init__(message)