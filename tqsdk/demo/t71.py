#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'yanqiong'

from tqsdk.api import TqApi
from tqsdk.lib import TargetPosTask

'''
连续3根阴线就做空，连续3根阳线就做多，否则空仓
'''

api = TqApi("SIM")
# 设定连续多少根阳线/阴线
length = 3
# 获得 rb1901 10秒K线的引用, 长度为 length+1
klines = api.get_kline_serial("SHFE.rb1901", 10, data_length = length + 1)
# 创建 rb1901 的目标持仓 task，该 task 负责调整 rb1901 的仓位到指定的目标仓位, offset_priority的用法详见文档
target_pos = TargetPosTask(api, "SHFE.rb1901", offset_priority="今昨开")

while True:
    api.wait_update()
    # 只有在新创建出K线时才判断开平仓条件
    if api.is_changing(klines[-1], "datetime"):
        # 将K线转为pandas.DataFrame, 跳过最后一根刚生成的K线
        df = klines.to_dataframe()[:-1]
        # 比较收盘价和开盘价，判断是阳线还是阴线
        # df["close"] 为收盘价序列, df["open"] 为开盘价序列, ">"(pandas.Series.gt) 返回收盘价是否大于开盘价的一个新序列
        up = df["close"] > df["open"]
        down = df["close"] < df["open"]
        if all(up):
            print("连续阳线: 目标持仓 多头1手")
            # 设置目标持仓为正数表示多头，负数表示空头，0表示空仓
            target_pos.set_target_volume(1)
        elif all(down):
            print("连续阴线: 目标持仓 空头1手")
            target_pos.set_target_volume(-1)
        else:
            print("目标持仓: 空仓")
            target_pos.set_target_volume(0)
