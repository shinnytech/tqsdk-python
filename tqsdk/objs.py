#:!/usr/bin/env python
#:  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from collections.abc import MutableMapping
import copy


class Entity(MutableMapping):
    def __setitem__(self, key, value):
        return self.__dict__.__setitem__(key, value)

    def __delitem__(self, key):
        return self.__dict__.__delitem__(key)

    def __getitem__(self, key):
        return self.__dict__.__getitem__(key)

    def __iter__(self):
        return iter({k: v for k, v in self.__dict__.items() if not k.startswith("_")})

    def __len__(self):
        return len({k: v for k, v in self.__dict__.items() if not k.startswith("_")})

    def __str__(self):
        return str({k: v for k, v in self.__dict__.items() if not k.startswith("_")})

    def __repr__(self):
        return '{}, D({})'.format(super(Entity, self).__repr__(),
                                  {k: v for k, v in self.__dict__.items() if not k.startswith("_")})

    def copy(self):
        return copy.copy(self)


class Quote(Entity):
    """ Quote 是一个行情对象 """

    def __init__(self, api):
        self._api = api
        #: 行情从交易所发出的时间(北京时间), 格式为 "2017-07-26 23:04:21.000001"
        self.datetime = ""
        #: 卖一价
        self.ask_price1 = float("nan")
        #: 卖一量
        self.ask_volume1 = 0
        #: 买一价
        self.bid_price1 = float("nan")
        #: 买一量
        self.bid_volume1 = 0
        #: 最新价
        self.last_price = float("nan")
        #: 当日最高价
        self.highest = float("nan")
        #: 当日最低价
        self.lowest = float("nan")
        #: 开盘价
        self.open = float("nan")
        #: 收盘价
        self.close = float("nan")
        #: 当日均价
        self.average = float("nan")
        #: 成交量
        self.volume = 0
        #: 成交额
        self.amount = float("nan")
        #: 持仓量
        self.open_interest = 0
        #: 结算价
        self.settlement = float("nan")
        #: 涨停价
        self.upper_limit = float("nan")
        #: 跌停价
        self.lower_limit = float("nan")
        #: 昨持仓量
        self.pre_open_interest = 0
        #: 昨结算价
        self.pre_settlement = float("nan")
        #: 昨收盘价
        self.pre_close = float("nan")
        #: 合约价格变动单位
        self.price_tick = float("nan")
        #: 合约价格小数位数
        self.price_decs = 0
        #: 合约乘数
        self.volume_multiple = 0
        #: 最大限价单手数
        self.max_limit_order_volume = 0
        #: 最大市价单手数
        self.max_market_order_volume = 0
        #: 最小限价单手数
        self.min_limit_order_volume = 0
        #: 最小市价单手数
        self.min_market_order_volume = 0
        #: 标的合约
        self.underlying_symbol = ""
        #: 行权价
        self.strike_price = float("nan")
        #: 涨跌
        self.change = float("nan")
        #: 涨跌幅
        self.change_percent = float("nan")
        #: 合约是否已下市
        self.expired = False


class Kline(Entity):
    """ Kline 是一个K线对象 """

    def __init__(self, api):
        self._api = api
        #: K线起点时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数
        self.datetime = 0
        #: K线起始时刻的最新价
        self.open = float("nan")
        #: K线时间范围内的最高价
        self.high = float("nan")
        #: K线时间范围内的最低价
        self.low = float("nan")
        #: K线结束时刻的最新价
        self.close = float("nan")
        #: K线时间范围内的成交量
        self.volume = 0
        #: K线起始时刻的持仓量
        self.open_oi = 0
        #: K线结束时刻的持仓量
        self.close_oi = 0


class Tick(Entity):
    """ Tick 是一个tick对象 """

    def __init__(self, api):
        self._api = api
        #: tick从交易所发出的时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数
        self.datetime = 0
        #: 最新价
        self.last_price = float("nan")
        #: 当日均价
        self.average = float("nan")
        #: 当日最高价
        self.highest = float("nan")
        #: 当日最低价
        self.lowest = float("nan")
        #: 卖一价
        self.ask_price1 = float("nan")
        #: 卖一量
        self.ask_volume1 = 0
        #: 买一价
        self.bid_price1 = float("nan")
        #:买一量
        self.bid_volume1 = 0
        #: 当日成交量
        self.volume = 0
        #: 成交额
        self.amount = float("nan")
        #: 持仓量
        self.open_interest = 0


