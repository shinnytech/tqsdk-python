#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk.api import TqApi

api = TqApi("SIM")
quote = api.get_quote("SHFE.cu1812")

while api.peek_message():
    if api.is_changing(quote):
        print(quote)
    if api.is_changing(quote, "last_price"):
        print(quote["last_price"])
    if api.is_changing(quote, ["ask_price1", "ask_volume1", "bid_price1", "bid_volume1"]):
        print(quote["ask_price1"], quote["ask_volume1"], quote["bid_price1"], quote["bid_volume1"])