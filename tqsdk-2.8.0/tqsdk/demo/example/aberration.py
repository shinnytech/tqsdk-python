#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = "Ringo"

'''
Aberration策略 (难度：初级)
参考: https://www.shinnytech.com/blog/aberration/
注: 该示例策略仅用于功能示范, 实盘时请根据自己的策略/经验进行修改
'''

from tqsdk import TqApi, TqAuth, TargetPosTask
from tqsdk.ta import BOLL

# 设置合约代码
SYMBOL = "DCE.m2105"
api = TqApi(auth=TqAuth("信易账户", "账户密码"))
quote = api.get_quote(SYMBOL)
klines = api.get_kline_serial(SYMBOL, 60 * 60 * 24)
position = api.get_position(SYMBOL)
target_pos = TargetPosTask(api, SYMBOL)


# 使用BOLL指标计算中轨、上轨和下轨，其中26为周期N  ，2为参数p
def boll_line(klines):
    boll = BOLL(klines, 26, 2)
    midline = boll["mid"].iloc[-1]
    topline = boll["top"].iloc[-1]
    bottomline = boll["bottom"].iloc[-1]
    print("策略运行，中轨：%.2f，上轨为:%.2f，下轨为:%.2f" % (midline, topline, bottomline))
    return midline, topline, bottomline


midline, topline, bottomline = boll_line(klines)

while True:
    api.wait_update()
    # 每次生成新的K线时重新计算BOLL指标
    if api.is_changing(klines.iloc[-1], "datetime"):
        midline, topline, bottomline = boll_line(klines)

    # 每次最新价发生变化时进行判断
    if api.is_changing(quote, "last_price"):
        # 判断开仓条件
        if position.pos_long == 0 and position.pos_short == 0:
            # 如果最新价大于上轨，K线上穿上轨，开多仓
            if quote.last_price > topline:
                print("K线上穿上轨，开多仓")
                target_pos.set_target_volume(20)
            # 如果最新价小于轨，K线下穿下轨，开空仓
            elif quote.last_price < bottomline:
                print("K线下穿下轨，开空仓")
                target_pos.set_target_volume(-20)
            else:
                print("当前最新价%.2f,未穿上轨或下轨，不开仓" % quote.last_price)

        # 在多头情况下，空仓条件
        elif position.pos_long > 0:
            # 如果最新价低于中线，多头清仓离场
            if quote.last_price < midline:
                print("最新价低于中线，多头清仓离场")
                target_pos.set_target_volume(0)
            else:
                print("当前多仓，未穿越中线，仓位无变化")

        # 在空头情况下，空仓条件
        elif position.pos_short > 0:
            # 如果最新价高于中线，空头清仓离场
            if quote.last_price > midline:
                print("最新价高于中线，空头清仓离场")
                target_pos.set_target_volume(0)
            else:
                print("当前空仓，未穿越中线，仓位无变化")
