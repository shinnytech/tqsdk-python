#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'mayanqiong'


import asyncio
import math
from datetime import date, datetime
from typing import Union, Any

from tqsdk.backtest.utils import TqBacktestContinuous, TqBacktestDividend
from tqsdk.channel import TqChan
from tqsdk.datetime import _get_trading_day_start_time, _get_trading_day_end_time, _get_trading_day_from_timestamp
from tqsdk.diff import _merge_diff, _get_obj
from tqsdk.entity import Entity
from tqsdk.exceptions import BacktestFinished
from tqsdk.objs import Kline, Tick
from tqsdk.rangeset import _rangeset_range_union, _rangeset_difference, _rangeset_union
from tqsdk.utils import _generate_uuid, _query_for_quote


class BtQuote(Entity):
    """ Quote 是一个行情对象 """
    def __init__(self, api):
        self._api = api
        self.price_tick: float = float("nan")


class TqBacktest(object):
    """
    天勤回测类

    将该类传入 TqApi 的构造函数, 则策略就会进入回测模式。

    回测模式下 k线会在刚创建出来时和结束时分别更新一次, 在这之间 k线是不会更新的。

    回测模式下 quote 的更新频率由所订阅的 tick 和 k线周期确定:
        * 只要订阅了 tick, 则对应合约的 quote 就会使用 tick 生成, 更新频率也和 tick 一致, 但 **只有下字段** :
          datetime/ask&bid_price1/ask&bid_volume1/last_price/highest/lowest/average/volume/amount/open_interest/
          price_tick/price_decs/volume_multiple/max&min_limit&market_order_volume/underlying_symbol/strike_price

        * 如果没有订阅 tick, 但是订阅了 k线, 则对应合约的 quote 会使用 k线生成, 更新频率和 k线的周期一致， 如果订阅了某个合约的多个周期的 k线,
          则任一个周期的 k线有更新时, quote 都会更新. 使用 k线生成的 quote 的盘口由收盘价分别加/减一个最小变动单位, 并且 highest/lowest/average/amount
          始终为 nan, volume 始终为0

        * 如果即没有订阅 tick, 也没有订阅k线或 订阅的k线周期大于分钟线, 则 TqBacktest 会 **自动订阅分钟线** 来生成 quote

        * 如果没有订阅 tick, 但是订阅了 k线, 则对应合约的 quote **只有下字段** :
          datetime/ask&bid_price1/ask&bid_volume1/last_price/open_interest/
          price_tick/price_decs/volume_multiple/max&min_limit&market_order_volume/underlying_symbol/strike_price

    **注意** ：如果未订阅 quote，模拟交易在下单时会自动为此合约订阅 quote ，根据回测时 quote 的更新规则，如果此合约没有订阅K线或K线周期大于分钟线 **则会自动订阅一个分钟线** 。

    模拟交易要求报单价格大于等于对手盘价格才会成交, 例如下买单, 要求价格大于等于卖一价才会成交, 如果不能立即成交则会等到下次行情更新再重新判断。

    回测模式下 wait_update 每次最多推进一个行情时间。

    回测结束后会抛出 BacktestFinished 例外。

    对 **组合合约** 进行回测时需注意：只能通过订阅 tick 数据来回测，不能订阅K线，因为K线是由最新价合成的，而交易所发回的组合合约数据中无最新价。
    """

    def __init__(self, start_dt: Union[date, datetime], end_dt: Union[date, datetime]) -> None:
        """
        创建天勤回测类

        Args:
            start_dt (date/datetime): 回测起始时间, 如果类型为 date 则指的是交易日, 如果为 datetime 则指的是具体时间点

            end_dt (date/datetime): 回测结束时间, 如果类型为 date 则指的是交易日, 如果为 datetime 则指的是具体时间点
        """
        if isinstance(start_dt, datetime):
            self._start_dt = int(start_dt.timestamp() * 1e9)
        elif isinstance(start_dt, date):
            self._start_dt = _get_trading_day_start_time(
                int(datetime(start_dt.year, start_dt.month, start_dt.day).timestamp()) * 1000000000)
        else:
            raise Exception("回测起始时间(start_dt)类型 %s 错误, 请检查 start_dt 数据类型是否填写正确" % (type(start_dt)))
        if isinstance(end_dt, datetime):
            self._end_dt = int(end_dt.timestamp() * 1e9)
        elif isinstance(end_dt, date):
            self._end_dt = _get_trading_day_end_time(
                int(datetime(end_dt.year, end_dt.month, end_dt.day).timestamp()) * 1000000000)
        else:
            raise Exception("回测结束时间(end_dt)类型 %s 错误, 请检查 end_dt 数据类型是否填写正确" % (type(end_dt)))
        self._current_dt = self._start_dt
        # 记录当前的交易日 开始时间/结束时间
        self._trading_day = _get_trading_day_from_timestamp(self._current_dt)
        self._trading_day_start = _get_trading_day_start_time(self._trading_day)
        self._trading_day_end = _get_trading_day_end_time(self._trading_day)

    async def _run(self, api, sim_send_chan, sim_recv_chan, md_send_chan, md_recv_chan):
        """回测task"""
        self._api = api
        # 下载历史主连合约信息
        start_trading_day = _get_trading_day_from_timestamp(self._start_dt)  # 回测开始交易日
        end_trading_day = _get_trading_day_from_timestamp(self._end_dt)  # 回测结束交易日
        self._continuous_table = TqBacktestContinuous(start_dt=start_trading_day,
                                                      end_dt=end_trading_day,
                                                      headers=self._api._base_headers)
        self._stock_dividend = TqBacktestDividend(start_dt=start_trading_day,
                                                  end_dt=end_trading_day,
                                                  headers=self._api._base_headers)
        self._logger = api._logger.getChild("TqBacktest")  # 调试信息输出
        self._sim_send_chan = sim_send_chan
        self._sim_recv_chan = sim_recv_chan
        self._md_send_chan = md_send_chan
        self._md_recv_chan = md_recv_chan
        self._pending_peek = False
        self._data = Entity()  # 数据存储
        self._data._instance_entity([])
        self._prototype = {
            "quotes": {
                "#": BtQuote(self._api),  # 行情的数据原型
            },
            "klines": {
                "*": {
                    "*": {
                        "data": {
                            "@": Kline(self._api),  # K线的数据原型
                        }
                    }
                }
            },
            "ticks": {
                "*": {
                    "data": {
                        "@": Tick(self._api),  # Tick的数据原型
                    }
                }
            }
        }
        self._sended_to_api = {}  # 已经发给 api 的 rangeset  (symbol, dur)，只记录了 kline
        self._serials = {}  # 所有用户请求的 chart 序列，如果用户订阅行情，默认请求 1 分钟 Kline
        # gc 是会循环 self._serials，来计算用户需要的数据，self._serials 不应该被删除，
        self._generators = {}  # 所有用户请求的 chart 序列相应的 generator 对象，创建时与 self._serials 一一对应，会在一个序列计算到最后一根 kline 时被删除
        self._had_any_generator = False  # 回测过程中是否有过 generator 对象
        self._sim_recv_chan_send_count = 0  # 统计向下游发送的 diff 的次数，每 1w 次执行一次 gc
        self._quotes = {}  # 记录 min_duration 记录某一合约的最小duration； sended_init_quote 是否已经过这个合约的初始行情
        self._diffs: list[dict[str, Any]] = []
        self._is_first_send = True
        md_task = self._api.create_task(self._md_handler())
        try:
            await self._send_snapshot()
            async for pack in self._sim_send_chan:
                if pack["aid"] == "ins_query":
                    await self._md_send_chan.send(pack)
                    # 回测 query 不为空时需要ensure_query
                    # 1. 在api初始化时会发送初始化请求（2.5.0版本开始已经不再发送初始化请求），接着会发送peek_message，如果这里没有等到结果，那么在收到 peek_message 的时候，会发现没有数据需要发送，回测结束
                    # 2. api在发送请求后，会调用 wait_update 更新数据，如果这里没有等到结果，行情可能会被推进
                    # query 为空时，表示清空数据的请求，这个可以直接发出去，不需要等到收到回复
                    if pack["query"] != "":
                        await self._ensure_query(pack)
                    await self._send_diff()
                elif pack["aid"] == "subscribe_quote":
                    # todo: 回测时，用户如果先订阅日线，再订阅行情，会直接返回以日线 datetime 标识的行情信息，而不是当前真正的行情时间
                    self._diffs.append({
                        "ins_list": pack["ins_list"]
                    })
                    for ins in pack["ins_list"].split(","):
                        await self._ensure_quote(ins)
                    await self._send_diff()  # 处理上一次未处理的 peek_message
                elif pack["aid"] == "set_chart":
                    if pack["ins_list"]:
                        # 回测模块中已保证每次将一个行情时间的数据全部发送给api，因此更新行情时 保持与初始化时一样的charts信息（即不作修改）
                        self._diffs.append({
                            "charts": {
                                pack["chart_id"]: {
                                    # 两个id设置为0：保证api在回测中判断此值时不是-1，即直接通过对数据接收完全的验证
                                    "left_id": 0,
                                    "right_id": 0,
                                    "more_data": False,  # 直接发送False给api，表明数据发送完全，使api中通过数据接收完全的验证
                                    "state": pack
                                }
                            }
                        })
                        await self._ensure_serial(pack["ins_list"], pack["duration"], pack["chart_id"])
                    else:
                        self._diffs.append({
                            "charts": {
                                pack["chart_id"]: None
                            }
                        })
                    await self._send_diff()  # 处理上一次未处理的 peek_message
                elif pack["aid"] == "peek_message":
                    self._pending_peek = True
                    await self._send_diff()
        finally:
            # 关闭所有 generator
            for s in self._generators.values():
                await s.aclose()
            md_task.cancel()
            await asyncio.gather(md_task, return_exceptions=True)

    async def _md_handler(self):
        async for pack in self._md_recv_chan:
            await self._md_send_chan.send({
                "aid": "peek_message"
            })
            recv_quotes = False
            for d in pack.get("data", []):
                _merge_diff(self._data, d, self._prototype, False)
                # 收到的 quotes 转发给下游
                quotes = d.get("quotes", {})
                if quotes:
                    recv_quotes = True
                    quotes = self._update_valid_quotes(quotes)  # 删去回测 quotes 不应该下发的字段
                    self._diffs.append({"quotes": quotes})
                # 收到的 symbols 应该转发给下游
                if d.get("symbols"):
                    self._diffs.append({"symbols": d["symbols"]})
            # 如果没有收到 quotes（合约信息），或者当前的 self._data.get('quotes', {}) 里没有股票，那么不应该向 _diffs 里添加元素
            if recv_quotes:
                quotes_stock = self._stock_dividend._get_dividend(self._data.get('quotes', {}), self._trading_day)
                if quotes_stock:
                    self._diffs.append({"quotes": quotes_stock})

    def _update_valid_quotes(self, quotes):
        # 从 quotes 返回只剩余合约信息的字段的 quotes，防止发生未来数据发送给下游
        # backtest 模块会生成的数据
        invalid_keys = {f"{d}{i+1}" for d in ['ask_price', 'ask_volume', 'bid_price', 'bid_volume'] for i in range(5)}
        invalid_keys.union({'datetime', 'last_price', 'highest', 'lowest', 'average', 'volume', 'amount', 'open_interest'})
        invalid_keys.union({'cash_dividend_ratio', 'stock_dividend_ratio'})  # 这两个字段完全由 self._stock_dividend 负责处理
        # backtest 模块不会生成的数据，下游服务也不应该收到的数据
        invalid_keys.union({'open', 'close', 'settlement', 'lowest', 'lower_limit', 'upper_limit', 'pre_open_interest', 'pre_settlement', 'pre_close', 'expired'})
        for symbol, quote in quotes.items():
            [quote.pop(k, None) for k in invalid_keys]
            if symbol.startswith("KQ.m"):
                quote.pop("underlying_symbol", None)
            if quote.get('expire_datetime'):
                # 先删除所有的 quote 的 expired 字段，只在有 expire_datetime 字段时才会添加 expired 字段
                quote['expired'] = quote.get('expire_datetime') * 1e9 <= self._trading_day_start
        return quotes

    async def _send_snapshot(self):
        """发送初始合约信息"""
        async with TqChan(self._api, last_only=True) as update_chan:  # 等待与行情服务器连接成功
            self._data["_listener"].add(update_chan)
            while self._data.get("mdhis_more_data", True):
                await update_chan.recv()
        # 发送初始行情(合约信息截面)时
        quotes = {}
        for ins, quote in self._data["quotes"].items():
            if not ins.startswith("_"):
                trading_time = quote.get("trading_time", {})
                quotes[ins] = {
                    "open": None,  # 填写None: 删除api中的这个字段
                    "close": None,
                    "settlement": None,
                    "lower_limit": None,
                    "upper_limit": None,
                    "pre_open_interest": None,
                    "pre_settlement": None,
                    "pre_close": None,
                    "ins_class": quote.get("ins_class", ""),
                    "instrument_id": quote.get("instrument_id", ""),
                    "exchange_id": quote.get("exchange_id", ""),
                    "margin": quote.get("margin"),  # 用于内部实现模拟交易, 不作为api对外可用数据（即 Quote 类中无此字段）
                    "commission": quote.get("commission"),  # 用于内部实现模拟交易, 不作为api对外可用数据（即 Quote 类中无此字段）
                    "price_tick": quote["price_tick"],
                    "price_decs": quote["price_decs"],
                    "volume_multiple": quote["volume_multiple"],
                    "max_limit_order_volume": quote["max_limit_order_volume"],
                    "max_market_order_volume": quote["max_market_order_volume"],
                    "min_limit_order_volume": quote["min_limit_order_volume"],
                    "min_market_order_volume": quote["min_market_order_volume"],
                    "underlying_symbol": quote["underlying_symbol"],
                    "strike_price": quote["strike_price"],
                    "expired": quote.get('expire_datetime', float('nan')) <= self._trading_day_start,  # expired 默认值就是 False
                    "trading_time": {"day": trading_time.get("day", []), "night": trading_time.get("night", [])},
                    "expire_datetime": quote.get("expire_datetime"),
                    "delivery_month": quote.get("delivery_month"),
                    "delivery_year": quote.get("delivery_year"),
                    "option_class": quote.get("option_class", ""),
                    "product_id": quote.get("product_id", ""),
                }
        # 修改历史主连合约信息
        cont_quotes = self._continuous_table._get_history_cont_quotes(self._trading_day)
        for k, v in cont_quotes.items():
            quotes.setdefault(k, {})  # 实际上，初始行情截面中只有下市合约，没有主连
            quotes[k].update(v)
        self._diffs.append({
            "quotes": quotes,
            "ins_list": "",
            "mdhis_more_data": False,
            "_tqsdk_backtest": self._get_backtest_time()
        })

    async def _send_diff(self):
        """发送数据到 api, 如果 self._diffs 不为空则发送 self._diffs, 不推进行情时间, 否则将时间推进一格, 并发送对应的行情"""
        if self._pending_peek:
            if not self._diffs:
                quotes = await self._generator_diffs(False)
            else:
                quotes = await self._generator_diffs(True)
            for ins, diff in quotes.items():
                self._quotes[ins]["sended_init_quote"] = True
                for d in diff:
                    self._diffs.append({
                        "quotes": {
                            ins: d
                        }
                    })
            if self._diffs:
                # 发送数据集中添加 backtest 字段，开始时间、结束时间、当前时间，表示当前行情推进是由 backtest 推进
                self._diffs.append({"_tqsdk_backtest": self._get_backtest_time()})

                # 切换交易日，将历史的主连合约信息添加的 diffs
                if self._current_dt > self._trading_day_end:
                    # 使用交易日结束时间，每个交易日切换只需要计算一次交易日结束时间
                    # 相比发送 diffs 前每次都用 _current_dt 计算当前交易日，计算次数更少
                    self._trading_day = _get_trading_day_from_timestamp(self._current_dt)
                    self._trading_day_start = _get_trading_day_start_time(self._trading_day)
                    self._trading_day_end = _get_trading_day_end_time(self._trading_day)
                    self._diffs.append({
                        "quotes": self._continuous_table._get_history_cont_quotes(self._trading_day)
                    })
                    self._diffs.append({
                        "quotes": self._stock_dividend._get_dividend(self._data.get('quotes'), self._trading_day)
                    })
                    self._diffs.append({
                        "quotes": {k: {'expired': v.get('expire_datetime', float('nan')) <= self._trading_day_start}
                                   for k, v in self._data.get('quotes').items()}
                    })

                self._sim_recv_chan_send_count += 1
                if self._sim_recv_chan_send_count > 10000:
                    self._sim_recv_chan_send_count = 0
                    self._diffs.append(self._gc_data())
                rtn_data = {
                    "aid": "rtn_data",
                    "data": self._diffs,
                }
                self._diffs = []
                self._pending_peek = False
                await self._sim_recv_chan.send(rtn_data)

    async def _generator_diffs(self, keep_current):
        """
        keep_current 为 True 表示不会推进行情，为 False 表示需要推进行情
        即 self._diffs 为 None 并且 keep_current = True 会推进行情
        """
        quotes = {}
        while self._generators:
            # self._generators 存储了 generator，self._serials 记录一些辅助的信息
            min_request_key = min(self._generators.keys(), key=lambda serial: self._serials[serial]["timestamp"])
            timestamp = self._serials[min_request_key]["timestamp"]  # 所有已订阅数据中的最小行情时间
            quotes_diff = self._serials[min_request_key]["quotes"]
            if timestamp < self._current_dt and self._quotes.get(min_request_key[0], {}).get("sended_init_quote"):
                # 先订阅 A 合约，再订阅 A 合约日线，那么 A 合约的行情时间会回退: 2021-01-04 09:31:59.999999 -> 2021-01-01 18:00:00.000000
                # 如果当前 timestamp 小于 _current_dt，那么这个 quote_diff 不需要发到下游
                # 如果先订阅 A 合约（有夜盘），时间停留在夜盘开始时间， 再订阅 B 合约（没有夜盘），那么 B 合约的行情（前一天收盘时间）应该发下去，
                # 否则 get_quote(B) 等到收到行情才返回，会直接把时间推进到第二天白盘。
                quotes_diff = None
            # 推进时间，一次只会推进最多一个(补数据时有可能是0个)行情时间，并确保<=该行情时间的行情都被发出
            # 如果行情时间大于当前回测时间 则 判断是否diff中已有数据；否则表明此行情时间的数据未全部保存在diff中，则继续append
            if timestamp > self._current_dt:
                if self._diffs or keep_current:  # 如果diffs中已有数据：退出循环并发送数据给下游api
                    break
                else:
                    self._current_dt = timestamp  # 否则将回测时间更新至最新行情时间
            diff = self._serials[min_request_key]["diff"]
            self._diffs.append(diff)
            # klines 请求，需要记录已经发送 api 的数据
            for symbol in diff.get("klines", {}):
                for dur in diff["klines"][symbol]:
                    for kid in diff["klines"][symbol][dur]["data"]:
                        rs = self._sended_to_api.setdefault((symbol, int(dur)), [])
                        kid = int(kid)
                        self._sended_to_api[(symbol, int(dur))] = _rangeset_range_union(rs, (kid, kid + 1))
            quote_info = self._quotes[min_request_key[0]]
            if quotes_diff and (quote_info["min_duration"] != 0 or min_request_key[1] == 0):
                quotes[min_request_key[0]] = quotes_diff
            await self._fetch_serial(min_request_key)
        if self._had_any_generator and not self._generators and not self._diffs:  # 当无可发送数据时则抛出BacktestFinished例外,包括未订阅任何行情 或 所有已订阅行情的最后一笔行情获取完成
            self._api._print("回测结束")
            self._logger.debug("backtest finished")
            if self._current_dt < self._end_dt:
                self._current_dt = 2145888000000000000  # 一个远大于 end_dt 的日期 20380101
            await self._sim_recv_chan.send({
                "aid": "rtn_data",
                "data": [{"_tqsdk_backtest": self._get_backtest_time()}]
            })
            await self._api._wait_until_idle()
            raise BacktestFinished(self._api) from None
        return quotes

    def _get_backtest_time(self) -> dict:
        if self._is_first_send:
            self._is_first_send = False
            return {
                    "start_dt": self._start_dt,
                    "current_dt": self._current_dt,
                    "end_dt": self._end_dt
                }
        else:
            return {
                "current_dt": self._current_dt
            }

    async def _ensure_serial(self, ins, dur, chart_id=None):
        if (ins, dur) not in self._serials:
            quote = self._quotes.setdefault(ins, {  # 在此处设置 min_duration: 每次生成K线的时候会自动生成quote, 记录某一合约的最小duration
                "min_duration": dur
            })
            quote["min_duration"] = min(quote["min_duration"], dur)
            self._serials[(ins, dur)] = {
                "chart_id_set": {chart_id} if chart_id else set()  # 记录当前 serial 对应的 chart_id
            }
            self._generators[(ins, dur)] = self._gen_serial(ins, dur)
            self._had_any_generator = True
            await self._fetch_serial((ins, dur))
        elif chart_id:
            self._serials[(ins, dur)]["chart_id_set"].add(chart_id)

    async def _ensure_query(self, pack):
        """一定收到了对应 query 返回的包"""
        query_pack = {"query": pack["query"]}
        if query_pack.items() <= self._data.get("symbols", {}).get(pack["query_id"], {}).items():
            return
        async with TqChan(self._api, last_only=True) as update_chan:
            self._data["_listener"].add(update_chan)
            while not query_pack.items() <= self._data.get("symbols", {}).get(pack["query_id"], {}).items():
                await update_chan.recv()

    async def _ensure_quote(self, ins):
        # 在接新版合约服务器后，合约信息程序运行过程中查询得到的，这里不再能保证合约一定存在，需要添加 quote 默认值
        quote = _get_obj(self._data, ["quotes", ins], BtQuote(self._api))
        if math.isnan(quote.get("price_tick")):
            query_pack = _query_for_quote(ins)
            await self._md_send_chan.send(query_pack)
            async with TqChan(self._api, last_only=True) as update_chan:
                quote["_listener"].add(update_chan)
                while math.isnan(quote.get("price_tick")):
                    await update_chan.recv()
        if ins not in self._quotes or self._quotes[ins]["min_duration"] > 60000000000:
            await self._ensure_serial(ins, 60000000000)

    async def _fetch_serial(self, key):
        s = self._serials[key]
        try:
            s["timestamp"], s["diff"], s["quotes"] = await self._generators[key].__anext__()
        except StopAsyncIteration:
            del self._generators[key]  # 删除一个行情时间超过结束时间的 generator

    async def _gen_serial(self, ins, dur):
        """k线/tick 序列的 async generator, yield 出来的行情数据带有时间戳, 因此 _send_diff 可以据此归并"""
        # 先定位左端点, focus_datetime 是 lower_bound ,这里需要的是 upper_bound
        # 因此将 view_width 和 focus_position 设置成一样，这样 focus_datetime 所对应的 k线刚好位于屏幕外
        # 使用两个长度为 8964 的 chart，去缓存/回收下游需要的数据
        chart_id_a = _generate_uuid("PYSDK_backtest")
        chart_id_b = _generate_uuid("PYSDK_backtest")
        chart_info = {
            "aid": "set_chart",
            "chart_id": chart_id_a,
            "ins_list": ins,
            "duration": dur,
            "view_width": 8964,  # 设为8964原因：可满足用户所有的订阅长度，并在backtest中将所有的 相同合约及周期 的K线用同一个serial存储
            "focus_datetime": int(self._current_dt),
            "focus_position": 8964,
        }
        chart_a = _get_obj(self._data, ["charts", chart_id_a])
        chart_b = _get_obj(self._data, ["charts", chart_id_b])
        symbol_list = ins.split(',')
        current_id = None  # 当前数据指针
        if dur == 0:
            serials = [_get_obj(self._data, ["ticks", symbol_list[0]])]
        else:
            serials = [_get_obj(self._data, ["klines", s, str(dur)]) for s in symbol_list]
        async with TqChan(self._api, last_only=True) as update_chan:
            for serial in serials:
                serial["_listener"].add(update_chan)
            chart_a["_listener"].add(update_chan)
            chart_b["_listener"].add(update_chan)
            await self._md_send_chan.send(chart_info.copy())
            try:
                async for _ in update_chan:
                    chart = _get_obj(self._data, ["charts", chart_info["chart_id"]])
                    if not (chart_info.items() <= _get_obj(chart, ["state"]).items()):
                        # 当前请求还没收齐回应, 不应继续处理
                        continue
                    left_id = chart.get("left_id", -1)
                    right_id = chart.get("right_id", -1)
                    if (left_id == -1 and right_id == -1) or chart.get("more_data", True):
                        continue  # 定位信息还没收到, 数据没有完全收到
                    last_id = serials[0].get("last_id", -1)
                    if last_id == -1:
                        continue  # 数据序列还没收到
                    if self._data.get("mdhis_more_data", True):
                        self._data["_listener"].add(update_chan)
                        continue
                    else:
                        self._data["_listener"].discard(update_chan)
                    if current_id is None:
                        current_id = max(left_id, 0)
                    # 发送下一段 chart 8964 根 kline
                    chart_info["chart_id"] = chart_id_b if chart_info["chart_id"] == chart_id_a else chart_id_a
                    chart_info["left_kline_id"] = right_id
                    chart_info.pop("focus_datetime", None)
                    chart_info.pop("focus_position", None)
                    await self._md_send_chan.send(chart_info.copy())
                    while True:
                        if current_id > last_id:
                            # 当前 id 已超过 last_id
                            return
                        # 将订阅的8964长度的窗口中的数据都遍历完后，退出循环，然后再次进入并处理下一窗口数据
                        if current_id > right_id:
                            break
                        item = {k: v for k, v in serials[0]["data"].get(str(current_id), {}).items()}
                        if dur == 0:
                            diff = {
                                "ticks": {
                                    ins: {
                                        "last_id": current_id,
                                        "data": {
                                            str(current_id): item,
                                            str(current_id - 8964): None,
                                        }
                                    }
                                }
                            }
                            if item["datetime"] > self._end_dt:  # 超过结束时间
                                return
                            yield item["datetime"], diff, self._get_quotes_from_tick(item)
                        else:
                            timestamp = item["datetime"] if dur < 86400000000000 else _get_trading_day_start_time(
                                item["datetime"])
                            if timestamp > self._end_dt:  # 超过结束时间
                                return
                            binding = serials[0].get("binding", {})
                            diff = {
                                "klines": {
                                    symbol_list[0]: {
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
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            for chart_id in self._serials[(ins, dur)]["chart_id_set"]:
                                diff["charts"] = {
                                    chart_id: {
                                        "right_id": current_id  # api 中处理多合约 kline 需要 right_id 信息
                                    }
                                }
                            for i, symbol in enumerate(symbol_list):
                                if i == 0:
                                    diff_binding = diff["klines"][symbol_list[0]][str(dur)].setdefault("binding", {})
                                    continue
                                other_id = binding.get(symbol, {}).get(str(current_id), -1)
                                if other_id >= 0:
                                    diff_binding[symbol] = {str(current_id): str(other_id)}
                                    other_item = serials[i]["data"].get(str(other_id), {})
                                    diff["klines"][symbol] = {
                                        str(dur): {
                                            "last_id": other_id,
                                            "data": {
                                                str(other_id): {
                                                    "datetime": other_item["datetime"],
                                                    "open": other_item["open"],
                                                    "high": other_item["open"],
                                                    "low": other_item["open"],
                                                    "close": other_item["open"],
                                                    "volume": 0,
                                                    "open_oi": other_item["open_oi"],
                                                    "close_oi": other_item["open_oi"],
                                                }
                                            }
                                        }
                                    }
                            yield timestamp, diff, self._get_quotes_from_kline_open(
                                self._data["quotes"][symbol_list[0]],
                                timestamp,
                                item)  # K线刚生成时的数据都为开盘价
                            timestamp = item["datetime"] + dur - 1000 \
                                if dur < 86400000000000 else _get_trading_day_start_time(item["datetime"] + dur) - 1000
                            if timestamp > self._end_dt:  # 超过结束时间
                                return
                            diff = {
                                "klines": {
                                    symbol_list[0]: {
                                        str(dur): {
                                            "data": {
                                                str(current_id): item,
                                            }
                                        }
                                    }
                                }
                            }
                            for i, symbol in enumerate(symbol_list):
                                if i == 0:
                                    continue
                                other_id = binding.get(symbol, {}).get(str(current_id), -1)
                                if other_id >= 0:
                                    diff["klines"][symbol] = {
                                        str(dur): {
                                            "data": {
                                                str(other_id): {k: v for k, v in
                                                                serials[i]["data"].get(str(other_id), {}).items()}
                                            }
                                        }
                                    }
                            yield timestamp, diff, self._get_quotes_from_kline(self._data["quotes"][symbol_list[0]],
                                                                               timestamp,
                                                                               item)  # K线结束时生成quote数据
                        current_id += 1
            finally:
                # 释放chart资源
                chart_info["ins_list"] = ""
                await self._md_send_chan.send(chart_info.copy())
                chart_info["chart_id"] = chart_id_b if chart_info["chart_id"] == chart_id_a else chart_id_a
                await self._md_send_chan.send(chart_info.copy())

    def _gc_data(self):
        # api 应该删除的数据 diff
        need_rangeset = {}
        for ins, dur in self._serials:
            if dur == 0:  # tick 在发送数据过程中已经回收内存
                continue
            symbol_list = ins.split(',')
            for s in symbol_list:
                need_rangeset.setdefault((s, dur), [])
            main_serial = _get_obj(self._data, ["klines", symbol_list[0], str(dur)])
            main_serial_rangeset = self._sended_to_api.get((symbol_list[0], dur), [])  # 此 request 还没有给 api 发送过任何数据时为 []
            if not main_serial_rangeset:
                continue
            last_id = main_serial_rangeset[-1][-1] - 1
            assert last_id > -1
            need_rangeset[(symbol_list[0], dur)] = _rangeset_range_union(need_rangeset[(symbol_list[0], dur)],
                                                                         (last_id - 8963, last_id + 1))
            for symbol in symbol_list[1:]:
                symbol_need_rangeset = []
                symbol_binding = main_serial.get("binding", {}).get(symbol, {})
                if symbol_binding:
                    for i in range(last_id - 8963, last_id + 1):
                        other_id = symbol_binding.get(str(i))
                        if other_id:
                            symbol_need_rangeset = _rangeset_range_union(symbol_need_rangeset, (other_id, other_id + 1))
                if symbol_need_rangeset:
                    need_rangeset[(symbol, dur)] = _rangeset_union(need_rangeset[(symbol, dur)], symbol_need_rangeset)

        gc_rangeset = {}
        for key, rs in self._sended_to_api.items():
            gc_rangeset[key] = _rangeset_difference(rs, need_rangeset.get(key, []))

        # 更新 self._sended_to_api
        for key, rs in gc_rangeset.items():
            self._sended_to_api[key] = _rangeset_difference(self._sended_to_api[key], rs)

        gc_klines_diff = {}
        for (symbol, dur), rs in gc_rangeset.items():
            gc_klines_diff.setdefault(symbol, {})
            gc_klines_diff[symbol][str(dur)] = {"data": {}}
            serial = _get_obj(self._data, ["klines", symbol, str(dur)])
            serial_binding = serial.get("binding", None)
            if serial_binding:
                gc_klines_diff[symbol][str(dur)]["binding"] = {s: {} for s in serial_binding.keys()}
            for start_id, end_id in rs:
                for i in range(start_id, end_id):
                    gc_klines_diff[symbol][str(dur)]["data"][str(i)] = None
                    if serial_binding:
                        for s, s_binding in serial_binding.items():
                            gc_klines_diff[symbol][str(dur)]["binding"][s][str(i)] = None
        return {"klines": gc_klines_diff}

    @staticmethod
    def _get_quotes_from_tick(tick):
        quote = {k: v for k, v in tick.items()}
        quote["datetime"] = datetime.fromtimestamp(tick["datetime"] / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f")
        return [quote]

    @staticmethod
    def _get_quotes_from_kline_open(info, timestamp, kline):
        return [
            {  # K线刚生成时的数据都为开盘价
                "datetime": datetime.fromtimestamp(timestamp / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f"),
                "ask_price1": kline["open"] + info["price_tick"],
                "ask_volume1": 1,
                "bid_price1": kline["open"] - info["price_tick"],
                "bid_volume1": 1,
                "last_price": kline["open"],
                "highest": float("nan"),
                "lowest": float("nan"),
                "average": float("nan"),
                "volume": 0,
                "amount": float("nan"),
                "open_interest": kline["open_oi"],
            },
        ]

    @staticmethod
    def _get_quotes_from_kline(info, timestamp, kline):
        """
        分为三个包发给下游：
        1. 根据 diff 协议，对于用户收到的最终结果没有影响
        2. TqSim 撮合交易会按顺序处理收到的包，分别比较 high、low、close 三个价格对应的买卖价
        3. TqSim 撮合交易只用到了买卖价，所以最新价只产生一次 close，而不会发送三次
        """
        return [
            {
                "datetime": datetime.fromtimestamp(timestamp / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f"),
                "ask_price1": kline["high"] + info["price_tick"],
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
                "ask_price1": kline["low"] + info["price_tick"],
                "bid_price1": kline["low"] - info["price_tick"],
            },
            {
                "ask_price1": kline["close"] + info["price_tick"],
                "bid_price1": kline["close"] - info["price_tick"],
            }
        ]
