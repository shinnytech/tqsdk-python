#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chaos'

from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))

ls = api.query_options("SSE.510050", option_class="CALL", expired=False)  # 所有未下市上交所上证50etf期权
df = api.query_symbol_info(ls)
print(df.to_string())

# 关闭api,释放相应资源
api.close()