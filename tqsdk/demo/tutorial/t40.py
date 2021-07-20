#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("信易账户", "账户密码"))
# 获得 m2105 的持仓引用，当持仓有变化时 position 中的字段会对应更新
position = api.get_position("DCE.m2105")
# 获得资金账户引用，当账户有变化时 account 中的字段会对应更新
account = api.get_account()
# 下单并返回委托单的引用，当该委托单有变化时 order 中的字段会对应更新
order = api.insert_order(symbol="DCE.m2105", direction="BUY", offset="OPEN", volume=5, limit_price=2750)

while True:
    api.wait_update()
    if api.is_changing(order, ["status", "volume_orign", "volume_left"]):
        print("单状态: %s, 已成交: %d 手" % (order.status, order.volume_orign - order.volume_left))
    if api.is_changing(position, "pos_long_today"):
        print("今多头: %d 手" % (position.pos_long_today))
    if api.is_changing(account, "available"):
        print("可用资金: %.2f" % (account.available))
