#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chaos'

from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))
# 注意：该函数返回的对象不会更新，不建议在循环内调用该方法

# 最近 1 天持仓排名信息，以成交量排序
df = api.query_symbol_ranking("SHFE.ag2504", ranking_type="VOLUME")
print(df.to_string())

# 最近 3 天持仓排名信息，以多头持仓量排序
df = api.query_symbol_ranking("SHFE.ag2504", ranking_type="LONG",days=3)
print(df.to_string())

# 关闭api,释放相应资源
api.close()