#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chaos'

from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))

# 不推荐使用以下方式获取符合某种条件的合约列表，推荐使用接口来完成此功能。
# ls = [k for k,v in api._data["quotes"].items() if k.startswith("KQ.m")]
# print(ls)

# au 品种的全部合约，包括已下市以及未下市合约
ls = api.query_quotes(ins_class="FUTURE", product_id="au")
print(ls)

# au、cu 品种的全部未下市合约合约
ls = api.query_quotes(ins_class=["FUTURE"], product_id=["au", "cu"], expired=False)
print(ls)

# au 品种指数合约
ls = api.query_quotes(ins_class="INDEX", product_id="au")
print(ls)

# 全部主连合约
ls = api.query_quotes(ins_class="CONT")
print(ls)

# au 品种主连合约
ls = api.query_quotes(ins_class="CONT", product_id="au")
print(ls)

# 上期所带夜盘的期货合约列表
ls = api.query_quotes(ins_class="FUTURE", exchange_id="SHFE", has_night=True)
print(ls)

# au 品种的全部未下市合约、指数、主连
ls = api.query_quotes(product_id="au", expired=False)
print(ls)

# 上海交易所股票代码列表
ls = api.query_quotes(ins_class="STOCK", exchange_id="SSE", expired=False)
print(ls)

# 上海交易所基金代码列表
ls = api.query_quotes(ins_class="FUND", exchange_id="SSE", expired=False)
print(ls)

# 关闭api,释放相应资源
api.close()