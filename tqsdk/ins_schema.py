#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'


import sgqlc.types
from sgqlc.operation import Fragment


########################################################################
# Monkey patching 检查请求的参数是否合法，与 api.query_graphql 函数的校验规则保持一致
########################################################################
_origin__to_graphql_input__ = sgqlc.types.Arg.__to_graphql_input__


def _tqsdk__to_graphql_input__(self, value, *args, **kwargs):
    if value == "" or isinstance(value, list) and (any([s == "" for s in value]) or len(value) == 0):
        raise Exception(f"variables 中变量值不支持空字符串、空列表或者列表中包括空字符串。")
    return _origin__to_graphql_input__(self, value, *args, **kwargs)


sgqlc.types.Arg.__to_graphql_input__ = _tqsdk__to_graphql_input__


ins_schema = sgqlc.types.Schema()


########################################################################
# Scalars and Enumerations
########################################################################
Boolean = sgqlc.types.Boolean


class Category(sgqlc.types.Enum):
    '''全部板块

    Enumeration Choices:

    * `AGRICULTURAL`: 农副
    * `CHEMICAL`: 化工
    * `COAL`: 煤炭
    * `EQUITY_INDEX`: 股指期货
    * `FERROUS`: 黑色金属
    * `GRAIN`: 谷物
    * `GREASE`: 油脂油料
    * `LIGHT_INDUSTRY`: 轻工
    * `NONFERROUS_METALS`: 有色金属
    * `OIL`: 石油
    * `PRECIOUS_METALS`: 贵金属
    * `SOFT_COMMODITY`: 软商
    * `TREASURY_BOND`: 国债期货
    '''
    __schema__ = ins_schema
    __choices__ = ('AGRICULTURAL', 'CHEMICAL', 'COAL', 'EQUITY_INDEX', 'FERROUS', 'GRAIN', 'GREASE', 'LIGHT_INDUSTRY', 'NONFERROUS_METALS', 'OIL', 'PRECIOUS_METALS', 'SOFT_COMMODITY', 'TREASURY_BOND')


class Class(sgqlc.types.Enum):
    '''全部类别

    Enumeration Choices:

    * `BOND`: 债券
    * `COMBINE`: 组合
    * `CONT`: 连续
    * `FUND`: 基金
    * `FUTURE`: 期货
    * `INDEX`: 指数
    * `OPTION`: 期权
    * `SPOT`: 现货
    * `STOCK`: 股票
    '''
    __schema__ = ins_schema
    __choices__ = ('BOND', 'COMBINE', 'CONT', 'FUND', 'FUTURE', 'INDEX', 'OPTION', 'SPOT', 'STOCK')


Float = sgqlc.types.Float

Int = sgqlc.types.Int


class Int64(sgqlc.types.Scalar):
    __schema__ = ins_schema


String = sgqlc.types.String


########################################################################
# Input Objects
########################################################################

