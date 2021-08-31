#:!/usr/bin/env python
#:  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import copy
import json
import warnings

from tqsdk.datetime import _get_expire_rest_days
from tqsdk.diff import _get_obj
from tqsdk.entity import Entity
from tqsdk.utils import _query_for_init, _generate_uuid


class QuotesEntity(Entity):

    def __init__(self, api):
        self._api = api
        self._not_send_init_query = True

    def __iter__(self):
        message = """
            不推荐使用 api._data['quotes'] 获取全部合约，该使用方法会在 20201101 之后的版本中放弃维护。
            需要注意：
            * 在同步代码中，初次使用 api._data['quotes'] 获取全部合约会产生一个耗时很长的查询。
            * 在协程中，api._data['quotes'] 这种用法不支持使用。
            请尽快修改使用新的接口，参考链接 http://doc.shinnytech.com/tqsdk/reference/tqsdk.api.html#tqsdk.api.TqApi.query_quotes
        """
        warnings.warn(message, DeprecationWarning, stacklevel=3)
        self._api._logger.warning("deprecation", content="Deprecation Warning in api._data['quotes']")

        # 兼容旧版 tqsdk 所做的修改，来支持用户使用 for k,v in api._data.quotes.items() 类似的用法
        # 从 api._init_() 最后 3 行移到这里
        if self._not_send_init_query and self._api._stock:
            self._not_send_init_query = False
            q, v = _query_for_init()
            self._api.query_graphql(q, v, _generate_uuid("PYSDK_quote"))
        return super().__iter__()


class Quote(Entity):
    """ Quote 是一个行情对象 """

    def __init__(self, api):
        self._api = api
        #: 行情从交易所发出的时间(北京时间), 格式为 "2017-07-26 23:04:21.000001"
        self.datetime: str = ""
        #: 卖一价
        self.ask_price1: float = float("nan")
        #: 卖一量
        self.ask_volume1: int = 0
        #: 买一价
        self.bid_price1: float = float("nan")
        #: 买一量
        self.bid_volume1: int = 0
        #: 卖二价
        self.ask_price2: float = float("nan")
        #: 卖二量
        self.ask_volume2: int = 0
        #: 买二价
        self.bid_price2: float = float("nan")
        #: 买二量
        self.bid_volume2: int = 0
        #: 卖三价
        self.ask_price3: float = float("nan")
        #: 卖三量
        self.ask_volume3: int = 0
        #: 买三价
        self.bid_price3: float = float("nan")
        #: 买三量
        self.bid_volume3: int = 0
        #: 卖四价
        self.ask_price4: float = float("nan")
        #: 卖四量
        self.ask_volume4: int = 0
        #: 买四价
        self.bid_price4: float = float("nan")
        #: 买四量
        self.bid_volume4: int = 0
        #: 卖五价
        self.ask_price5: float = float("nan")
        #: 卖五量
        self.ask_volume5: int = 0
        #: 买五价
        self.bid_price5: float = float("nan")
        #: 买五量
        self.bid_volume5: int = 0
        #: 最新价
        self.last_price: float = float("nan")
        #: 当日最高价
        self.highest: float = float("nan")
        #: 当日最低价
        self.lowest: float = float("nan")
        #: 开盘价
        self.open: float = float("nan")
        #: 收盘价
        self.close: float = float("nan")
        #: 当日均价
        self.average: float = float("nan")
        #: 成交量
        self.volume: int = 0
        #: 成交额
        self.amount: float = float("nan")
        #: 持仓量
        self.open_interest: int = 0
        #: 结算价
        self.settlement: float = float("nan")
        #: 涨停价
        self.upper_limit: float = float("nan")
        #: 跌停价
        self.lower_limit: float = float("nan")
        #: 昨持仓量
        self.pre_open_interest: int = 0
        #: 昨结算价
        self.pre_settlement: float = float("nan")
        #: 昨收盘价
        self.pre_close: float = float("nan")
        #: 合约价格变动单位
        self.price_tick: float = float("nan")
        #: 合约价格小数位数
        self.price_decs: int = 0
        #: 合约乘数
        self.volume_multiple: int = 0
        #: 最大限价单手数
        self.max_limit_order_volume: int = 0
        #: 最大市价单手数
        self.max_market_order_volume: int = 0
        #: 最小限价单手数
        self.min_limit_order_volume: int = 0
        #: 最小市价单手数
        self.min_market_order_volume: int = 0
        #: 标的合约
        self.underlying_symbol: str = ""
        #: 行权价
        self.strike_price: float = float("nan")
        #: 合约类型
        self.ins_class: str = ""
        #: 交易所内的合约代码
        self.instrument_id: str = ""
        #: 合约中文名
        self.instrument_name: str = ""
        #: 交易所代码
        self.exchange_id: str = ""
        #: 合约是否已下市
        self.expired: bool = False
        #: 交易时间段
        self.trading_time: TradingTime = TradingTime(self._api)
        #: 到期具体日，以秒为单位的 timestamp 值
        self.expire_datetime: float = float("nan")
        #: 期货交割日年份，只对期货品种有效。期权推荐使用最后行权日年份
        self.delivery_year: int = 0
        #: 期货交割日月份，只对期货品种有效。期权推荐使用最后行权日月份
        self.delivery_month: int = 0
        #: 期权最后行权日，以秒为单位的 timestamp 值
        self.last_exercise_datetime: float = float("nan")
        #: 期权最后行权日年份，只对期权品种有效。
        self.exercise_year: int = 0
        #: 期权最后行权日月份，只对期权品种有效。
        self.exercise_month: int = 0
        #: 期权方向
        self.option_class: str = ""
        #: 期权行权方式，美式:'A'，欧式:'E'
        self.exercise_type: str = ""
        #: 品种代码
        self.product_id: str = ""
        #: ETF实时单位基金净值
        self.iopv: float = float("nan")
        #: 日流通股数，只对证券产品有效。
        self.public_float_share_quantity: int = 0
        #: 除权表 ["20190601,0.15","20200107,0.2"…]
        self.stock_dividend_ratio: list = []
        #: 除息表 ["20190601,0.15","20200107,0.2"…]
        self.cash_dividend_ratio: list = []
        #: 距离到期日的剩余天数（自然日天数），正数表示距离到期日的剩余天数，0表示到期日当天，负数表示距离到期日已经过去的天数
        self.expire_rest_days: int = float('nan')

    def _instance_entity(self, path):
        super(Quote, self)._instance_entity(path)
        self.trading_time = copy.copy(self.trading_time)
        self.trading_time._instance_entity(path + ["trading_time"])

    @property
    def underlying_quote(self):
        if self.underlying_symbol:
            return _get_obj(self._api._data, ["quotes", self.underlying_symbol], self._api._prototype["quotes"]["#"])
        return None

    def __await__(self):
        assert self._task
        return self._task.__await__()


