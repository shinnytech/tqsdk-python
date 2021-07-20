#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = "Ringo"

from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("信易账户", "账户密码"))

# 订阅螺纹钢主连
quote = api.get_quote("KQ.m@SHFE.rb")
# 打印现在螺纹钢主连的标的合约
print(quote.underlying_symbol)

api.close()