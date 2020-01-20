#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import json
import time
import requests
import asyncio
from typing import Union
from datetime import date, datetime
from tqsdk.exceptions import BacktestFinished
from tqsdk.objs import Entity
import tqsdk.api


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
            self._start_dt = tqsdk.api.TqApi._get_trading_day_start_time(
                int(datetime(start_dt.year, start_dt.month, start_dt.day).timestamp()) * 1000000000)
        else:
            raise Exception("回测起始时间(start_dt)类型 %s 错误, 请检查 start_dt 数据类型是否填写正确" % (type(start_dt)))
        if isinstance(end_dt, datetime):
            self._end_dt = int(end_dt.timestamp() * 1e9)
        elif isinstance(end_dt, date):
            self._end_dt = tqsdk.api.TqApi._get_trading_day_end_time(
                int(datetime(end_dt.year, end_dt.month, end_dt.day).timestamp()) * 1000000000)
        else:
            raise Exception("回测结束时间(end_dt)类型 %s 错误, 请检查 end_dt 数据类型是否填写正确" % (type(end_dt)))
        self._current_dt = self._start_dt

    async def _run(self, api, sim_send_chan, sim_recv_chan, md_send_chan, md_recv_chan):
        """回测task"""
        self._api = api
        self._logger = api._logger.getChild("TqBacktest")  # 调试信息输出
        self._sim_send_chan = sim_send_chan
        self._sim_recv_chan = sim_recv_chan
        self._md_send_chan = md_send_chan
        self._md_recv_chan = md_recv_chan
        self._pending_peek = False
        self._data = Entity()  # 数据存储
        self._data._instance_entity([])
        self._serials = {}  # 所有原始数据序列
        self._quotes = {}
        self._diffs = []
        self._is_first_send = True
        md_task = self._api.create_task(self._md_handler())
        try:
            await self._send_snapshot()
            async for pack in self._sim_send_chan:
                self._logger.debug("TqBacktest message received: %s", pack)
                if pack["aid"] == "subscribe_quote":
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
                        await self._ensure_serial(pack["ins_list"], pack["duration"])
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
            # 关闭所有serials
            for s in self._serials.values():
                await s["generator"].aclose()
            md_task.cancel()

    async def _md_handler(self):
        async for pack in self._md_recv_chan:
            await self._md_send_chan.send({
                "aid": "peek_message"
            })
            for d in pack.get("data", []):
                tqsdk.api.TqApi._merge_diff(self._data, d, self._api._prototype, False)

    async def _send_snapshot(self):
        """发送初始合约信息"""
        async with tqsdk.api.TqChan(self._api, last_only=True) as update_chan:  # 等待与行情服务器连接成功
            self._data["_listener"].add(update_chan)
            while self._data.get("mdhis_more_data", True):
                await update_chan.recv()
        # 发送合约信息截面
        quotes = {}
        for ins, quote in self._data["quotes"].items():
            if not ins.startswith("_"):
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
                    'instrument_id': quote.get("instrument_id", ""),
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
                    "expired": None,
                    "trading_time": quote.get("trading_time"),
                    "expire_datetime": quote.get("expire_datetime"),
                    "delivery_month": quote.get("delivery_month"),
                    "delivery_year": quote.get("delivery_year"),
                }
        self._diffs.append({
            "quotes": quotes,
            "ins_list": "",
            "mdhis_more_data": False,
        })

    async def _send_diff(self):
        """发送数据到 api, 如果 self._diffs 不为空则发送 self._diffs, 不推进行情时间, 否则将时间推进一格, 并发送对应的行情"""
        if self._pending_peek:
            quotes = {}
            if not self._diffs:
                while self._serials:
                    min_serial = min(self._serials.keys(), key=lambda serial: self._serials[serial]["timestamp"])
                    timestamp = self._serials[min_serial]["timestamp"]  # 所有已订阅数据中的最小行情时间
                    quotes_diff = self._serials[min_serial]["quotes"]
                    # 推进时间，一次只会推进最多一个(补数据时有可能是0个)行情时间，并确保<=该行情时间的行情都被发出
                    # 如果行情时间大于当前回测时间 则 判断是否diff中已有数据；否则表明此行情时间的数据未全部保存在diff中，则继续append
                    if timestamp > self._current_dt:
                        if self._diffs:  # 如果diffs中已有数据：退出循环并发送数据给下游api
                            break
                        else:
                            self._current_dt = timestamp  # 否则将回测时间更新至最新行情时间
                    self._diffs.append(self._serials[min_serial]["diff"])
                    quote_info = self._quotes[min_serial[0]]
                    if quotes_diff and (quote_info["min_duration"] != 0 or min_serial[1] == 0):
                        quotes[min_serial[0]] = quotes_diff
                    await self._fetch_serial(min_serial)
                if not self._serials and not self._diffs:  # 当无可发送数据时则抛出BacktestFinished例外,包括未订阅任何行情 或 所有已订阅行情的最后一笔行情获取完成
                    self._logger.warning("回测结束")
                    if self._current_dt < self._end_dt:
                        self._current_dt = 2145888000000000000  # 一个远大于 end_dt 的日期 20380101
                    await self._sim_recv_chan.send({
                        "aid": "rtn_data",
                        "data": [{
                            "_tqsdk_backtest": {
                                "start_dt": self._start_dt,
                                "current_dt": self._current_dt,
                                "end_dt": self._end_dt
                            }
                        }]
                    })
                    raise BacktestFinished(self._api) from None
            for ins, diff in quotes.items():
                for d in diff:
                    self._diffs.append({
                        "quotes": {
                            ins: d
                        }
                    })
            if self._diffs:
                # 发送数据集中添加 backtest 字段，开始时间、结束时间、当前时间，表示当前行情推进是由 backtest 推进
                if self._is_first_send:
                    self._diffs.append({
                        "_tqsdk_backtest": {
                            "start_dt": self._start_dt,
                            "current_dt": self._current_dt,
                            "end_dt": self._end_dt
                        }
                    })
                    self._is_first_send = False
                else:
                    self._diffs.append({
                        "_tqsdk_backtest": {
                            "current_dt": self._current_dt
                        }
                    })
                rtn_data = {
                    "aid": "rtn_data",
                    "data": self._diffs,
                }
                self._diffs = []
                self._pending_peek = False
                self._logger.debug("backtest message send: %s", rtn_data)
                await self._sim_recv_chan.send(rtn_data)

    async def _ensure_serial(self, ins, dur):
        if (ins, dur) not in self._serials:
            quote = self._quotes.setdefault(ins, {  # 在此处设置 min_duration: 每次生成K线的时候会自动生成quote, 记录某一合约的最小duration
                "min_duration": dur
            })
            quote["min_duration"] = min(quote["min_duration"], dur)
            self._serials[(ins, dur)] = {
                "generator": self._gen_serial(ins, dur),
            }
            await self._fetch_serial((ins, dur))

    async def _ensure_quote(self, ins):
        if ins not in self._quotes or self._quotes[ins]["min_duration"] > 60000000000:
            await self._ensure_serial(ins, 60000000000)

    async def _fetch_serial(self, serial):
        s = self._serials[serial]
        try:
            s["timestamp"], s["diff"], s["quotes"] = await s["generator"].__anext__()
        except StopAsyncIteration:
            del self._serials[serial]  # 删除一个行情时间超过结束时间的serial

    async def _gen_serial(self, ins, dur):
        """k线/tick 序列的 async generator, yield 出来的行情数据带有时间戳, 因此 _send_diff 可以据此归并"""
        # 先定位左端点, focus_datetime 是 lower_bound ,这里需要的是 upper_bound
        # 因此将 view_width 和 focus_position 设置成一样，这样 focus_datetime 所对应的 k线刚好位于屏幕外
        chart_info = {
            "aid": "set_chart",
            "chart_id": tqsdk.api.TqApi._generate_chart_id("backtest"),
            "ins_list": ins,
            "duration": dur,
            "view_width": 8964,  # 设为8964原因：可满足用户所有的订阅长度，并在backtest中将所有的 相同合约及周期 的K线用同一个serial存储
            "focus_datetime": int(self._current_dt),
            "focus_position": 8964,
        }
        chart = tqsdk.api.TqApi._get_obj(self._data, ["charts", chart_info["chart_id"]])
        current_id = None  # 当前数据指针
        serial = tqsdk.api.TqApi._get_obj(self._data, ["klines", ins, str(dur)] if dur != 0 else ["ticks", ins])
        async with tqsdk.api.TqChan(self._api, last_only=True) as update_chan:
            serial["_listener"].add(update_chan)
            chart["_listener"].add(update_chan)
            await self._md_send_chan.send(chart_info.copy())
            try:
                async for _ in update_chan:
                    if not (chart_info.items() <= tqsdk.api.TqApi._get_obj(chart, ["state"]).items()):
                        # 当前请求还没收齐回应, 不应继续处理
                        continue
                    left_id = chart.get("left_id", -1)
                    right_id = chart.get("right_id", -1)
                    last_id = serial.get("last_id", -1)
                    if (left_id == -1 and right_id == -1) or last_id == -1:
                        # 定位信息还没收到, 或数据序列还没收到
                        continue
                    if self._data.get("mdhis_more_data", True):
                        self._data["_listener"].add(update_chan)
                        continue
                    else:
                        self._data["_listener"].discard(update_chan)
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
                            await self._md_send_chan.send(chart_info.copy())
                        # 将订阅的8964长度的窗口中的数据都遍历完后，退出循环，然后再次进入并处理下一窗口数据
                        # （因为在处理过5000条数据的同时向服务器订阅从当前id开始的新一窗口的数据，在当前窗口剩下的3000条数据处理完后，下一窗口数据也已经收到）
                        if current_id > right_id:
                            break
                        item = {k: v for k, v in serial["data"].get(str(current_id), {}).items()}
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
                                                str(current_id - 8964): None,
                                            }
                                        }
                                    }
                                }
                            }
                            timestamp = item[
                                "datetime"] if dur < 86400000000000 else tqsdk.api.TqApi._get_trading_day_start_time(
                                item["datetime"])
                            if timestamp > self._end_dt:  # 超过结束时间
                                return
                            yield timestamp, diff, None  # K线刚生成时的数据都为开盘价
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
                            timestamp = item[
                                            "datetime"] + dur - 1000 if dur < 86400000000000 else tqsdk.api.TqApi._get_trading_day_end_time(
                                item["datetime"])
                            if timestamp > self._end_dt:  # 超过结束时间
                                return
                            yield timestamp, diff, self._get_quotes_from_kline(self._data["quotes"][ins], timestamp,
                                                                               item)  # K线结束时生成quote数据
                        current_id += 1
            finally:
                # 释放chart资源
                chart_info["ins_list"] = ""
                await self._md_send_chan.send(chart_info.copy())

    @staticmethod
    def _get_quotes_from_tick(tick):
        quote = {k: v for k, v in tick.items()}
        quote["datetime"] = datetime.fromtimestamp(tick["datetime"] / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f")
        return [quote]

    @staticmethod
    def _get_quotes_from_kline(info, timestamp, kline):
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


class TqReplay(object):
    """天勤复盘类"""
    def __init__(self, replay_dt: date):
        """
        除了传统的回测模式以外，TqSdk 提供独具特色的复盘模式，它与回测模式有以下区别

        1.复盘模式为时间驱动，回测模式为事件驱动

        复盘模式下，你可以指定任意一天交易日，后端行情服务器会传输用户订阅合约的当天的所有历史行情数据，重演当天行情，而在回测模式下，我们根据用户订阅的合约周期数据来进行推送

        因此在复盘模式下K线更新和实盘一模一样，而回测模式下就算订阅了 Tick 数据，回测中任意周期 K 线最后一根的 close 和其他数据也不会随着 Tick 更新而更新，而是随着K线频率生成和结束时更新一次

        2.复盘和回测的行情速度

        因为两者的驱动机制不同，回测会更快，但是我们在复盘模式下也提供行情速度调节功能，可以结合web_gui来实现

        3.复盘目前只支持单日复盘

        因为复盘提供对应合约当日全部历史行情数据，对后端服务器会有较大压力，目前只支持复盘模式下选择单日进行复盘

        Args:
            replay_dt (date): 指定复盘交易日
        """
        if isinstance(replay_dt, date):
            self._replay_dt = replay_dt
        else:
            raise Exception("复盘时间(dt)类型 %s 错误, 请检查 dt 数据类型是否填写正确" % (type(replay_dt)))
        if self._replay_dt.weekday() >= 5:
            # 0~6, 检查周末[5,6] 提前抛错退出
            raise Exception("无法创建复盘服务器，请检查复盘日期后重试。")

    def _create_server(self, api):
        self._api = api
        self._logger = api._logger.getChild("TqReplay")  # 调试信息输出
        self._logger.warning('开始启动复盘服务器，请稍候。')

        session = self._prepare_session()
        self._session_url = "http://%s:%d/t/rmd/replay/session/%s" % (session["ip"], session["session_port"], session["session"])
        self._ins_url = "http://%s:%d/t/rmd/replay/session/%s/symbol" % (session["ip"], session["session_port"], session["session"])
        self._md_url = "ws://%s:%d/t/rmd/front/mobile" % (session["ip"], session["gateway_web_port"])

        self._server_status = None
        timeout = time.time() + 30  # 最多等待 30 s
        # 同步等待复盘服务状态 initializing / running
        while self._server_status is None:
            time.sleep(1)
            response = self._get_server_status()
            if response and response["status"]:
                self._server_status = response["status"]
            if timeout < time.time():
                break

        try_times = 30  # 最多尝试 30 次
        # 同步等待复盘服务状态 running
        while self._server_status == "initializing" and try_times > 0:
            time.sleep(1)
            response = self._get_server_status()
            try_times -= 1
            if response and response["status"]:
                self._server_status = response["status"]

        if self._server_status == "running":
            self._set_server_session({"aid": "ratio", "speed": 1})
            return self._ins_url, self._md_url
        else:
            raise Exception("无法创建复盘服务器，请检查复盘日期后重试。")

    async def _run(self):
        while True:
            self._set_server_session({"aid": "heartbeat"})
            await asyncio.sleep(30)

    def _prepare_session(self):
        create_session_url = "http://replay.api.shinnytech.com/t/rmd/replay/create_session"
        response = requests.post(create_session_url,
                                 headers=self._api._base_headers,
                                 data=json.dumps({'dt': self._replay_dt.strftime("%Y%m%d")}),
                                 timeout=5)
        if response.status_code == 200:
            return json.loads(response.content)
        else:
            raise Exception("创建复盘服务器失败，请检查复盘日期后重试。")

    def _get_server_status(self):
        try:
            response = requests.get(self._session_url,
                                    headers=self._api._base_headers,
                                    timeout=5)
            if response.status_code == 200:
                return json.loads(response.content)
            else:
                raise Exception("无法创建复盘服务器，请检查复盘日期后重试。")
        except requests.exceptions.ConnectionError as e:
            # 刚开始 _session_url 还不能访问的时候～
            return None

    def _set_server_session(self, data=None):
        if data is not None:
            requests.post(self._session_url,
                          headers=self._api._base_headers,
                          data=json.dumps(data),
                          timeout=30)
