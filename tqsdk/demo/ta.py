#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import datetime
import time
from tqsdk import TqApi, TqSim
from tqsdk.ta import *

api = TqApi(TqSim())
# 获得 cu1905 10秒K线的引用
klines = api.get_kline_serial("SHFE.cu1905", 10, data_length=3000)

print("K线时间", datetime.datetime.fromtimestamp(klines.iloc[-1]["datetime"] / 1e9))
start = time.time()
for i in range(100):
    ATR(klines, 26)
    BIAS(klines, 6, 12, 24)
    BOLL(klines, 3, 5)
    DMI(klines, 14, 6)
    KDJ(klines, 9, 3, 3)
    MA(klines, 3, 5, 10, 20)
    MACD(klines, 20, 35, 10)
    SAR(klines, 4, 0.02, 0.2)
print(time.time() - start)
print(klines)

api.close()
