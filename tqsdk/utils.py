#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'


import random
import secrets
from bisect import bisect_right

from pandas.core.internals import BlockManager


RD = random.Random(secrets.randbits(128))  # 初始化随机数引擎，使用随机数作为seed，防止用户同时拉起多个策略，产生同样的 seed


def _generate_uuid(prefix=''):
    return f"{prefix + '_' if prefix else ''}{RD.getrandbits(128):032x}"


query_all_fields = """
    ... on basic{ class trading_time{day night} trading_day instrument_id instrument_name price_tick price_decs exchange_id english_name}
    ... on stock{ stock_dividend_ratio cash_dividend_ratio}
    ... on fund{ cash_dividend_ratio}
    ... on bond{ maturity_datetime }
    ... on tradeable{ volume_multiple quote_multiple}
    ... on index{ index_multiple}
    ... on securities{ currency face_value first_trading_datetime buy_volume_unit sell_volume_unit status public_float_share_quantity}
    ... on future{ expired product_id product_short_name delivery_year delivery_month expire_datetime settlement_price max_market_order_volume max_limit_order_volume margin commission mmsa}
    ... on option{ expired product_short_name expire_datetime last_exercise_datetime settlement_price max_market_order_volume max_limit_order_volume strike_price call_or_put exercise_type}
    ... on combine{ expired product_id expire_datetime max_market_order_volume max_limit_order_volume leg1{ ... on basic{instrument_id}} leg2{ ... on basic{instrument_id}} }
    ... on derivative{ 
        underlying{ 
            count edges{ underlying_multiple node{
                ... on basic{ class trading_time{day night} trading_day instrument_id instrument_name price_tick price_decs exchange_id english_name }
                ... on stock{ stock_dividend_ratio cash_dividend_ratio }
                ... on fund{ cash_dividend_ratio }
                ... on bond{ maturity_datetime }
                ... on tradeable{ volume_multiple quote_multiple}
                ... on index{ index_multiple}
                ... on securities{ currency face_value first_trading_datetime buy_volume_unit sell_volume_unit public_float_share_quantity }
                ... on future{ expired product_id product_short_name delivery_year delivery_month expire_datetime settlement_price max_market_order_volume max_limit_order_volume margin commission mmsa}
                }
            }
        }
    }
"""


def _query_for_quote(symbol):
    """
    返回请求某个合约的合约信息的 query_pack
    调用次函数应该全部都是sdk的代码主动请求合约信息
    用户请求合约信息一定是 PYSDK_api 开头的请求，因为用户请求的合约信息在回测时带有 timestamp 参数，是不应该调用此函数的
    """
    symbol_list = symbol if isinstance(symbol, list) else [symbol]
    if any([s == "" for s in symbol_list]) or len(symbol_list) == 0:
        raise Exception("发送的 ins_query 请求合约代码不支持空字符串、空列表或者列表中包括空字符串。")
    query = "query ($instrument_id:[String]) {"
    query += "multi_symbol_info(instrument_id:$instrument_id) {" + query_all_fields + "}}"
    return {
        "aid": "ins_query",
        "query_id": _generate_uuid(prefix='PYSDK_quote_'),
        "query": query,
        "variables": {"instrument_id": symbol_list}
    }


def _get_query_args(variables):
    types = {
        "instrument_id": "[String]",
        "class": "[Class]",
        "exchange_id": "[String]",
        "product_id": "[String]",
        "expired": "Boolean",
        "has_night": "Boolean",
        "timestamp": "Int64"
    }
    args_definitions = ",".join([f"${v}:{types[v]}" for v in variables])
    args = ",".join([f"{v}:${v}" for v in variables])
    return args_definitions, args


def _query_for_init():
    """
    返回某些类型合约的 query 和 variables
    todo: 为了兼容旧版提供给用户的 api._data["quote"].items() 类似用法，应该限制交易所 ["SHFE", "DCE", "CZCE", "INE", "CFFEX", "KQ"]
    """
    query = "query ($class_list:[Class], $exchange_list:[String]) {"
    query += "multi_symbol_info(class:$class_list, exchange_id:$exchange_list) {" + query_all_fields + "}}"
    return query, {
        "class_list": ["FUTURE", "INDEX", "OPTION", "COMBINE", "CONT"],
        "exchange_list": ["SHFE", "DCE", "CZCE", "INE", "CFFEX", "KQ"]
    }


