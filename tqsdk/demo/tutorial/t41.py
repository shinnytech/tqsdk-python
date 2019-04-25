#!/usr/bin/env python
#  -*- coding: utf-8 -*-

from tqsdk import TqApi, TqSim

api = TqApi(TqSim())
quote = api.get_quote("SHFE.rb1910")
# 开仓两手并等待完成
order = api.insert_order(symbol="SHFE.rb1910", direction="BUY", offset="OPEN", limit_price=quote["ask_price1"],volume=2)
while order["status"] != "FINISHED":
    api.wait_update()
print("已开仓")
# 平今两手并等待完成
order = api.insert_order(symbol="SHFE.rb1910", direction="SELL", offset="CLOSETODAY", limit_price=quote["bid_price1"],volume=2)
while order["status"] != "FINISHED":
    api.wait_update()
print("已平今")
# 关闭api,释放相应资源
api.close()
