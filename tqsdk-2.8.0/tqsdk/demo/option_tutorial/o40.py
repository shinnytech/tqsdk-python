#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'ringo'

from tqsdk import TqApi, TqAuth
from tqsdk.ta import OPTION_GREEKS

api = TqApi(auth=TqAuth("信易账户", "账户密码"))

# 获取指定期权行情
quote = api.get_quote("SHFE.cu2006C44000")

# 获取期权和其对应标的的多合约的 kline 数据
klines = api.get_kline_serial(["SHFE.cu2006C44000", "SHFE.cu2006"], 24 * 60 * 60, 30)

# 运行 OPTION_GREEKS 希腊值计算函数
greeks = OPTION_GREEKS(klines, quote, 0.025)

# 输出希腊字母
print(list(greeks["delta"]))
print(list(greeks["theta"]))
print(list(greeks["gamma"]))
print(list(greeks["vega"]))
print(list(greeks["rho"]))

api.close()
