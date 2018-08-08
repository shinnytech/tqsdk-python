#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk.api import TqChan

class TargetPosTask:
    """目标持仓 task, 该 task 可以将指定合约调整到目标头寸"""
	def __init__(self, api, symbol, price="ACTIVE",init_pos=0,init_pos_today=0, trade_chan=None, settle_yesterday_first=True):
		"""
        创建目标持仓task实例

        Args:
            api (TqApi): TqApi实例，该task依托于指定api下单/撤单
            symbol (str): 负责调整的合约代码
            price (str): [可选]下单方式, ACTIVE=对价下单, PASSIVE=挂价下单
            init_pos (int): [可选]初始持仓，默认为0 (全部持仓)
            init_pos_today (int): [可选]初始持仓，默认为0 (此字段只有上期所合约有效: 持今仓)
            trade_chan (TqChan): [可选]成交通知channel, 当有成交发生时会将成交手数(多头为正数，空头为负数)发到该channel上
	    settle_yesterday_first(bool):是否优先平昨
        """
		self.settle_yes_first=settle_yesterday_first
        self.api = api
        self.symbol = symbol
        self.price = price
        self.init_pos = init_pos
        self.init_pos_today = init_pos_today
        self.pos_chan = TqChan(last_only=True)
        self.trade_chan = trade_chan if trade_chan is not None else TqChan()
        self.task = self.api.create_task(self._target_pos_task())
		
		
	def shfe_settle(self, delta_volume):
		'''平上海仓'''
		
		target_direction_type="SELL" if delta_volume>0 else "BUY"
		operations_to_go=[]
		position_status=self.api.get_position(self.symbol)
		
		#昨今多空可用仓
		yes_long_available=position_status['volume_long_his']-position_status['volume_long_frozen']
		yes_short_available=position_status['volume_short_his']-position_status['volume_short_frozen']
		today_long_available=position_status['volume_long_today']-position_status['volume_long_frozen_today']
		today_short_available=position_status['volume_short_today']-position_status['volume_short_frozen_today']
		
		#读取优先仓
		if self.settle_yes_first:  #本品种优先平昨
			prior_available_position= yes_short_available if delta_volume>0 else yes_long_available
			prior_offset="CLOSE"
			secondary_offset="CLOSETODAY"
		else:  #本品种优先平今
			prior_available_position=today_short_available if delta_volume>0 else today_long_available
			prior_offset="CLOSETODAY"
			secondary_offset="CLOSE"
		
		#次要仓
		secondary_position=abs(delta_volume)-prior_available_position
		if secondary_position>0:  #优先仓不够平
			secondary_operation=InsertOrderUntilAllTradedTask(self.api, self.symbol,target_direction_type,secondary_offset,secondary_position, price=self.price,trade_chan=self.trade_chan)
			prior_operation=InsertOrderUntilAllTradedTask(self.api, self.symbol,target_direction_type,prior_offset,prior_available_position, price=self.price,trade_chan=self.trade_chan)
			if prior_available_position>0:  #解决优先仓没有持仓，只平次要仓的情况
				operations_to_go.append(prior_operation)
			operations_to_go.append(secondary_operation)
		else:  #优先仓够平
			operations_to_go.append(InsertOrderUntilAllTradedTask(self.api, self.symbol,target_direction_type,prior_offset,abs(delta_volume), price=self.price,trade_chan=self.trade_chan))
		
		return operations_to_go
		
	def open_position(self, delta_volume):
		'''开仓'''
		long_short=(delta_volume>0)  #开多还是开空
		insert_order_until_all_traded_task=InsertOrderUntilAllTradedTask(self.api, self.symbol,"BUY" if long_short else "SELL", "OPEN",abs(delta_volume), price=self.price,trade_chan=self.trade_chan)
		return [insert_order_until_all_traded_task]
		
	def settle_position(self, delta_volume):
		'''平仓'''
		target_direction_type="SELL" if delta_volume>0 else "BUY"  #大于0平多，小于0平空
		
		if not self.symbol.startswith("SHFE"):#非上期所
			return [InsertOrderUntilAllTradedTask(self.api, self.symbol, target_direction_type, "CLOSE", abs(delta_volume),
										  price=self.price, trade_chan=self.trade_chan)]
		else:
			return self.shfe_settle(delta_volume)

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
			
	async def _target_pos_task(self):
		"""负责调整目标持仓的task,根据构造函数的选项决定上期所先平昨还是先平今，默认平昨"""
		current_pos=self.init_pos
		async for target_pos in self.pos_chan:
		
			delta_volume=target_pos-current_pos
			
			operation_list_to_go=[]
			
			if (current_pos>=0 and delta_volume>0) or (current_pos<=0 and delta_volume<0):  #增多仓或者增空仓
				operation_list_to_go.extend(self.open_position(delta_volume))
				pass
			
			if (0<=target_pos<current_pos) or (0>=target_pos>current_pos):  #减多仓或者减空仓
				operation_list_to_go.extend(self.settle_position(-delta_volume,current_pos))
				pass
			if target_pos>0>current_pos or target_pos<0<current_pos:  #空换多或者多换空
				operation_list_to_go.extend(self.settle_position(current_pos))
				operation_list_to_go.extend(self.open_position(target_pos))
				pass
			
			await gather(*[each.task for each in operation_list_to_go])
			current_pos+=delta_volume
        """
        负责调整目标持仓的task
        上期所区分平今平昨，先平今仓
        """
        current_pos = self.init_pos
        current_pos_today = self.init_pos_today
        async for target_pos in self.pos_chan:
            # 平仓
            if self.symbol.startswith('SHFE'):
                if (current_pos < 0 and target_pos > current_pos) or (current_pos > 0 and target_pos < current_pos):
                    vol = min(abs(target_pos - current_pos), abs(current_pos))
                    if vol <= abs(current_pos_today):
                        insert_order_until_all_traded_task = InsertOrderUntilAllTradedTask(self.api, self.symbol,
                                                                                           "BUY" if current_pos < 0 else "SELL",
                                                                                           "CLOSETODAY", vol, price=self.price,
                                                                                           trade_chan=self.trade_chan)
                        await insert_order_until_all_traded_task.task
                        current_pos_today += vol if current_pos_today < 0 else -vol
                        current_pos += vol if current_pos < 0 else -vol
                    else:
                        insert_order_until_all_traded_task = InsertOrderUntilAllTradedTask(self.api, self.symbol,
                                                                                           "BUY" if current_pos < 0 else "SELL",
                                                                                           "CLOSETODAY", abs(current_pos_today),
                                                                                           price=self.price,
                                                                                           trade_chan=self.trade_chan)
                        insert_order_until_all_traded_task_his = InsertOrderUntilAllTradedTask(self.api, self.symbol,
                                                                                           "BUY" if current_pos < 0 else "SELL",
                                                                                           "CLOSE", vol - abs(current_pos_today),
                                                                                           price=self.price,
                                                                                           trade_chan=self.trade_chan)
                        await insert_order_until_all_traded_task.task
                        await insert_order_until_all_traded_task_his.task
                        current_pos += vol if current_pos < 0 else -vol
                        current_pos_today += abs(current_pos_today) if current_pos_today < 0 else -abs(current_pos_today)
            elif (current_pos < 0 and target_pos > current_pos) or (current_pos > 0 and target_pos < current_pos):
                vol = min(abs(target_pos-current_pos), abs(current_pos))
                insert_order_until_all_traded_task = InsertOrderUntilAllTradedTask(self.api, self.symbol, "BUY" if current_pos < 0 else "SELL", "CLOSE", vol, price=self.price, trade_chan=self.trade_chan)
                await insert_order_until_all_traded_task.task
                current_pos += vol if current_pos < 0 else -vol
            if target_pos != current_pos:
                # 开仓
                vol = target_pos-current_pos
                insert_order_until_all_traded_task = InsertOrderUntilAllTradedTask(self.api, self.symbol, "BUY" if vol > 0 else "SELL", "OPEN", abs(vol), price = self.price, trade_chan=self.trade_chan)
                await insert_order_until_all_traded_task.task
                current_pos += vol


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
