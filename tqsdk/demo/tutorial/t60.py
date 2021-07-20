#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk import TqApi, TqAuth

'''
如果当前价格大于10秒K线的MA15则开多仓 (使用 insert_order() 函数)
如果小于则平仓
'''
api = TqApi(auth=TqAuth("信易账户", "账户密码"))
# 获得 m2105 10秒K线的引用
klines = api.get_kline_serial("DCE.m2105", 10)

# 判断开仓条件
while True:
    api.wait_update()
    if api.is_changing(klines):
        ma = sum(klines.close.iloc[-15:]) / 15
        print("最新价", klines.close.iloc[-1], "MA", ma)
        if klines.close.iloc[-1] > ma:
            print("最新价大于MA: 市价开仓")
            api.insert_order(symbol="DCE.m2105", direction="BUY", offset="OPEN", volume=5)
            break
# 判断平仓条件
while True:
    api.wait_update()
    if api.is_changing(klines):
        ma = sum(klines.close.iloc[-15:]) / 15
        print("最新价", klines.close.iloc[-1], "MA", ma)
        if klines.close.iloc[-1] < ma:
            print("最新价小于MA: 市价平仓")
            api.insert_order(symbol="DCE.m2105", direction="SELL", offset="CLOSE", volume=5)
            break
# 关闭api,释放相应资源
api.close()