########################################################################
# Output Objects and Interfaces
########################################################################
class basic(sgqlc.types.Interface):
    '''基础信息'''
    __schema__ = ins_schema
    __field_names__ = ('instrument_name_wh', 'price_decs', 'price_tick', 'ins_id', 'instrument_id', 'derivatives', 'exchange_id',
                       'instrument_name', 'trading_time', 'class_', 'py_wh', 'english_name', 'derivative', 'trading_day')
    instrument_name_wh = sgqlc.types.Field(String, graphql_name='instrument_name_wh')
    '''合约名称（文华风格）'''

    price_decs = sgqlc.types.Field(Int, graphql_name='price_decs')
    '''价格小数位数'''

    price_tick = sgqlc.types.Field(Float, graphql_name='price_tick')
    '''最小变动价位'''

    ins_id = sgqlc.types.Field(String, graphql_name='ins_id')
    '''合约代码（不含交易所）'''

    instrument_id = sgqlc.types.Field(String, graphql_name='instrument_id')
    '''合约代码'''

    derivatives = sgqlc.types.Field('derivativeConnection', graphql_name='derivatives', args=sgqlc.types.ArgDict((
        ('class_', sgqlc.types.Arg(sgqlc.types.list_of(Class), graphql_name='class', default=None)),
        ('exchange_id', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='exchange_id', default=None)),
        ('expired', sgqlc.types.Arg(Boolean, graphql_name='expired', default=None)),
        ('timestamp', sgqlc.types.Arg(Int64, graphql_name='timestamp', default=None)),
    ))
    )
    '''衍生品

    Arguments:

    * `class_` (`[Class]`): placeholder
    * `exchange_id` (`[String]`): placeholder
    * `expired` (`Boolean`)
    * `timestamp` (`Int64`)
    '''

    exchange_id = sgqlc.types.Field(String, graphql_name='exchange_id')
    '''交易所代码'''

    instrument_name = sgqlc.types.Field(String, graphql_name='instrument_name')
    '''合约名称'''

    trading_time = sgqlc.types.Field('tradingTime', graphql_name='trading_time')
    '''交易时间'''

    class_ = sgqlc.types.Field(String, graphql_name='class')
    '''类别'''

    py_wh = sgqlc.types.Field(String, graphql_name='py_wh')
    '''拼音（文华风格）'''

    english_name = sgqlc.types.Field(String, graphql_name='english_name')
    '''英文名称'''

    derivative = sgqlc.types.Field('derivativeConnection', graphql_name='derivative', args=sgqlc.types.ArgDict((
        ('class_', sgqlc.types.Arg(Class, graphql_name='class', default=None)),
        ('exchange_id', sgqlc.types.Arg(String, graphql_name='exchange_id', default=None)),
        ('expired', sgqlc.types.Arg(Boolean, graphql_name='expired', default=None)),
    ))
    )
    '''衍生品（旧）

    Arguments:

    * `class_` (`Class`): placeholder
    * `exchange_id` (`String`): placeholder
    * `expired` (`Boolean`)
    '''

    trading_day = sgqlc.types.Field(String, graphql_name='trading_day')
    '''交易日'''


class derivative(sgqlc.types.Interface):
    '''衍生品信息'''
    __schema__ = ins_schema
    __field_names__ = ('underlying',)
    underlying = sgqlc.types.Field('derivativeConnection', graphql_name='underlying')
    '''标的合约'''


class securities(sgqlc.types.Interface):
    '''证券信息'''
    __schema__ = ins_schema
    __field_names__ = ('first_trading_datetime', 'buy_volume_unit', 'sell_volume_unit', 'status', 'public_float_share_quantity', 'currency', 'face_value', 'first_trading_day')
    first_trading_datetime = sgqlc.types.Field(Int64, graphql_name='first_trading_datetime')
    '''起始交易时间'''

    buy_volume_unit = sgqlc.types.Field(Float, graphql_name='buy_volume_unit')
    '''买入单位'''

    sell_volume_unit = sgqlc.types.Field(Float, graphql_name='sell_volume_unit')
    '''卖出单位'''

    status = sgqlc.types.Field(String, graphql_name='status')
    '''状态'''

    public_float_share_quantity = sgqlc.types.Field(Int64, graphql_name='public_float_share_quantity')
    '''流通股本'''

    currency = sgqlc.types.Field(String, graphql_name='currency')
    '''币种'''

    face_value = sgqlc.types.Field(Float, graphql_name='face_value')
    '''面值'''

    first_trading_day = sgqlc.types.Field(Int64, graphql_name='first_trading_day')
    '''首个交易日'''


