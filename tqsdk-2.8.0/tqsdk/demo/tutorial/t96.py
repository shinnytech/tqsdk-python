#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'yanqiong'

from tqsdk import TqApi, TqAuth
from tqsdk.ta import MACD

'''
画图示例: 在附图中画 macd 指标示例
注意: 画图示例中用到的数据不含有实际意义，请根据自己的实际策略情况进行修改
'''

def calc_macd_klines(klines):
    # 计算 macd 指标
    macd = MACD(klines, 12, 26, 9)
    # 用 K 线图模拟 MACD 指标柱状图
    klines["MACD.open"] = 0.0
    klines["MACD.close"] = macd["bar"]
    klines["MACD.high"] = klines["MACD.close"].where(klines["MACD.close"] > 0, 0)
    klines["MACD.low"] = klines["MACD.close"].where(klines["MACD.close"] < 0, 0)
    klines["MACD.board"] = "MACD"
    # 在 board=MACD 上添加 diff、dea 线
    klines["diff"] = macd["diff"]
    klines["diff.board"] = "MACD"
    klines["diff.color"] = "gray"
    klines["dea"] = macd["dea"]
    klines["dea.board"] = "MACD"
    klines["dea.color"] = "rgb(255,128,0)"


api = TqApi(auth=TqAuth("信易账户", "账户密码"), web_gui=True)
klines = api.get_kline_serial("SHFE.rb2105", 5*60, 200)
while True:
    calc_macd_klines(klines)
    api.wait_update()
