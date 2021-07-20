#!usr/bin/env python3
#-*- coding:utf-8 -*-

from tqsdk import TqApi, TqAuth, tafunc
from tqsdk.ta import *

api = TqApi(auth=TqAuth("信易账户", "账户密码"))

underlying_quote = api.get_quote("SHFE.cu2009")
klines = api.get_kline_serial('SHFE.cu2009', 24 * 60 * 60, 20)
v = tafunc.get_his_volatility(klines, underlying_quote)
print("历史波动率:", v)

quote = api.get_quote("SHFE.cu2009C44000")
bs_serise = BS_VALUE(klines, quote, 0.025)
print("理论价:", list(round(bs_serise['bs_price'], 2)))


klines2 = api.get_kline_serial(["SHFE.cu2009C44000", "SHFE.cu2009"], 24 * 60 * 60, 20)

values = OPTION_VALUE(klines2, quote)
print("内在价值:", list(values["intrins"]))
print("时间价值:", list(values["time"]))

impv = OPTION_IMPV(klines2, quote, 0.025)
print("隐含波动率:", list(round(impv['impv'] * 100, 2)))

greeks = OPTION_GREEKS(klines2, quote, 0.025, impv['impv'])
print("delta:", list(greeks["delta"]))
print("theta:", list(greeks["theta"]))
print("gamma:", list(greeks["gamma"]))
print("vega:", list(greeks["vega"]))
print("rho:", list(greeks["rho"]))

api.close()