class TradingTime(Entity):
    """ TradingTime 是一个交易时间对象
        它不是一个可单独使用的类，而是用于定义 Qoute 的 trading_time 字段的类型

        (每个连续的交易时间段是一个列表，包含两个字符串元素，分别为这个时间段的起止点)"""

    def __init__(self, api):
        self._api = api
        #: 白盘
        self.day: list = []
        #: 夜盘（注意：本字段中过了 24：00 的时间则在其基础往上加，如凌晨1点为 '25:00:00' ）
        self.night: list = []

    def __repr__(self):
        return json.dumps({"day": self.day, "night": self.night})


class Kline(Entity):
    """ Kline 是一个K线对象 """

    def __init__(self, api):
        self._api = api
        #: K线起点时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数
        self.datetime: int = 0
        #: K线起始时刻的最新价
        self.open: float = float("nan")
        #: K线时间范围内的最高价
        self.high: float = float("nan")
        #: K线时间范围内的最低价
        self.low: float = float("nan")
        #: K线结束时刻的最新价
        self.close: float = float("nan")
        #: K线时间范围内的成交量
        self.volume: int = 0
        #: K线起始时刻的持仓量
        self.open_oi: int = 0
        #: K线结束时刻的持仓量
        self.close_oi: int = 0


class Tick(Entity):
    """ Tick 是一个tick对象 """

    def __init__(self, api):
        self._api = api
        #: tick从交易所发出的时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数
        self.datetime: int = 0
        #: 最新价
        self.last_price: float = float("nan")
        #: 当日均价
        self.average: float = float("nan")
        #: 当日最高价
        self.highest: float = float("nan")
        #: 当日最低价
        self.lowest: float = float("nan")
        #: 卖1价
        self.ask_price1: float = float("nan")
        #: 卖1量
        self.ask_volume1: int = 0
        #: 买1价
        self.bid_price1: float = float("nan")
        #: 买1量
        self.bid_volume1: int = 0
        #: 卖2价
        self.ask_price2: float = float("nan")
        #: 卖2量
        self.ask_volume2: int = 0
        #: 买2价
        self.bid_price2: float = float("nan")
        #: 买2量
        self.bid_volume2: int = 0
        #: 卖3价
        self.ask_price3: float = float("nan")
        #: 卖3量
        self.ask_volume3: int = 0
        #: 买3价
        self.bid_price3: float = float("nan")
        #: 买3量
        self.bid_volume3: int = 0
        #: 卖4价
        self.ask_price4: float = float("nan")
        #: 卖4量
        self.ask_volume4: int = 0
        #: 买4价
        self.bid_price4: float = float("nan")
        #: 买4量
        self.bid_volume4: int = 0
        #: 卖5价
        self.ask_price5: float = float("nan")
        #: 卖5量
        self.ask_volume5: int = 0
        #: 买5价
        self.bid_price5: float = float("nan")
        #: 买5量
        self.bid_volume5: int = 0
        #: 当日成交量
        self.volume: int = 0
        #: 成交额
        self.amount: float = float("nan")
        #: 持仓量
        self.open_interest: int = 0


