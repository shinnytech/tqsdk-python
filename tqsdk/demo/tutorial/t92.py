#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk import TqApi

'''
画图示例: 在主图中画信号线及文字标注
注意:1 画图功能仅在天勤终端/天勤Vscode插件中生效，请在这两个平台中运行画图相关的代码
     2 画图示例中用到的数据不含有实际意义，请根据自己的实际策略情况进行修改
'''

api = TqApi()
klines = api.get_kline_serial("SHFE.cu1912", 86400)

# 在主图中最后一根K线上画射线以标注需要的信号
api.draw_line(klines, -1, klines.iloc[-1].close, -1, klines.iloc[-1].high, line_type="RAY", color=0xFFFF9900, width=3)
# 绘制字符串
api.draw_text(klines, "信号1", x=-1, y=klines.iloc[-1].high + 5, color=0xFFFF3333)

api.close()  # 需要调用此函数将画图数据发送给天勤并关闭api
