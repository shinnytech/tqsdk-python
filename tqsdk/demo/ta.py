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

while not klines.is_ready():
    api.wait_update()

print("K线时间", datetime.datetime.fromtimestamp(klines[-1]["datetime"] / 1e9))
start = time.time()
for i in range(100):
    df = klines.to_dataframe()
    ATR(df, 26)
    BIAS(df, 6, 12, 24)
    BOLL(df, 3, 5)
    DMI(df, 14, 6)
    KDJ(df, 9, 3, 3)
    MA(df, 3, 5, 10, 20)
    MACD(df, 20, 35, 10)
    SAR(df, 4, 0.02, 0.2)
print(time.time() - start)
print(df)

api.close()
