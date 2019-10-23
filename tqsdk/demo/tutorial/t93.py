#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk import TqApi

'''
画图示例: 在主中画线和方框
注意:1 画图功能仅在天勤终端/天勤Vscode插件中生效，请在这两个平台中运行画图相关的代码
     2 画图示例中用到的数据不含有实际意义，请根据自己的实际策略情况进行修改
'''

api = TqApi()
klines = api.get_kline_serial("SHFE.cu1910", 86400)

# 在主图中画直线
api.draw_line(klines, -4, klines.iloc[-4].low, -3, klines.iloc[-3].high, line_type="LINE", color=0xFF0000FF)

# 给主图最后5根K线加一个方框
api.draw_box(klines, x1=-5, y1=klines.iloc[-5]["high"], x2=-1, y2=klines.iloc[-1]["low"], width=1, color=0xFF0000FF,
             bg_color=0x7000FF00)

api.close()  # 需要调用此函数将画图数据发送给天勤并关闭api
