#!/usr/bin/env python
#  -*- coding: utf-8 -*-

from tqsdk.api import TqApi
from tqsdk.demo.config import user_id, url

api = TqApi(user_id, url)
# 获得 rb1810 的持仓引用，
quote = api.get_quote("SHFE.rb1810")
# 下单平仓单
# 只有上期所平仓区分 CLOSETODAY (平今) / CLOSE (平昨)
order = api.insert_order(symbol="SHFE.rb1810",
                         direction="BUY",
                         offset="CLOSETODAY",
                         limit_price=quote["last_price"],
                         volume=2)
position = api.get_position("SHFE.rb1810")

while True:
    api.wait_update()
    if api.is_changing(order, ["status", "volume_orign", "volume_left"]):
        print("单状态: %s, 已成交: %d 手" % (order["status"], order["volume_orign"] - order["volume_left"]))
        if order["status"] == 'FINISHED':
            break