class tradeable(sgqlc.types.Interface):
    '''交易信息'''
    __schema__ = ins_schema
    __field_names__ = ('upper_limit', 'lower_limit', 'volume_multiple', 'quote_multiple', 'pre_close')
    upper_limit = sgqlc.types.Field(Float, graphql_name='upper_limit')
    '''涨停板价'''

    lower_limit = sgqlc.types.Field(Float, graphql_name='lower_limit')
    '''跌停板价'''

    volume_multiple = sgqlc.types.Field(Float, graphql_name='volume_multiple')
    '''合约乘数（交易单位 / 报价单位）'''

    quote_multiple = sgqlc.types.Field(Float, graphql_name='quote_multiple')
    '''报价乘数（成交量单位 / 报价单位）'''

    pre_close = sgqlc.types.Field(Float, graphql_name='pre_close')
    '''昨收盘价'''


class categoryInfo(sgqlc.types.Type):
    '''板块信息'''
    __schema__ = ins_schema
    __field_names__ = ('id', 'name')
    id = sgqlc.types.Field(String, graphql_name='id')
    '''板块ID'''

    name = sgqlc.types.Field(String, graphql_name='name')
    '''板块中文名称'''


class derivativeConnection(sgqlc.types.Type):
    '''衍生品关系'''
    __schema__ = ins_schema
    __field_names__ = ('count', 'edges')
    count = sgqlc.types.Field(Int, graphql_name='count')

    edges = sgqlc.types.Field(sgqlc.types.list_of('derivativeEdges'), graphql_name='edges')


class derivativeEdges(sgqlc.types.Type):
    '''衍生品'''
    __schema__ = ins_schema
    __field_names__ = ('node', 'underlying_multiple')
    node = sgqlc.types.Field('allClassUnion', graphql_name='node')
    '''衍生品'''

    underlying_multiple = sgqlc.types.Field(Float, graphql_name='underlying_multiple')


class rootQuery(sgqlc.types.Type):
    '''symbol_info 为旧版单查询接口，multi_symbol_info 为新版多查询接口，即前者的兼容升级版本'''
    __schema__ = ins_schema
    __field_names__ = ('multi_symbol_info', 'symbol_info')
    multi_symbol_info = sgqlc.types.Field(sgqlc.types.list_of('allClassUnion'), graphql_name='multi_symbol_info', args=sgqlc.types.ArgDict((
        ('instrument_id', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='instrument_id', default=None)),
        ('class_', sgqlc.types.Arg(sgqlc.types.list_of(Class), graphql_name='class', default=None)),
        ('exchange_id', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='exchange_id', default=None)),
        ('product_id', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='product_id', default=None)),
        ('expired', sgqlc.types.Arg(Boolean, graphql_name='expired', default=None)),
        ('has_night', sgqlc.types.Arg(Boolean, graphql_name='has_night', default=None)),
        ('has_derivatives', sgqlc.types.Arg(Boolean, graphql_name='has_derivatives', default=None)),
        ('categories', sgqlc.types.Arg(sgqlc.types.list_of(Category), graphql_name='categories', default=None)),
        ('timestamp', sgqlc.types.Arg(Int64, graphql_name='timestamp', default=None)),
    ))
    )
    '''Arguments:

    * `instrument_id` (`[String]`): 合约代码
    * `class_` (`[Class]`): 类别
    * `exchange_id` (`[String]`): 交易所代码
    * `product_id` (`[String]`): 品种代码
    * `expired` (`Boolean`): 是否已到期
    * `has_night` (`Boolean`): 是否有夜盘
    * `has_derivatives` (`Boolean`): 是否有衍生品
    * `categories` (`[Category]`): 所属板块
    * `timestamp` (`Int64`): 回测时间点
    '''

    symbol_info = sgqlc.types.Field(sgqlc.types.list_of('allClassUnion'), graphql_name='symbol_info', args=sgqlc.types.ArgDict((
        ('instrument_id', sgqlc.types.Arg(String, graphql_name='instrument_id', default=None)),
        ('class_', sgqlc.types.Arg(Class, graphql_name='class', default=None)),
        ('exchange_id', sgqlc.types.Arg(String, graphql_name='exchange_id', default=None)),
        ('product_id', sgqlc.types.Arg(String, graphql_name='product_id', default=None)),
        ('expired', sgqlc.types.Arg(Boolean, graphql_name='expired', default=None)),
        ('has_night', sgqlc.types.Arg(Boolean, graphql_name='has_night', default=None)),
        ('has_derivatives', sgqlc.types.Arg(Boolean, graphql_name='has_derivatives', default=None)),
    ))
    )
    '''Arguments:

    * `instrument_id` (`String`)
    * `class_` (`Class`)
    * `exchange_id` (`String`)
    * `product_id` (`String`)
    * `expired` (`Boolean`)
    * `has_night` (`Boolean`)
    * `has_derivatives` (`Boolean`)
    '''