class Account(Entity):
    """ Account 是一个账户对象 """

    def __init__(self, api):
        self._api = api
        #: 币种
        self.currency: str = ""
        #: 昨日账户权益(不包含期权)
        self.pre_balance: float = float("nan")
        #: 静态权益 （静态权益 = 昨日结算的权益 + 今日入金 - 今日出金, 以服务器查询ctp后返回的金额为准）(不包含期权)
        self.static_balance: float = float("nan")
        #: 账户权益 （账户权益 = 动态权益 = 静态权益 + 平仓盈亏 + 持仓盈亏 - 手续费 + 权利金 + 期权市值）
        self.balance: float = float("nan")
        #: 可用资金（可用资金 = 账户权益 - 冻结保证金 - 保证金 - 冻结权利金 - 冻结手续费 - 期权市值）
        self.available: float = float("nan")
        #: 期货公司返回的balance（ctp_balance = 静态权益 + 平仓盈亏 + 持仓盈亏 - 手续费 + 权利金）
        self.ctp_balance: float = float("nan")
        #: 期货公司返回的available（ctp_available = ctp_balance - 保证金 - 冻结保证金 - 冻结手续费 - 冻结权利金）
        self.ctp_available: float = float("nan")
        #: 浮动盈亏
        self.float_profit: float = float("nan")
        #: 持仓盈亏
        self.position_profit: float = float("nan")
        #: 本交易日内平仓盈亏
        self.close_profit: float = float("nan")
        #: 冻结保证金
        self.frozen_margin: float = float("nan")
        #: 保证金占用
        self.margin: float = float("nan")
        #: 冻结手续费
        self.frozen_commission: float = float("nan")
        #: 本交易日内交纳的手续费
        self.commission: float = float("nan")
        #: 冻结权利金
        self.frozen_premium: float = float("nan")
        #: 本交易日内收入-交纳的权利金
        self.premium: float = float("nan")
        #: 本交易日内的入金金额
        self.deposit: float = float("nan")
        #: 本交易日内的出金金额
        self.withdraw: float = float("nan")
        #: 风险度（风险度 = 保证金 / 账户权益）
        self.risk_ratio: float = float("nan")
        #: 期权市值
        self.market_value: float = float("nan")


