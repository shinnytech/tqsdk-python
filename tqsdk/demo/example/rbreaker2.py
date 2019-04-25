# !/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

'''
R-Breaker策略(非隔夜留仓: 在每日收盘前，对所持合约进行平仓)
参考: https://www.shinnytech.com/blog/r-breaker
'''

from datetime import datetime
from tqsdk import TqApi, TqSim, TargetPosTask

SYMBOL = "SHFE.au1906"  # 合约代码
CLOSE_HOUR, CLOSE_MINUTE = 14, 50  # 平仓时间
STOP_LOSS_PRICE = 10  # 止损点(价格)

api = TqApi(TqSim())
print("策略开始运行")


def get_index_line(klines):
    '''计算指标线'''
    high = klines.high.iloc[-2]  # 前一日的最高价
    low = klines.low.iloc[-2]  # 前一日的最低价
    close = klines.close.iloc[-2]  # 前一日的收盘价
    pivot = (high + low + close) / 3  # 枢轴点
    bBreak = high + 2 * (pivot - low)  # 突破买入价
    sSetup = pivot + (high - low)  # 观察卖出价
    sEnter = 2 * pivot - low  # 反转卖出价
    bEnter = 2 * pivot - high  # 反转买入价
    bSetup = pivot - (high - low)  # 观察买入价
    sBreak = low - 2 * (high - pivot)  # 突破卖出价
    print("已计算新标志线, 枢轴点: %f, 突破买入价: %f, 观察卖出价: %f, 反转卖出价: %f, 反转买入价: %f, 观察买入价: %f, 突破卖出价: %f"
                % (pivot, bBreak, sSetup, sEnter, bEnter, bSetup, sBreak))
    return pivot, bBreak, sSetup, sEnter, bEnter, bSetup, sBreak


quote = api.get_quote(SYMBOL)
klines = api.get_kline_serial(SYMBOL, 24 * 60 * 60)  # 86400: 使用日线
position = api.get_position(SYMBOL)
target_pos = TargetPosTask(api, SYMBOL)
target_pos_value = position["volume_long"] - position["volume_short"]  # 净目标净持仓数
open_position_price = position["open_price_long"] if target_pos_value > 0 else position["open_price_short"]  # 开仓价
pivot, bBreak, sSetup, sEnter, bEnter, bSetup, sBreak = get_index_line(klines)  # 七条标准线

while True:
    target_pos.set_target_volume(target_pos_value)
    api.wait_update()
    if api.is_changing(klines.iloc[-1], "datetime"):  # 产生新k线,则重新计算7条指标线
        pivot, bBreak, sSetup, sEnter, bEnter, bSetup, sBreak = get_index_line(klines)

    if api.is_changing(quote, "datetime"):
        now = datetime.strptime(quote["datetime"], "%Y-%m-%d %H:%M:%S.%f")
        if now.hour == CLOSE_HOUR and now.minute >= CLOSE_MINUTE:  # 到达平仓时间: 平仓
            print("临近本交易日收盘: 平仓")
            target_pos_value = 0  # 平仓
            pivot = bBreak = sSetup = sEnter = bEnter = bSetup = sBreak = float("nan")  # 修改各指标线的值, 避免平仓后再次触发

    '''交易规则'''
    if api.is_changing(quote, "last_price"):
        print("最新价: %f" % quote["last_price"])

        # 开仓价与当前行情价之差大于止损点则止损
        if (target_pos_value > 0 and open_position_price - quote["last_price"] >= STOP_LOSS_PRICE) or \
                (target_pos_value < 0 and quote["last_price"] - open_position_price >= STOP_LOSS_PRICE):
            target_pos_value = 0  # 平仓

        # 反转:
        if target_pos_value > 0:  # 多头持仓
            if quote["highest"] > sSetup and quote["last_price"] < sEnter:
                # 多头持仓,当日内最高价超过观察卖出价后，
                # 盘中价格出现回落，且进一步跌破反转卖出价构成的支撑线时，
                # 采取反转策略，即在该点位反手做空
                print("多头持仓,当日内最高价超过观察卖出价后跌破反转卖出价: 反手做空")
                target_pos_value = -3  # 做空
                open_position_price = quote["last_price"]
        elif target_pos_value < 0:  # 空头持仓
            if quote["lowest"] < bSetup and quote["last_price"] > bEnter:
                # 空头持仓，当日内最低价低于观察买入价后，
                # 盘中价格出现反弹，且进一步超过反转买入价构成的阻力线时，
                # 采取反转策略，即在该点位反手做多
                print("空头持仓,当日最低价低于观察买入价后超过反转买入价: 反手做多")
                target_pos_value = 3  # 做多
                open_position_price = quote["last_price"]

        # 突破:
        elif target_pos_value == 0:  # 空仓条件
            if quote["last_price"] > bBreak:
                # 在空仓的情况下，如果盘中价格超过突破买入价，
                # 则采取趋势策略，即在该点位开仓做多
                print("空仓,盘中价格超过突破买入价: 开仓做多")
                target_pos_value = 3  # 做多
                open_position_price = quote["last_price"]
            elif quote["last_price"] < sBreak:
                # 在空仓的情况下，如果盘中价格跌破突破卖出价，
                # 则采取趋势策略，即在该点位开仓做空
                print("空仓,盘中价格跌破突破卖出价: 开仓做空")
                target_pos_value = -3  # 做空
                open_position_price = quote["last_price"]