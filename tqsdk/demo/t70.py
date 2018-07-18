#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk.api import TqApi
from tqsdk.lib import TargetPosTask

'''
如果当前价格大于10秒K线的MA15则开多仓
如果小于则平仓
'''
api = TqApi("SIM")
# 获得 m1901 10秒K线的引用
klines = api.get_kline_serial("DCE.m1901", 10)
# 创建 m1901 的目标持仓 task，该 task 负责调整 m1901 的仓位到指定的目标仓位
target_pos = TargetPosTask(api, "DCE.m1901")

while True:
    api.wait_update()
    if api.is_changing(klines):
        ma = sum(klines.close[-15:])/15
        print("最新价", klines.close[-1], "MA", ma)
        if klines.close[-1] > ma:
            print("最新价大于MA: 目标多头5手")
            # 设置目标持仓为多头5手
            target_pos.set_target_volume(5)
        elif klines.close[-1] < ma:
            print("最新价小于MA: 目标空仓")
            # 设置目标持仓为空仓
            target_pos.set_target_volume(0)
