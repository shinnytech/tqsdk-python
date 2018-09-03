#!/usr/bin/env python
#  -*- coding: utf-8 -*-

from tqsdk.api import TqApi

api = TqApi("SIM")
# 开仓两手并等待完成
order = api.insert_order(symbol="SHFE.rb1901", direction="BUY", offset="OPEN", limit_price=4310,volume=2)
while order["status"] != "FINISHED":
    api.wait_update()
print("已开仓")
# 平今两手并等待完成
order = api.insert_order(symbol="SHFE.rb1901", direction="SELL", offset="CLOSETODAY", limit_price=3925,volume=2)
while order["status"] != "FINISHED":
    api.wait_update()
print("已平今")
# 关闭api,释放相应资源
api.close()
