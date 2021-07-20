#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'ringo'

from tqsdk import TqApi, TqAuth
from tqsdk.ta import OPTION_IMPV

api = TqApi(auth=TqAuth("信易账户", "账户密码"))

# 获取指定期权行情
quote = api.get_quote("SHFE.cu2006C50000")

# 获取期权和对应标的的多合约 kline
klines = api.get_kline_serial(["SHFE.cu2006C50000", "SHFE.cu2006"], 24 * 60 * 60, 20)

# 通过 OPTION_IMPV 函数计算隐含波动率，设置无风险利率为 0.025
impv = OPTION_IMPV(klines, quote, 0.025)

print(list(impv["impv"] * 100))

api.close()
