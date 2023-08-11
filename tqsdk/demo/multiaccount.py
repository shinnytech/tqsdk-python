#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'hongyan'

from tqsdk import TqApi, TqAuth, TqAccount, TqKq, TqSim, TqMultiAccount
# 多账户模式下, 同时操作实盘、模拟交易和快期模拟账户交易
tqact = TqAccount("H海通期货", "123456", "123456")
sim = TqSim()
kq = TqKq()

with TqApi(TqMultiAccount([tqact, sim, kq]), auth=TqAuth("快期账户", "账户密码")) as api:
    order1 = api.insert_order(symbol="DCE.m2101", direction="BUY", offset="OPEN", volume=5, account=tqact)
    order2 = api.insert_order(symbol="SHFE.au2012C308", direction="BUY", offset="OPEN", volume=5, limit_price=78.1, account=sim)
    order3 = api.insert_order(symbol="SHFE.cu2101", direction="Sell", offset="OPEN", volume=10, limit_price=51610, account=kq)
    api.cancel_order(order3, kq)
    while order1.status != "FINISHED" or order2.status != "FINISHED":
        api.wait_update()
    # 分别获取账户资金信息
    account_info1 = tqact.get_account()
    account_info2 = sim.get_account()
    account_info3 = kq.get_account()
    # 分别获取账户持仓信息
    position1 = tqact.get_position("DCE.m2101", )
    position2 = sim.get_position()
    position3 = kq.get_position()
    # 分别获取账户委托数据
    orders1 = tqact.get_order(order_id=order1.order_id, )
    orders2 = sim.get_position()
    orders3 = kq.get_position()
    # 分别获取账户成交数据
    trades1 = tqact.get_trade()
    trades2 = sim.get_trade()
    trades3 = kq.get_trade()