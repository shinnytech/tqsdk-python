#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

'''
菲阿里四价(日内突破策略, 在每日收盘前对所持合约进行平仓)

注:
demo仅用于示范如何使用TqSdk获取行情及编写策略程序
若需实际应用, 需要用户根据自己的交易经验进行修改
'''

from tqsdk import TqApi, TqSim, TargetPosTask
from datetime import datetime
import time

symbol = "SHFE.cu1905"  # 合约代码
close_hour, close_minute = 14, 50  # 平仓时间

api = TqApi(TqSim())  # 使用模拟帐号直连行情和交易服务器
quote = api.get_quote(symbol)  # 获取指定合约的盘口行情
klines = api.get_kline_serial(symbol, 24 * 60 * 60)  # 获取日线
position = api.get_position(symbol)  # 持仓信息
target_pos = TargetPosTask(api, symbol)  # 目标持仓

top_rail = klines.high.iloc[-2]  # 上轨: 昨日高点
bottom_rail = klines.low.iloc[-2]  # 下轨: 昨日低点
print("上轨:", top_rail, ",下轨:", bottom_rail, ",昨日收盘价:", klines.close.iloc[-2], ",今日开盘价:", klines.open.iloc[-1])

while True:
    api.wait_update()
    if api.is_changing(klines.iloc[-1], "datetime"):  # 如果产生一根新日线 (即到达下一个交易日): 重新获取上下轨
        top_rail = klines.high.iloc[-2]
        bottom_rail = klines.low.iloc[-2]
        print("上轨:", top_rail, ",下轨:", bottom_rail, ",昨日收盘价:", klines.close.iloc[-2], ",今日开盘价:", klines.open.iloc[-1])

    if api.is_changing(quote, "last_price"):  # 如果行情最新价发生变化
        print("当前最新价", quote["last_price"])
        # 开仓突破
        if quote["last_price"] > top_rail and position["volume_long"] == 0:  # 如果价格突破上轨: 买入开仓
            print("最新价:", quote["last_price"], ", 价格突破上轨,买入开仓")
            target_pos.set_target_volume(3)  # 设置目标持仓手数，将指定合约调整到目标头寸
        elif quote["last_price"] < bottom_rail and position["volume_short"] == 0:  # 如果价格跌破下轨: 卖出开仓
            print("最新价:", quote["last_price"], ", 价格跌破下轨, 卖出开仓")
            target_pos.set_target_volume(-3)

        # 平仓止损: 当价格 向上突破上轨 或 向下突破下轨 后, 再次回破当日开盘价
        if (quote["highest"] > top_rail and quote["last_price"] <= quote["open"]) or (
                quote["lowest"] < bottom_rail and quote["last_price"] >= quote["open"]):
            print("平仓止损")
            target_pos.set_target_volume(0)

    if api.is_changing(quote, "datetime"):
        now_time = datetime.strptime(quote["datetime"], "%Y-%m-%d %H:%M:%S.%f")  # 获取当前的行情时间
        if now_time.hour == close_hour and now_time.minute >= close_minute:  # 到达平仓时间: 平仓
            print("临近本交易日收盘: 平仓")
            target_pos.set_target_volume(0)
            deadline = time.time() + 60  # 设置截止时间为当前时间的60秒以后
            while api.wait_update(deadline=deadline):  # 等待60秒
                pass
            api.close()  # 关闭api
            break  # 退出while循环
