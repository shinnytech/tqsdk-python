#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk import TqApi
from tqsdk.ta import MA

'''
画图示例: 在附图中画指标线
注意:1 画图功能仅在天勤终端/天勤Vscode插件中生效，请在这两个平台中运行画图相关的代码
     2 画图示例中用到的数据不含有实际意义，请根据自己的实际策略情况进行修改
'''

api = TqApi()
klines = api.get_kline_serial("SHFE.au1910", 24 * 60 * 60)
ma = MA(klines, 30)  # 使用tqsdk自带指标函数计算均线

# 示例: 在附图中画一根绿色的ma指标线
klines["ma_B2"] = ma.ma
klines["ma_B2.board"] = "B2"  # 设置附图: 可以设置任意字符串,同一字符串表示同一副图
klines["ma_B2.color"] = 0xFF00FF00  # 设置为绿色

# 示例: 在另一个附图画一根比ma小4的宽度为4的紫色指标线
klines["ma_4"] = ma.ma - 4
klines["ma_4.board"] = "MA4"  # 设置为另一个附图
klines["ma_4.color"] = 0xFF9933CC  # 设置为紫色
klines["ma_4.width"] = 4  # 设置宽度为4，默认为1

api.close()  # 需要调用此函数将画图指令发送给天勤并关闭api