class Account(Entity):
    """ Account 是一个账户对象 """

    def __init__(self, api):
        self._api = api
        #: 币种
        self.currency = ""
        #: 昨日账户权益
        self.pre_balance = float("nan")
        #: 静态权益 （静态权益 = 昨日结算的权益 + 今日入金 - 今日出金, 以服务器查询ctp后返回的金额为准）
        self.static_balance = float("nan")
        #: 账户权益 （账户权益 = 动态权益 = 静态权益 + 平仓盈亏 + 持仓盈亏 - 手续费）
        self.balance = float("nan")
        #: 可用资金
        self.available = float("nan")
        #: 浮动盈亏
        self.float_profit = float("nan")
        #: 持仓盈亏
        self.position_profit = float("nan")
        #: 本交易日内平仓盈亏
        self.close_profit = float("nan")
        #: 冻结保证金
        self.frozen_margin = float("nan")
        #: 保证金占用
        self.margin = float("nan")
        #: 冻结手续费
        self.frozen_commission = float("nan")
        #: 本交易日内交纳的手续费
        self.commission = float("nan")
        #: 冻结权利金
        self.frozen_premium = float("nan")
        #: 本交易日内交纳的权利金
        self.premium = float("nan")
        #: 本交易日内的入金金额
        self.deposit = float("nan")
        #: 本交易日内的出金金额
        self.withdraw = float("nan")
        #: 风险度
        self.risk_ratio = float("nan")


class Position(Entity):
    """ Position 是一个持仓对象 """

    def __init__(self, api):
        self._api = api
        #: 交易所
        self.exchange_id = ""
        #: 交易所内的合约代码
        self.instrument_id = ""
        #: 多头老仓手数
        self.pos_long_his = 0
        #: 多头今仓手数
        self.pos_long_today = 0
        #: 空头老仓手数
        self.pos_short_his = 0
        #: 空头今仓手数
        self.pos_short_today = 0
        #: 期货公司查询的多头今仓手数 (不推荐, 推荐使用pos_long_today)
        self.volume_long_today = 0
        #: 期货公司查询的多头老仓手数 (不推荐, 推荐使用pos_long_his)
        self.volume_long_his = 0
        #: 期货公司查询的多头手数 (不推荐, 推荐使用pos_long)
        self.volume_long = 0
        #: 期货公司查询的多头今仓冻结 (不推荐)
        self.volume_long_frozen_today = 0
        #: 期货公司查询的多头老仓冻结 (不推荐)
        self.volume_long_frozen_his = 0
        #: 期货公司查询的多头持仓冻结 (不推荐)
        self.volume_long_frozen = 0
        #: 期货公司查询的空头今仓手数 (不推荐, 推荐使用pos_short_today)
        self.volume_short_today = 0
        #: 期货公司查询的空头老仓手数 (不推荐, 推荐使用pos_short_his)
        self.volume_short_his = 0
        #: 期货公司查询的空头手数 (不推荐, 推荐使用pos_short)
        self.volume_short = 0
        #: 期货公司查询的空头今仓冻结 (不推荐)
        self.volume_short_frozen_today = 0
        #: 期货公司查询的空头老仓冻结 (不推荐)
        self.volume_short_frozen_his = 0
        #: 期货公司查询的空头持仓冻结 (不推荐)
        self.volume_short_frozen = 0
        #: 多头开仓均价
        self.open_price_long = float("nan")
        #: 空头开仓均价
        self.open_price_short = float("nan")
        #: 多头开仓市值
        self.open_cost_long = float("nan")
        #: 空头开仓市值
        self.open_cost_short = float("nan")
        #: 多头持仓均价
        self.position_price_long = float("nan")
        #: 空头持仓均价
        self.position_price_short = float("nan")
        #: 多头持仓市值
        self.position_cost_long = float("nan")
        #: 空头持仓市值
        self.position_cost_short = float("nan")
        #: 多头浮动盈亏
        self.float_profit_long = float("nan")
        #: 空头浮动盈亏
        self.float_profit_short = float("nan")
        #: 浮动盈亏 （浮动盈亏: 相对于开仓价的盈亏）
        self.float_profit = float("nan")
        #: 多头持仓盈亏
        self.position_profit_long = float("nan")
        #: 空头持仓盈亏
        self.position_profit_short = float("nan")
        #: 持仓盈亏 （持仓盈亏: 相对于上一交易日结算价的盈亏）
        self.position_profit = float("nan")
        #: 多头占用保证金
        self.margin_long = float("nan")
        #: 空头占用保证金
        self.margin_short = float("nan")
        #: 占用保证金
        self.margin = float("nan")

    @property
    def pos(self):
        """
        净持仓手数

        :return: int, ==0表示无持仓或多空持仓手数相等. <0表示空头持仓大于多头持仓, >0表示多头持仓大于空头持仓
        """
        return self.pos_long - self.pos_short

    @property
    def pos_long(self):
        """
        多头持仓手数

        :return: int, ==0表示无多头持仓. >0表示多头持仓手数
        """
        return (self.pos_long_his + self.pos_long_today)

    @property
    def pos_short(self):
        """
        空头持仓手数

        :return: int, ==0表示无空头持仓. >0表示空头持仓手数
        """
        return (self.pos_short_his + self.pos_short_today)

    @property
    def orders(self):
        """
        与此持仓相关的开仓/平仓挂单

        :return: dict, 其中每个元素的key为委托单ID, value为 :py:class:`~tqsdk.objs.Order`
        """
        tdict = self._api._get_obj(self._api._data, ["trade", self._api._account.account_id, "orders"])
        fts = {order_id: order for order_id, order in tdict.items() if (not order_id.startswith(
            "_")) and order.instrument_id == self.instrument_id and order.exchange_id == self.exchange_id and order.status == "ALIVE"}
        return fts


