#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chaos'

from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))

quote = api.get_quote("SSE.510300")
in_money_options, at_money_options, out_of_money_options = api.query_all_level_finance_options("SSE.510300", quote.last_price, "CALL", nearbys = 1)
ls = in_money_options + at_money_options + out_of_money_options  # 期权列表
df = api.query_option_greeks(ls)
print(df.to_string())  # 显示期权希腊指标

# 关闭api,释放相应资源
api.close()
