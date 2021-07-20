#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'ringo'

from tqsdk import TqApi, TqAuth

# 创建API实例,传入自己的信易账户
api = TqApi(auth=TqAuth("信易账户", "账户密码"))

# 获取大商所豆粕期权行情
quote_m = api.get_quote("DCE.m1807-C-2450")

# 获取中金所股指期权行情
quote_IO = api.get_quote("CFFEX.IO2002-C-3550")

# 输出 m1807-C-2450 的最新行情时间和最新价
print(quote_m.datetime, quote_m.last_price)

# 关闭api,释放资源
api.close()
