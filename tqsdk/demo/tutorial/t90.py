#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk import TqApi
from tqsdk.ta import MA

'''
画图示例: 在主图中画指标线
注意: 画图示例中用到的数据不含有实际意义，请根据自己的实际策略情况进行修改
'''

api = TqApi(web_gui=True) # web_gui=True, 开启使用 web 界面查看绘图结果的功能
klines = api.get_kline_serial("SHFE.au2006", 5)

ma = MA(klines, 30)  # 使用 tqsdk 自带指标函数计算均线
klines["ma_MAIN"] = ma.ma # 在主图中画一根默认颜色（红色）的 ma 指标线

# 由于需要在浏览器中查看绘图结果，因此程序不能退出
while True:
    api.wait_update()