class Order(Entity):
    """ Order 是一个委托单对象 """

    def __init__(self, api):
        self._api = api
        #: 委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
        self.order_id = ""
        #: 交易所单号
        self.exchange_order_id = ""
        #: 交易所
        self.exchange_id = ""
        #: 交易所内的合约代码
        self.instrument_id = ""
        #: 下单方向, BUY=买, SELL=卖
        self.direction = ""
        #: 开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今
        self.offset = ""
        #: 总报单手数
        self.volume_orign = 0
        #: 未成交手数
        self.volume_left = 0
        #: 委托价格, 仅当 price_type = LIMIT 时有效
        self.limit_price = float("nan")
        #: 价格类型, ANY=市价, LIMIT=限价
        self.price_type = ""
        #: 手数条件, ANY=任何数量, MIN=最小数量, ALL=全部数量
        self.volume_condition = ""
        #: 时间条件, IOC=立即完成，否则撤销, GFS=本节有效, GFD=当日有效, GTC=撤销前有效, GFA=集合竞价有效
        self.time_condition = ""
        #: 下单时间，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数.
        self.insert_date_time = 0
        #: 委托单状态信息
        self.last_msg = ""
        #: 委托单状态, ALIVE=有效, FINISHED=已完
        self.status = ""
        self._this_session = False

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

    @property
    def trade_price(self):
        """
        平均成交价

        :return: 当委托单部分成交或全部成交时, 返回成交部分的平均成交价. 无任何成交时, 返回 nan
        """
        tdict = self._api._get_obj(self._api._data, ["trade", self._api._account.account_id, "trades"])
        sum_volume = sum([trade.volume for trade_id, trade in tdict.items() if
                          (not trade_id.startswith("_")) and trade.order_id == self.order_id])
        if sum_volume == 0:
            return float('nan')
        sum_amount = sum([trade.volume * trade.price for trade_id, trade in tdict.items() if
                          (not trade_id.startswith("_")) and trade.order_id == self.order_id])
        return sum_amount / sum_volume

    @property
    def trade_records(self):
        """
        成交记录

        :return: dict, 其中每个元素的key为成交ID, value为 :py:class:`~tqsdk.objs.Trade`
        """
        tdict = self._api._get_obj(self._api._data, ["trade", self._api._account.account_id, "trades"])
        fts = {trade_id: trade for trade_id, trade in tdict.items() if
               (not trade_id.startswith("_")) and trade.order_id == self.order_id}
        return fts


class Trade(Entity):
    """ Trade 是一个成交对象 """

    def __init__(self, api):
        self._api = api
        #: 委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
        self.order_id = ""
        #: 成交ID, 对于一个用户的所有成交，这个ID都是不重复的
        self.trade_id = ""
        #: 交易所成交号
        self.exchange_trade_id = ""
        #: 交易所
        self.exchange_id = ""
        #: 交易所内的合约代码
        self.instrument_id = ""
        #: 下单方向, BUY=买, SELL=卖
        self.direction = ""
        #: 开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今
        self.offset = ""
        #: 成交价格
        self.price = float("nan")
        #: 成交手数
        self.volume = 0
        #: 成交时间，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数
        self.trade_date_time = 0
