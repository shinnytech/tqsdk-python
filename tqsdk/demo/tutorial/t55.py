#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chaos'

from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))

# 标的为 "SHFE.au2504" 的所有期权
ls = api.query_options("SHFE.au2504")
print(ls)

# 标的为 "SHFE.au2504" 的看跌期权
ls = api.query_options("SHFE.au2504", option_class="PUT")
print(ls)

# 标的为 "SHFE.au2504" 的看跌期权, 未下市的
ls = api.query_options("SHFE.au2504", option_class="PUT", expired=False)
print(ls)

# 标的为 "SHFE.au2504" 、行权价为 340 的期权
ls = api.query_options("SHFE.au2504", strike_price=340)
print(ls)

# 中金所沪深300股指期权
ls = api.query_options("SSE.000300")
print(ls)

# 上交所沪深300etf期权
ls = api.query_options("SSE.510300")
print(ls)

# 上交所沪深300etf期权, 限制条件 2020 年 12 月份行权
ls = api.query_options("SSE.510300", exercise_year=2020, exercise_month=12)
print(ls)

# 关闭api,释放相应资源
api.close()