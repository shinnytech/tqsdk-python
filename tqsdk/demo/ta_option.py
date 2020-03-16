#!usr/bin/env python3
#-*- coding:utf-8 -*-

from tqsdk import TqApi
from tqsdk.ta import *

api = TqApi()

underlying_quote = api.get_quote("SHFE.cu2006")
klines = api.get_kline_serial('SHFE.cu2006', 24 * 60 * 60, 20)
v = HIS_VOLATILITY(klines, underlying_quote)
print("历史波动率:", v)

quote = api.get_quote("SHFE.cu2009C44000")
klines2 = api.get_kline_serial(["SHFE.cu2009C44000", "SHFE.cu2006"], 24 * 60 * 60, 20)

values = VALUES(klines2, quote)
print(values)

bs_serise = BS_PRICE(klines2, quote, 0.025)
print("理论价:", list(round(bs_serise['bs_price'], 2)))

impv = IMP_VOLATILITY(klines2, quote, 0.025)
print("隐含波动率:", list(round(impv['impv'] * 100, 2)))

greeks = GREEKS(klines2, quote, 0.025, impv['impv'])
print(greeks)

api.close()