class Position(Entity):
    """ Position 是一个持仓对象 """

    def __init__(self, api):
        self._api = api
        #: 交易所
        self.exchange_id: str = ""
        #: 交易所内的合约代码
        self.instrument_id: str = ""
        #: 多头老仓手数
        self.pos_long_his: int = 0
        #: 多头今仓手数
        self.pos_long_today: int = 0
        #: 空头老仓手数
        self.pos_short_his: int = 0
        #: 空头今仓手数
        self.pos_short_today: int = 0
        #: 期货公司查询的多头今仓手数 (不推荐, 推荐使用pos_long_today)
        self.volume_long_today: int = 0
        #: 期货公司查询的多头老仓手数 (不推荐, 推荐使用pos_long_his)
        self.volume_long_his: int = 0
        #: 期货公司查询的多头手数 (不推荐, 推荐使用pos_long)
        self.volume_long: int = 0
        #: 期货公司查询的多头今仓冻结 (不推荐)
        self.volume_long_frozen_today: int = 0
        #: 期货公司查询的多头老仓冻结 (不推荐)
        self.volume_long_frozen_his: int = 0
        #: 期货公司查询的多头持仓冻结 (不推荐)
        self.volume_long_frozen: int = 0
        #: 期货公司查询的空头今仓手数 (不推荐, 推荐使用pos_short_today)
        self.volume_short_today: int = 0
        #: 期货公司查询的空头老仓手数 (不推荐, 推荐使用pos_short_his)
        self.volume_short_his: int = 0
        #: 期货公司查询的空头手数 (不推荐, 推荐使用pos_short)
        self.volume_short: int = 0
        #: 期货公司查询的空头今仓冻结 (不推荐)
        self.volume_short_frozen_today: int = 0
        #: 期货公司查询的空头老仓冻结 (不推荐)
        self.volume_short_frozen_his: int = 0
        #: 期货公司查询的空头持仓冻结 (不推荐)
        self.volume_short_frozen: int = 0
        #: 多头开仓均价,以开仓价来统计
        self.open_price_long: float = float("nan")
        #: 空头开仓均价,以开仓价来统计
        self.open_price_short: float = float("nan")
        #: 多头开仓成本,为开仓价乘以手数
        self.open_cost_long: float = float("nan")
        #: 空头开仓成本,为开仓价乘以手数
        self.open_cost_short: float = float("nan")
        #: 多头持仓均价,为多头持仓成本除以多头数量
        self.position_price_long: float = float("nan")
        #: 空头持仓均价,为空头持仓成本除以空头数量
        self.position_price_short: float = float("nan")
        #: 多头持仓成本,为今仓的开仓价乘以手数加上昨仓的昨结算价乘以手数的和
        self.position_cost_long: float = float("nan")
        #: 空头持仓成本,为今仓的开仓价乘以手数加上昨仓的昨结算价乘以手数的和
        self.position_cost_short: float = float("nan")
        #: 多头浮动盈亏
        self.float_profit_long: float = float("nan")
        #: 空头浮动盈亏
        self.float_profit_short: float = float("nan")
        #: 浮动盈亏 （浮动盈亏: 相对于开仓价的盈亏）
        self.float_profit: float = float("nan")
        #: 多头持仓盈亏
        self.position_profit_long: float = float("nan")
        #: 空头持仓盈亏
        self.position_profit_short: float = float("nan")
        #: 持仓盈亏 （持仓盈亏: 相对于上一交易日结算价的盈亏），期权持仓盈亏为 0
        self.position_profit: float = float("nan")
        #: 多头占用保证金
        self.margin_long: float = float("nan")
        #: 空头占用保证金
        self.margin_short: float = float("nan")
        #: 占用保证金
        self.margin: float = float("nan")
        #: 期权权利方市值(始终 >= 0)
        self.market_value_long: float = float("nan")
        #: 期权义务方市值(始终 <= 0)
        self.market_value_short: float = float("nan")
        #: 期权市值
        self.market_value: float = float("nan")
        #: 净持仓手数, ==0表示无持仓或多空持仓手数相等. <0表示空头持仓大于多头持仓, >0表示多头持仓大于空头持仓
        self.pos: int = 0
        #: 多头持仓手数, ==0表示无多头持仓. >0表示多头持仓手数
        self.pos_long: int = 0
        #: 空头持仓手数, ==0表示无空头持仓. >0表示空头持仓手数
        self.pos_short: int = 0

    @property
    def orders(self):
        """
        与此持仓相关的开仓/平仓挂单

        :return: dict, 其中每个元素的key为委托单ID, value为 :py:class:`~tqsdk.objs.Order`
        """
        tdict = _get_obj(self._api._data, ["trade", self._path[1], "orders"])
        fts = {order_id: order for order_id, order in tdict.items() if (not order_id.startswith(
            "_")) and order.instrument_id == self.instrument_id and order.exchange_id == self.exchange_id and order.status == "ALIVE"}
        return fts


