#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

'''
Dual Thrust策略 (难度：中级)
参考: https://www.shinnytech.com/blog/dual-thrust
注: 该示例策略仅用于功能示范, 实盘时请根据自己的策略/经验进行修改
'''

from tqsdk import TqApi, TqAuth, TargetPosTask

SYMBOL = "DCE.jd2011"  # 合约代码
NDAY = 5  # 天数
K1 = 0.2  # 上轨K值
K2 = 0.2  # 下轨K值

api = TqApi(auth=TqAuth("信易账户", "账户密码"))
print("策略开始运行")

quote = api.get_quote(SYMBOL)
klines = api.get_kline_serial(SYMBOL, 24 * 60 * 60)  # 86400使用日线
target_pos = TargetPosTask(api, SYMBOL)


def dual_thrust(quote, klines):
    current_open = klines.iloc[-1]["open"]
    HH = max(klines.high.iloc[-NDAY - 1:-1])  # N日最高价的最高价
    HC = max(klines.close.iloc[-NDAY - 1:-1])  # N日收盘价的最高价
    LC = min(klines.close.iloc[-NDAY - 1:-1])  # N日收盘价的最低价
    LL = min(klines.low.iloc[-NDAY - 1:-1])  # N日最低价的最低价
    range = max(HH - LC, HC - LL)
    buy_line = current_open + range * K1  # 上轨
    sell_line = current_open - range * K2  # 下轨
    print("当前开盘价: %f, 上轨: %f, 下轨: %f" % (current_open, buy_line, sell_line))
    return buy_line, sell_line


buy_line, sell_line = dual_thrust(quote, klines)  # 获取上下轨

while True:
    api.wait_update()
    if api.is_changing(klines.iloc[-1], ["datetime", "open"]):  # 新产生一根日线或开盘价发生变化: 重新计算上下轨
        buy_line, sell_line = dual_thrust(quote, klines)

    if api.is_changing(quote, "last_price"):
        if quote.last_price > buy_line:  # 高于上轨
            print("高于上轨,目标持仓 多头3手")
            target_pos.set_target_volume(3)  # 交易
        elif quote.last_price < sell_line:  # 低于下轨
            print("低于下轨,目标持仓 空头3手")
            target_pos.set_target_volume(-3)  # 交易
        else:
            print('未穿越上下轨,不调整持仓')