class tradingTime(sgqlc.types.Type):
    '''交易时间'''
    __schema__ = ins_schema
    __field_names__ = ('day', 'night')
    day = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.list_of(String)), graphql_name='day')
    '''白盘交易时间'''

    night = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.list_of(String)), graphql_name='night')
    '''夜盘交易时间'''


class bond(sgqlc.types.Type, basic, tradeable, securities):
    '''债券'''
    __schema__ = ins_schema
    __field_names__ = ('maturity_date', 'maturity_datetime')
    maturity_date = sgqlc.types.Field(Int64, graphql_name='maturity_date')
    '''到期日'''

    maturity_datetime = sgqlc.types.Field(Int64, graphql_name='maturity_datetime')
    '''到期时间'''


class combine(sgqlc.types.Type, basic):
    '''组合'''
    __schema__ = ins_schema
    __field_names__ = ('close_max_limit_order_volume', 'close_max_market_order_volume', 'close_min_limit_order_volume', 'close_min_market_order_volume', 'expire_datetime', 'expired', 'leg1', 'leg2', 'max_limit_order_volume',
                       'max_market_order_volume', 'min_limit_order_volume', 'min_market_order_volume', 'open_max_limit_order_volume', 'open_max_market_order_volume', 'open_min_limit_order_volume', 'open_min_market_order_volume', 'product_id')
    close_max_limit_order_volume = sgqlc.types.Field(Int, graphql_name='close_max_limit_order_volume')
    '''平仓限价单最大下单量'''

    close_max_market_order_volume = sgqlc.types.Field(Int, graphql_name='close_max_market_order_volume')
    '''平仓市价单最大下单量'''

    close_min_limit_order_volume = sgqlc.types.Field(Int, graphql_name='close_min_limit_order_volume')
    '''平仓限价单最小下单量'''

    close_min_market_order_volume = sgqlc.types.Field(Int, graphql_name='close_min_market_order_volume')
    '''平仓市价单最小下单量'''

    expire_datetime = sgqlc.types.Field(Int64, graphql_name='expire_datetime')
    '''到期时间'''

    expired = sgqlc.types.Field(Boolean, graphql_name='expired')
    '''是否到期'''

    leg1 = sgqlc.types.Field('allClassUnion', graphql_name='leg1')
    '''组合单腿1'''

    leg2 = sgqlc.types.Field('allClassUnion', graphql_name='leg2')
    '''组合单腿2'''

    max_limit_order_volume = sgqlc.types.Field(Int, graphql_name='max_limit_order_volume')
    '''限价单最大下单量'''

    max_market_order_volume = sgqlc.types.Field(Int, graphql_name='max_market_order_volume')
    '''市价单最大下单量'''

    min_limit_order_volume = sgqlc.types.Field(Int, graphql_name='min_limit_order_volume')
    '''限价单最小下单量'''

    min_market_order_volume = sgqlc.types.Field(Int, graphql_name='min_market_order_volume')
    '''市价单最小下单量'''

    open_max_limit_order_volume = sgqlc.types.Field(Int, graphql_name='open_max_limit_order_volume')
    '''开仓限价单最大下单量'''

    open_max_market_order_volume = sgqlc.types.Field(Int, graphql_name='open_max_market_order_volume')
    '''开仓市价单最大下单量'''

    open_min_limit_order_volume = sgqlc.types.Field(Int, graphql_name='open_min_limit_order_volume')
    '''开仓限价单最小下单量'''

    open_min_market_order_volume = sgqlc.types.Field(Int, graphql_name='open_min_market_order_volume')
    '''开仓市价单最小下单量'''

    product_id = sgqlc.types.Field(String, graphql_name='product_id')
    '''品种代码'''


