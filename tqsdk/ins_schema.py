#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'


import sgqlc.types
from sgqlc.operation import Fragment

ins_schema = sgqlc.types.Schema()


########################################################################
# Scalars and Enumerations
########################################################################
Boolean = sgqlc.types.Boolean

class Class(sgqlc.types.Enum):
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
    __schema__ = ins_schema
    __field_names__ = ('price_tick', 'derivatives', 'trading_time', 'trading_day', 'instrument_name', 'english_name', 'price_decs', 'class_', 'instrument_id', 'exchange_id', 'derivative')
    price_tick = sgqlc.types.Field(Float, graphql_name='price_tick')
    derivatives = sgqlc.types.Field('derivativeConnection', graphql_name='derivatives', args=sgqlc.types.ArgDict((
        ('class_', sgqlc.types.Arg(sgqlc.types.list_of(Class), graphql_name='class', default=None)),
        ('exchange_id', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='exchange_id', default=None)),
        ('timestamp', sgqlc.types.Arg(Int64, graphql_name='timestamp', default=None)),
))
    )
    trading_time = sgqlc.types.Field('tradingTime', graphql_name='trading_time')
    trading_day = sgqlc.types.Field(String, graphql_name='trading_day')
    instrument_name = sgqlc.types.Field(String, graphql_name='instrument_name')
    english_name = sgqlc.types.Field(String, graphql_name='english_name')
    price_decs = sgqlc.types.Field(Int, graphql_name='price_decs')
    class_ = sgqlc.types.Field(String, graphql_name='class')
    instrument_id = sgqlc.types.Field(String, graphql_name='instrument_id')
    exchange_id = sgqlc.types.Field(String, graphql_name='exchange_id')
    derivative = sgqlc.types.Field('derivativeConnection', graphql_name='derivative', args=sgqlc.types.ArgDict((
        ('class_', sgqlc.types.Arg(Class, graphql_name='class', default=None)),
        ('exchange_id', sgqlc.types.Arg(String, graphql_name='exchange_id', default=None)),
))
    )


class derivative(sgqlc.types.Interface):
    __schema__ = ins_schema
    __field_names__ = ('underlying',)
    underlying = sgqlc.types.Field('derivativeConnection', graphql_name='underlying')


class derivativeConnection(sgqlc.types.Type):
    __schema__ = ins_schema
    __field_names__ = ('count', 'edges')
    count = sgqlc.types.Field(Int, graphql_name='count')
    edges = sgqlc.types.Field(sgqlc.types.list_of('derivativeEdges'), graphql_name='edges')


class derivativeEdges(sgqlc.types.Type):
    __schema__ = ins_schema
    __field_names__ = ('node', 'underlying_multiple')
    node = sgqlc.types.Field('allClassUnion', graphql_name='node')
    underlying_multiple = sgqlc.types.Field(Float, graphql_name='underlying_multiple')


class rootQuery(sgqlc.types.Type):
    __schema__ = ins_schema
    __field_names__ = ('multi_symbol_info', 'symbol_info')
    multi_symbol_info = sgqlc.types.Field(sgqlc.types.list_of('allClassUnion'), graphql_name='multi_symbol_info', args=sgqlc.types.ArgDict((
        ('timestamp', sgqlc.types.Arg(Int64, graphql_name='timestamp', default=None)),
        ('instrument_id', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='instrument_id', default=None)),
        ('class_', sgqlc.types.Arg(sgqlc.types.list_of(Class), graphql_name='class', default=None)),
        ('exchange_id', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='exchange_id', default=None)),
        ('product_id', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='product_id', default=None)),
        ('expired', sgqlc.types.Arg(Boolean, graphql_name='expired', default=None)),
        ('has_night', sgqlc.types.Arg(Boolean, graphql_name='has_night', default=None)),
        ('has_derivatives', sgqlc.types.Arg(Boolean, graphql_name='has_derivatives', default=None)),
))
    )
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


