#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'

from datetime import date
from tqsdk import TqApi, TqReplay

'''
复盘模式示例: 指定日期行情完全复盘
复盘 2019-09-10 行情
'''
# 在创建 api 实例时传入 TqReplay 就会进入复盘模式
api = TqApi(TqReplay(date(2019, 9, 10)))
quote = api.get_quote("SHFE.cu1912")

# 复盘服务器设置速度 0 ～ 100, 默认为 1
api.set_replay_speed(10)

while True:
    api.wait_update()
    if api.is_changing(quote):
        print("最新价", quote.datetime, quote.last_price)
