#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chaos'

from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))
quote = api.get_quote("SHFE.au2504")

# 预计输出的为以au2504现在最新价来比对的认购的平值期权，当没有符合的平值期权时返回为空
# ['SHFE.au2504C680']
ls = api.query_atm_options("SHFE.au2504", quote.last_price, 0, "CALL")
print(ls)

# 预计输出的为以au2504开盘价来比对的认购的实值1档，平值期权，虚值1档，如果没有符合要求的期权则对应栏返回为None，如果有则返回格式例如
# ['SHFE.au2504C680', 'SHFE.au2504C688', 'SHFE.au2504C696']
ls = api.query_atm_options("SHFE.au2504", quote.open, [1,0,-1], "CALL")
print(ls)

# 预计输出沪深300股指期权,2025年12月的虚值1档期权
ls = api.query_atm_options("SSE.000300", quote.last_price, -1, "CALL", exercise_year=2025, exercise_month=12)
print(ls)

# 关闭api,释放相应资源
api.close()
