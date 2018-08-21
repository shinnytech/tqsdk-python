#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk.api import TqChan
from asyncio import gather

class TargetPosTask(object):
    """目标持仓 task, 该 task 可以将指定合约调整到目标头寸"""
    def __init__(self, api, symbol, price="ACTIVE", init_pos=None, init_pos_today=None, settle_yesterday_first=False, trade_chan=None,offset_priority="昨今开"):
        """
        创建目标持仓task实例，负责调整归属于该task的持仓(默认为整个账户的该合约净持仓)

        Args:
            api (TqApi): TqApi实例，该task依托于指定api下单/撤单

            symbol (str): 负责调整的合约代码

            price (str): [可选]下单方式, ACTIVE=对价下单, PASSIVE=挂价下单

            init_pos (int): [可选]初始总持仓，默认整个账户的该合约净持仓

            init_pos_today (int): [可选]初始今仓，只有上期所合约需要设置该值，默认为整个账户的该合约今净持仓

            settle_yesterday_first(bool):[可选]是否优先平昨

            trade_chan (TqChan): [可选]成交通知channel, 当有成交发生时会将成交手数(多头为正数，空头为负数)发到该channel上
        """
        super(TargetPosTask, self).__init__()
        self.api = api
        self.symbol = symbol
        self.price = price
        self.current_pos = init_pos
        self.current_pos_today = init_pos_today
        self.settle_yesterday_first = settle_yesterday_first
        self.pos_chan = TqChan(last_only=True)
        self.trade_chan = trade_chan if trade_chan is not None else TqChan()
        self.offset_priority=offset_priority
        self.task = self.api.create_task(self._target_pos_task())

    def set_target_volume(self, volume):
        """
        设置目标持仓手数

        Args:
            volume (int): 目标持仓手数，正数表示多头，负数表示空头，0表示空仓

        Example::

            # 设置 rb1810 持仓为多头5手
            from tqsdk.api import TqApi
            from tqsdk.lib import TargetPosTask

            api = TqApi("SIM")
            target_pos = TargetPosTask(api, "SHFE.rb1810")
            while True:
                api.wait_update()
                target_pos.set_target_volume(5)
        """
        self.pos_chan.put_nowait(volume)

    def _init_position(self):
        '''初始化当前持仓'''
        pos = self.api.get_position(self.symbol)
        if self.current_pos is None:
            self.current_pos = pos["volume_long_today"] + pos["volume_long_his"] - pos["volume_short_today"] - pos["volume_short_his"]
        if self.current_pos_today is None:
            self.current_pos_today = pos["volume_long_today"] - pos["volume_short_today"]
        # 总净持仓=今净持仓+昨净持仓
        # 这里为了避免处理锁仓的情况，会将今净持仓调整为与总净持仓同向并小于等于总净持仓，即总净持仓中有多少手是今仓
        # 如果今净持仓与昨净持仓同向，不需要调整。如果不同向，当今净持仓与总净持仓同向时今净持仓=总净持仓，否则等于0
        # 即将今净持仓调整到 0 与 总净持仓 之间
        self.current_pos_today = max(self.current_pos_today, min(0, self.current_pos))
        self.current_pos_today = min(self.current_pos_today, max(0, self.current_pos))
        self.pos=pos

    async def _target_pos_task(self):
        """负责调整目标持仓的task"""
        self._init_position()
        all_tasks=[]
        
        async for target_pos in self.pos_chan:
            #确定调仓增减方向
            delta_volume=target_pos-self.current_pos
            if delta_volume>0:  #买单(增加净持仓)
                dir="BUY"
                ydAvailable=self.pos['volume_short_his']-self.pos['volume_short_frozen']  #昨空可用
                tdAvailable=self.pos['volume_short_today']-self.pos['volume_short_frozen_today']  #今空可用
            else:  #卖单
                dir="SELL"
                ydAvailable=self.pos['volume_long_his']-self.pos['volume_long_frozen']  #昨多可用
                tdAvailable=self.pos['volume_long_today']-self.pos['volume_long_frozen_today']  #今多可用
                
            volume_to_order=abs(delta_volume)  #报单任务总手数
        
            for each_priority in self.offset_priority:  #按不同模式的优先级顺序报出不同的offset单，股指(“昨开”)平昨优先从不平今就先报平昨，原油平今优先("今昨开")就报平今
                if volume_to_order<=0:  #总手数已经发完，跳出
                    break
            
                if each_priority=="昨":  #平昨手数
                    if ydAvailable<=0:  #如果没有昨仓直接到下一种offset
                        continue
                    close_yesterday_volume=min(volume_to_order, ydAvailable)
                    order_task=InsertOrderUntilAllTradedTask(self.api, self.symbol, dir, offset="CLOSE",volume=close_yesterday_volume, price=self.price,trade_chan=self.trade_chan)
                    all_tasks.append(order_task)
                    volume_to_order-=close_yesterday_volume  #报单任务减去已经发出的数量
                    self.current_pos+=(close_yesterday_volume if delta_volume>0 else -close_yesterday_volume)
                    
                if each_priority=="今":  #平今手数
                    if tdAvailable<=0:  #如果没有今仓直接到下一种offset
                        continue
                    close_today_volume=min(volume_to_order, tdAvailable)
                    order_task=InsertOrderUntilAllTradedTask(self.api, self.symbol, dir, offset="CLOSETODAY" if (self.symbol.startswith("SHFE") or self.symbol.startswith("INE")) else "CLOSE",volume=close_today_volume, price=self.price,trade_chan=self.trade_chan)
                    all_tasks.append(order_task)
                    volume_to_order-=close_today_volume  #报单任务减去已经发出的数量
                    self.current_pos+=(close_today_volume if delta_volume>0 else -close_today_volume)
                    self.current_pos_today+=(close_today_volume if delta_volume>0 else -close_today_volume)
                    
                if each_priority=="开":  #开仓手数
                    open_volume=volume_to_order
                    order_task=InsertOrderUntilAllTradedTask(self.api, self.symbol, dir, offset="OPEN",volume=open_volume, price=self.price,trade_chan=self.trade_chan)
                    all_tasks.append(order_task)
                    volume_to_order-=open_volume  #报单任务减去已经发出的数量
                    self.current_pos+=(open_volume if delta_volume>0 else -open_volume)
                    self.current_pos_today+=(open_volume if delta_volume>0 else -open_volume)
            await gather(*[each.task for each in all_tasks])

class InsertOrderUntilAllTradedTask:
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
        self.trade_chan = trade_chan if trade_chan is not None else TqChan()
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
                check_chan = TqChan(last_only=True)
                check_task = self.api.create_task(self._check_price(check_chan, limit_price, order))
                await insert_order_task.task
                await check_chan.close()
                await check_task
                order = insert_order_task.order_chan.recv_latest(order)
                self.volume = order["volume_left"]

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

class InsertOrderTask:
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
        self.order_chan = order_chan if order_chan is not None else TqChan()
        self.trade_chan = trade_chan if trade_chan is not None else TqChan()
        self.task = self.api.create_task(self._run())

    async def _run(self):
        """负责下单的task"""
        order = self.api.insert_order(self.symbol, self.direction, self.offset, self.volume, self.limit_price)
        last_order = order.copy()
        last_left = 0
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
