#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'

import base64
import json
import random
import secrets
import uuid

RD = random.Random(secrets.randbits(128))  # 初始化随机数引擎，使用随机数作为seed，防止用户同时拉起多个策略，产生同样的 seed


def _generate_uuid(prefix=''):
    return f"{prefix + '_' if prefix else ''}{uuid.UUID(int=RD.getrandbits(128)).hex}"


def _quote_query_id(symbol):
    """返回请求合约信息的 query_id, 每个合约生成的 query_id 是唯一的"""
    return "PYSDK_quote_" + base64.urlsafe_b64encode(symbol.encode()).decode().replace('=', '')


def _query_for_quote(symbol):
    """返回请求某个合约的合约信息的 query_pack"""
    query = """
        query ($instrument_id: String){symbol_info(instrument_id: $instrument_id){
        ... on basic{ class trading_time{day night} trading_day instrument_id price_tick price_decs volume_multiple exchange_id english_name}
        ... on stock{ stock_dividend_ratio cash_dividend_ratio}
        ... on fund{ cash_dividend_ratio}
        ... on bond{ maturity_date }
        ... on securities{ currency face_value first_trading_day buy_volume_unit sell_volume_unit status public_float_share_quantity}
        ... on future{ expired product_id product_short_name delivery_year delivery_month expire_datetime settlement_price max_market_order_volume max_limit_order_volume margin commission mmsa}
        ... on option{ expired product_short_name expire_datetime last_exercise_day settlement_price max_market_order_volume max_limit_order_volume strike_price call_or_put exercise_type}
        ... on combine{ expired product_id expire_datetime max_market_order_volume max_limit_order_volume }
        ... on derivative{ 
            underlying{ 
                count edges{ underlying_multiple node{
                    ... on basic{ class trading_time{day night} trading_day instrument_id price_tick price_decs volume_multiple exchange_id english_name }
                    ... on stock{ stock_dividend_ratio cash_dividend_ratio }
                    ... on fund{ cash_dividend_ratio }
                    ... on bond{ maturity_date }
                    ... on securities{ currency face_value first_trading_day buy_volume_unit sell_volume_unit status public_float_share_quantity }
                    ... on future{ expired product_id product_short_name delivery_year delivery_month expire_datetime settlement_price max_market_order_volume max_limit_order_volume margin commission mmsa}
                    }}
                }
            }
        }}
    """
    return {
        "aid": "ins_query",
        "query_id": _quote_query_id(symbol),
        "query": query,
        "variables": json.dumps({"instrument_id": symbol})
    }


def _query_for_init():
    """
    返回某些类型合约的 query 和 variables
    todo: 为了兼容旧版提供给用户的 api._data["quote"].items() 类似用法，应该限制交易所 ["SHFE", "DCE", "CZCE", "INE", "CFFEX", "KQ"]
    todo: 现在加了未下市的查询条件，需要去掉 expired
    """
    query = "query ($var:Boolean,$future:Class,$index:Class,$option:Class,$combine:Class,$cont:Class,$exSHFE:String,$exDCE:String,$exCZCE:String,$exINE:String,$exCFFEX:String,$exKQ:String){"
    for ex in ["SHFE", "DCE", "CZCE", "INE", "CFFEX", "KQ"]:
        for ins_class in ["future", "index", "option", "combine", "cont"]:
            query += ex + ins_class + ":symbol_info(expired:$var,class:$" + ins_class + ",exchange_id:$ex" + ex + "){" +\
                 """
                    ... on basic{ class trading_time{day night} trading_day instrument_id price_tick price_decs volume_multiple exchange_id english_name}
                    ... on stock{ stock_dividend_ratio cash_dividend_ratio}
                    ... on fund{ cash_dividend_ratio}
                    ... on bond{ maturity_date }
                    ... on securities{ currency face_value first_trading_day buy_volume_unit sell_volume_unit status public_float_share_quantity}
                    ... on future{ expired product_id product_short_name delivery_year delivery_month expire_datetime settlement_price max_market_order_volume max_limit_order_volume margin commission mmsa}
                    ... on option{ expired product_short_name expire_datetime last_exercise_day settlement_price max_market_order_volume max_limit_order_volume strike_price call_or_put exercise_type}
                    ... on combine{ expired product_id expire_datetime max_market_order_volume max_limit_order_volume }
                    ... on derivative{ 
                        underlying{ 
                            count edges{ underlying_multiple node{
                                ... on basic{ class trading_time{day night} trading_day instrument_id price_tick price_decs volume_multiple exchange_id english_name }
                                ... on stock{ stock_dividend_ratio cash_dividend_ratio }
                                ... on fund{ cash_dividend_ratio }
                                ... on bond{ maturity_date }
                                ... on securities{ currency face_value first_trading_day buy_volume_unit sell_volume_unit status public_float_share_quantity }
                                ... on future{ expired product_id product_short_name delivery_year delivery_month expire_datetime settlement_price max_market_order_volume max_limit_order_volume margin commission mmsa}
                                }}
                            }
                        }
                    }
                """
    query += "}"
    return query, json.dumps({
        "future": "future",
        "index": "index",
        "option": "option",
        "combine": "combine",
        "cont": "cont",
        "exSHFE": "SHFE",
        "exDCE": "DCE",
        "exCZCE": "CZCE",
        "exINE": "INE",
        "exCFFEX": "CFFEX",
        "exKQ": "KQ",
        "var": False
    })


def _symbols_to_quotes(symbols):
    result = json.loads(symbols.get("result", "{}"))
    quotes = {}
    for k in result["data"]:
        for quote in result["data"][k]:
            if quote.get("class", None):
                quote["ins_class"] = quote["class"]
                del quote["class"]
            if quote.get("call_or_put"):
                quote["option_class"] = quote["call_or_put"]
                del quote["call_or_put"]
            if quote.get("underlying"):  # 展开标的合约
                for edge in quote["underlying"]["edges"]:
                    underlying_quote = edge["node"]
                    if underlying_quote.get("class"):
                        underlying_quote["ins_class"] = underlying_quote["class"]
                        del underlying_quote["class"]
                    quote["underlying_symbol"] = underlying_quote["instrument_id"]
                    del quote["underlying"]
                    quotes[underlying_quote["instrument_id"]] = underlying_quote
            quotes[quote["instrument_id"]] = quote
    return quotes


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
        product_id = quotes[symbol]["product_id"]
        if quotes[symbol].get("trading_time") and product_id in night_trading_table:
            quotes[symbol]["trading_time"].setdefault("night", [night_trading_table[product_id]])
