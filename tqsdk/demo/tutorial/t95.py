#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk import TqApi
from tqsdk.ta import MA

'''
画图示例: 在同一副图中画K线、线段和方框
注意:1 画图功能仅在天勤终端/天勤Vscode插件中生效，请在这两个平台中运行画图相关的代码
     2 画图示例中用到的数据不含有实际意义，请根据自己的实际策略情况进行修改
'''

api = TqApi()


klines = api.get_kline_serial("CFFEX.T1912", 10)
klines2 = api.get_kline_serial("CFFEX.T2003", 10)

while True:

    # 在附图画出 cu1911 的K线: 需要将open、high、log、close的数据都设置正确
    klines["cu1911.open"] = klines2["open"]
    klines["cu1911.high"] = klines2["high"]
    klines["cu1911.low"] = klines2["low"]
    klines["cu1911.close"] = klines2["close"]
    klines["cu1911.board"] = "B2"
    ma = MA(klines, 30)
    klines["ma_MAIN"] = ma.ma

    # 在附图中画线段(默认为红色)
    api.draw_line(klines, -10, klines2.iloc[-10].low, -3, klines2.iloc[-3].high, id="my_line", board="B2", line_type="SEG", color=0xFFFF00FF, width=3)

    # 在附图K线上画黄色的方框: 需要设置画在附图时, 将board参数选择到对应的图板即可
    api.draw_box(klines, x1=-5, y1=klines2.iloc[-5]["high"], x2=-1, y2=klines2.iloc[-1]["low"], id="my_box", board="B2", width=1,
                 color=0xFF0000FF, bg_color=0x70FFFF00)

    api.wait_update()

