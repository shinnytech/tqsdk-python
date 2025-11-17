#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Chaos"

from datetime import date
import pandas as pd
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished
from tqsdk.ta import ATR

# ===== 全局参数设置 =====
SYMBOL = "CFFEX.IC2306"  # 黄金期货合约
POSITION_SIZE = 30  # 基础持仓手数
START_DATE = date(2022, 11, 1)  # 回测开始日期
END_DATE = date(2023, 4, 30)  # 回测结束日期

# TRIX指标参数
TRIX_PERIOD = 12  # TRIX计算周期
SIGNAL_PERIOD = 9  # 信号线计算周期
MA_PERIOD = 60    # 长期移动平均线周期，用于趋势过滤

# 信号阈值参数
SIGNAL_THRESHOLD = 0.05  # TRIX与信号线差值的阈值，避免微小交叉

# 风控参数
ATR_PERIOD = 14  # ATR计算周期
STOP_LOSS_MULTIPLIER = 2.0  # 止损ATR倍数
TAKE_PROFIT_MULTIPLIER = 3.0  # 止盈ATR倍数
MAX_HOLDING_DAYS = 15  # 最大持仓天数

# ===== 全局变量 =====
current_direction = 0  # 当前持仓方向：1=多头，-1=空头，0=空仓
entry_price = 0  # 开仓价格
stop_loss_price = 0  # 止损价格
entry_date = None  # 开仓日期
trade_count = 0  # 交易次数
win_count = 0  # 盈利次数

# ===== TRIX指标计算函数 =====
def calculate_trix(close_prices, period):
    """计算TRIX指标和信号线"""
    # 第一重EMA
    ema1 = close_prices.ewm(span=period, adjust=False).mean()
    # 第二重EMA
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    # 第三重EMA
    ema3 = ema2.ewm(span=period, adjust=False).mean()
    # 计算TRIX
    trix = 100 * (ema3 / ema3.shift(1) - 1)
    # 计算信号线
    signal = trix.rolling(SIGNAL_PERIOD).mean()
    
    return trix, signal

# ===== 策略开始 =====
print("开始运行TRIX指标期货策略...")
print(f"品种: {SYMBOL}, 回测周期: {START_DATE} - {END_DATE}")
print(f"TRIX参数: 周期={TRIX_PERIOD}, 信号线周期={SIGNAL_PERIOD}")

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
            if len(klines) < max(TRIX_PERIOD, SIGNAL_PERIOD, MA_PERIOD, ATR_PERIOD) + 10:
                continue
                
            # 计算TRIX指标和信号线
            klines['trix'], klines['signal'] = calculate_trix(klines.close, TRIX_PERIOD)
            
            # 计算长期移动平均线，用于趋势过滤
            klines['ma'] = klines.close.rolling(window=MA_PERIOD).mean()
            
            # 计算ATR用于设置止损
            atr_data = ATR(klines, ATR_PERIOD)
            
            # 获取最新数据
            current_price = float(klines.close.iloc[-1])
            current_datetime = pd.to_datetime(klines.datetime.iloc[-1], unit='ns')
            current_trix = float(klines.trix.iloc[-1])
            previous_trix = float(klines.trix.iloc[-2])
            current_signal = float(klines.signal.iloc[-1])
            previous_signal = float(klines.signal.iloc[-2])
            current_ma = float(klines.ma.iloc[-1])
            current_atr = float(atr_data.atr.iloc[-1])
            
            # 计算TRIX与信号线的差值
            trix_diff = current_trix - current_signal
            previous_trix_diff = previous_trix - previous_signal
            
            # 输出调试信息
            print(f"日期: {current_datetime.strftime('%Y-%m-%d')}, 价格: {current_price:.2f}")
            print(f"TRIX: {current_trix:.4f}, 信号线: {current_signal:.4f}, 差值: {trix_diff:.4f}")
            
            # ===== 交易逻辑 =====
            
            # 空仓状态 - 寻找开仓机会
            if current_direction == 0:
                # 多头开仓条件：TRIX上穿信号线
                if previous_trix < previous_signal and current_trix > current_signal:
                    current_direction = 1
                    target_pos.set_target_volume(POSITION_SIZE)
                    entry_price = current_price
                    stop_loss_price = entry_price - STOP_LOSS_MULTIPLIER * current_atr
                    take_profit_price = entry_price + TAKE_PROFIT_MULTIPLIER * current_atr
                    print(f"多头开仓: 价格={entry_price}, 止损={stop_loss_price:.2f}, 止盈={take_profit_price:.2f}")
                
                # 空头开仓条件：TRIX下穿信号线
                elif previous_trix > previous_signal and current_trix < current_signal:
                    current_direction = -1
                    target_pos.set_target_volume(-POSITION_SIZE)
                    entry_price = current_price
                    stop_loss_price = entry_price + STOP_LOSS_MULTIPLIER * current_atr
                    take_profit_price = entry_price - TAKE_PROFIT_MULTIPLIER * current_atr
                    print(f"空头开仓: 价格={entry_price}, 止损={stop_loss_price:.2f}, 止盈={take_profit_price:.2f}")
            
            # 多头持仓 - 检查平仓条件
            elif current_direction == 1:
                # 止损条件
                if current_price <= stop_loss_price:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止损平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")
                
                # 止盈条件
                elif current_price >= take_profit_price:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止盈平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")
                
                # 信号平仓：TRIX下穿信号线
                elif previous_trix > previous_signal and current_trix < current_signal:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头信号平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")
            
            # 空头持仓 - 检查平仓条件
            elif current_direction == -1:
                # 止损条件
                if current_price >= stop_loss_price:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止损平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")
                
                # 止盈条件
                elif current_price <= take_profit_price:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止盈平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")
                
                # 信号平仓：TRIX上穿信号线
                elif previous_trix < previous_signal and current_trix > current_signal:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头信号平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")

except BacktestFinished as e:
    print("回测结束")
    api.close()
