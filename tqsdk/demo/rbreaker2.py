#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk.api import *
from tqsdk.lib import TargetPosTask

'''
R-Breaker策略(非隔夜留仓: 在每日收盘前，对所持合约进行平仓)
'''
symbol = "SHFE.au1812"  # 合约代码
close_hour, close_minute = 14, 50  # 平仓时间
stop_loss_price = 10  # 止损点(价格)


def get_index_line(klines):
    '''计算指标线'''
    high = klines[-2]["high"]  # 前一日的最高价
    low = klines[-2]["low"]  # 前一日的最低价
    close = klines[-2]["close"]  # 前一日的收盘价

    pivot = (high + low + close) / 3  # 枢轴点
    bBreak = high + 2 * (pivot - low)  # 突破买入价
    sSetup = pivot + (high - low)  # 观察卖出价
    sEnter = 2 * pivot - low  # 反转卖出价
    bEnter = 2 * pivot - high  # 反转买入价
    bSetup = pivot - (high - low)  # 观察买入价
    sBreak = low - 2 * (high - pivot)  # 突破卖出价

    print("已计算新标志线: ", "\n枢轴点", pivot, "\n突破买入价", bBreak, "\n观察卖出价", sSetup,
          "\n反转卖出价", sEnter, "\n反转买入价", bEnter, "\n观察买入价", bSetup, "\n突破卖出价", sBreak)
    return pivot, bBreak, sSetup, sEnter, bEnter, bSetup, sBreak


api = TqApi("SIM")
quote = api.get_quote(symbol)
klines = api.get_kline_serial(symbol, 24*60*60)  # 86400: 使用日线
position = api.get_position(symbol)
target_pos = TargetPosTask(api, symbol)
target_pos_value = position["volume_long"] - position["volume_short"]  # 净目标净持仓数
open_position_price = position["open_price_long"] if target_pos_value > 0 else position["open_price_short"]  # 开仓价
pivot, bBreak, sSetup, sEnter, bEnter, bSetup, sBreak = get_index_line(klines)  # 七条标准线

while True:
    target_pos.set_target_volume(target_pos_value)
    api.wait_update()
    if api.is_changing(klines[-1], "datetime"):  # 产生新k线,则重新计算7条指标线
        pivot, bBreak, sSetup, sEnter, bEnter, bSetup, sBreak = get_index_line(klines)

    nowTime = quote["datetime"].split()[1].split(":")  # 当前行情时间: [时,分,秒]
    if int(nowTime[0]) == close_hour and int(nowTime[1]) >= close_minute:  # 到达平仓时间: 平仓
        break

    '''交易规则'''
    if api.is_changing(quote, "last_price"):
        print("最新价: ", quote["last_price"])

        # 开仓价与当前行情价之差大于止损点则止损
        if (target_pos_value > 0 and open_position_price - quote["last_price"] >= stop_loss_price) or\
            (target_pos_value < 0 and quote["last_price"] - open_position_price >= stop_loss_price):
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


print("临近本交易日收盘: 平仓")
target_pos.set_target_volume(0)  # 平仓
deadline = time.time() + 60
while api.wait_update(deadline=deadline):  # 等待60秒
    pass
api.close()
