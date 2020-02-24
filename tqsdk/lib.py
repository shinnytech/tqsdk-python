#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import datetime
import time
from tqsdk.api import TqChan, TqApi
from asyncio import gather
from typing import Optional


class TargetPosTaskSingleton(type):
    _instances = {}

    def __call__(cls, api, symbol, price="ACTIVE", offset_priority="今昨,开", trade_chan=None, *args, **kwargs):
        if symbol not in TargetPosTaskSingleton._instances:
            TargetPosTaskSingleton._instances[symbol] = super(TargetPosTaskSingleton, cls).__call__(api, symbol, price,
                                                                                                    offset_priority,
                                                                                                    trade_chan, *args,
                                                                                                    **kwargs)
        else:
            instance = TargetPosTaskSingleton._instances[symbol]
            if instance._offset_priority != offset_priority:
                raise Exception("您试图用不同的 offset_priority 参数创建两个 %s 调仓任务, offset_priority参数原为 %s, 现为 %s" % (
                    symbol, instance._offset_priority, offset_priority))
            if instance._price != price:
                raise Exception("您试图用不同的 price 参数创建两个 %s 调仓任务, price参数原为 %s, 现为 %s" % (symbol, instance._price, price))
        return TargetPosTaskSingleton._instances[symbol]


class TargetPosTask(object, metaclass=TargetPosTaskSingleton):
    """目标持仓 task, 该 task 可以将指定合约调整到目标头寸"""

    def __init__(self, api: TqApi, symbol: str, price: str = "ACTIVE", offset_priority: str = "今昨,开",
                 trade_chan: Optional[TqChan] = None) -> None:
        """
        创建目标持仓task实例，负责调整归属于该task的持仓 **(默认为整个账户的该合约净持仓)**.

        **注意:**
            1. TargetPosTask 在 set_target_volume 时并不下单或撤单, 它的下单和撤单动作, 是在之后的每次 wait_update 时执行的. 因此, **需保证 set_target_volume 后还会继续调用wait_update()** 。

            2. 请勿在使用 TargetPosTask 的同时使用 insert_order() 函数, 否则将导致 TargetPosTask 报错或错误下单。

        Args:
            api (TqApi): TqApi实例，该task依托于指定api下单/撤单

            symbol (str): 负责调整的合约代码

            price (str): [可选]下单方式, ACTIVE=对价下单, PASSIVE=挂价下单.

                * 在持仓调整过程中,若下单方向为买: 对价为卖一价, 挂价为买一价
                * 在持仓调整过程中,若下单方向为卖: 对价为买一价, 挂价为卖一价

            offset_priority (str): [可选]开平仓顺序，昨=平昨仓，今=平今仓，开=开仓，逗号=等待之前操作完成

                                   对于下单指令区分平今/昨的交易所(如上期所)，按照今/昨仓的数量计算是否能平今/昨仓
                                   对于下单指令不区分平今/昨的交易所(如中金所)，按照“先平当日新开仓，再平历史仓”的规则计算是否能平今/昨仓

                                   * "今昨,开" 表示先平今仓，再平昨仓，等待平仓完成后开仓，对于没有单向大边的品种避免了开仓保证金不足
                                   * "今昨开" 表示先平今仓，再平昨仓，并开仓，所有指令同时发出，适合有单向大边的品种
                                   * "昨开" 表示先平昨仓，再开仓，禁止平今仓，适合股指这样平今手续费较高的品种

            trade_chan (TqChan): [可选]成交通知channel, 当有成交发生时会将成交手数(多头为正数，空头为负数)发到该channel上
        """
        super(TargetPosTask, self).__init__()
        self._api = api
        if symbol not in api._data.get("quotes", {}):
            raise Exception("代码 %s 不存在, 请检查合约代码是否填写正确" % (symbol))
        self._symbol = symbol
        self._exchange = symbol.split(".")[0]
        if price not in ("ACTIVE", "PASSIVE"):
            raise Exception("下单方式(price) %s 错误, 请检查 price 参数是否填写正确" % (price))
        self._price = price
        if len(offset_priority.replace(",", "").replace("今", "", 1).replace("昨", "", 1).replace("开", "", 1)) > 0:
            raise Exception("开平仓顺序(offset_priority) %s 错误, 请检查 offset_priority 参数是否填写正确" % (offset_priority))
        self._offset_priority = offset_priority
        self._pos = self._api.get_position(self._symbol)
        self._pos_chan = TqChan(self._api, last_only=True)
        self._trade_chan = trade_chan if trade_chan is not None else TqChan(self._api)
        self._task = self._api.create_task(self._target_pos_task())

        self._quote = self._api.get_quote(self._symbol)
        self._quote_update_chan = TqChan(self._api, last_only=True)
        self._time_update_task = self._api.create_task(
            self._update_time_from_md(symbol))  # 监听行情更新并记录当时本地时间的task
        self._local_time_record = time.time() - 0.005  # 更新最新行情时间时的本地时间
        self._trading_day_end = ""  # self._quote["datetime"] 所在交易日的结束时间
        self._trading_timestamp = {
            "day": [],
            "night": []
        }  # 此quote的可交易时间段
        self._update_trading_timestamp()  # 更新self._trading_timestamp

    def _update_trading_timestamp(self):
        """ 计算 当前qoute 所在交易日,并将这一日的交易时间段转换为纳秒时间戳（tqsdk内部使用的时间戳统一为纳秒） """
        if not self._quote["datetime"]:  # 确认已经收到行情
            return
        if len(self._trading_timestamp["day"]) != 0:  # 清空
            self._trading_timestamp = {
                "day": [],
                "night": []
            }
        current_dt = datetime.datetime.strptime(self._quote["datetime"], '%Y-%m-%d %H:%M:%S.%f')
        current_trading_day = current_dt.date() + datetime.timedelta(
            days=1) if current_dt.hour >= 18 else current_dt.date()
        if int(current_trading_day.strftime("%w")) % 6 == 0:  # 周六
            current_trading_day += datetime.timedelta(days=2)
        last_trading_day = current_trading_day - datetime.timedelta(
            days=3 if int(current_trading_day.strftime("%w")) % 6 == 1 else 1)  # 获取上一交易日
        # 处理夜盘交易时间段, period：每个交易时间段 (起、止时间点)
        for period in self._quote["trading_time"].get("night", []):
            self._trading_timestamp["night"].append([])
            self._trading_timestamp["night"][-1].append(
                int(datetime.datetime.strptime(datetime.date.strftime(last_trading_day, "%Y-%m-%d") + " " + period[0],
                                               '%Y-%m-%d %H:%M:%S').timestamp() * 1e6) * 1000)  # 起始时间(默认起始时间在上一个交易日,可优化为与结束时间相同的判断方法)
            if int(period[1][1]) >= 4:  # 如果夜盘结束时间跨日，则结束时间在上一交易日的后一自然日
                self._trading_timestamp["night"][-1].append(
                    int(datetime.datetime.strptime(
                        datetime.date.strftime(last_trading_day + datetime.timedelta(days=1), "%Y-%m-%d") + " " + str(
                            int(period[1][1]) - 4) + period[1][2:], '%Y-%m-%d %H:%M:%S').timestamp() * 1e6) * 1000)
            else:  # 未跨日，则结束时间在上一交易日
                self._trading_timestamp["night"][-1].append(
                    int(datetime.datetime.strptime(
                        datetime.date.strftime(last_trading_day, "%Y-%m-%d") + " " + period[1],
                        '%Y-%m-%d %H:%M:%S').timestamp() * 1e6) * 1000)
        # 处理白盘交易时间段
        for period in self._quote["trading_time"]["day"]:
            self._trading_timestamp["day"].append([])
            self._trading_timestamp["day"][-1].append(
                int(datetime.datetime.strptime(
                    datetime.date.strftime(current_trading_day, "%Y-%m-%d") + " " + period[0],
                    '%Y-%m-%d %H:%M:%S').timestamp() * 1e6) * 1000)
            self._trading_timestamp["day"][-1].append(
                int(datetime.datetime.strptime(
                    datetime.date.strftime(current_trading_day, "%Y-%m-%d") + " " + period[1],
                    '%Y-%m-%d %H:%M:%S').timestamp() * 1e6) * 1000)
        current_timestamp = int(
            datetime.datetime.strptime(self._quote["datetime"], "%Y-%m-%d %H:%M:%S.%f").timestamp() * 1e6) * 1000
        trading_day = self._api._get_trading_day_from_timestamp(current_timestamp)
        self._trading_day_end = datetime.datetime.fromtimestamp(
            (self._api._get_trading_day_end_time(trading_day) - 1000) / 1e9).strftime("%Y-%m-%d %H:%M:%S.%f")

    def set_target_volume(self, volume: int) -> None:
        """
        设置目标持仓手数

        Args:
            volume (int): 目标持仓手数，正数表示多头，负数表示空头，0表示空仓

        Example::

            # 设置 rb1810 持仓为多头5手
            from tqsdk import TqApi, TargetPosTask

            api = TqApi()
            target_pos = TargetPosTask(api, "SHFE.rb1810")
            target_pos.set_target_volume(5)
            while True:
                # 需在 set_target_volume 后调用wait_update()以发出指令
                api.wait_update()
        """
        self._pos_chan.send_nowait(int(volume))

    def _get_order(self, offset, vol, pending_frozen):
        """
        根据指定的offset和预期下单手数vol, 返回符合要求的委托单最大报单手数
        :param offset: "昨" / "今" / "开"
        :param vol: int, <0表示SELL, >0表示BUY
        :return: order_offset: "CLOSE"/"CLOSETODAY"/"OPEN"; order_dir: "BUY"/"SELL"; "order_volume": >=0, 报单手数
        """
        if vol > 0:  # 买单(增加净持仓)
            order_dir = "BUY"
            pos_all = self._pos.pos_short
        else:  # 卖单
            order_dir = "SELL"
            pos_all = self._pos.pos_long
        if offset == "昨":
            order_offset = "CLOSE"
            if self._exchange == "SHFE" or self._exchange == "INE":
                if vol > 0:
                    pos_all = self._pos.pos_short_his
                else:
                    pos_all = self._pos.pos_long_his
                frozen_volume = sum([order.volume_left for order in self._pos.orders.values() if
                                     not order.is_dead and order.offset == order_offset and order.direction == order_dir])
            else:
                frozen_volume = pending_frozen + sum([order.volume_left for order in self._pos.orders.values() if
                                                      not order.is_dead and order.offset != "OPEN" and order.direction == order_dir])
                # 判断是否有未冻结的今仓手数: 若有则不平昨仓
                if (self._pos.pos_short_today if vol > 0 else self._pos.pos_long_today) - frozen_volume > 0:
                    pos_all = frozen_volume
            order_volume = min(abs(vol), max(0, pos_all - frozen_volume))
        elif offset == "今":
            if self._exchange == "SHFE" or self._exchange == "INE":
                order_offset = "CLOSETODAY"
                if vol > 0:
                    pos_all = self._pos.pos_short_today
                else:
                    pos_all = self._pos.pos_long_today
                frozen_volume = sum([order.volume_left for order in self._pos.orders.values() if
                                     not order.is_dead and order.offset == order_offset and order.direction == order_dir])
            else:
                order_offset = "CLOSE"
                frozen_volume = pending_frozen + sum([order.volume_left for order in self._pos.orders.values() if
                                                      not order.is_dead and order.offset != "OPEN" and order.direction == order_dir])
                pos_all = self._pos.pos_short_today if vol > 0 else self._pos.pos_long_today
            order_volume = min(abs(vol), max(0, pos_all - frozen_volume))
        elif offset == "开":
            order_offset = "OPEN"
            order_volume = abs(vol)
        else:
            order_offset = ""
            order_volume = 0
        return order_offset, order_dir, order_volume

    async def _update_time_from_md(self, symbol):
        """监听行情更新并记录当时本地时间的task"""
        async with self._api.register_update_notify(self._quote, chan=self._quote_update_chan):
            async for _ in self._quote_update_chan:  # quote有更新
                self._update_time_record()

    def _update_time_record(self):
        self._local_time_record = time.time() - 0.005  # 更新最新行情时间时的本地时间
        if self._quote["datetime"] > self._trading_day_end:  # 新交易日
            self._update_trading_timestamp()

    def _is_in_trading_time(self):
        now_ns_timestamp = int(
            (datetime.datetime.strptime(self._quote["datetime"], "%Y-%m-%d %H:%M:%S.%f").timestamp() + (
                    time.time() - self._local_time_record)) * 1e6) * 1000
        # 判断当前交易所时间（估计值）是否在交易时间段内
        for v in self._trading_timestamp.values():
            for period in v:
                if now_ns_timestamp >= period[0] and now_ns_timestamp <= period[1]:
                    return True
        return False

    async def _target_pos_task(self):
        """负责调整目标持仓的task"""
        try:
            async for target_pos in self._pos_chan:
                # todo: 交易时间判断相关的函数在 lib 和 sim 中有两份几乎相同代码，可修改为通用函数避免代码冗余
                # lib 中对于时间判断的方案:
                # 如果当前时间（模拟交易所时间）不在交易时间段内，则：等待直到行情更新
                # 行情更新（即下一交易时段开始）后：获取target_pos最新的目标仓位, 开始调整仓位
                async with self._api.register_update_notify(self._quote) as update_chan:
                    # 确保获得初始行情
                    while not self._is_in_trading_time():  # 如果在交易时间段内
                        await update_chan.recv()
                        # 如果_time_update_task在这之后运行，则下一次判断是否在交易时间段内时使用的是旧数据，因此增加一次判断并更新为最新数据
                        if self._quote_update_chan:
                            self._update_time_record()
                target_pos = self._pos_chan.recv_latest(target_pos)  # 获取最后一个target_pos目标仓位

                # 确定调仓增减方向
                delta_volume = target_pos - self._pos.pos
                pending_forzen = 0
                all_tasks = []
                for each_priority in self._offset_priority + ",":  # 按不同模式的优先级顺序报出不同的offset单，股指(“昨开”)平昨优先从不平今就先报平昨，原油平今优先("今昨开")就报平今
                    if each_priority == ",":
                        await gather(*[each._task for each in all_tasks])
                        pending_forzen = 0
                        all_tasks = []
                        continue
                    order_offset, order_dir, order_volume = self._get_order(each_priority, delta_volume, pending_forzen)
                    if order_volume == 0:  # 如果没有则直接到下一种offset
                        continue
                    elif order_offset != "OPEN":
                        pending_forzen += order_volume
                    order_task = InsertOrderUntilAllTradedTask(self._api, self._symbol, order_dir, offset=order_offset,
                                                               volume=order_volume, price=self._price,
                                                               trade_chan=self._trade_chan)
                    all_tasks.append(order_task)
                    delta_volume -= order_volume if order_dir == "BUY" else -order_volume
        finally:
            # 执行 task.cancel() 时, 删除掉该 symbol 对应的 TargetPosTask 实例
            TargetPosTaskSingleton._instances.pop(self._symbol, None)


