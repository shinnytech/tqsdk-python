#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Chaos"

from datetime import date
import numpy as np
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished
from tqsdk.tafunc import time_to_str

# ===== 全局参数设置 =====
SYMBOL = "SHFE.au2106"
POSITION_SIZE = 50  # 每次交易手数
START_DATE = date(2020, 11, 1)  # 回测开始日期
END_DATE = date(2020, 12, 15)  # 回测结束日期

# Z-Score参数
WINDOW_SIZE = 14  # Z-Score计算窗口期
ENTRY_THRESHOLD = 1.8  # 开仓阈值
EXIT_THRESHOLD = 0.4  # 平仓阈值
STOP_LOSS_THRESHOLD = 2.5  # 止损阈值

# 风控参数
TIME_STOP_DAYS = 8  # 时间止损天数

# ===== 全局变量 =====
current_direction = 0  # 当前持仓方向：1=多头，-1=空头，0=空仓
entry_price = 0  # 开仓价格
entry_date = None  # 开仓日期

# ===== 策略开始 =====
print("开始运行Z-Score均值回归策略...")

# 创建API实例
api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
            auth=TqAuth("快期账号", "快期密码"))

# 订阅合约的K线数据
klines = api.get_kline_serial(SYMBOL, 60 * 60 * 24)  # 日线数据

# 创建目标持仓任务
target_pos = TargetPosTask(api, SYMBOL)

try:
    while True:
        # 等待更新
        api.wait_update()

        # 如果K线有更新
        if api.is_changing(klines.iloc[-1], "datetime"):
            # 确保有足够的数据计算指标
            if len(klines) < WINDOW_SIZE + 10:
                continue

            # 计算Z-Score
            prices = klines.close.iloc[-WINDOW_SIZE:]  # 获取最近20天的收盘价
            mean = np.mean(prices)  # 计算均值
            std = np.std(prices)  # 计算标准差
            current_price = float(klines.close.iloc[-1])  # 当前价格

            # 处理标准差为0的情况
            if std == 0:
                z_score = 0  # 如果标准差为0，说明所有价格都相同，Z-Score设为0
            else:
                z_score = (current_price - mean) / std  # 计算Z-Score

            # 获取最新数据
            current_timestamp = klines.datetime.iloc[-1]
            current_datetime = time_to_str(current_timestamp)

            # 打印当前状态
            print(f"日期: {current_datetime}, 价格: {current_price:.2f}, Z-Score: {z_score:.2f}")

            # ===== 交易逻辑 =====

            # 空仓状态 - 寻找开仓机会
            if current_direction == 0:
                # 多头开仓条件：Z-Score显著低于均值
                if z_score < -ENTRY_THRESHOLD:
                    current_direction = 1
                    target_pos.set_target_volume(POSITION_SIZE)
                    entry_price = current_price
                    entry_date = current_timestamp
                    print(f"多头开仓: 价格={entry_price:.2f}, Z-Score={z_score:.2f}")

                # 空头开仓条件：Z-Score显著高于均值
                elif z_score > ENTRY_THRESHOLD:
                    current_direction = -1
                    target_pos.set_target_volume(-POSITION_SIZE)
                    entry_price = current_price
                    entry_date = current_timestamp
                    print(f"空头开仓: 价格={entry_price:.2f}, Z-Score={z_score:.2f}")

            # 多头持仓 - 检查平仓条件
            elif current_direction == 1:
                # 止损条件：Z-Score继续大幅下跌
                if z_score < -STOP_LOSS_THRESHOLD:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止损平仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")

                # 止盈条件：Z-Score回归到均值附近
                elif -EXIT_THRESHOLD <= z_score <= EXIT_THRESHOLD:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止盈平仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")

                # 时间止损
                elif (current_timestamp - entry_date) / (60 * 60 * 24) >= TIME_STOP_DAYS:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头时间止损: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")

            # 空头持仓 - 检查平仓条件
            elif current_direction == -1:
                # 止损条件：Z-Score继续大幅上涨
                if z_score > STOP_LOSS_THRESHOLD:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止损平仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")

                # 止盈条件：Z-Score回归到均值附近
                elif -EXIT_THRESHOLD <= z_score <= EXIT_THRESHOLD:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止盈平仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")

                # 时间止损
                elif (current_timestamp - entry_date) / (60 * 60 * 24) >= TIME_STOP_DAYS:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头时间止损: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")

except BacktestFinished as e:
    print("回测结束")
    api.close()