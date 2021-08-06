#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'ringo'

from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("信易账户", "账户密码"))

ls = api.query_options("SHFE.au2012")
print(ls)  # 标的为 "SHFE.au2012" 的所有期权

ls = api.query_options("SHFE.au2012", option_class="PUT")
print(ls)  # 标的为 "SHFE.au2012" 的看跌期权

ls = api.query_options("SHFE.au2012", option_class="PUT", expired=False)
print(ls)  # 标的为 "SHFE.au2012" 的看跌期权, 未下市的

ls = api.query_options("SHFE.au2012", strike_price=340)
print(ls)  # 标的为 "SHFE.au2012" 、行权价为 340 的期权

ls = api.query_options("SSE.510300", exchange_id="CFFEX")
print(ls)  # 中金所沪深300股指期权

ls = api.query_options("SSE.510300", exchange_id="SSE")
print(ls)  # 上交所沪深300etf期权

ls = api.query_options("SSE.510300", exchange_id="SSE", exercise_year=2020, exercise_month=12)
print(ls)  # 上交所沪深300etf期权, 限制条件 2020 年 12 月份行权

api.close()