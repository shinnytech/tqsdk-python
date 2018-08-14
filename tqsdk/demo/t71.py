#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'yanqiong'

from tqsdk.api import TqApi
from tqsdk.lib import TargetPosTask
from tqsdk.demo.config import user_id, url

'''
目标持仓模型 - 优先平今
只有上期所平仓区分 CLOSETODAY (平今) / CLOSE (平昨) 指令，目标持仓模型会优先使用平今指令下单。
'''

api = TqApi(user_id, url)

quote = api.get_quote("SHFE.rb1810")
klines = api.get_kline_serial("SHFE.rb1810", 3)

# 不设置总持仓 set_target_volume(0) 11 / 38 =>  11 / 11
target_pos = TargetPosTask(api, "SHFE.rb1810")

# target_pos = TargetPosTask(api, "SHFE.rb1810", init_pos=2, init_pos_today=1)
# target_pos = TargetPosTask(api, "SHFE.rb1810", init_pos=1)
# target_pos = TargetPosTask(api, "SHFE.rb1810", init_pos=1, init_pos_today=2)
# target_pos = TargetPosTask(api, "SHFE.rb1810", init_pos=1, init_pos_today=-1)

length = 2

while True:
    api.wait_update()
    if api.is_changing(quote):
        always_down = True
        last_klines = klines.close[-length:]
        # length 个 K 线收盘价连续下跌
        for i in range(0, length-1):
            if last_klines[i] <= last_klines[i + 1]:
                always_down = False
                break
        if always_down:
            print(last_klines, always_down, "目标持仓: 0")
            target_pos.set_target_volume(0)

