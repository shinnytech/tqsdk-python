#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = "Ringo"

"""
豆油、棕榈油、菜油套利策略
注: 该示例策略仅用于功能示范, 实盘时请根据自己的策略/经验进行修改
"""
from tqsdk import TqApi, TargetPosTask
from tqsdk.tafunc import ma

# 设定豆油，菜油，棕榈油指定合约
SYMBOL_Y = "DCE.y2001"
SYMBOL_OI = "CZCE.OI001"
SYMBOL_P = "DCE.p2001"

api = TqApi()

klines_y = api.get_kline_serial(SYMBOL_Y, 24 * 60 * 60)
klines_oi = api.get_kline_serial(SYMBOL_OI, 24 * 60 * 60)
klines_p = api.get_kline_serial(SYMBOL_P, 24 * 60 * 60)

target_pos_oi = TargetPosTask(api, SYMBOL_OI)
target_pos_y = TargetPosTask(api, SYMBOL_Y)
target_pos_p = TargetPosTask(api, SYMBOL_P)


# 设置指标计算函数，计算三种合约品种的相对位置，并将指标画在副图
def cal_spread(klines_y, klines_p, klines_oi):
    index_spread = ((klines_y.close - klines_p.close) - (klines_oi.close - klines_y.close)) / (
            klines_oi.close - klines_p.close)
    klines_y["index_spread"] = index_spread
    ma_short = ma(index_spread, 5)
    ma_long = ma(index_spread, 15)
    return index_spread, ma_short, ma_long


index_spread, ma_short, ma_long = cal_spread(klines_y, klines_p, klines_oi)

klines_y["index_spread.board"] = "index_spread"

print("ma_short是%.2f,ma_long是%.2f，index_spread是%.2f" % (ma_short.iloc[-2], ma_long.iloc[-2], index_spread.iloc[-2]))

while True:
    api.wait_update()
    if api.is_changing(klines_y.iloc[-1], "datetime"):
        index_spread, ma_short, ma_long = cal_spread(klines_y, klines_p, klines_oi)
        print("日线更新，ma_short是%.2f,ma_long是%.2f，index_spread是%.2f" % (
            ma_short.iloc[-2], ma_long.iloc[-2], index_spread.iloc[-2]))

    # 指数上涨，短期上穿长期，则认为相对于y，oi被低估，做多oi，做空y
    if (ma_short.iloc[-2] > ma_long.iloc[-2]) and (ma_short.iloc[-3] < ma_long.iloc[-3]) and (
            index_spread.iloc[-2] > 1.02 * ma_short.iloc[-2]):
        target_pos_y.set_target_volume(-100)
        target_pos_oi.set_target_volume(100)
    # 指数下跌，短期下穿长期，则认为相对于y，p被高估，做多y，做空p
    elif (ma_short.iloc[-2] < ma_long.iloc[-2]) and (ma_short.iloc[-3] > ma_long.iloc[-3]) and (
            index_spread.iloc[-2] < 0.98 * ma_short.iloc[-2]):
        target_pos_y.set_target_volume(100)
        target_pos_p.set_target_volume(-100)
    # 现在策略表现平稳，则平仓，赚取之前策略收益
    elif ma_short.iloc[-2] * 0.98 < index_spread.iloc[-2] < ma_long.iloc[-2] * 1.02:
        target_pos_oi.set_target_volume(0)
        target_pos_p.set_target_volume(0)
        target_pos_y.set_target_volume(0)

