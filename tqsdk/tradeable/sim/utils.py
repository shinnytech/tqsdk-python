#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'


TRADING_DAYS_OF_YEAR = 250


def _get_price_range(quote):
    """ 返回合约对应的买一卖一盘口价格"""
    ask_price = quote["ask_price1"]
    bid_price = quote["bid_price1"]
    if quote["ins_class"].endswith("INDEX"):
        # 在指数交易时，使用 tick 进行回测时，backtest 发的 quote 没有买一卖一价；或者在实时行情中，指数的 quote 也没有买一卖一价
        if ask_price != ask_price:
            ask_price = quote["last_price"] + quote["price_tick"]
        if bid_price != bid_price:
            bid_price = quote["last_price"] - quote["price_tick"]
    return ask_price, bid_price


def _get_option_margin(quote, last_price, underlying_last_price):
    """返回每张期权占用保证金，只有空头持仓占用保证金"""
    # 期权保证金计算公式参考深交所文档 http://docs.static.szse.cn/www/disclosure/notice/general/W020191207433397366259.pdf
    if quote["option_class"] == "CALL":
        # 认购期权义务仓开仓保证金＝[合约最新价 + Max（12% × 合约标的最新价 - 认购期权虚值， 7% × 合约标的最新价）] × 合约单位
        # 认购期权虚值＝Max（行权价 - 合约标的最新价，0）
        out_value = max(quote["strike_price"] - underlying_last_price, 0)
        return (last_price + max(0.12 * underlying_last_price - out_value,
                                 0.07 * underlying_last_price)) * quote["volume_multiple"]
    else:
        # 认沽期权义务仓开仓保证金＝Min[合约最新价+ Max（12% × 合约标的最新价 - 认沽期权虚值，7% × 行权价），行权价] × 合约单位
        # 认沽期权虚值＝Max（合约标的最新价 - 行权价，0）
        out_value = max(underlying_last_price - quote["strike_price"], 0)
        return min(quote["last_price"] + max(0.12 * underlying_last_price - out_value,
                                             0.07 * quote["strike_price"]),
                   quote["strike_price"]) * quote["volume_multiple"]


def _get_premium(trade, quote):
    """返回成交导致的权利金变化"""
    if quote["ins_class"].endswith("OPTION"):
        premium = trade["price"] * trade["volume"] * quote["volume_multiple"]
        return -premium if trade["direction"] == "BUY" else premium
    else:
        return 0


def _get_close_profit(trade, quote, position):
    """返回成交导致的平仓盈亏变化"""
    if quote["ins_class"].endswith("OPTION"):
        # 期权没有持仓盈亏没有持仓价，其平仓的盈亏体现在市价变化中
        return 0
    # 期货及其他使用持仓价计算
    elif trade["direction"] == "SELL":
        return (trade["price"] - position["position_price_long"]) * trade["volume"] * quote["volume_multiple"]
    else:
        return (position["position_price_short"] - trade["price"]) * trade["volume"] * quote["volume_multiple"]


def _get_commission(quote={}):
    """返回每手手续费"""
    if quote.get("ins_class", "").endswith("OPTION"):
        return quote.get("user_commission", 10)  # 期权quote没有commission字段, 设为固定10元一张, 优先采用用户设置的参数
    return quote.get("user_commission", quote.get('commission', float('nan')))


def _get_future_margin(quote={}):
    """返回期货每手保证金"""
    if quote.get("ins_class", "").endswith("OPTION"):
        return float('nan')
    return quote.get("user_margin", quote.get("margin", float('nan')))