class Order(Entity):
    """ Order 是一个委托单对象 """

    def __init__(self, api):
        self._api = api
        #: 委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
        self.order_id: str = ""
        #: 交易所单号
        self.exchange_order_id: str = ""
        #: 交易所
        self.exchange_id: str = ""
        #: 交易所内的合约代码
        self.instrument_id: str = ""
        #: 下单方向, BUY=买, SELL=卖
        self.direction: str = ""
        #: 开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今
        self.offset: str = ""
        #: 总报单手数
        self.volume_orign: int = 0
        #: 未成交手数
        self.volume_left: int = 0
        #: 委托价格, 仅当 price_type = LIMIT 时有效
        self.limit_price: float = float("nan")
        #: 价格类型, ANY=市价, LIMIT=限价
        self.price_type: str = ""
        #: 手数条件, ANY=任何数量, MIN=最小数量, ALL=全部数量
        self.volume_condition: str = ""
        #: 时间条件, IOC=立即完成，否则撤销, GFS=本节有效, GFD=当日有效, GTC=撤销前有效, GFA=集合竞价有效
        self.time_condition: str = ""
        #: 下单时间，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数.
        self.insert_date_time: int = 0
        #: 委托单状态信息
        self.last_msg: str = ""
        #: 委托单状态, ALIVE=有效, FINISHED=已完
        self.status: str = ""
        #: 委托单是否确定已死亡（以后一定不会再产生成交）(注意，False 不代表委托单还存活，有可能交易所回来的信息还在路上或者丢掉了)
        self.is_dead: bool = None
        #: 委托单是否确定已报入交易所并等待成交 (注意，返回 False 不代表确定未报入交易所，有可能交易所回来的信息还在路上或者丢掉了)
        self.is_online: bool = None
        #: 委托单是否确定是错单（即下单失败，一定不会有成交）(注意，返回 False 不代表确定不是错单，有可能交易所回来的信息还在路上或者丢掉了)
        self.is_error: bool = None
        #: 平均成交价
        self.trade_price: float = float('nan')

        self._this_session = False

    @property
    def trade_records(self):
        """
        成交记录

        :return: dict, 其中每个元素的key为成交ID, value为 :py:class:`~tqsdk.objs.Trade`
        """
        tdict = _get_obj(self._api._data, ["trade", self._path[1], "trades"])
        fts = {trade_id: trade for trade_id, trade in tdict.items() if
               (not trade_id.startswith("_")) and trade.order_id == self.order_id}
        return fts


class Trade(Entity):
    """ Trade 是一个成交对象 """

    def __init__(self, api):
        self._api = api
        #: 委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
        self.order_id: str = ""
        #: 成交ID, 对于一个用户的所有成交，这个ID都是不重复的
        self.trade_id: str = ""
        #: 交易所成交编号
        self.exchange_trade_id: str = ""
        #: 交易所
        self.exchange_id: str = ""
        #: 交易所内的合约代码
        self.instrument_id: str = ""
        #: 下单方向, BUY=买, SELL=卖
        self.direction: str = ""
        #: 开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今
        self.offset: str = ""
        #: 成交价格
        self.price: float = float("nan")
        #: 成交手数
        self.volume: int = 0
        #: 成交时间，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数
        self.trade_date_time: int = 0


class RiskManagementRule(Entity):

    def __init__(self, api):
        self._api = api
        self.user_id = ""
        self.exchange_id = ""
        self.enable = False
        self.self_trade = SelfTradeRule(self._api)
        self.frequent_cancellation = FrequentCancellationRule(self._api)
        self.trade_position_ratio = TradePositionRatioRule(self._api)

    def _instance_entity(self, path):
        super(RiskManagementRule, self)._instance_entity(path)
        self.self_trade = copy.copy(self.self_trade)
        self.self_trade._instance_entity(path + ["self_trade"])
        self.frequent_cancellation = copy.copy(self.frequent_cancellation)
        self.frequent_cancellation._instance_entity(path + ["frequent_cancellation"])
        self.trade_position_ratio = copy.copy(self.trade_position_ratio)
        self.trade_position_ratio._instance_entity(path + ["trade_position_ratio"])


class SelfTradeRule(Entity):
    """自成交风控规则"""

    def __init__(self, api):
        self._api = api
        #: 最大自成交次数限制
        self.count_limit = 0

    def __repr__(self):
        return json.dumps({"count_limit": self.count_limit})


class FrequentCancellationRule(Entity):
    """频繁报撤单风控规则"""

    def __init__(self, api):
        self._api = api
        #: 频繁报撤单起算报单次数
        self.insert_order_count_limit = 0
        #: 频繁报撤单起算撤单次数
        self.cancel_order_count_limit = 0
        #: 频繁报撤单撤单比例限额,为百分比
        self.cancel_order_percent_limit = float("nan")

    def __repr__(self):
        return json.dumps({
            "insert_order_count_limit": self.insert_order_count_limit,
            "cancel_order_count_limit": self.cancel_order_count_limit,
            "cancel_order_percent_limit": self.cancel_order_percent_limit
        })