class cont(sgqlc.types.Type, basic, tradeable, derivative):
    '''连续'''
    __schema__ = ins_schema
    __field_names__ = ()


class fund(sgqlc.types.Type, basic, tradeable, securities):
    '''基金'''
    __schema__ = ins_schema
    __field_names__ = ('cash_dividend_ratio',)
    cash_dividend_ratio = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='cash_dividend_ratio')
    '''现金分红'''


class future(sgqlc.types.Type, basic, tradeable):
    '''期货'''
    __schema__ = ins_schema
    __field_names__ = ('categories', 'close_max_limit_order_volume', 'close_max_market_order_volume', 'close_min_limit_order_volume', 'close_min_market_order_volume', 'commission', 'delivery_month', 'delivery_year', 'expire_datetime', 'expired', 'margin', 'max_limit_order_volume', 'max_market_order_volume', 'min_limit_order_volume',
                       'min_market_order_volume', 'mmsa', 'open_max_limit_order_volume', 'open_max_market_order_volume', 'open_min_limit_order_volume', 'open_min_market_order_volume', 'position_limit', 'pre_open_interest', 'pre_open_interest2', 'product_id', 'product_short_name', 'product_short_name_wh', 'settlement_price')
    categories = sgqlc.types.Field(sgqlc.types.list_of(categoryInfo), graphql_name='categories')
    '''所属板块'''

    close_max_limit_order_volume = sgqlc.types.Field(Int, graphql_name='close_max_limit_order_volume')
    '''平仓限价单最大下单量'''

    close_max_market_order_volume = sgqlc.types.Field(Int, graphql_name='close_max_market_order_volume')
    '''平仓市价单最大下单量'''

    close_min_limit_order_volume = sgqlc.types.Field(Int, graphql_name='close_min_limit_order_volume')
    '''平仓限价单最小下单量'''

    close_min_market_order_volume = sgqlc.types.Field(Int, graphql_name='close_min_market_order_volume')
    '''平仓市价单最小下单量'''

    commission = sgqlc.types.Field(Float, graphql_name='commission')
    '''手续费'''

    delivery_month = sgqlc.types.Field(Int, graphql_name='delivery_month')
    '''交割月份'''

    delivery_year = sgqlc.types.Field(Int, graphql_name='delivery_year')
    '''交割年份'''

    expire_datetime = sgqlc.types.Field(Int64, graphql_name='expire_datetime')
    '''到期时间'''

    expired = sgqlc.types.Field(Boolean, graphql_name='expired')
    '''是否到期'''

    margin = sgqlc.types.Field(Float, graphql_name='margin')
    '''保证金'''

    max_limit_order_volume = sgqlc.types.Field(Int, graphql_name='max_limit_order_volume')
    '''限价单最大下单量'''

    max_market_order_volume = sgqlc.types.Field(Int, graphql_name='max_market_order_volume')
    '''市价单最大下单量'''

    min_limit_order_volume = sgqlc.types.Field(Int, graphql_name='min_limit_order_volume')
    '''限价单最小下单量'''

    min_market_order_volume = sgqlc.types.Field(Int, graphql_name='min_market_order_volume')
    '''市价单最小下单量'''

    mmsa = sgqlc.types.Field(Boolean, graphql_name='mmsa')
    '''单向大边'''

    open_max_limit_order_volume = sgqlc.types.Field(Int, graphql_name='open_max_limit_order_volume')
    '''开仓限价单最大下单量'''

    open_max_market_order_volume = sgqlc.types.Field(Int, graphql_name='open_max_market_order_volume')
    '''开仓市价单最大下单量'''

    open_min_limit_order_volume = sgqlc.types.Field(Int, graphql_name='open_min_limit_order_volume')
    '''开仓限价单最小下单量'''

    open_min_market_order_volume = sgqlc.types.Field(Int, graphql_name='open_min_market_order_volume')
    '''开仓市价单最小下单量'''

    position_limit = sgqlc.types.Field(Int, graphql_name='position_limit')
    '''持仓限额手数，为 null 时表示无该信息，为 0 则不允许持仓'''

    pre_open_interest = sgqlc.types.Field(Int64, graphql_name='pre_open_interest')
    '''昨持仓量（SHFE/INE/CZCE/DCE 为双边计量，其余为单边计量）'''

    pre_open_interest2 = sgqlc.types.Field(Int64, graphql_name='pre_open_interest2')
    '''昨持仓量（单边计量）'''

    product_id = sgqlc.types.Field(String, graphql_name='product_id')
    '''品种代码'''

    product_short_name = sgqlc.types.Field(String, graphql_name='product_short_name')
    '''品种简称'''

    product_short_name_wh = sgqlc.types.Field(String, graphql_name='product_short_name_wh')
    '''品种简称（文华风格）'''

    settlement_price = sgqlc.types.Field(Float, graphql_name='settlement_price')
    '''结算价'''


