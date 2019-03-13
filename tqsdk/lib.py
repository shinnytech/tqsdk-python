#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk.api import TqChan
from asyncio import gather


class TargetPosTask(object):
    """目标持仓 task, 该 task 可以将指定合约调整到目标头寸"""
    def __init__(self, api, symbol, price="ACTIVE", init_pos=None, offset_priority="今昨,开", trade_chan=None):
        """
        创建目标持仓task实例，负责调整归属于该task的持仓(默认为整个账户的该合约净持仓)

        Args:
            api (TqApi): TqApi实例，该task依托于指定api下单/撤单

            symbol (str): 负责调整的合约代码

            price (str): [可选]下单方式, ACTIVE=对价下单, PASSIVE=挂价下单

            init_pos (int): [可选]初始持仓，默认整个账户的该合净持仓

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
        self.symbol = symbol
        self.exchange = symbol.split(".")[0]
        self.price = price
        self.pos = self.api.get_position(self.symbol)
        self.current_pos = init_pos
        self.offset_priority = offset_priority
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
            from tqsdk import TqApi, TqSim, TargetPosTask

            api = TqApi(TqSim())
            target_pos = TargetPosTask(api, "SHFE.rb1810")
            while True:
                api.wait_update()
                target_pos.set_target_volume(5)
        """
        self.pos_chan.send_nowait(volume)

    def _init_position(self):
        """初始化当前持仓"""
        if self.current_pos is None:
            self.current_pos = self.pos["volume_long_today"] + self.pos["volume_long_his"] - self.pos["volume_short_today"] - self.pos["volume_short_his"]

    def _get_order(self, offset, vol, pos):
        """获得可平手数"""
        if vol > 0:  # 买单(增加净持仓)
            order_dir = "BUY"
            ydAvailable=pos["volume_short_his"] - (pos["volume_short_frozen"] - pos["volume_short_frozen_today"])  # 昨空可用
            tdAvailable=pos["volume_short_today"] - pos["volume_short_frozen_today"]  # 今空可用
        else:  # 卖单
            order_dir = "SELL"
            ydAvailable=pos["volume_long_his"] - (pos["volume_long_frozen"] - pos["volume_long_frozen_today"])  # 昨多可用
            tdAvailable=pos["volume_long_today"] - pos["volume_long_frozen_today"]  # 今多可用
        if offset == "昨":
            order_offset = "CLOSE"
            order_volume = min(abs(vol), ydAvailable if self.exchange == "SHFE" or self.exchange == "INE" or tdAvailable == 0 else 0)
            if vol > 0:
                pos["volume_short_frozen"] += order_volume
                pos["volume_short_frozen_his"] += order_volume
            else:
                pos["volume_long_frozen"] += order_volume
                pos["volume_long_frozen_his"] += order_volume
        elif offset == "今":
            order_offset = "CLOSETODAY" if self.exchange == "SHFE" or self.exchange == "INE" else "CLOSE"
            order_volume = min(abs(vol), tdAvailable if self.exchange == "SHFE" or self.exchange == "INE" else tdAvailable + ydAvailable)
            if vol > 0:
                pos["volume_short_frozen"] += order_volume
                pos["volume_short_frozen_today"] += order_volume
                pos["volume_short_frozen_his"] += max(0, pos["volume_short_frozen_today"] - pos["volume_short_today"])
                pos["volume_short_frozen_today"] = min(pos["volume_short_frozen_today"], pos["volume_short_today"])
            else:
                pos["volume_long_frozen"] += order_volume
                pos["volume_long_frozen_today"] += order_volume
                pos["volume_long_frozen_his"] += max(0, pos["volume_long_frozen_today"] - pos["volume_long_today"])
                pos["volume_long_frozen_today"] = min(pos["volume_long_frozen_today"], pos["volume_long_today"])
        elif offset == "开":
            order_offset = "OPEN"
            order_volume = abs(vol)
        else:
            order_offset = ""
            order_volume = 0
        return order_offset, order_dir, order_volume

    async def _target_pos_task(self):
        """负责调整目标持仓的task"""
        self._init_position()
        async for target_pos in self.pos_chan:
            # 确定调仓增减方向
            delta_volume = target_pos - self.current_pos
            all_tasks = []
            pos = self.pos.copy()
            for each_priority in self.offset_priority + ",":  # 按不同模式的优先级顺序报出不同的offset单，股指(“昨开”)平昨优先从不平今就先报平昨，原油平今优先("今昨开")就报平今
                if each_priority == ",":
                    await gather(*[each.task for each in all_tasks])
                    all_tasks =[]
                    pos = self.pos.copy()
                    continue
                order_offset, order_dir, order_volume = self._get_order(each_priority, delta_volume, pos)
                if order_volume == 0:  # 如果没有则直接到下一种offset
                    continue
                order_task = InsertOrderUntilAllTradedTask(self.api, self.symbol, order_dir, offset=order_offset,volume=order_volume, price=self.price,trade_chan=self.trade_chan)
                all_tasks.append(order_task)
                delta_volume -= order_volume if order_dir == "BUY" else -order_volume
            self.current_pos = target_pos


