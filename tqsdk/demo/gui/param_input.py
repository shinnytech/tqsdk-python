#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

"""
本程序演示如何为策略程序增加一个GUI参数输入框, 方便用户在运行策略前输入运行参数
"""

import PySimpleGUI as sg
from tqsdk import TqApi, TargetPosTask, TqAccount
from tqsdk.tafunc import ma

# 创建一个参数输入对话框
layout = [[sg.Text('交易账户')],
          [sg.Text('期货公司'), sg.Input("快期模拟", key="broker_id")],
          [sg.Text('账号'), sg.Input("111", key="user_id")],
          [sg.Text('密码'), sg.Input("111", key="password")],
          [sg.Text('策略参数')],
          [sg.Text('合约代码'), sg.Input("SHFE.bu1912", key="symbol")],
          [sg.Text('短周期'), sg.Input(30, key="short")],
          [sg.Text('长周期'), sg.Input(60, key="long")],
          [sg.OK(), sg.Cancel()]]
window = sg.Window('请输入策略运行参数', layout)

# 读取用户输入值
event, values = window.Read()
print(event, values)
window.close()


# 正常运行策略代码
SHORT = int(values["short"])  # 短周期
LONG = int(values["long"])  # 长周期
SYMBOL = values["symbol"]

api = TqApi(TqAccount(values["broker_id"], values["user_id"], values["password"]))
print("策略开始运行")

data_length = LONG + 2  # k线数据长度
klines = api.get_kline_serial(SYMBOL, duration_seconds=60, data_length=data_length)
target_pos = TargetPosTask(api, SYMBOL)

while True:
    api.wait_update()

    if api.is_changing(klines.iloc[-1], "datetime"):  # 产生新k线:重新计算SMA
        short_avg = ma(klines["close"], SHORT)  # 短周期
        long_avg = ma(klines["close"], LONG)  # 长周期

        # 均线下穿，做空
        if long_avg.iloc[-2] < short_avg.iloc[-2] and long_avg.iloc[-1] > short_avg.iloc[-1]:
            target_pos.set_target_volume(-3)
            print("均线下穿，做空")

        # 均线上穿，做多
        if short_avg.iloc[-2] < long_avg.iloc[-2] and short_avg.iloc[-1] > long_avg.iloc[-1]:
            target_pos.set_target_volume(3)
            print("均线上穿，做多")