class index(sgqlc.types.Type, basic):
    '''指数'''
    __schema__ = ins_schema
    __field_names__ = ('index_multiple',)
    index_multiple = sgqlc.types.Field(Float, graphql_name='index_multiple')
    '''指数乘数（指数成交量单位 / 成份股报价单位）'''


class option(sgqlc.types.Type, basic, tradeable, derivative):
    '''期权'''
    __schema__ = ins_schema
    __field_names__ = ('call_or_put', 'close_max_limit_order_volume', 'close_max_market_order_volume', 'close_min_limit_order_volume', 'close_min_market_order_volume', 'exercise_type', 'expire_datetime', 'expired', 'last_exercise_datetime', 'last_exercise_day', 'max_limit_order_volume', 'max_market_order_volume',
                       'min_limit_order_volume', 'min_market_order_volume', 'open_max_limit_order_volume', 'open_max_market_order_volume', 'open_min_limit_order_volume', 'open_min_market_order_volume', 'position_limit', 'pre_open_interest', 'pre_open_interest2', 'product_short_name', 'settlement_price', 'strike_price')
    call_or_put = sgqlc.types.Field(String, graphql_name='call_or_put')
    '''认购/认沽'''

    close_max_limit_order_volume = sgqlc.types.Field(Int, graphql_name='close_max_limit_order_volume')
    '''平仓限价单最大下单量'''

    close_max_market_order_volume = sgqlc.types.Field(Int, graphql_name='close_max_market_order_volume')
    '''平仓市价单最大下单量'''

    close_min_limit_order_volume = sgqlc.types.Field(Int, graphql_name='close_min_limit_order_volume')
    '''平仓限价单最小下单量'''

    close_min_market_order_volume = sgqlc.types.Field(Int, graphql_name='close_min_market_order_volume')
    '''平仓市价单最小下单量'''

    exercise_type = sgqlc.types.Field(String, graphql_name='exercise_type')
    '''行权方式'''

    expire_datetime = sgqlc.types.Field(Int64, graphql_name='expire_datetime')
    '''到期时间'''

    expired = sgqlc.types.Field(Boolean, graphql_name='expired')
    '''是否到期'''

    last_exercise_datetime = sgqlc.types.Field(Int64, graphql_name='last_exercise_datetime')
    '''最后行权时间'''

    last_exercise_day = sgqlc.types.Field(Int64, graphql_name='last_exercise_day')
    '''最后行权日'''

    max_limit_order_volume = sgqlc.types.Field(Int, graphql_name='max_limit_order_volume')
    '''限价单最大下单量'''

    max_market_order_volume = sgqlc.types.Field(Int, graphql_name='max_market_order_volume')
    '''市价单最大下单量'''

    min_limit_order_volume = sgqlc.types.Field(Int, graphql_name='min_limit_order_volume')
    '''限价单最小下单量'''

    min_market_order_volume = sgqlc.types.Field(Int, graphql_name='min_market_order_volume')
    '''市价单最小下单量'''

    open_max_limit_order_volume = sgqlc.types.Field(Int, graphql_name='open_max_limit_order_volume')
    '''开仓限价单最大下单量'''

    open_max_market_order_volume = sgqlc.types.Field(Int, graphql_name='open_max_market_order_volume')
    '''开仓市价单最大下单量'''

    open_min_limit_order_volume = sgqlc.types.Field(Int, graphql_name='open_min_limit_order_volume')
    '''开仓限价单最小下单量'''

    open_min_market_order_volume = sgqlc.types.Field(Int, graphql_name='open_min_market_order_volume')
    '''开仓市价单最小下单量'''

    position_limit = sgqlc.types.Field(Int, graphql_name='position_limit')
    '''持仓限额手数，为 null 时表示无该信息，为 0 则不允许持仓'''

    pre_open_interest = sgqlc.types.Field(Int64, graphql_name='pre_open_interest')
    '''昨持仓量（SHFE/INE/CZCE/DCE 为双边计量，其余为单边计量）'''

    pre_open_interest2 = sgqlc.types.Field(Int64, graphql_name='pre_open_interest2')
    '''昨持仓量（单边计量）'''

    product_short_name = sgqlc.types.Field(String, graphql_name='product_short_name')
    '''品种简称'''

    settlement_price = sgqlc.types.Field(Float, graphql_name='settlement_price')
    '''结算价'''

    strike_price = sgqlc.types.Field(Float, graphql_name='strike_price')
    '''行权价'''