class InsertOrderUntilAllTradedTask(object):
    """追价下单task, 该task会在行情变化后自动撤单重下，直到全部成交"""
    def __init__(self, api, symbol, direction, offset, volume, price = "ACTIVE", trade_chan = None):
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
        self.symbol = symbol
        self.direction = direction
        self.offset = offset
        self.volume = volume
        self.price = price
        self.trade_chan = trade_chan if trade_chan is not None else TqChan(self.api)
        self.quote = self.api.get_quote(self.symbol)
        self.task = self.api.create_task(self._run())

    async def _run(self):
        """负责追价下单的task"""
        async with self.api.register_update_notify() as update_chan:
            # 确保获得初始行情
            while self.quote["datetime"] == "":
                await update_chan.recv()
            while self.volume != 0:
                limit_price = self._get_price()
                insert_order_task = InsertOrderTask(self.api, self.symbol, self.direction, self.offset, self.volume, limit_price = limit_price, trade_chan = self.trade_chan)
                order = await insert_order_task.order_chan.recv()
                check_chan = TqChan(self.api, last_only=True)
                check_task = self.api.create_task(self._check_price(check_chan, limit_price, order))
                try:
                    await insert_order_task.task
                    order = insert_order_task.order_chan.recv_latest(order)
                    self.volume = order["volume_left"]
                    if self.volume != 0 and not check_task.done():
                        raise Exception("遇到错单: %s %s %s %d手 %f %s" % (self.symbol, self.direction, self.offset, self.volume, limit_price, order["last_msg"]))
                finally:
                    await check_chan.close()
                    await check_task

    def _get_price(self):
        """根据最新行情和下单方式计算出最优的下单价格"""
        # 主动买的价格序列(优先判断卖价，如果没有则用买价)
        price_list = [self.quote["ask_price1"], self.quote["bid_price1"]]
        if self.direction == "SELL":
            price_list.reverse()
        if self.price == "PASSIVE":
            price_list.reverse()
        limit_price = price_list[0]
        if limit_price != limit_price:
            limit_price = price_list[1]
        if limit_price != limit_price:
            limit_price = self.quote["last_price"]
        if limit_price != limit_price:
            limit_price = self.quote["pre_close"]
        return limit_price

    async def _check_price(self, update_chan, order_price, order):
        """判断价格是否变化的task"""
        async with self.api.register_update_notify(chan = update_chan):
            async for _ in update_chan:
                new_price = self._get_price()
                if (self.direction == "BUY" and new_price > order_price) or (self.direction == "SELL" and new_price < order_price):
                    self.api.cancel_order(order)
                    break


class InsertOrderTask(object):
    """下单task"""
    def __init__(self, api, symbol, direction, offset, volume, limit_price=None, order_chan = None, trade_chan = None):
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
        self.symbol = symbol
        self.direction = direction
        self.offset = offset
        self.volume = volume
        self.limit_price = limit_price
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
            while order["status"] != "FINISHED":
                await update_chan.recv()
                if order["volume_left"] != last_left:
                    vol = last_left - order["volume_left"]
                    last_left = order["volume_left"]
                    await self.trade_chan.send(vol if order["direction"] == "BUY" else -vol)
                if order != last_order:
                    last_order = order.copy()
                    await self.order_chan.send(last_order)
