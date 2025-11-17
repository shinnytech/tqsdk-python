#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Chaos"

from datetime import date
import numpy as np
import pandas as pd
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished
from tqsdk.ta import ATR

# ===== 全局参数设置 =====
SYMBOL = "CFFEX.IC2306"  # 螺纹钢期货合约
POSITION_SIZE = 30  # 固定交易手数
START_DATE = date(2022, 11, 1)  # 回测开始日期
END_DATE = date(2023, 4, 19)  # 回测结束日期

# 涡旋指标参数
VI_PERIOD = 14  # 涡旋指标周期
ATR_PERIOD = 14  # ATR指标周期
ATR_MULTIPLIER = 2.0  # 止损倍数
VI_THRESHOLD = 1.0  # VI值阈值，筛选强度较大的信号

# ===== 全局变量 =====
current_direction = 0   # 当前持仓方向：1=多头，-1=空头，0=空仓
entry_price = 0         # 开仓价格
stop_loss_price = 0     # 止损价格

# ===== 涡旋指标计算函数 =====
def calculate_vortex(df, period=14):
    """计算涡旋指标"""
    # 计算真实范围(TR)
    df['tr'] = np.maximum(
        np.maximum(
            df['high'] - df['low'],
            np.abs(df['high'] - df['close'].shift(1))
        ),
        np.abs(df['low'] - df['close'].shift(1))
    )

    # 计算正向涡旋运动(+VM)
    df['plus_vm'] = np.abs(df['high'] - df['low'].shift(1))

    # 计算负向涡旋运动(-VM)
    df['minus_vm'] = np.abs(df['low'] - df['high'].shift(1))

    # 计算N周期内的总和
    df['tr_sum'] = df['tr'].rolling(window=period).sum()
    df['plus_vm_sum'] = df['plus_vm'].rolling(window=period).sum()
    df['minus_vm_sum'] = df['minus_vm'].rolling(window=period).sum()

    # 计算涡旋指标
    df['plus_vi'] = df['plus_vm_sum'] / df['tr_sum']
    df['minus_vi'] = df['minus_vm_sum'] / df['tr_sum']

    return df

# ===== 策略开始 =====
print("开始运行涡旋指标(VI)期货策略...")

# 创建API实例
api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
            auth=TqAuth("快期账号", "快期密码"))

# 订阅合约的日K线数据
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
            if len(klines) < max(VI_PERIOD, ATR_PERIOD) + 5:
                continue

            # 计算涡旋指标
            df = pd.DataFrame(klines)
            df = calculate_vortex(df, VI_PERIOD)

            # 计算ATR
            atr_data = ATR(klines, ATR_PERIOD)
            current_atr = float(atr_data.atr.iloc[-1])

            # 获取最新和前一个周期的数据
            current_price = float(klines.close.iloc[-1])
            current_plus_vi = float(df.plus_vi.iloc[-1])
            current_minus_vi = float(df.minus_vi.iloc[-1])

            prev_plus_vi = float(df.plus_vi.iloc[-2])
            prev_minus_vi = float(df.minus_vi.iloc[-2])

            # 获取当前日期
            current_datetime = pd.to_datetime(klines.datetime.iloc[-1], unit='ns')
            date_str = current_datetime.strftime('%Y-%m-%d')

            # 输出调试信息
            print(f"日期: {date_str}, 价格: {current_price}, +VI: {current_plus_vi:.4f}, -VI: {current_minus_vi:.4f}, ATR: {current_atr:.2f}")

            # ===== 交易逻辑 =====

            # 空仓状态 - 寻找开仓机会
            if current_direction == 0:
                # 多头信号: +VI上穿-VI且+VI > 阈值
                if prev_plus_vi <= prev_minus_vi and current_plus_vi > current_minus_vi and current_plus_vi > VI_THRESHOLD:
                    # 设置入场价格
                    entry_price = current_price

                    # 设置止损价格
                    stop_loss_price = entry_price - ATR_MULTIPLIER * current_atr

                    # 设置持仓方向和目标持仓
                    current_direction = 1
                    target_pos.set_target_volume(POSITION_SIZE)

                    print(f"多头开仓: 价格={entry_price}, 手数={POSITION_SIZE}, 止损价={stop_loss_price:.2f}")

                # 空头信号: -VI上穿+VI且-VI > 阈值
                elif prev_minus_vi <= prev_plus_vi and current_minus_vi > current_plus_vi and current_minus_vi > VI_THRESHOLD:
                    # 设置入场价格
                    entry_price = current_price

                    # 设置止损价格
                    stop_loss_price = entry_price + ATR_MULTIPLIER * current_atr

                    # 设置持仓方向和目标持仓
                    current_direction = -1
                    target_pos.set_target_volume(-POSITION_SIZE)

                    print(f"空头开仓: 价格={entry_price}, 手数={POSITION_SIZE}, 止损价={stop_loss_price:.2f}")

            # 多头持仓 - 检查平仓条件
            elif current_direction == 1:
                # 条件1: 止损触发
                if current_price <= stop_loss_price:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止损平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")

                # 条件2: 信号反转 (-VI上穿+VI)
                elif prev_minus_vi <= prev_plus_vi and current_minus_vi > current_plus_vi:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头信号平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")

            # 空头持仓 - 检查平仓条件
            elif current_direction == -1:
                # 条件1: 止损触发
                if current_price >= stop_loss_price:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止损平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")

                # 条件2: 信号反转 (+VI上穿-VI)
                elif prev_plus_vi <= prev_minus_vi and current_plus_vi > current_minus_vi:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头信号平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")

except BacktestFinished as e:
    print(f"策略运行异常: {e}")
    api.close()