class spot(sgqlc.types.Type, basic, tradeable):
    '''现货'''
    __schema__ = ins_schema
    __field_names__ = ()


class stock(sgqlc.types.Type, basic, tradeable, securities):
    '''股票'''
    __schema__ = ins_schema
    __field_names__ = ('cash_dividend_ratio', 'stock_dividend_ratio')
    cash_dividend_ratio = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='cash_dividend_ratio')
    '''现金分红'''

    stock_dividend_ratio = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='stock_dividend_ratio')
    '''股票分红'''


########################################################################
# Unions
########################################################################
class allClassUnion(sgqlc.types.Union):
    '''分类型结果集'''
    __schema__ = ins_schema
    __types__ = (future, index, option, combine, spot, cont, stock, bond, fund)


########################################################################
# Schema Entry Points
########################################################################
ins_schema.query_type = rootQuery
ins_schema.mutation_type = None
ins_schema.subscription_type = None


########################################################################
# Fragments
########################################################################
basic_frag = Fragment(basic, 'basic')
basic_frag.instrument_id()
basic_frag.exchange_id()
basic_frag.instrument_name()
basic_frag.english_name()
basic_frag.class_()
basic_frag.price_tick()
basic_frag.price_decs()
basic_frag.trading_day()
basic_frag.trading_time().day()
basic_frag.trading_time().night()

stock_frag = Fragment(stock, 'stock')
stock_frag.stock_dividend_ratio()
stock_frag.cash_dividend_ratio()

fund_frag = Fragment(fund, 'fund')
fund_frag.cash_dividend_ratio()

bond_frag = Fragment(bond, 'bond')
bond_frag.maturity_datetime()

