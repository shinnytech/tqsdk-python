#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk.api import TqChan
from asyncio import gather


class TargetPosTask(object):
    """目标持仓 task, 该 task 可以将指定合约调整到目标头寸"""

    def __init__(self, api, symbol, price="ACTIVE", offset_priority="今昨,开", trade_chan=None):
        """
        创建目标持仓task实例，负责调整归属于该task的持仓 **(默认为整个账户的该合约净持仓)**.

        **注意:** TargetPosTask 在 set_target_volume 时并不下单或撤单, 它的下单和撤单动作, 是在之后的每次 wait_update 时执行的. 因此, **需保证 set_target_volume 后还会继续调用wait_update()**

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
        self.api = api
        if symbol not in api._data.get("quotes", {}):
            raise Exception("代码 %s 不存在, 请检查合约代码是否填写正确" % (symbol))
        self.symbol = symbol
        self.exchange = symbol.split(".")[0]
        if price not in ("ACTIVE", "PASSIVE"):
            raise Exception("下单方式(price) %s 错误, 请检查 price 参数是否填写正确" % (price))
        self.price = price
        if len(offset_priority.replace(",", "").replace("今", "", 1).replace("昨", "", 1).replace("开", "", 1)) > 0:
            raise Exception("开平仓顺序(offset_priority) %s 错误, 请检查 offset_priority 参数是否填写正确" % (offset_priority))
        self.offset_priority = offset_priority
        self.pos = self.api.get_position(self.symbol)
        self.pos_chan = TqChan(self.api, last_only=True)
        self.trade_chan = trade_chan if trade_chan is not None else TqChan(self.api)
        self.task = self.api.create_task(self._target_pos_task())

    def set_target_volume(self, volume):
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
        self.pos_chan.send_nowait(int(volume))

    def _get_order(self, offset, vol, pending_frozen):
        """
        根据指定的offset和预期下单手数vol, 返回符合要求的委托单最大报单手数
        :param offset: "昨" / "今" / "开"
        :param vol: int, <0表示SELL, >0表示BUY
        :return: order_offset: "CLOSE"/"CLOSETODAY"/"OPEN"; order_dir: "BUY"/"SELL"; "order_volume": >=0, 报单手数
        """
        if vol > 0:  # 买单(增加净持仓)
            order_dir = "BUY"
            pos_all = self.pos.pos_short
        else:  # 卖单
            order_dir = "SELL"
            pos_all = self.pos.pos_long
        if offset == "昨":
            order_offset = "CLOSE"
            if self.exchange == "SHFE" or self.exchange == "INE":
                if vol > 0:
                    pos_all = self.pos.pos_short_his
                else:
                    pos_all = self.pos.pos_long_his
                frozen_volume = sum([order.volume_left for order in self.pos.orders.values() if
                                     not order.is_dead and order.offset == order_offset and order.direction == order_dir])
            else:
                frozen_volume = pending_frozen + sum([order.volume_left for order in self.pos.orders.values() if
                                                      not order.is_dead and order.offset != "OPEN" and order.direction == order_dir])
                if (
                self.pos.pos_short_today if vol > 0 else self.pos.pos_long_today) - frozen_volume > 0:  # 判断是否有未冻结的今仓手数: 若有则不平昨仓
                    pos_all = frozen_volume
            order_volume = min(abs(vol), max(0, pos_all - frozen_volume))
        elif offset == "今":
            if self.exchange == "SHFE" or self.exchange == "INE":
                order_offset = "CLOSETODAY"
                if vol > 0:
                    pos_all = self.pos.pos_short_today
                else:
                    pos_all = self.pos.pos_long_today
                frozen_volume = sum([order.volume_left for order in self.pos.orders.values() if
                                     not order.is_dead and order.offset == order_offset and order.direction == order_dir])
            else:
                order_offset = "CLOSE"
                frozen_volume = pending_frozen + sum([order.volume_left for order in self.pos.orders.values() if
                                                      not order.is_dead and order.offset != "OPEN" and order.direction == order_dir])
                pos_all = self.pos.pos_short_today if vol > 0 else self.pos.pos_long_today
            order_volume = min(abs(vol), max(0, pos_all - frozen_volume))
        elif offset == "开":
            order_offset = "OPEN"
            order_volume = abs(vol)
        else:
            order_offset = ""
            order_volume = 0
        return order_offset, order_dir, order_volume

    async def _target_pos_task(self):
        """负责调整目标持仓的task"""
        async for target_pos in self.pos_chan:
            # 确定调仓增减方向
            delta_volume = target_pos - self.pos.pos
            pending_forzen = 0
            all_tasks = []
            for each_priority in self.offset_priority + ",":  # 按不同模式的优先级顺序报出不同的offset单，股指(“昨开”)平昨优先从不平今就先报平昨，原油平今优先("今昨开")就报平今
                if each_priority == ",":
                    await gather(*[each.task for each in all_tasks])
                    pending_forzen = 0
                    all_tasks = []
                    continue
                order_offset, order_dir, order_volume = self._get_order(each_priority, delta_volume, pending_forzen)
                if order_volume == 0:  # 如果没有则直接到下一种offset
                    continue
                elif order_offset != "OPEN":
                    pending_forzen += order_volume
                order_task = InsertOrderUntilAllTradedTask(self.api, self.symbol, order_dir, offset=order_offset,
                                                           volume=order_volume, price=self.price,
                                                           trade_chan=self.trade_chan)
                all_tasks.append(order_task)
                delta_volume -= order_volume if order_dir == "BUY" else -order_volume


class InsertOrderUntilAllTradedTask(object):
    """追价下单task, 该task会在行情变化后自动撤单重下，直到全部成交"""

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
        self.api = api
        if symbol not in api._data.get("quotes", {}):
            raise Exception("代码 %s 不存在, 请检查合约代码是否填写正确" % (symbol))
        self.symbol = symbol
        if direction not in ("BUY", "SELL"):
            raise Exception("下单方向(direction) %s 错误, 请检查 direction 参数是否填写正确" % (direction))
        self.direction = direction
        if offset not in ("OPEN", "CLOSE", "CLOSETODAY"):
            raise Exception("开平标志(offset) %s 错误, 请检查 offset 是否填写正确" % (offset))
        self.offset = offset
        self.volume = int(volume)
        if self.volume <= 0:
            raise Exception("下单手数(volume) %s 错误, 请检查 volume 是否填写正确" % (volume))
        if price not in ("ACTIVE", "PASSIVE"):
            raise Exception("下单方式(price) %s 错误, 请检查 price 参数是否填写正确" % (price))
        self.price = price
        self.trade_chan = trade_chan if trade_chan is not None else TqChan(self.api)
        self.quote = self.api.get_quote(self.symbol)
        self.task = self.api.create_task(self._run())

    async def _run(self):
        """负责追价下单的task"""
        async with self.api.register_update_notify() as update_chan:
            # 确保获得初始行情
            while self.quote.datetime == "":
                await update_chan.recv()
            while self.volume != 0:
                limit_price = self._get_price()
                insert_order_task = InsertOrderTask(self.api, self.symbol, self.direction, self.offset, self.volume,
                                                    limit_price=limit_price, trade_chan=self.trade_chan)
                order = await insert_order_task.order_chan.recv()
                check_chan = TqChan(self.api, last_only=True)
                check_task = self.api.create_task(self._check_price(check_chan, limit_price, order))
                try:
                    await insert_order_task.task
                    order = insert_order_task.order_chan.recv_latest(order)
                    self.volume = order.volume_left
                    if self.volume != 0 and not check_task.done():
                        raise Exception("遇到错单: %s %s %s %d手 %f %s" % (
                        self.symbol, self.direction, self.offset, self.volume, limit_price, order.last_msg))
                finally:
                    await check_chan.close()
                    await check_task

    def _get_price(self):
        """根据最新行情和下单方式计算出最优的下单价格"""
        # 主动买的价格序列(优先判断卖价，如果没有则用买价)
        price_list = [self.quote.ask_price1, self.quote.bid_price1]
        if self.direction == "SELL":
            price_list.reverse()
        if self.price == "PASSIVE":
            price_list.reverse()
        limit_price = price_list[0]
        if limit_price != limit_price:
            limit_price = price_list[1]
        if limit_price != limit_price:
            limit_price = self.quote.last_price
        if limit_price != limit_price:
            limit_price = self.quote.pre_close
        return limit_price

    async def _check_price(self, update_chan, order_price, order):
        """判断价格是否变化的task"""
        async with self.api.register_update_notify(chan=update_chan):
            async for _ in update_chan:
                new_price = self._get_price()
                if (self.direction == "BUY" and new_price > order_price) or (
                        self.direction == "SELL" and new_price < order_price):
                    self.api.cancel_order(order)
                    break


class InsertOrderTask(object):
    """下单task"""

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
        self.api = api
        if symbol not in api._data.get("quotes", {}):
            raise Exception("代码 %s 不存在, 请检查合约代码是否填写正确" % (symbol))
        self.symbol = symbol
        if direction not in ("BUY", "SELL"):
            raise Exception("下单方向(direction) %s 错误, 请检查 direction 参数是否填写正确" % (direction))
        self.direction = direction
        if offset not in ("OPEN", "CLOSE", "CLOSETODAY"):
            raise Exception("开平标志(offset) %s 错误, 请检查 offset 是否填写正确" % (offset))
        self.offset = offset
        self.volume = int(volume)
        self.limit_price = float(limit_price) if limit_price is not None else None
        self.order_chan = order_chan if order_chan is not None else TqChan(self.api)
        self.trade_chan = trade_chan if trade_chan is not None else TqChan(self.api)
        self.task = self.api.create_task(self._run())

    async def _run(self):
        """负责下单的task"""
        order = self.api.insert_order(self.symbol, self.direction, self.offset, self.volume, self.limit_price)
        last_order = order.copy()
        last_left = self.volume
        async with self.api.register_update_notify() as update_chan:
            await self.order_chan.send(last_order)
            while order.status != "FINISHED" or (order.volume_orign - order.volume_left) != sum(
                    [trade.volume for trade in order.trade_records.values()]):
                await update_chan.recv()
                if order.volume_left != last_left:
                    vol = last_left - order.volume_left
                    last_left = order.volume_left
                    await self.trade_chan.send(vol if order.direction == "BUY" else -vol)
                if order != last_order:
                    last_order = order.copy()
                    await self.order_chan.send(last_order)
