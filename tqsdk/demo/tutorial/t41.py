#!/usr/bin/env python
#  -*- coding: utf-8 -*-

from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("信易账户", "账户密码"))
quote = api.get_quote("SHFE.ni2101")
# 开仓两手并等待完成
order = api.insert_order(symbol="SHFE.ni2101", direction="BUY", offset="OPEN", limit_price=quote.ask_price1, volume=2)
while order.status != "FINISHED":
    api.wait_update()
print("已开仓")
# 平今两手并等待完成
order = api.insert_order(symbol="SHFE.ni2101", direction="SELL", offset="CLOSETODAY", limit_price=quote.bid_price1,
                         volume=2)
while order.status != "FINISHED":
    api.wait_update()
print("已平今")
# 关闭api,释放相应资源
api.close()
