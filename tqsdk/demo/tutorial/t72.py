#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'ringo'

from tqsdk import TqApi, TqAuth
from tqsdk.tafunc import time_to_datetime

'''
判断收到的行情是否为正式开盘9点的行情
'''

api = TqApi(auth=TqAuth("信易账户", "账户密码"))
quote = api.get_quote("SHFE.rb2209")

while True:
    api.wait_update()
    # 判断收到的这笔行情是否为开盘九点的这笔行情
    if time_to_datetime(quote.datetime).hour == 9:
        order = api.insert_order("SHFE.rb2209", "BUY", "OPEN", 10, quote.ask_price1)
        break


# 用户其他任务的代码
while True:
    api.wait_update()

