#!usr/bin/env python3
#-*- coding:utf-8 -*-
#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from datetime import date
from tqsdk import TqApi, TqReplay, TargetPosTask

'''
复盘 2019-11-12
如果当前价格大于5分钟K线的MA15则开多仓,如果小于则平仓
'''
# 在创建 api 实例时传入 TqReplay 就会进入复盘模式, 同时打开 web_gui
api = TqApi(backtest=TqReplay(date(2019, 11, 12)), web_gui=True)
# 获得 m1901 5分钟K线的引用
klines = api.get_kline_serial("SHFE.cu2001", 5 * 60, data_length=15)
# 创建 m1901 的目标持仓 task，该 task 负责调整 m1901 的仓位到指定的目标仓位
target_pos = TargetPosTask(api, "SHFE.cu2001")

while True:
    api.wait_update()
    if api.is_changing(klines):
        ma = sum(klines.close.iloc[-15:]) / 15
        print("最新价", klines.close.iloc[-1], "MA", ma)
        if klines.close.iloc[-1] > ma:
            print("最新价大于MA: 目标多头5手")
            # 设置目标持仓为多头5手
            target_pos.set_target_volume(5)
        elif klines.close.iloc[-1] < ma:
            print("最新价小于MA: 目标空仓")
            # 设置目标持仓为空仓
            target_pos.set_target_volume(0)