class securities(sgqlc.types.Interface):
    __schema__ = ins_schema
    __field_names__ = ('status', 'public_float_share_quantity', 'currency', 'face_value', 'first_trading_day', 'first_trading_datetime', 'buy_volume_unit', 'sell_volume_unit')
    status = sgqlc.types.Field(String, graphql_name='status')
    public_float_share_quantity = sgqlc.types.Field(Int64, graphql_name='public_float_share_quantity')
    currency = sgqlc.types.Field(String, graphql_name='currency')
    face_value = sgqlc.types.Field(Float, graphql_name='face_value')
    first_trading_day = sgqlc.types.Field(Int64, graphql_name='first_trading_day')
    first_trading_datetime = sgqlc.types.Field(Int64, graphql_name='first_trading_datetime')
    buy_volume_unit = sgqlc.types.Field(Float, graphql_name='buy_volume_unit')
    sell_volume_unit = sgqlc.types.Field(Float, graphql_name='sell_volume_unit')


class tradeable(sgqlc.types.Interface):
    __schema__ = ins_schema
    __field_names__ = ('quote_multiple', 'pre_close', 'upper_limit', 'lower_limit', 'volume_multiple')
    quote_multiple = sgqlc.types.Field(Float, graphql_name='quote_multiple')
    pre_close = sgqlc.types.Field(Float, graphql_name='pre_close')
    upper_limit = sgqlc.types.Field(Float, graphql_name='upper_limit')
    lower_limit = sgqlc.types.Field(Float, graphql_name='lower_limit')
    volume_multiple = sgqlc.types.Field(Float, graphql_name='volume_multiple')


class tradingTime(sgqlc.types.Type):
    __schema__ = ins_schema
    __field_names__ = ('day', 'night')
    day = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.list_of(String)), graphql_name='day')
    night = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.list_of(String)), graphql_name='night')


class bond(sgqlc.types.Type, basic, tradeable, securities):
    __schema__ = ins_schema
    __field_names__ = ('maturity_date', 'maturity_datetime')
    maturity_date = sgqlc.types.Field(Int64, graphql_name='maturity_date')
    maturity_datetime = sgqlc.types.Field(Int64, graphql_name='maturity_datetime')


class combine(sgqlc.types.Type, basic):
    __schema__ = ins_schema
    __field_names__ = ('expire_datetime', 'expired', 'leg1', 'leg2', 'max_limit_order_volume', 'max_market_order_volume', 'product_id')
    expire_datetime = sgqlc.types.Field(Int64, graphql_name='expire_datetime')
    expired = sgqlc.types.Field(Boolean, graphql_name='expired')
    leg1 = sgqlc.types.Field('allClassUnion', graphql_name='leg1')
    leg2 = sgqlc.types.Field('allClassUnion', graphql_name='leg2')
    max_limit_order_volume = sgqlc.types.Field(Int, graphql_name='max_limit_order_volume')
    max_market_order_volume = sgqlc.types.Field(Int, graphql_name='max_market_order_volume')
    product_id = sgqlc.types.Field(String, graphql_name='product_id')


class cont(sgqlc.types.Type, basic, tradeable, derivative):
    __schema__ = ins_schema
    __field_names__ = ()


class fund(sgqlc.types.Type, basic, tradeable, securities):
    __schema__ = ins_schema
    __field_names__ = ('cash_dividend_ratio',)
    cash_dividend_ratio = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='cash_dividend_ratio')


