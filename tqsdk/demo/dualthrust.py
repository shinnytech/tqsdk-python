#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk.api import TqApi
from tqsdk.lib import TargetPosTask

'''
Dual Thrust策略
'''
symbol = "SHFE.rb1901"  # 合约代码
Nday = 5  # 天数
K1 = 0.2  # 上轨K值
K2 = 0.2  # 下轨K值


def dual_thrust(quote, klines):
    current_open = quote["open"]
    HH = max(klines.high[-Nday - 1:-1])  # N日最高价的最高价
    HC = max(klines.close[-Nday - 1:-1])  # N日收盘价的最高价
    LC = min(klines.close[-Nday - 1:-1])  # N日收盘价的最低价
    LL = min(klines.low[-Nday - 1:-1])  # N日最低价的最低价
    range = max(HH - LC, HC - LL)
    buy_line = current_open + range * K1  # 上轨
    sell_line = current_open - range * K2  # 下轨

    print("当前开盘价:", current_open, "\n上轨:", buy_line, "\n下轨:", sell_line)
    return buy_line, sell_line


api = TqApi("SIM")
quote = api.get_quote(symbol)
klines = api.get_kline_serial(symbol, 24*60*60)  # 86400使用日线
target_pos = TargetPosTask(api, symbol)
buy_line, sell_line = dual_thrust(quote, klines)  # 获取上下轨

while True:
    api.wait_update()
    if api.is_changing(klines[-1], "datetime") or api.is_changing(quote, "open"):  # 新产生一根日线或开盘价发生变化: 重新计算上下轨
        buy_line, sell_line = dual_thrust(quote, klines)

    if api.is_changing(quote, "last_price"):
        print("最新价变化", quote["last_price"], end=':')
        if quote["last_price"] > buy_line:  # 高于上轨
            print("高于上轨,目标持仓 多头3手")
            target_pos.set_target_volume(3)  # 交易
        elif quote["last_price"] < sell_line:  # 低于下轨
            print("低于下轨,目标持仓 空头3手")
            target_pos.set_target_volume(-3)  # 交易
        else:
            print('未穿越上下轨,不调整持仓')
