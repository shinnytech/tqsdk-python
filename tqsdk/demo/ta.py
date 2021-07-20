#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import datetime
from tqsdk import TqApi, TqAuth
from tqsdk.ta import *

api = TqApi(auth=TqAuth("信易账户", "账户密码"))
# 获得 cu1909 10秒K线的引用
klines = api.get_kline_serial("SHFE.cu1910", 10, data_length=3000)

print("K线时间", datetime.datetime.fromtimestamp(klines.iloc[-1]["datetime"] / 1e9))
print(klines)

print("ATR", ATR(klines, 26))
print("BIAS", BIAS(klines, 6))
print("BOLL", BOLL(klines, 3, 5))
print("DMI", DMI(klines, 14, 6))
print("KDJ", KDJ(klines, 9, 3, 3))
print("MA", MA(klines, 3))
print("MACD", MACD(klines, 20, 35, 10))
print("SAR", SAR(klines, 4, 0.02, 0.2))

api.close()
