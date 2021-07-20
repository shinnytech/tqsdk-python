#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk import TqApi, TqAuth

'''
画图示例: 在主图中画线和方框
注意: 画图示例中用到的数据不含有实际意义，请根据自己的实际策略情况进行修改
'''

api = TqApi(web_gui=True, auth=TqAuth("信易账户", "账户密码")) # web_gui=True, 开启使用 web 界面查看绘图结果的功能
klines = api.get_kline_serial("SHFE.rb2105", 60)

# 由于需要在浏览器中查看绘图结果，因此程序不能退出
while True:
    api.wait_update() # 当有业务信息发生变化时执行
    # 当最后 1 根柱子最大最小值价差大于 0.05 时，在主图绘制信号
    high = klines.iloc[-1].high
    low = klines.iloc[-1].low
    if high - low > 0.05:
        # 绘制直线, 每一个 id 对应同一条直线
        api.draw_line(klines, -1, high, -1, low, id="box%.0f" % (klines.iloc[-1].id), color=0xaa662244, width=4)
        # 绘制字符串
        api.draw_text(klines, "信号1", x=-1, y=low, id="text%.0f" % (klines.iloc[-1].id), color=0xFFFF3333)

