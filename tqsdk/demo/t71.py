#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'yanqiong'

from tqsdk.api import TqApi
from tqsdk.lib import TargetPosTask

'''
目标持仓模型 - 优先平今
只有上期所平仓区分 CLOSETODAY (平今) / CLOSE (平昨) 指令，目标持仓模型会优先使用平今指令下单。
'''

api = TqApi("SIM")

quote = api.get_quote("SHFE.rb1810")
klines = api.get_kline_serial("SHFE.rb1810", 10)

# 设置总持仓 2 手，今仓 1 手，昨仓 2 - 1 手
target_pos = TargetPosTask(api, "SHFE.rb1810", init_pos=2, init_pos_today=1)
length = 3

while True:
    api.wait_update()
    if api.is_changing(quote):
        always_down = True
        last_klines = klines.close[-length:]
        # length 个 K 线收盘价连续下跌
        for i in range(0, length-1):
            always_down = False if last_klines[i] <= last_klines[i+1] else True
        if always_down:
            print(last_klines, "目标持仓: 0")
            # 平掉 1 手昨仓， 1 手今仓
            target_pos.set_target_volume(0)

