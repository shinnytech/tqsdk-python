#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk.api import TqApi
import datetime

api = TqApi("SIM")
# 获得cu1812 tick序列的引用
ticks = api.get_tick_serial("SHFE.cu1812")
# 获得cu1812 10秒K线的引用
klines = api.get_kline_serial("SHFE.cu1812", 10)

while True:
    api.wait_update()
    # 判断整个tick序列是否有变化
    if api.is_changing(ticks):
        # ticks[-1]返回序列中最后一个tick
        print("tick变化", ticks[-1])
    # 判断最后一根K线的时间是否有变化，如果发生变化则表示新产生了一根K线
    if api.is_changing(klines[-1], "datetime"):
        # datetime: 自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数
        print("新K线", datetime.datetime.fromtimestamp(klines[-1]["datetime"]/1e9))
    # 判断最后一根K线的收盘价是否有变化
    if api.is_changing(klines[-1], "close"):
        # klines.close返回收盘价序列
        print("K线变化", datetime.datetime.fromtimestamp(klines[-1]["datetime"]/1e9), klines.close[-1])