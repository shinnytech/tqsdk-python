#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'ringo'

from tqsdk import TqApi, TqAuth
from tqsdk.tafunc import time_to_datetime

'''
使用get_trading_status来判断合约是否进入交易状态来进行下单，该接口需要有天勤量化专业版资格才可使用
'''

api = TqApi(auth=TqAuth("信易账户", "账户密码"))
ts = api.get_trading_status("SHFE.cu2201")
print(ts.trade_status)

while True:
    api.wait_update()
    # 如果处于集合竞价状态则进行下单
    if ts.trade_status == "AUCTIONORDERING":
        order = api.insert_order("SHFE.cu2201", "BUY", "OPEN", 1, 71400)
        break
# insert_order指令会在下一次wait_update()发出
api.wait_update()

api.close()