tradeable_frag = Fragment(tradeable, 'tradeable')
tradeable_frag.pre_close()
tradeable_frag.volume_multiple()
tradeable_frag.quote_multiple()
tradeable_frag.upper_limit()
tradeable_frag.lower_limit()

index_frag = Fragment(index, 'index')
index_frag.index_multiple()

securities_frag = Fragment(securities, 'securities')
securities_frag.currency()
securities_frag.face_value()
securities_frag.first_trading_datetime()
securities_frag.buy_volume_unit()
securities_frag.sell_volume_unit()
securities_frag.status()
securities_frag.public_float_share_quantity()

future_frag = Fragment(future, 'future')
future_frag.pre_open_interest()
future_frag.expired()
future_frag.product_id()
future_frag.product_short_name()
future_frag.delivery_year()
future_frag.delivery_month()
future_frag.expire_datetime()
future_frag.settlement_price()
future_frag.max_market_order_volume()
future_frag.max_limit_order_volume()
future_frag.min_market_order_volume()
future_frag.min_limit_order_volume()
future_frag.open_max_market_order_volume()
future_frag.open_max_limit_order_volume()
future_frag.open_min_market_order_volume()
future_frag.open_min_limit_order_volume()
future_frag.margin()
future_frag.commission()
future_frag.mmsa()
future_frag.categories()
future_frag.position_limit()

option_frag = Fragment(option, 'option')
option_frag.pre_open_interest()
option_frag.expired()
option_frag.product_short_name()
option_frag.expire_datetime()
option_frag.last_exercise_datetime()
option_frag.settlement_price()
option_frag.max_market_order_volume()
option_frag.max_limit_order_volume()
option_frag.min_market_order_volume()
option_frag.min_limit_order_volume()
option_frag.open_max_market_order_volume()
option_frag.open_max_limit_order_volume()
option_frag.open_min_market_order_volume()
option_frag.open_min_limit_order_volume()
option_frag.strike_price()
option_frag.call_or_put()
option_frag.exercise_type()
option_frag.position_limit()

combine_frag = Fragment(combine, 'combine')
combine_frag.expired()
combine_frag.product_id()
combine_frag.expire_datetime()
combine_frag.max_market_order_volume()
combine_frag.max_limit_order_volume()
combine_frag.min_market_order_volume()
combine_frag.min_limit_order_volume()
combine_frag.open_max_market_order_volume()
combine_frag.open_max_limit_order_volume()
combine_frag.open_min_market_order_volume()
combine_frag.open_min_limit_order_volume()
combine_frag.leg1().__as__(basic).instrument_id()
combine_frag.leg2().__as__(basic).instrument_id()

derivative_frag = Fragment(derivative, 'derivative')
derivative_frag.underlying()
derivative_frag.underlying().count()
derivative_frag.underlying().edges().underlying_multiple()
derivative_frag.underlying().edges().node().__fragment__(basic_frag)
derivative_frag.underlying().edges().node().__fragment__(stock_frag)
derivative_frag.underlying().edges().node().__fragment__(fund_frag)
derivative_frag.underlying().edges().node().__fragment__(bond_frag)
derivative_frag.underlying().edges().node().__fragment__(tradeable_frag)
derivative_frag.underlying().edges().node().__fragment__(index_frag)
derivative_frag.underlying().edges().node().__fragment__(securities_frag)
derivative_frag.underlying().edges().node().__fragment__(future_frag)


def _add_all_frags(field):
    field.__fragment__(basic_frag)
    field.__fragment__(stock_frag)
    field.__fragment__(fund_frag)
    field.__fragment__(bond_frag)
    field.__fragment__(tradeable_frag)
    field.__fragment__(index_frag)
    field.__fragment__(securities_frag)
    field.__fragment__(future_frag)
    field.__fragment__(option_frag)
    field.__fragment__(combine_frag)
    field.__fragment__(derivative_frag)
