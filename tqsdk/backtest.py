#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import weakref
from datetime import date, datetime
from tqsdk.api import TqApi, TqChan
from tqsdk.exceptions import BacktestFinished


class TqBacktest(object):
    """
    天勤回测类

    将该类传入 TqApi 的构造函数, 则策略就会进入回测模式

    回测模式下 k线会在刚创建出来时和结束时分别更新一次, 在这之间 k线是不会更新的

    回测模式下 quote 的更新频率由所订阅的 tick 和 k线周期确定:
        * 只要订阅了 tick, 则对应合约的 quote 就会使用 tick 生成, 更新频率也和 tick 一致, 但只有下字段:
              datetime/ask&bid_price1/ask&bid_volume1/last_price/highest/lowest/average/volume/amount/open_interest/
              price_tick/price_decs/volume_multiple/max&min_limit&market_order_volume/underlying_symbol/strike_price

        * 如果没有订阅 tick, 但是订阅了 k线, 则对应合约的 quote 会使用 k线生成, 更新频率和 k线的周期一致， 如果订阅了某个合约的多个周期的 k线,
          则任一个周期的 k线有更新时, quote 都会更新. 使用 k线生成的 quote 的盘口由收盘价分别加/减一个最小变动单位, 并且 highest/lowest/average/amount
          始终为 nan, volume 始终为0

        * 如果即没有订阅 tick, 也没有订阅 k线或订阅的 k线周期大于分钟线, 则 TqBacktest 会自动订阅分钟线来生成 quote

    模拟交易要求报单价格大于等于对手盘价格才会成交, 例如下买单, 要求价格大于等于卖一价才会成交, 如果不能立即成交则会等到下次行情更新再重新判断

    回测模式下 wait_update 每次最多推进一个行情时间

    回测结束后会抛出 BacktestFinished 例外
    """
    def __init__(self, start_dt, end_dt):
        """
        创建天勤回测类

        Args:
            start_dt (date/datetime): 回测起始时间, 如果类型为 date 则指的是交易日, 如果为 datetime 则指的是具体时间点

            end_dt (date/datetime): 回测结束时间, 如果类型为 date 则指的是交易日, 如果为 datetime 则指的是具体时间点
        """
        if isinstance(start_dt, datetime):
            self.current_dt = int(start_dt.timestamp()*1e9)
        else:
            self.current_dt = TqApi._get_trading_day_start_time(int(datetime(start_dt.year, start_dt.month, start_dt.day).timestamp())*1000000000)
        if isinstance(end_dt, datetime):
            self.end_dt = int(end_dt.timestamp()*1e9)
        else:
            self.end_dt = TqApi._get_trading_day_end_time(int(datetime(end_dt.year, end_dt.month, end_dt.day).timestamp())*1000000000)

    async def _run(self, api, sim_send_chan, sim_recv_chan, md_send_chan, md_recv_chan):
        """回测task"""
        self.api = api
        self.logger = api.logger.getChild("TqBacktest")  # 调试信息输出
        self.sim_send_chan = sim_send_chan
        self.sim_recv_chan = sim_recv_chan
        self.md_send_chan = md_send_chan
        self.md_recv_chan = md_recv_chan
        self.pending_peek = False
        self.data = {"_path": [], "_listener": weakref.WeakSet()}  # 数据存储
        self.serials = {}  # 所有原始数据序列
        self.quotes = {}
        self.diffs = []
        md_task = self.api.create_task(self._md_handler())
        try:
            await self._send_snapshot()
            async for pack in self.sim_send_chan:
                self.logger.debug("TqBacktest message received: %s", pack)
                if pack["aid"] == "subscribe_quote":
                    self.diffs.append({"ins_list": pack["ins_list"]})
                    for ins in pack["ins_list"].split(","):
                        await self._ensure_quote(ins)
                    await self._send_diff()
                elif pack["aid"] == "set_chart":
                    if pack["ins_list"]:
                        self.diffs.append({"charts": {pack["chart_id"]: {"state": pack}}})
                        await self._ensure_serial(pack["ins_list"], pack["duration"])
                    else:
                        self.diffs.append({"charts": {pack["chart_id"]: None}})
                    await self._send_diff()
                elif pack["aid"] == "peek_message":
                    self.pending_peek = True
                    await self._send_diff()
        finally:
            # 关闭所有serials
            for s in self.serials.values():
                await s["generator"].aclose()
            md_task.cancel()

    async def _md_handler(self):
        async for pack in self.md_recv_chan:
            await self.md_send_chan.send({"aid": "peek_message"})
            for d in pack.get("data", []):
                TqApi._merge_diff(self.data, d, self.api.prototype, False)

    async def _send_snapshot(self):
        """发送初始合约信息"""
        async with TqChan(self.api, last_only=True) as update_chan:
            self.data["_listener"].add(update_chan)
            while self.data.get("mdhis_more_data", True):
                await update_chan.recv()
        # 发送合约信息截面
        quotes = {}
        for ins, quote in self.data["quotes"].items():
            if not ins.startswith("_"):
                quotes[ins] = {
                    "open": None,
                    "close": None,
                    "settlement": None,
                    "lower_limit": None,
                    "upper_limit": None,
                    "pre_open_interest": None,
                    "pre_settlement": None,
                    "pre_close": None,
                    "margin": quote.get("margin"),
                    "commission": quote.get("commission"),
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
        """发送数据到 api, 如果 self.diffs 不为空则发送 self.diffs, 不推进行情时间, 否则将时间推进一格, 并发送对应的行情"""
        if self.pending_peek:
            quotes = {}
            if not self.diffs:
                while self.serials:
                    min_serial = min(self.serials.keys(), key=lambda serial: self.serials[serial]["timestamp"])
                    timestamp = self.serials[min_serial]["timestamp"]
                    quotes_diff = self.serials[min_serial]["quotes"]
                    # 推进时间，一次只会推进最多一个(补数据时有可能是0个)行情时间，并确保<=该行情时间的行情都被发出
                    if timestamp > self.current_dt:
                        if self.diffs:
                            break
                        else:
                            self.current_dt = timestamp
                    self.diffs.append(self.serials[min_serial]["diff"])
                    quote_info = self.quotes[min_serial[0]]
                    if quotes_diff and (quote_info["min_duration"] != 0 or min_serial[1] == 0):
                        quotes[min_serial[0]] = quotes_diff
                    await self._fetch_serial(min_serial)
            for ins, diff in quotes.items():
                for d in diff:
                    self.diffs.append({"quotes": {ins: d}})
            if self.diffs:
                rtn_data = {
                    "aid": "rtn_data",
                    "data": self.diffs,
                }
                self.diffs = []
                self.pending_peek = False
                self.logger.debug("backtest message send: %s", rtn_data)
                await self.sim_recv_chan.send(rtn_data)

    async def _ensure_serial(self, ins, dur):
        if (ins, dur) not in self.serials:
            quote = self.quotes.setdefault(ins, {"min_duration": dur})
            quote["min_duration"] = min(quote["min_duration"], dur)
            self.serials[(ins, dur)] = {
                "generator": self._gen_serial(ins, dur),
            }
            await self._fetch_serial((ins, dur))

    async def _ensure_quote(self, ins):
        if ins not in self.quotes or self.quotes[ins]["min_duration"] > 60000000000:
            await self._ensure_serial(ins, 60000000000)

    async def _fetch_serial(self, serial):
        s = self.serials[serial]
        try:
            s["timestamp"], s["diff"], s["quotes"] = await s["generator"].__anext__()
        except StopAsyncIteration:
            del self.serials[serial]
            if not self.serials:
                raise BacktestFinished() from None

    async def _gen_serial(self, ins, dur):
        """k线/tick 序列的 async generator, yield 出来的行情数据带有时间戳, 因此 _send_diff 可以据此归并"""
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
            await self.md_send_chan.send(chart_info.copy())
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
                        if current_id > last_id:
                            # 当前 id 已超过 last_id
                            return
                        if current_id - chart_info.get("left_kline_id", left_id) > 5000:
                            # 当前 id 已超出订阅范围, 需重新订阅后续数据
                            chart_info["left_kline_id"] = current_id
                            chart_info.pop("focus_datetime", None)
                            chart_info.pop("focus_position", None)
                            await self.md_send_chan.send(chart_info.copy())
                        if current_id > right_id:
                            break
                        item = serial["data"].get(str(current_id), {}).copy()
                        del item["_path"]
                        del item["_listener"]
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
                            if item["datetime"] > self.end_dt:  # 超过结束时间
                                return
                            yield item["datetime"], diff, self._get_quotes_from_tick(item)
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
                            timestamp = item["datetime"] if dur < 86400000000000 else TqApi._get_trading_day_start_time(item["datetime"])
                            if timestamp > self.end_dt:  # 超过结束时间
                                return
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
                            timestamp = item["datetime"] + dur - 1000 if dur < 86400000000000 else TqApi._get_trading_day_end_time(item["datetime"])
                            if timestamp > self.end_dt:  # 超过结束时间
                                return
                            yield timestamp, diff, self._get_quotes_from_kline(self.data["quotes"][ins], timestamp, item)
                        current_id += 1
            finally:
                # 释放chart资源
                chart_info["ins_list"] = ""
                await self.md_send_chan.send(chart_info.copy())

    @staticmethod
    def _get_quotes_from_tick(tick):
        quote = tick.copy()
        quote["datetime"] = datetime.fromtimestamp(tick["datetime"] / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f")
        return [quote]

    @staticmethod
    def _get_quotes_from_kline(info, timestamp, kline):
        return [
            {
                "datetime": datetime.fromtimestamp(timestamp / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f"),
                "ask_price1":  kline["high"] + info["price_tick"],
                "ask_volume1": 1,
                "bid_price1": kline["high"] - info["price_tick"],
                "bid_volume1": 1,
                "last_price": kline["close"],
                "highest": float("nan"),
                "lowest": float("nan"),
                "average": float("nan"),
                "volume": 0,
                "amount": float("nan"),
                "open_interest": kline["close_oi"],
            },
            {
                "ask_price1":  kline["low"] + info["price_tick"],
                "bid_price1": kline["low"] - info["price_tick"],
            },
            {
                "ask_price1":  kline["close"] + info["price_tick"],
                "bid_price1": kline["close"] - info["price_tick"],
            }
        ]

