#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Chaos"

from datetime import date
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished
from tqsdk.tafunc import time_to_str

# ===== 全局参数设置 =====
SYMBOL = "SHFE.cu2309"
POSITION_SIZE = 100
START_DATE = date(2023, 2, 10)  # 回测开始日期
END_DATE = date(2023, 3, 15)  # 回测结束日期

# 策略参数
REVERSAL_CONFIRM = 50  # 反转确认点数
STOP_LOSS_POINTS = 100  # 止损点数

# ===== 全局变量 =====
current_direction = 0  # 当前持仓方向：1=多头，-1=空头，0=空仓
entry_price = 0  # 开仓价格
stop_loss_price = 0  # 止损价格
prev_high = 0  # 前一日最高价
prev_low = 0  # 前一日最低价
prev_close = 0  # 前一日收盘价

# ===== 策略开始 =====
print("开始运行枢轴点反转策略...")

# 创建API实例
api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
            auth=TqAuth("快期账号", "快期密码"))

# 订阅合约的K线数据
klines = api.get_kline_serial(SYMBOL, 60 * 60 * 24)  # 日线数据

# 创建目标持仓任务
target_pos = TargetPosTask(api, SYMBOL)

def calculate_pivot_points(high, low, close):
    """计算枢轴点及支撑阻力位"""
    pivot = (high + low + close) / 3
    r1 = (2 * pivot) - low
    s1 = (2 * pivot) - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    r3 = r1 + (high - low)
    s3 = s1 - (high - low)
    return pivot, r1, r2, r3, s1, s2, s3

try:
    while True:
        # 等待更新
        api.wait_update()

        # 如果K线有更新
        if api.is_changing(klines.iloc[-1], "datetime"):
            # 确保有足够的数据
            if len(klines) < 2:
                continue

            # 获取当前价格和前一日数据
            current_price = klines.close.iloc[-1].item()
            current_high = klines.high.iloc[-1].item()
            current_low = klines.low.iloc[-1].item()
            prev_close = klines.close.iloc[-2].item()

            # 如果是新的一天，更新前一日数据
            if klines.datetime.iloc[-1] != klines.datetime.iloc[-2]:
                prev_high = klines.high.iloc[-2].item()
                prev_low = klines.low.iloc[-2].item()
                prev_close = klines.close.iloc[-2].item()
                print(f"\n新的一天开始:")
                print(f"前一日数据 - 最高价: {prev_high:.2f}, 最低价: {prev_low:.2f}, 收盘价: {prev_close:.2f}")

            # 计算枢轴点及支撑阻力位
            pivot, r1, r2, r3, s1, s2, s3 = calculate_pivot_points(prev_high, prev_low, prev_close)

            # 获取最新数据
            current_timestamp = klines.datetime.iloc[-1]
            current_datetime = time_to_str(current_timestamp)

            # 打印当前状态
            print(f"\n日期: {current_datetime}")
            print(f"当前价格: {current_price:.2f}")
            print(f"枢轴点: {pivot:.2f}")
            print(f"支撑位: S1={s1:.2f}, S2={s2:.2f}, S3={s3:.2f}")
            print(f"阻力位: R1={r1:.2f}, R2={r2:.2f}, R3={r3:.2f}")

            # 打印信号条件
            print("\n多头信号条件:")
            print(f"1. 价格在S1附近: {current_price <= s1 + REVERSAL_CONFIRM and current_price > s1 - REVERSAL_CONFIRM}")
            print(f"2. 价格高于当日最低价: {current_price > klines.low.iloc[-1].item()}")
            print(f"3. 价格高于前一日收盘价: {current_price > prev_close}")

            print("\n空头信号条件:")
            print(f"1. 价格在R1附近: {current_price >= r1 - REVERSAL_CONFIRM and current_price < r1 + REVERSAL_CONFIRM}")
            print(f"2. 价格低于当日最高价: {current_price < klines.high.iloc[-1].item()}")
            print(f"3. 价格低于前一日收盘价: {current_price < prev_close}")

            # ===== 交易逻辑 =====

            # 空仓状态 - 寻找开仓机会
            if current_direction == 0:
                # 多头开仓条件：价格低于S1
                if current_price < s1:
                    current_direction = 1
                    target_pos.set_target_volume(POSITION_SIZE)
                    entry_price = current_price
                    stop_loss_price = entry_price - STOP_LOSS_POINTS
                    print(f"\n多头开仓信号! 开仓价: {entry_price:.2f}, 止损价: {stop_loss_price:.2f}")

                # 空头开仓条件：价格高于R1
                elif current_price > r1:
                    current_direction = -1
                    target_pos.set_target_volume(-POSITION_SIZE)
                    entry_price = current_price
                    stop_loss_price = entry_price + STOP_LOSS_POINTS
                    print(f"\n空头开仓信号! 开仓价: {entry_price:.2f}, 止损价: {stop_loss_price:.2f}")

            # 多头持仓 - 检查平仓条件
            elif current_direction == 1:
                # 止盈条件：价格回到枢轴点或更高
                if current_price >= pivot:
                    profit = (current_price - entry_price) * POSITION_SIZE
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止盈平仓: 价格={current_price:.2f}, 盈利={profit:.2f}")
                # 止损条件
                elif current_price <= stop_loss_price:
                    loss = (entry_price - current_price) * POSITION_SIZE
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止损平仓: 价格={current_price:.2f}, 亏损={loss:.2f}")

            # 空头持仓 - 检查平仓条件
            elif current_direction == -1:
                # 止盈条件：价格回到枢轴点或更低
                if current_price <= pivot:
                    profit = (entry_price - current_price) * POSITION_SIZE
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止盈平仓: 价格={current_price:.2f}, 盈利={profit:.2f}")
                # 止损条件
                elif current_price >= stop_loss_price:
                    loss = (current_price - entry_price) * POSITION_SIZE
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止损平仓: 价格={current_price:.2f}, 亏损={loss:.2f}")

except BacktestFinished as e:
    print("回测结束")
    api.close()