class TradePositionRatioRule(Entity):
    """成交持仓比风控规则"""

    def __init__(self, api):
        self._api = api
        #: 成交持仓比起算成交手数
        self.trade_units_limit = 0
        #: 成交持仓比例限额,为百分比
        self.trade_position_ratio_limit = float("nan")

    def __repr__(self):
        return json.dumps({
            "trade_units_limit": self.trade_units_limit,
            "trade_position_ratio_limit": self.trade_position_ratio_limit
        })


class RiskManagementData(Entity):

    def __init__(self, api):
        self._api = api
        #: 用户ID
        self.user_id = ""
        #: 交易所ID
        self.exchange_id = ""
        #: 合约ID
        self.instrument_id = ""
        #: 自成交情况
        self.self_trade = SelfTrade(self._api)
        #: 频繁报撤单情况
        self.frequent_cancellation = FrequentCancellation(self._api)
        #: 成交持仓比情况
        self.trade_position_ratio = TradePositionRatio(self._api)

    def _instance_entity(self, path):
        super(RiskManagementData, self)._instance_entity(path)
        self.self_trade = copy.copy(self.self_trade)
        self.self_trade._instance_entity(path + ["self_trade"])
        self.frequent_cancellation = copy.copy(self.frequent_cancellation)
        self.frequent_cancellation._instance_entity(path + ["frequent_cancellation"])
        self.trade_position_ratio = copy.copy(self.trade_position_ratio)
        self.trade_position_ratio._instance_entity(path + ["trade_position_ratio"])


class SelfTrade(Entity):
    """自成交情况"""

    def __init__(self, api):
        self._api = api
        #: 当前最高买价
        self.highest_buy_price = float("nan")
        #: 当前最低卖价
        self.lowest_sell_price = float("nan")
        #: 当天已经发生的自成交次数
        self.self_trade_count = 0
        #: 当天由于自成交而被拒的报单次数
        self.rejected_count = 0

    def __repr__(self):
        return json.dumps({
            "highest_buy_price": self.highest_buy_price,
            "lowest_sell_price": self.lowest_sell_price,
            "self_trade_count": self.self_trade_count,
            "rejected_count": self.rejected_count
        })


class FrequentCancellation(Entity):
    """频繁报撤单情况"""

    def __init__(self, api):
        self._api = api
        #: 当天已经发生的报单次数
        self.insert_order_count = 0
        #: 当天已经发生的撤单次数
        self.cancel_order_count = 0
        #: 当天的撤单比例，为百分比
        self.cancel_order_percent = float("nan")
        #: 当天由于撤单比例超限而被拒的撤单次数
        self.rejected_count = 0

    def __repr__(self):
        return json.dumps({
            "insert_order_count": self.insert_order_count,
            "cancel_order_count": self.cancel_order_count,
            "cancel_order_percent": self.cancel_order_percent,
            "rejected_count": self.rejected_count
        })


class TradePositionRatio(Entity):
    """成交持仓比情况"""

    def __init__(self, api):
        self._api = api
        #: 当天已经发生的成交手数
        self.trade_units = 0
        #: 当前的净持仓手数, 正为多仓, 负为空仓
        self.net_position_units = 0
        #: 当前的成交持仓比, 为百分比
        self.trade_position_ratio = float("nan")
        #: 当天由于成交持仓比超限而被拒的报单次数
        self.rejected_count = 0

    def __repr__(self):
        return json.dumps({
            "trade_units": self.trade_units,
            "net_position_units": self.net_position_units,
            "trade_position_ratio": self.trade_position_ratio,
            "rejected_count": self.rejected_count
        })


