#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Chaos"

from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished
from datetime import date
import numpy as np
import pandas as pd

# ===== 全局参数设置 =====
SYMBOL = "CFFEX.IC2306"  # 中证500指数期货合约
POSITION_SIZE = 30  # 持仓手数（黄金的合适仓位）
START_DATE = date(2022, 11, 1)  # 回测开始日期
END_DATE = date(2023, 4, 30)  # 回测结束日期

# Keltner Channel参数
EMA_PERIOD = 8  # EMA周期
ATR_PERIOD = 7  # ATR周期
ATR_MULTIPLIER = 1.5  # ATR乘数

# 新增参数 - 趋势确认与止损
SHORT_EMA_PERIOD = 5  # 短期EMA用于趋势确认
STOP_LOSS_PCT = 0.8  # 止损百分比（相对于ATR）
TRAILING_STOP = True  # 使用移动止损

print(f"开始回测 {SYMBOL} 的Keltner Channel策略...")
print(f"参数: EMA周期={EMA_PERIOD}, ATR周期={ATR_PERIOD}, ATR乘数={ATR_MULTIPLIER}")
print(f"额外参数: 短期EMA={SHORT_EMA_PERIOD}, 止损参数={STOP_LOSS_PCT}ATR, 移动止损={TRAILING_STOP}")

try:
    api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
                auth=TqAuth("快期账号", "快期密码"))

    # 订阅K线数据
    klines = api.get_kline_serial(SYMBOL, 60 * 60 * 24)  # 日K线
    # 订阅行情获取交易时间
    quote = api.get_quote(SYMBOL)
    target_pos = TargetPosTask(api, SYMBOL)

    # 初始化交易状态
    position = 0  # 当前持仓
    entry_price = 0  # 入场价格
    stop_loss = 0  # 止损价格
    high_since_entry = 0  # 入场后的最高价（用于移动止损）
    low_since_entry = 0  # 入场后的最低价（用于移动止损）
    trend_strength = 0  # 趋势强度

    # 记录交易信息
    trades = []

    while True:
        api.wait_update()

        if api.is_changing(klines):
            # 确保有足够的数据
            if len(klines) < max(EMA_PERIOD, ATR_PERIOD, SHORT_EMA_PERIOD) + 1:
                continue

            # 计算指标
            close = klines.close.values
            high = klines.high.values
            low = klines.low.values

            # 计算中轨（EMA）和短期EMA（用于趋势确认）
            ema = pd.Series(close).ewm(span=EMA_PERIOD, adjust=False).mean().values
            ema_short = pd.Series(close).ewm(span=SHORT_EMA_PERIOD, adjust=False).mean().values

            # 计算趋势方向和强度
            trend_direction = 1 if ema_short[-1] > ema[-1] else -1 if ema_short[-1] < ema[-1] else 0
            trend_strength = abs(ema_short[-1] - ema[-1]) / close[-1] * 100  # 趋势强度百分比

            # 计算ATR
            tr = np.maximum(high - low,
                            np.maximum(
                                np.abs(high - np.roll(close, 1)),
                                np.abs(low - np.roll(close, 1))
                            ))
            atr = pd.Series(tr).rolling(ATR_PERIOD).mean().values
            current_atr = float(atr[-1])

            # 动态调整ATR乘数，根据趋势强度调整通道宽度
            dynamic_multiplier = ATR_MULTIPLIER
            if trend_strength > 0.5:  # 强趋势时使用更窄的通道
                dynamic_multiplier = ATR_MULTIPLIER * 0.8

            # 计算通道上下轨
            upper_band = ema + dynamic_multiplier * atr
            lower_band = ema - dynamic_multiplier * atr

            # 获取当前价格和指标值
            current_price = float(close[-1])
            current_upper = float(upper_band[-1])
            current_lower = float(lower_band[-1])
            current_ema = float(ema[-1])
            current_time = quote.datetime  # 使用quote的datetime获取当前时间

            # 更新入场后的最高/最低价
            if position > 0:
                high_since_entry = max(high_since_entry, current_price)
                # 更新移动止损
                if TRAILING_STOP and high_since_entry > entry_price:
                    trailing_stop = high_since_entry * (1 - STOP_LOSS_PCT * current_atr / current_price)
                    stop_loss = max(stop_loss, trailing_stop)
            elif position < 0:
                low_since_entry = min(low_since_entry, current_price)
                # 更新移动止损
                if TRAILING_STOP and low_since_entry < entry_price:
                    trailing_stop = low_since_entry * (1 + STOP_LOSS_PCT * current_atr / current_price)
                    stop_loss = min(stop_loss if stop_loss > 0 else float('inf'), trailing_stop)

            # 交易逻辑
            if position == 0:  # 空仓
                # 确认趋势方向并突破通道
                if current_price > current_upper and trend_direction > 0:
                    # 增加成交量过滤
                    position = POSITION_SIZE
                    entry_price = current_price
                    high_since_entry = current_price
                    low_since_entry = current_price
                    # 设置初始止损
                    stop_loss = current_price * (1 - STOP_LOSS_PCT * current_atr / current_price)
                    target_pos.set_target_volume(position)
                    print(f"开多仓: 价格={current_price:.2f}, 上轨={current_upper:.2f}, 止损={stop_loss:.2f}")
                    trades.append(("开多", current_time, current_price))

                elif current_price < current_lower and trend_direction < 0:
                    position = -POSITION_SIZE
                    entry_price = current_price
                    high_since_entry = current_price
                    low_since_entry = current_price
                    # 设置初始止损
                    stop_loss = current_price * (1 + STOP_LOSS_PCT * current_atr / current_price)
                    target_pos.set_target_volume(position)
                    print(f"开空仓: 价格={current_price:.2f}, 下轨={current_lower:.2f}, 止损={stop_loss:.2f}")
                    trades.append(("开空", current_time, current_price))

            elif position > 0:  # 持有多头
                # 止损、回落到中轨或趋势转向时平仓
                if (current_price <= stop_loss or
                        current_price <= current_ema or
                        (current_price < current_lower and trend_direction < 0)):
                    profit_pct = (current_price / entry_price - 1) * 100
                    profit_points = current_price - entry_price
                    target_pos.set_target_volume(0)
                    print(f"平多仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%, {profit_points:.2f}点")
                    position = 0
                    entry_price = 0
                    stop_loss = 0
                    trades.append(("平多", current_time, current_price))

            elif position < 0:  # 持有空头
                # 止损、回升到中轨或趋势转向时平仓
                if (current_price >= stop_loss or
                        current_price >= current_ema or
                        (current_price > current_upper and trend_direction > 0)):
                    profit_pct = (entry_price / current_price - 1) * 100
                    profit_points = entry_price - current_price
                    target_pos.set_target_volume(0)
                    print(f"平空仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%, {profit_points:.2f}点")
                    position = 0
                    entry_price = 0
                    stop_loss = 0
                    trades.append(("平空", current_time, current_price))

except BacktestFinished as e:
    print(f"回测完成: {e}")
    api.close()