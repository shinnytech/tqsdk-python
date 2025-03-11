#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chaos'

from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))

quote = api.get_quote("SSE.510050")
in_money_options, at_money_options, out_of_money_options = api.query_all_level_finance_options("SSE.510300", quote.last_price, "CALL", nearbys = 1)
print(in_money_options)  # 实值期权列表
print(at_money_options)  # 平值期权列表
print(out_of_money_options)  # 虚值期权列表

# 关闭api,释放相应资源
api.close()