class SecurityAccount(Entity):
    """股票资金账户"""

    def __init__(self, api):
        self._api = api
        #: 用户客户号
        self.user_id: str = ""
        #: 资金账户(普通账户、信用账户、衍生品账户)
        self.account_id: str = ""
        #: 资金帐户状态, NORMAL=正常, DISABLED=非正常, LOCKED=锁定
        self.account_status: str = ""
        #: 帐户类别, SPOT=普通, CREDIT=信用, OPTION=衍生品
        self.account_type: str = ""
        #: 当前可用余额
        self.available: float = float("nan")
        #: 当前余额
        self.balance: float = float("nan")
        #: 当前交易冻结金额
        self.buy_frozen_balance: float = float("nan")
        #: 币种, CNY=人民币
        self.currency: float = float("nan")
        #: 日中累计存入资金金额
        self.deposit: float = float("nan")
        #: 当前可取余额
        self.drawable: float = float("nan")
        #: 浮动盈亏
        self.float_profit: float = float("nan")
        #: 当前冻结交易费用金额
        self.frozen_fee: float = float("nan")
        #: 当前冻结的保证金(衍生品账户时指开仓在途冻结保证金)金额
        self.frozen_margin: float = float("nan")
        #: 当前提取冻结资金金额
        self.frozen_withdraw: float = float("nan")
        #: 手动冻结资金
        self.manual_frozen_balance: float = float("nan")
        #: 当前维持的保证金(衍生品账户时指开仓保证金)金额
        self.margin: float = float("nan")
        #: 期初可取余额
        self.pre_available_balance: float = float("nan")
        #: 期初余额
        self.pre_balance: float = float("nan")
        #: 期初可取余额
        self.pre_drawable_balance: float = float("nan")
        #: 当前冲正金额
        self.reversal_balance: float = float("nan")
        #: 日中累计买、申购、逆回购使用资金金额
        self.total_buy_balance: float = float("nan")
        #: 日中累计交易费用金额
        self.total_fee: float = float("nan")
        #: 日中累计卖、赎回获得的可用资金金额
        self.total_sell_balance: float = float("nan")
        #: 不可用资金余额
        self.unavailable_balance: float = float("nan")
        #: 不可用资金余额
        self.unavailable_balance: float = float("nan")
        #: 日中累计提取资金金额
        self.withdraw: float = float("nan")


class SecurityPosition(Entity):
    """ Position 是一个持仓对象 """

    def __init__(self, api):
        self._api = api
        #: 用户客户号
        self.user_id: str = ""
        #: 证券资金账户
        self.account_id: str = ""
        #: 成本价
        self.cost_price: float = float("nan")
        #: 持仓成本
        self.cost: float = float("nan")
        #: 浮动盈亏
        self.float_profit: float = float("nan")
        #: 交易所
        self.exchange_id: str = ""
        #: 证券代码
        self.instrument_id: str = ""
        #: 股东账户代码
        self.inv_account_id: str = ""
        #: 当前可锁定持仓
        self.lock_available_volume: int = 0
        #: 手动冻结持仓
        self.manual_frozen_volume: int = 0
        #: 当日最大可减持额度
        self.max_reduce_quota: int = 0
        #: 持仓类型
        self.position_type: str = ""
        #: 日初可用持仓
        self.pre_available_volume: int = 0
        #: 日初总持仓成本
        self.pre_cost: float = float("nan")
        #: 日初锁定持仓
        self.pre_frozen_volume: int = 0
        #: 日初持仓
        self.pre_volume: int = 0
        #: 产品类型, EQUITY=普通股票、债券、基金、科创板,BOND_STD=逆回购标准券, IPO=新股认购, ALLOTMENT=配股认购, OPTION=期权
        self.product_type: str = ""
        #: 证券类型, STOCK=股票
        self.security_type: str = ""
        #: 证券子类型, STOCK_ASH=A股股票, STOCK_SME=中小板股票, STOCK_GEM=创业板股票, STOCK_KSH=科创板股票
        self.security_sub_type: str = ""
        #: 当前可卖持仓
        self.sell_available_volume: int = 0
        #: 当前卖出冻结持仓
        self.sell_frozen_volume: int = 0
        #: 日中累计买入持仓
        self.today_buy_volume: int = 0
        #: 日中累计买入持仓
        self.today_buy_volume: int = 0
        #: 日中累计卖出持仓
        self.today_sell_volume: int = 0
        #: 日中累计买入金额
        self.total_buy_balance: float = float("nan")
        #: 日中累计买入费用
        self.total_buy_fee: float = float("nan")
        #: 日中累计锁定持仓
        self.total_frozen_volume: int = 0
        #: 日中累计卖出金额
        self.total_sell_balance: float = float("nan")
        #: 日中累计卖出费用
        self.total_sell_fee: float = float("nan")
        #: 日中累计转换获得持仓
        self.total_trsfin_volume: int = 0
        #: 日中累计转换付出持仓
        self.total_trsfout_volume: int = 0
        #: 日中累计解锁持仓
        self.total_unfrozen_volume: int = 0
        #: 当前可转换付出持仓
        self.trsf_out_available_volume: int = 0
        #: 当前转换付出冻结持仓
        self.trsf_out_frozen_volume: int = 0
        #: 总持仓
        self.volume: int = 0

    @property
    def orders(self):
        tdict = _get_obj(self._api._data, ["trade", self._path[1], "orders"])
        fts = {order_id: order for order_id, order in tdict.items() if (not order_id.startswith(
            "_")) and order.instrument_id == self.instrument_id and order.exchange_id == self.exchange_id and order.status == "ALIVE"}
        return fts


