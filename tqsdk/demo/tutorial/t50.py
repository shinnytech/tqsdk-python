#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chaos'

from datetime import datetime
from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))
# 注意：该函数返回的对象不会更新，不建议在循环内调用该方法

# 最近3天结算价信息
df = api.query_symbol_settlement("SHFE.ag2504", days=3)
print(df.to_string())

# 查询从2025年2月10日开始两天的结算价信息
df = api.query_symbol_settlement("SHFE.ag2504", days=2, start_dt=datetime(2025,2,10).date())
print(df.to_string())

# 关闭api,释放相应资源
api.close()