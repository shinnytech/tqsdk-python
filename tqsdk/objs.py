#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from collections.abc import MutableMapping


class Entity(MutableMapping):
    def __setitem__(self, key, value):
        return self.__dict__.__setitem__(key, value)

    def __delitem__(self, key):
        return

    def __getitem__(self, key):
        return self.__dict__.__getitem__(key)

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return '{}, D({})'.format(super(Entity, self).__repr__(),
                                  self.__dict__)


class Quote(Entity):
    """ Quote 是一个行情对象 """

    def __init__(self, api):
        self._api = api
        #: "2017-07-26 23:04:21.000001" (行情从交易所发出的时间(北京时间))
        self.datetime = ""
        #: 6122.0 (卖一价)
        self.ask_price1 = float("nan")
        #: 3 (卖一量)
        self.ask_volume1 = 0
        #: 6121.0 (买一价)
        self.bid_price1 = float("nan")
        #: 7 (买一量)
        self.bid_volume1 = 0
        #: 6122.0 (最新价)
        self.last_price = float("nan")
        #: 6129.0 (当日最高价)
        self.highest = float("nan")
        #: 6101.0 (当日最低价)
        self.lowest = float("nan")
        #: 6102.0 (开盘价)
        self.open = float("nan")
        #: nan (收盘价)
        self.close = float("nan")
        #: 6119.0 (当日均价)
        self.average = float("nan")
        #: 89252 (成交量)
        self.volume = 0
        #: 5461329880.0 (成交额)
        self.amount = float("nan")
        #: 616424 (持仓量)
        self.open_interest = 0
        #: nan (结算价)
        self.settlement = float("nan")
        #: 6388.0 (涨停价)
        self.upper_limit = float("nan")
        #: 5896.0 (跌停价)
        self.lower_limit = float("nan")
        #: 616620 (昨持仓量)
        self.pre_open_interest = 0
        #: 6142.0 (昨结算价)
        self.pre_settlement = float("nan")
        #: 6106.0 (昨收盘价)
        self.pre_close = float("nan")
        #: 10.0 (合约价格单位)
        self.price_tick = float("nan")
        #: 0 (合约价格小数位数)
        self.price_decs = 0
        #: 10 (合约乘数)
        self.volume_multiple = 0
        #: 500 (最大限价单手数)
        self.max_limit_order_volume = 0
        #: 0 (最大市价单手数)
        self.max_market_order_volume = 0
        #: 1 (最小限价单手数)
        self.min_limit_order_volume = 0
        #: 0 (最小市价单手数)
        self.min_market_order_volume = 0
        #: SHFE.rb1901 (标的合约)
        self.underlying_symbol = ""
        #: nan (行权价)
        self.strike_price = float("nan")
        #: −20.0 (涨跌)
        self.change = float("nan")
        #: −0.00325 (涨跌幅)
        self.change_percent = float("nan")
        #: False (合约是否已下市)
        self.expired = False


class Account(Entity):
    """ Account 是一个账户对象 """

    def __init__(self, api):
        self._api = api
        #: "CNY" (币种)
        self.currency = ""
        #: 9912934.78 (昨日账户权益)
        self.pre_balance = float("nan")
        #: (静态权益)
        self.static_balance = float("nan")
        #: 9963216.55 (账户权益)
        self.balance = float("nan")
        #: 9480176.15 (可用资金)
        self.available = float("nan")
        #: 8910.0 (浮动盈亏)
        self.float_profit = float("nan")
        #: 1120.0(持仓盈亏)
        self.position_profit = float("nan")
        #: -11120.0 (本交易日内平仓盈亏)
        self.close_profit = float("nan")
        #: 0.0(冻结保证金)
        self.frozen_margin = float("nan")
        #: 11232.23 (保证金占用)
        self.margin = float("nan")
        #: 0.0 (冻结手续费)
        self.frozen_commission = float("nan")
        #: 123.0 (本交易日内交纳的手续费)
        self.commission = float("nan")
        #: 0.0 (冻结权利金)
        self.frozen_premium = float("nan")
        #: 0.0 (本交易日内交纳的权利金)
        self.premium = float("nan")
        #: 1234.0 (本交易日内的入金金额)
        self.deposit = float("nan")
        #: 890.0 (本交易日内的出金金额)
        self.withdraw = float("nan")
        #: 0.048482375 (风险度)
        self.risk_ratio = float("nan")


