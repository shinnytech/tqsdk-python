#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk.api import TqApi

api = TqApi("SIM")
position = api.get_position("SHFE.cu1812")
account = api.get_account()
order = api.insert_order(symbol="SHFE.cu1812", direction="BUY", offset="OPEN", volume=20)

while api.peek_message():
    if api.is_changing(order, ["status", "volume_orign", "volume_left"]):
        print("单ID: %s 状态: %s, 已成交: %d 手" % (order["order_id"], order["status"], order["volume_orign"] - order["volume_left"]))
    if api.is_changing(position, "volume_long_today"):
        print("今多仓: %d 手" % (position["volume_long_today"]))
    if api.is_changing(account, "available"):
        print("可用资金: %.2f" % (account["available"]))