class future(sgqlc.types.Type, basic, tradeable):
    __schema__ = ins_schema
    __field_names__ = ('commission', 'delivery_month', 'delivery_year', 'expire_datetime', 'expired', 'margin', 'max_limit_order_volume', 'max_market_order_volume', 'mmsa', 'pre_open_interest', 'product_id', 'product_short_name', 'settlement_price')
    commission = sgqlc.types.Field(Float, graphql_name='commission')
    delivery_month = sgqlc.types.Field(Int, graphql_name='delivery_month')
    delivery_year = sgqlc.types.Field(Int, graphql_name='delivery_year')
    expire_datetime = sgqlc.types.Field(Int64, graphql_name='expire_datetime')
    expired = sgqlc.types.Field(Boolean, graphql_name='expired')
    margin = sgqlc.types.Field(Float, graphql_name='margin')
    max_limit_order_volume = sgqlc.types.Field(Int, graphql_name='max_limit_order_volume')
    max_market_order_volume = sgqlc.types.Field(Int, graphql_name='max_market_order_volume')
    mmsa = sgqlc.types.Field(Boolean, graphql_name='mmsa')
    pre_open_interest = sgqlc.types.Field(Int64, graphql_name='pre_open_interest')
    product_id = sgqlc.types.Field(String, graphql_name='product_id')
    product_short_name = sgqlc.types.Field(String, graphql_name='product_short_name')
    settlement_price = sgqlc.types.Field(Float, graphql_name='settlement_price')


class index(sgqlc.types.Type, basic):
    __schema__ = ins_schema
    __field_names__ = ('index_multiple',)
    index_multiple = sgqlc.types.Field(Float, graphql_name='index_multiple')


class option(sgqlc.types.Type, basic, tradeable, derivative):
    __schema__ = ins_schema
    __field_names__ = ('call_or_put', 'exercise_type', 'expire_datetime', 'expired', 'last_exercise_datetime', 'last_exercise_day', 'max_limit_order_volume', 'max_market_order_volume', 'pre_open_interest', 'product_short_name', 'settlement_price', 'strike_price')
    call_or_put = sgqlc.types.Field(String, graphql_name='call_or_put')
    exercise_type = sgqlc.types.Field(String, graphql_name='exercise_type')
    expire_datetime = sgqlc.types.Field(Int64, graphql_name='expire_datetime')
    expired = sgqlc.types.Field(Boolean, graphql_name='expired')
    last_exercise_datetime = sgqlc.types.Field(Int64, graphql_name='last_exercise_datetime')
    last_exercise_day = sgqlc.types.Field(Int64, graphql_name='last_exercise_day')
    max_limit_order_volume = sgqlc.types.Field(Int, graphql_name='max_limit_order_volume')
    max_market_order_volume = sgqlc.types.Field(Int, graphql_name='max_market_order_volume')
    pre_open_interest = sgqlc.types.Field(Int64, graphql_name='pre_open_interest')
    product_short_name = sgqlc.types.Field(String, graphql_name='product_short_name')
    settlement_price = sgqlc.types.Field(Float, graphql_name='settlement_price')
    strike_price = sgqlc.types.Field(Float, graphql_name='strike_price')


class spot(sgqlc.types.Type, basic, tradeable):
    __schema__ = ins_schema
    __field_names__ = ()


class stock(sgqlc.types.Type, basic, tradeable, securities):
    __schema__ = ins_schema
    __field_names__ = ('cash_dividend_ratio', 'stock_dividend_ratio')
    cash_dividend_ratio = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='cash_dividend_ratio')
    stock_dividend_ratio = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='stock_dividend_ratio')



########################################################################
# Unions
########################################################################
class allClassUnion(sgqlc.types.Union):
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
future_frag.margin()
future_frag.commission()
future_frag.mmsa()

option_frag = Fragment(option, 'option')
option_frag.pre_open_interest()
option_frag.expired()
option_frag.product_short_name()
option_frag.expire_datetime()
option_frag.last_exercise_datetime()
option_frag.settlement_price()
option_frag.max_market_order_volume()
option_frag.max_limit_order_volume()
option_frag.strike_price()
option_frag.call_or_put()
option_frag.exercise_type()

combine_frag = Fragment(combine, 'combine')
combine_frag.expired()
combine_frag.product_id()
combine_frag.expire_datetime()
combine_frag.max_market_order_volume()
combine_frag.max_limit_order_volume()
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
