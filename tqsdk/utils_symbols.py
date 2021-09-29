#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'

from datetime import datetime

from tqsdk.objs import Quote


def _symbols_to_quotes(symbols, keys=set(Quote(None).keys())):
    """将 symbols 转为 quotes，只输出 keys 包括的字段"""
    result = symbols.get("result", {})
    quotes = {}
    for k in result:
        for symbol in result[k]:
            quote = quotes.setdefault(symbol["instrument_id"], {})
            quote.update(_convert_symbol_to_quote(symbol, keys))
            if symbol.get("underlying"):
                for edge in symbol["underlying"]["edges"]:
                    underlying_symbol = edge["node"]
                    if "underlying_symbol" in keys:
                        quote["underlying_symbol"] = underlying_symbol["instrument_id"]
                    underlying_quote = quotes.setdefault(underlying_symbol["instrument_id"], {})
                    underlying_quote.update(_convert_symbol_to_quote(underlying_symbol, keys))
                    # 为期权合约补充 delivery_year delivery_month 商品期权根据标的赋值；金融期权与 exercise_year exercise_month 相同
                    # 为期权补充 delivery_year delivery_month 完全是为了兼容旧版合约服务
                    for key in ["delivery_year", "delivery_month"]:
                        if key in keys and symbol["class"] == "OPTION":
                            if symbol["exchange_id"] in ["DCE", "CZCE", "SHFE"]:
                                quote[key] = underlying_quote[key]
                            if symbol["exchange_id"] == "CFFEX" and "last_exercise_datetime" in symbol:
                                if key == "delivery_year":
                                    quote[key] = datetime.fromtimestamp(symbol["last_exercise_datetime"] / 1e9).year
                                else:
                                    quote[key] = datetime.fromtimestamp(symbol["last_exercise_datetime"] / 1e9).month
    for k in quotes:
        if quotes[k].get("ins_class", "") == "COMBINE":
            # 为组合合约补充 volume_multiple
            leg1_quote = quotes.get(quotes[k].get("leg1_symbol", ""), {})
            if leg1_quote:
                if leg1_quote.get("volume_multiple"):
                    quotes[k]["volume_multiple"] = leg1_quote["volume_multiple"]
    return quotes


def _convert_symbol_to_quote(symbol, keys):
    quote = {}
    for key in keys:
        if key == "leg1_symbol" and "leg1" in symbol:
            quote["leg1_symbol"] = symbol["leg1"]["instrument_id"]
        elif key == "leg2_symbol" and "leg2" in symbol:
            quote["leg2_symbol"] = symbol["leg2"]["instrument_id"]
        elif key == "ins_class" and "class" in symbol:
            quote["ins_class"] = symbol["class"]
        elif key == "option_class" and "call_or_put" in symbol:
            quote["option_class"] = symbol["call_or_put"]
        elif key == "volume_multiple" and "index_multiple" in symbol:
            quote["volume_multiple"] = symbol["index_multiple"]
        elif key == "expire_datetime" and symbol.get("expire_datetime"):
            quote["expire_datetime"] = symbol["expire_datetime"] / 1e9
        elif key == "last_exercise_datetime" and symbol.get("last_exercise_datetime"):
            quote["last_exercise_datetime"] = symbol["last_exercise_datetime"] / 1e9
        elif key == "exercise_year" and symbol.get("last_exercise_datetime"):
            quote["exercise_year"] = datetime.fromtimestamp(symbol["last_exercise_datetime"] / 1e9).year
        elif key == "exercise_month" and symbol.get("last_exercise_datetime"):
            quote["exercise_month"] = datetime.fromtimestamp(symbol["last_exercise_datetime"] / 1e9).month
        elif key == "pre_settlement" and "settlement_price" in symbol:
            quote["pre_settlement"] = symbol["settlement_price"]
        elif key in symbol:
            quote[key] = symbol[key]
    return quote