class Position(Entity):
    """ Position 是一个持仓对象 """

    def __init__(self, api):
        self._api = api
        #: "SHFE" (交易所)
        self.exchange_id = ""
        #: "rb1901" (交易所内的合约代码)
        self.instrument_id = ""
        #: 10 (多头今仓手数)
        self.volume_long_today = 0
        #: 5 (多头老仓手数)
        self.volume_long_his = 0
        #: 15 (多头手数)
        self.volume_long = 0
        #: 3 (多头今仓冻结)
        self.volume_long_frozen_today = 0
        #: 2 (多头老仓冻结)
        self.volume_long_frozen_his = 0
        #: 5 (多头持仓冻结)
        self.volume_long_frozen = 0
        #: 3 (空头今仓手数)
        self.volume_short_today = 0
        #: 0 (空头老仓手数)
        self.volume_short_his = 0
        #: 3 (空头手数)
        self.volume_short = 0
        #: 0 (空头今仓冻结)
        self.volume_short_frozen_today = 0
        #: 0 (空头老仓冻结)
        self.volume_short_frozen_his = 0
        #: 0 (空头持仓冻结)
        self.volume_short_frozen = 0
        #: 3120.0 (多头开仓均价)
        self.open_price_long = float("nan")
        #: 3310.0 (空头开仓均价)
        self.open_price_short = float("nan")
        #: 468000.0 (多头开仓市值)
        self.open_cost_long = float("nan")
        #: 99300.0 (空头开仓市值)
        self.open_cost_short = float("nan")
        #: 3200.0 (多头持仓均价)
        self.position_price_long = float("nan")
        #: 3330.0 (空头持仓均价)
        self.position_price_short = float("nan")
        #: 480000.0 (多头持仓市值)
        self.position_cost_long = float("nan")
        #: 99900.0 (空头持仓市值)
        self.position_cost_short = float("nan")
        #: 12000.0 (多头浮动盈亏)
        self.float_profit_long = float("nan")
        #: 3300.0 (空头浮动盈亏)
        self.float_profit_short = float("nan")
        #: 15300.0 (浮动盈亏)
        self.float_profit = float("nan")
        #: 0.0 (多头持仓盈亏)
        self.position_profit_long = float("nan")
        #: 3900.0 (空头持仓盈亏)
        self.position_profit_short = float("nan")
        #: 3900.0 (持仓盈亏)
        self.position_profit = float("nan")
        #: 50000.0 (多头占用保证金)
        self.margin_long = float("nan")
        #: 10000.0 (空头占用保证金)
        self.margin_short = float("nan")
        #: 60000.0 (占用保证金)
        self.margin = float("nan")


class Order(Entity):
    """ Order 是一个委托单对象 """
    def __init__(self, api):
        self._api = api
        #: "123" (委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的)
        self.order_id = ""
        #: "1928341" (交易所单号)
        self.exchange_order_id = ""
        #: "SHFE" (交易所)
        self.exchange_id = ""
        #: "rb1901" (交易所内的合约代码)
        self.instrument_id = ""
        #: "BUY" (下单方向, BUY=买, SELL=卖)
        self.direction = ""
        #: "OPEN" (开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今)
        self.offset = ""
        #: 10 (总报单手数)
        self.volume_orign = 0
        #: 5 (未成交手数)
        self.volume_left = 0
        #: 4500.0 (委托价格, 仅当 price_type = LIMIT 时有效)
        self.limit_price = float("nan")
        #: "LIMIT" (价格类型, ANY=市价, LIMIT=限价)
        self.price_type = ""
        #: "ANY" (手数条件, ANY=任何数量, MIN=最小数量, ALL=全部数量)
        self.volume_condition = ""
        #: "GFD" (时间条件, IOC=立即完成，否则撤销, GFS=本节有效, GFD=当日有效, GTC=撤销前有效, GFA=集合竞价有效)
        self.time_condition = ""
        #: 1501074872000000000 (下单时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
        self.insert_date_time = 0
        #: "报单成功" (委托单状态信息)
        self.last_msg = ""
        #: "ALIVE" (委托单状态, ALIVE=有效, FINISHED=已完)
        self.status = ""

    @property
    def is_dead(self):
        """
        判定这个委托单是否确定已死亡（以后一定不会再产生成交）

        :return: 确定委托单已死时，返回 True, 否则返回 False. 注意，返回 False 不代表委托单还存活，有可能交易所回来的信息还在路上或者丢掉了
        """
        return self.status == "FINISHED"

    @property
    def is_online(self):
        """
        判定这个委托单是否确定已报入交易所（即下单成功，无论是否成交）

        :return: 确定委托单已报入交易所时，返回 True, 否则返回 False. 注意，返回 False 不代表确定未报入交易所，有可能交易所回来的信息还在路上或者丢掉了
        """
        return self.exchange_order_id != "" and self.status == "ALIVE"

    @property
    def is_error(self):
        """
        判定这个委托单是否确定是错单（即下单失败，一定不会有成交）

        :return: 确定委托单是错单时，返回 True, 否则返回 False. 注意，返回 False 不代表确定不是错单，有可能交易所回来的信息还在路上或者丢掉了
        """
        return self.exchange_order_id == "" and self.status == "FINISHED"


class Trade(Entity):
    """ Trade 是一个成交对象 """

    def __init__(self, api):
        self._api = api
        #: "123" (委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的)
        self.order_id = ""
        #: "123|19723" (成交ID, 对于一个用户的所有成交，这个ID都是不重复的)
        self.trade_id = ""
        #: "829414" (交易所成交号)
        self.exchange_trade_id = ""
        #: "SHFE" (交易所)
        self.exchange_id = ""
        #: "rb1901" (交易所内的合约代码)
        self.instrument_id = ""
        #: "BUY" (下单方向, BUY=买, SELL=卖)
        self.direction = ""
        #: "OPEN" (开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今)
        self.offset = ""
        #: 4510.0 (成交价格)
        self.price = float("nan")
        #: 5 (成交手数)
        self.volume = 0
        #: 1501074872000000000 (成交时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
        self.trade_date_time = 0