class InsertOrderUntilAllTradedTask(object):
    """追价下单task, 该task会在行情变化后自动撤单重下，直到全部成交
     （注：此类主要在tqsdk内部使用，并非简单用法，不建议用户使用）"""

    def __init__(self, api, symbol, direction, offset, volume, price="ACTIVE", trade_chan=None):
        """
        创建追价下单task实例

        Args:
            api (TqApi): TqApi实例，该task依托于指定api下单/撤单

            symbol (str): 拟下单的合约symbol, 格式为 交易所代码.合约代码,  例如 "SHFE.cu1801"

            direction (str): "BUY" 或 "SELL"

            offset (str): "OPEN", "CLOSE" 或 "CLOSETODAY"

            volume (int): 需要下单的手数

            price (str): [可选]下单方式, ACTIVE=对价下单, PASSIVE=挂价下单

            trade_chan (TqChan): [可选]成交通知channel, 当有成交发生时会将成交手数(多头为正数，空头为负数)发到该channel上
        """
        self._api = api
        if symbol not in api._data.get("quotes", {}):
            raise Exception("代码 %s 不存在, 请检查合约代码是否填写正确" % (symbol))
        self._symbol = symbol
        if direction not in ("BUY", "SELL"):
            raise Exception("下单方向(direction) %s 错误, 请检查 direction 参数是否填写正确" % (direction))
        self._direction = direction
        if offset not in ("OPEN", "CLOSE", "CLOSETODAY"):
            raise Exception("开平标志(offset) %s 错误, 请检查 offset 是否填写正确" % (offset))
        self._offset = offset
        self._volume = int(volume)
        if self._volume <= 0:
            raise Exception("下单手数(volume) %s 错误, 请检查 volume 是否填写正确" % (volume))
        if price not in ("ACTIVE", "PASSIVE"):
            raise Exception("下单方式(price) %s 错误, 请检查 price 参数是否填写正确" % (price))
        self._price = price
        self._trade_chan = trade_chan if trade_chan is not None else TqChan(self._api)
        self._quote = self._api.get_quote(self._symbol)
        self._task = self._api.create_task(self._run())

    async def _run(self):
        """负责追价下单的task"""
        async with self._api.register_update_notify() as update_chan:
            # 确保获得初始行情
            while self._quote.datetime == "":
                await update_chan.recv()
            while self._volume != 0:
                limit_price = self._get_price()
                insert_order_task = InsertOrderTask(self._api, self._symbol, self._direction, self._offset,
                                                    self._volume, limit_price=limit_price, trade_chan=self._trade_chan)
                order = await insert_order_task._order_chan.recv()
                check_chan = TqChan(self._api, last_only=True)
                check_task = self._api.create_task(self._check_price(check_chan, limit_price, order))
                try:
                    await insert_order_task._task
                    order = insert_order_task._order_chan.recv_latest(order)
                    self._volume = order.volume_left
                    if self._volume != 0 and not check_task.done():
                        raise Exception("遇到错单: %s %s %s %d手 %f %s" % (
                            self._symbol, self._direction, self._offset, self._volume, limit_price, order.last_msg))
                finally:
                    await check_chan.close()
                    await check_task

    def _get_price(self):
        """根据最新行情和下单方式计算出最优的下单价格"""
        # 主动买的价格序列(优先判断卖价，如果没有则用买价)
        price_list = [self._quote.ask_price1, self._quote.bid_price1]
        if self._direction == "SELL":
            price_list.reverse()
        if self._price == "PASSIVE":
            price_list.reverse()
        limit_price = price_list[0]
        if limit_price != limit_price:
            limit_price = price_list[1]
        if limit_price != limit_price:
            limit_price = self._quote.last_price
        if limit_price != limit_price:
            limit_price = self._quote.pre_close
        return limit_price

    async def _check_price(self, update_chan, order_price, order):
        """判断价格是否变化的task"""
        async with self._api.register_update_notify(chan=update_chan):
            async for _ in update_chan:
                new_price = self._get_price()
                if (self._direction == "BUY" and new_price > order_price) or (
                        self._direction == "SELL" and new_price < order_price):
                    self._api.cancel_order(order)
                    break


