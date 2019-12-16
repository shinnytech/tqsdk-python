#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk import TqApi

'''
画图示例: 在附图中画K线
注意: 画图示例中用到的数据不含有实际意义，请根据自己的实际策略情况进行修改
'''

api = TqApi(web_gui=True)

klines = api.get_kline_serial("SHFE.cu1910", 86400)
klines2 = api.get_kline_serial("SHFE.cu1911", 86400)

# 在附图画出 cu1911 的K线: 需要将open、high、log、close的数据都设置正确
klines["cu1911.open"] = klines2["open"]
klines["cu1911.high"] = klines2["high"]
klines["cu1911.low"] = klines2["low"]
klines["cu1911.close"] = klines2["close"]
klines["cu1911.board"] = "B2"

# 由于需要在浏览器中查看绘图结果，因此程序不能退出
while True:
    api.wait_update()
