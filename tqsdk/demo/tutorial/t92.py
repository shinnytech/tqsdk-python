#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk import TqApi, TqAuth

'''
画图示例: 在主图中画信号线及文字标注
注意: 画图示例中用到的数据不含有实际意义，请根据自己的实际策略情况进行修改
'''

api = TqApi(web_gui=True, auth=TqAuth("信易账户", "账户密码"))  # web_gui=True, 开启使用 web 界面查看绘图结果的功能
klines = api.get_kline_serial("SHFE.rb2105", 300)

# 示例1: 在主图中最后一根K线上画射线以标注需要的信号
api.draw_line(klines, -1, klines.iloc[-1].close, -1, klines.iloc[-1].high, line_type="SEG", color=0xFFFF9900, width=3)

# 示例2: 绘制字符串
api.draw_text(klines, "信号1", x=-1, y=klines.iloc[-1].high + 5, color=0xFFFF3333)

# 示例3: 给主图最后5根K线加一个方框
api.draw_box(klines, x1=-5, y1=klines.iloc[-5]["high"], x2=-1, y2=klines.iloc[-1]["low"], width=1, color=0xFF0000FF,
             bg_color=0x7000FF00)

# 由于需要在浏览器中查看绘图结果，因此程序不能退出
while True:
    api.wait_update()