class SecurityOrder(Entity):
    """ Order 是一个委托单对象 """

    def __init__(self, api):
        self._api = api
        #: 用户客户号
        self.user_id: str = ""
        #: 订单号,要求客户端保证其在一个交易日内的唯一性
        self.order_id: str = ""
        #: 客户端编号
        self.client_id: int = 0
        #: 客户端环境号
        self.client_env_id: int = 0
        #: 客户端订单编号
        self.client_order_id: int = 0
        #: 客户委托流水号,通常和order_id相同
        self.client_seq_no: str = ""
        #: 委托确认时间
        self.confirm_date_time: int = 0
        #: 委托单当前确认状态
        self.confirm_status: str = ""
        #: 委托累计已经发生的交易金额
        self.cum_balance: float = float("nan")
        #: 委托累计已经发生的交易费用
        self.cum_fee: float = float("nan")
        #: 委托累计已经发生的利息
        self.cum_interest: float = float("nan")
        #: 委托累计已经发生数量
        self.cum_volume: float = float("nan")
        #: 下单方向, BUY=买, SELL=卖
        self.direction: str = ""
        #: 交易所代码
        self.exchange_id: str = ""
        #: 交易所订单编号
        self.exchange_order_id: str = ""
        #: 委托当前冻结的交易金额
        self.frozen_balance: float = float("nan")
        #: 委托当前冻结的交易费用
        self.frozen_fee: float = float("nan")
        #: 委托时间
        self.insert_date_time: int = 0
        #: 证券代码
        self.instrument_id: str = ""
        #: 股东账户代码
        self.inv_account_id: str = ""
        #: 报单价格类型
        self.price_type: str = ""
        #: 报单委托价格
        self.limit_price: float = float("nan")
        #: 所有者类型
        self.owner_type: str = ""
        #: 产品类型
        self.product_type: str = ""
        #: 证券类型
        self.security_type: str = ""
        #: 证券子类型
        self.security_sub_type: str = ""
        #: 委托单当前状态
        self.status: str = ""
        #: 已撤单数量
        self.volume_canceled: int = 0
        #: 总报单股数
        self.volume_orign: int = 0
        #: 剩余还没有执行委托数量
        self.volume_left: int = 0
        #: 委托单状态信息
        self.last_msg: str = ""

class SecurityTrade(Entity):
    """ Trade 是一个成交对象 """

    def __init__(self, api):
        self._api = api
        #: 用户客户号
        self.user_id: str = ""
        #: 成交金额
        self.balance: float = float("nan")
        #: 客户订单编号
        self.client_order_id: int = 0
        #: 客户委托流水号
        self.client_seq_no: str = ""
        #: 成交累计已经发生的交易金额
        self.cum_balance: float = float("nan")
        #: 成交累计已经发生的交易费用
        self.cum_fee: float = float("nan")
        #: 成交累计已经发生的利息
        self.cum_interest: float = float("nan")
        #: 成交累计已经发生数量
        self.cum_volume: float = float("nan")
        #: 买卖类型
        self.direction: str = ""
        #: 交易所
        self.exchange_id: str = ""
        #: 证券代码
        self.instrument_id: str = ""
        #: 股东账户代码
        self.inv_account_id: str = ""
        #: 报单价格类型
        self.price_type: str = ""
        #: 委托价格
        self.limit_price: int = 0
        #: 成交价格
        self.price: float = float("nan")
        #: 产品类型
        self.product_type: str = ""
        #: 证券类型
        self.security_type: str = ""
        #: 证券子类型
        self.security_sub_type: str = ""
        #: 成交数量
        self.volume: int = 0
        #: 原始委托数量
        self.volume_orign: int = 0
