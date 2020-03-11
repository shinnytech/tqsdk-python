#!usr/bin/env python3
#-*- coding:utf-8 -*-

from tqsdk import TqApi
from tqsdk.ta import *

api = TqApi()
option = api.get_quote("CFFEX.IO2012-C-4000")
r = 0.025  # 无风险利率
klines = api.get_kline_serial(["CFFEX.IO2012-C-4000", "CSI.000300"], 24 * 60 * 60, 30)

values = VALUES(klines)
print("==== 内在价值 时间价值 ====")
print(values.iloc[-1:])
bs_serise = BS_PRICE(klines, option.expire_datetime, r)
print("==== 理论价格 ====")
print(bs_serise.iloc[-1:])
impv = IMPV(klines, option.expire_datetime, r)
print("==== 隐含波动率 ====")
print(impv.iloc[-1:])
greeks = GREEKS(klines, option.expire_datetime, r)
print("==== 希腊指标 ====")
print(greeks.iloc[-1:])
api.close()
