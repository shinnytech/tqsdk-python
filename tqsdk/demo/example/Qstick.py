#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Chaos"

from datetime import date
import pandas as pd
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished
from tqsdk.ta import ATR

# ===== 全局参数设置 =====
SYMBOL = "CFFEX.IC2303"  # 中证500指数期货
POSITION_SIZE = 30  # 持仓手数
START_DATE = date(2022, 8, 1)  # 回测开始日期
END_DATE = date(2023, 1, 30)  # 回测结束日期

# Qstick指标参数
QSTICK_PERIOD = 10  # Qstick周期
SMA_PERIOD = 8  # 价格SMA周期，用于确认趋势

# 风控参数
ATR_PERIOD = 14  # ATR计算周期
STOP_LOSS_MULTIPLIER = 2.0  # 止损ATR倍数
MAX_HOLDING_DAYS = 5  # 最大持仓天数

# ===== 全局变量 =====
current_direction = 0  # 当前持仓方向：1=多头，-1=空头，0=空仓
entry_price = 0  # 开仓价格
stop_loss_price = 0  # 止损价格
entry_date = None  # 开仓日期


# ===== Qstick指标计算函数 =====
def calculate_qstick(open_prices, close_prices, period):
    """计算Qstick指标"""
    # 计算收盘价与开盘价的差值
    diff = close_prices - open_prices
    # 计算移动平均
    qstick = diff.rolling(window=period).mean()
    return qstick


# ===== 策略开始 =====
print("开始运行Qstick趋势指标期货策略...")

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
            if len(klines) < max(QSTICK_PERIOD, SMA_PERIOD, ATR_PERIOD) + 5:
                continue

            # 计算Qstick指标
            klines['qstick'] = calculate_qstick(klines.open, klines.close, QSTICK_PERIOD)

            # 计算价格SMA，用于确认趋势
            klines['price_sma'] = klines.close.rolling(window=SMA_PERIOD).mean()

            # 计算ATR用于设置止损
            atr_data = ATR(klines, ATR_PERIOD)

            # 获取最新数据
            current_price = float(klines.close.iloc[-1])
            current_datetime = pd.to_datetime(klines.datetime.iloc[-1], unit='ns')
            current_qstick = float(klines.qstick.iloc[-1])
            previous_qstick = float(klines.qstick.iloc[-2])
            current_price_sma = float(klines.price_sma.iloc[-1])
            current_atr = float(atr_data.atr.iloc[-1])

            # 输出调试信息
            print(f"日期: {current_datetime.strftime('%Y-%m-%d')}, 价格: {current_price:.2f}")
            print(f"Qstick: {current_qstick:.4f}")

            # ===== 交易逻辑 =====

            # 空仓状态 - 寻找开仓机会
            if current_direction == 0:
                # 多头开仓条件：Qstick从负值向上穿越零轴，价格在SMA上方
                if previous_qstick < 0 and current_qstick > 0 and current_price > current_price_sma:
                    current_direction = 1
                    target_pos.set_target_volume(POSITION_SIZE)
                    entry_price = current_price
                    entry_date = current_datetime

                    # 设置止损价格
                    stop_loss_price = entry_price - STOP_LOSS_MULTIPLIER * current_atr

                    print(f"多头开仓: 价格={entry_price}, 止损={stop_loss_price:.2f}")

                # 空头开仓条件：Qstick从正值向下穿越零轴，价格在SMA下方
                elif previous_qstick > 0 and current_qstick < 0 and current_price < current_price_sma:
                    current_direction = -1
                    target_pos.set_target_volume(-POSITION_SIZE)
                    entry_price = current_price
                    entry_date = current_datetime

                    # 设置止损价格
                    stop_loss_price = entry_price + STOP_LOSS_MULTIPLIER * current_atr

                    print(f"空头开仓: 价格={entry_price}, 止损={stop_loss_price:.2f}")

            # 多头持仓 - 检查平仓条件
            elif current_direction == 1:
                # 计算持仓天数
                holding_days = (current_datetime - entry_date).days

                # 1. 止损条件：价格低于止损价格
                if current_price <= stop_loss_price:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止损平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%, 持仓天数={holding_days}")

                # 2. 反向信号平仓：Qstick从正值向下穿越零轴
                elif previous_qstick > 0 and current_qstick < 0:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头信号平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%, 持仓天数={holding_days}")

                # 3. 时间止损：持仓时间过长
                elif holding_days >= MAX_HOLDING_DAYS:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头时间平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%, 持仓天数={holding_days}")

            # 空头持仓 - 检查平仓条件
            elif current_direction == -1:
                # 计算持仓天数
                holding_days = (current_datetime - entry_date).days

                # 1. 止损条件：价格高于止损价格
                if current_price >= stop_loss_price:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止损平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%, 持仓天数={holding_days}")

                # 2. 反向信号平仓：Qstick从负值向上穿越零轴
                elif previous_qstick < 0 and current_qstick > 0:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头信号平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%, 持仓天数={holding_days}")

                # 3. 时间止损：持仓时间过长
                elif holding_days >= MAX_HOLDING_DAYS:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头时间平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%, 持仓天数={holding_days}")

except BacktestFinished as e:
    print("回测结束")
    api.close()