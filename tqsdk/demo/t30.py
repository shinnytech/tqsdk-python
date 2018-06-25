#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk.api import TqApi

api = TqApi("SIM")
ticks = api.get_tick_serial("SHFE.cu1812")
klines = api.get_kline_serial("SHFE.cu1812", 10)

while api.peek_message():
    if api.is_changing(ticks):
        print("tick", ticks[-1])
    if api.is_changing(klines[-1], "close"):
        print("kline", klines[-1])