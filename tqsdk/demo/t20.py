#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk.api import TqApi

# 可以指定debug选项将调试信息写入指定的文件中
api = TqApi("SIM", debug="debug.log")
quote = api.get_quote("SHFE.cu1812")

while True:
    api.wait_update()
    # 如果 cu1812 的任何字段有变化，is_changing就会返回 True
    if api.is_changing(quote):
        print(quote)
    # 只有当 cu1812 的最新价有变化，is_changing才会返回 True
    if api.is_changing(quote, "last_price"):
        print("最新价变化", quote["last_price"])
    # 当 cu1812 的买1价/买1量/卖1价/卖1量中任何一个有变化，is_changing都会返回 True
    if api.is_changing(quote, ["ask_price1", "ask_volume1", "bid_price1", "bid_volume1"]):
        print("盘口变化", quote["ask_price1"], quote["ask_volume1"], quote["bid_price1"], quote["bid_volume1"])
