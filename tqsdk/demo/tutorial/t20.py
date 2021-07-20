#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk import TqApi, TqAuth

# 可以指定debug选项将调试信息写入指定的文件中
api = TqApi(debug="debug.log", auth=TqAuth("信易账户", "账户密码"))
quote = api.get_quote("SHFE.ni2011")
print(quote.datetime, quote.last_price, quote.ask_price1, quote.ask_price2)

while True:
    # 调用 wait_update 等待业务信息发生变化，例如: 行情发生变化, 委托单状态变化, 发生成交等等
    # 注意：其他合约的行情的更新也会触发业务信息变化，因此下面使用 is_changing 判断 ni2011 的行情是否有变化
    api.wait_update()
    # 如果 ni2011 的任何字段有变化，is_changing就会返回 True
    if api.is_changing(quote):
        print("行情变化", quote)
    # 只有当 ni2011 的最新价有变化，is_changing才会返回 True
    if api.is_changing(quote, "last_price"):
        print("最新价变化", quote.last_price)
    # 当 ni2011 的买1价/买1量/卖1价/卖1量中任何一个有变化，is_changing都会返回 True
    if api.is_changing(quote, ["ask_price1", "ask_volume1", "bid_price1", "bid_volume1"]):
        print("盘口变化", quote.ask_price1, quote.ask_volume1, quote.bid_price1, quote.bid_volume1)
