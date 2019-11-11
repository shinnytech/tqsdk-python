#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk import TqApi
from tqsdk.ta import MA

'''
画图示例: 在主图中画指标线
注意:1 画图功能仅在天勤终端/天勤Vscode插件中生效，请在这两个平台中运行画图相关的代码
     2 画图示例中用到的数据不含有实际意义，请根据自己的实际策略情况进行修改
'''

api = TqApi()
klines = api.get_kline_serial("SHFE.au2006", 5)

ma = MA(klines, 30)  # 使用tqsdk自带指标函数计算均线
klines["ma_MAIN"] = ma.ma
# 在主图中画一根默认颜色（红色）的ma指标线

while True:
    api.wait_update()
    if api.is_changing(klines):
        ma = MA(klines, 30)  # 使用tqsdk自带指标函数计算均线
        klines["ma_MAIN"] = ma.ma