night_trading_table = {
    "DCE.a": ["21:00:00", "23:00:00"],
    "DCE.b": ["21:00:00", "23:00:00"],
    "DCE.c": ["21:00:00", "23:00:00"],
    "DCE.cs": ["21:00:00", "23:00:00"],
    "DCE.m": ["21:00:00", "23:00:00"],
    "DCE.y": ["21:00:00", "23:00:00"],
    "DCE.p": ["21:00:00", "23:00:00"],
    "DCE.l": ["21:00:00", "23:00:00"],
    "DCE.v": ["21:00:00", "23:00:00"],
    "DCE.pp": ["21:00:00", "23:00:00"],
    "DCE.j": ["21:00:00", "23:00:00"],
    "DCE.jm": ["21:00:00", "23:00:00"],
    "DCE.i": ["21:00:00", "23:00:00"],
    "DCE.eg": ["21:00:00", "23:00:00"],
    "DCE.eb": ["21:00:00", "23:00:00"],
    "DCE.rr": ["21:00:00", "23:00:00"],
    "DCE.pg": ["21:00:00", "23:00:00"],
    "CZCE.CF": ["21:00:00", "23:00:00"],
    "CZCE.CY": ["21:00:00", "23:00:00"],
    "CZCE.SA": ["21:00:00", "23:00:00"],
    "CZCE.SR": ["21:00:00", "23:00:00"],
    "CZCE.TA": ["21:00:00", "23:00:00"],
    "CZCE.OI": ["21:00:00", "23:00:00"],
    "CZCE.MA": ["21:00:00", "23:00:00"],
    "CZCE.FG": ["21:00:00", "23:00:00"],
    "CZCE.RM": ["21:00:00", "23:00:00"],
    "CZCE.ZC": ["21:00:00", "23:00:00"],
    "CZCE.TC": ["21:00:00", "23:00:00"],
    "SHFE.rb": ["21:00:00", "23:00:00"],
    "SHFE.hc": ["21:00:00", "23:00:00"],
    "SHFE.fu": ["21:00:00", "23:00:00"],
    "SHFE.bu": ["21:00:00", "23:00:00"],
    "SHFE.ru": ["21:00:00", "23:00:00"],
    "SHFE.sp": ["21:00:00", "23:00:00"],
    "INE.nr": ["21:00:00", "23:00:00"],
    "SHFE.cu": ["21:00:00", "25:00:00"],
    "SHFE.al": ["21:00:00", "25:00:00"],
    "SHFE.zn": ["21:00:00", "25:00:00"],
    "SHFE.pb": ["21:00:00", "25:00:00"],
    "SHFE.ni": ["21:00:00", "25:00:00"],
    "SHFE.sn": ["21:00:00", "25:00:00"],
    "SHFE.ss": ["21:00:00", "25:00:00"],
    "SHFE.au": ["21:00:00", "26:30:00"],
    "SHFE.ag": ["21:00:00", "26:30:00"],
    "INE.sc": ["21:00:00", "26:30:00"],
}


def _quotes_add_night(quotes):
    """为 quotes 中应该有夜盘但是市价合约文件中没有夜盘的品种，添加夜盘时间"""
    for symbol in quotes:
        product_id = quotes[symbol].get("product_id")
        if quotes[symbol].get("trading_time") and product_id:
            key = f"{quotes[symbol].get('exchange_id')}.{product_id}"
            if key in night_trading_table and (not quotes[symbol]["trading_time"].get("night")):
                quotes[symbol]["trading_time"]["night"] = [night_trading_table[key]]


def _bisect_value(a, x, priority="right"):
    """
    返回 bisect_right() 取得下标对应的值，当插入点距离前后元素距离相等，priority 表示优先返回右边的值还是左边的值
    a: 必须是已经排序好（升序排列）的 list
    bisect_right : Return the index where to insert item x in list a, assuming a is sorted.
    """
    assert priority in ['left', 'right']
    insert_index = bisect_right(a, x)
    if 0 < insert_index < len(a):
        left_dis = x - a[insert_index - 1]
        right_dis = a[insert_index] - x
        if left_dis == right_dis:
            mid_index = insert_index - 1 if priority == "left" else insert_index
        elif left_dis < right_dis:
            mid_index = insert_index - 1
        else:
            mid_index = insert_index
    else:
        assert insert_index == 0 or insert_index == len(a)
        mid_index = 0 if insert_index == 0 else (len(a) - 1)
    return a[mid_index]


class BlockManagerUnconsolidated(BlockManager):
    """mock BlockManager for unconsolidated, 不会因为自动合并同类型的 blocks 而导致 k 线数据不更新"""
    def __init__(self, *args, **kwargs):
        BlockManager.__init__(self, *args, **kwargs)
        self._is_consolidated = False
        self._known_consolidated = False

    def _consolidate_inplace(self): pass