class InsertOrderTask(object):
    """下单task （注：此类主要在tqsdk内部使用，并非简单用法，不建议用户使用）"""

    def __init__(self, api, symbol, direction, offset, volume, limit_price=None, order_chan=None, trade_chan=None):
        """
        创建下单task实例

        Args:
            api (TqApi): TqApi实例，该task依托于指定api下单/撤单

            symbol (str): 拟下单的合约symbol, 格式为 交易所代码.合约代码,  例如 "SHFE.cu1801"

            direction (str): "BUY" 或 "SELL"

            offset (str): "OPEN", "CLOSE" 或 "CLOSETODAY"

            volume (int): 需要下单的手数

            limit_price (float): [可选]下单价格, 默认市价单

            order_chan (TqChan): [可选]委托单通知channel, 当委托单状态发生时会将委托单信息发到该channel上

            trade_chan (TqChan): [可选]成交通知channel, 当有成交发生时会将成交手数(多头为正数，空头为负数)发到该channel上
        """
        self._api = api
        if symbol not in api._data.get("quotes", {}):
            raise Exception("代码 %s 不存在, 请检查合约代码是否填写正确" % (symbol))
        self._symbol = symbol
        if direction not in ("BUY", "SELL"):
            raise Exception("下单方向(direction) %s 错误, 请检查 direction 参数是否填写正确" % (direction))
        self._direction = direction
        if offset not in ("OPEN", "CLOSE", "CLOSETODAY"):
            raise Exception("开平标志(offset) %s 错误, 请检查 offset 是否填写正确" % (offset))
        self._offset = offset
        self._volume = int(volume)
        self._limit_price = float(limit_price) if limit_price is not None else None
        self._order_chan = order_chan if order_chan is not None else TqChan(self._api)
        self._trade_chan = trade_chan if trade_chan is not None else TqChan(self._api)
        self._task = self._api.create_task(self._run())

    async def _run(self):
        """负责下单的task"""
        order = self._api.insert_order(self._symbol, self._direction, self._offset, self._volume, self._limit_price)
        last_order = order.copy()  # 保存当前 order 的状态
        last_left = self._volume
        async with self._api.register_update_notify() as update_chan:
            await self._order_chan.send(last_order.copy())  # 将副本的数据及所有权转移
            while order.status != "FINISHED" or (order.volume_orign - order.volume_left) != sum(
                    [trade.volume for trade in order.trade_records.values()]):
                await update_chan.recv()
                if order.volume_left != last_left:
                    vol = last_left - order.volume_left
                    last_left = order.volume_left
                    await self._trade_chan.send(vol if order.direction == "BUY" else -vol)
                if order != last_order:
                    last_order = order.copy()
                    await self._order_chan.send(last_order.copy())
