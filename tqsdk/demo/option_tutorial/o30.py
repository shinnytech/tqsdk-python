#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'ringo'

from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("信易账户", "账户密码"))

quote = api.get_quote("SHFE.au2012")

# 预计输出的为以au2012现在最新价来比对的认购的平值期权，当没有符合的平值期权时返回为空,如果有返回则格式为 ["SHFE.au2012C30000"]
ls = api.query_atm_options("SHFE.au2012", quote.last_price, 0, "CALL")

# 预计输出的为au2012，以开盘价来比对的认购的实值3档，实值2档，实值1档期权，如果没有符合要求的期权则对应栏返回为None，如果有则返回格式例如 [None,None,"SHFE.au2012C30000"]
ls = api.query_atm_options("SHFE.au2012", quote.open, [3, 2, 1], "CALL")

# 预计输出的为au2012，以开盘价来比对的认购的实值1档，平值期权，虚值1档，如果没有符合要求的期权则对应栏返回为None，如果有则返回格式例如
ls = api.query_atm_options("SHFE.au2012", quote.open, [1, 0, -1], "CALL")

# 预计输出的为au2012，以现在最新价来比对的认购的虚值1档期权
ls = api.query_atm_options("SHFE.au2012", quote.last_price, -1, "CALL")

# 预计输出沪深300股指期权,2020年12月的虚值1档期权
ls = api.query_atm_options("SSE.000300", quote.last_price, -1, "CALL", exercise_year=2020, exercise_month=12)

# 预计输出 上交所 沪深300股指ETF期权,2020年12月的虚值1档期权
ls = api.query_atm_options("SSE.510300", quote.last_price, -1, "CALL", exercise_year=2020, exercise_month=12)

api.close()
