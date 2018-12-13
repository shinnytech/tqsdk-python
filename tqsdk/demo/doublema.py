#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

import talib
import numpy as np
from tqsdk import TqApi, TqSim, TargetPosTask

'''
双均线策略
'''
short = 30  # 短周期
long = 60  # 长周期

symbol = "SHFE.bu1906"  # 合约代码
api = TqApi(TqSim())
data_length = long + 2  # k线数据长度
# "duration_seconds=60"为一分钟线, 日线的duration_seconds参数为: 24*60*60
klines = api.get_kline_serial(symbol, duration_seconds=60, data_length=data_length)
target_pos = TargetPosTask(api, symbol)

while True:
    api.wait_update()

    if api.is_changing(klines[-1], "datetime"):  # 产生新k线:重新计算SMA
        short_avg = talib.SMA(np.array(klines.close), timeperiod=short)  # 短周期
        long_avg = talib.SMA(np.array(klines.close), timeperiod=long)  # 长周期

        # 均线下穿，做空
        if long_avg[-2] < short_avg[-2] and long_avg[-1] > short_avg[-1]:
            target_pos.set_target_volume(-3)
            print("均线下穿，做空")
        # 均线上穿，做多
        if short_avg[-2] < long_avg[-2] and short_avg[-1] > long_avg[-1]:
            target_pos.set_target_volume(3)
            print("均线上穿，做多")
