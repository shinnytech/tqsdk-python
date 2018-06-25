#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk.api import TqApi

api = TqApi("SIM")
quote = api.get_quote("SHFE.cu1812")
order = {}

while api.peek_message():
    if order and api.is_changing(quote) and order["status"] == "ALIVE" and quote["bid_price1"] > order["limit_price"]:
        print("价格改变，撤单重下")
        api.cancel_order(order)
    if (not order and api.is_changing(quote)) or (api.is_changing(order) and order["volume_left"] != 0 and order["status"] == "FINISHED"):
        print("下单: 价格 %f" % quote["bid_price1"])
        order = api.insert_order(symbol="SHFE.cu1812", direction="BUY", offset="OPEN", volume=order.get("volume_left", 3), limit_price=quote["bid_price1"])
    if api.is_changing(order):
        print("单ID: %s 状态: %s 已成交: %d 手" % (order["order_id"], order["status"], order["volume_orign"] - order["volume_left"]))