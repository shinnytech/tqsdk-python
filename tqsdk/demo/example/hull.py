#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Chaos"

from datetime import date

import numpy as np
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished
from tqsdk.ta import ATR

# ===== 全局参数设置 =====
SYMBOL = "SHFE.au2306"  # 黄金期货合约
POSITION_SIZE = 30  # 单次交易手数
START_DATE = date(2022, 11, 1)  # 回测开始日期
END_DATE = date(2023, 4, 1)  # 回测结束日期

# Hull Moving Average 参数
LONG_HMA_PERIOD = 30  # 长周期HMA，用于确定大趋势
SHORT_HMA_PERIOD = 5  # 短周期HMA，用于入场信号

# 止损止盈参数
ATR_PERIOD = 14  # ATR计算周期
STOP_LOSS_ATR = 2.0  # 止损为入场点的2倍ATR
TAKE_PROFIT_ATR = 4.0  # 获利为入场点的4倍ATR
TRAILING_STOP = True  # 使用移动止损

# 新增止盈参数
FIXED_TAKE_PROFIT_PCT = 0.03  # 固定止盈比例（3%）
USE_TRAILING_PROFIT = True  # 是否使用追踪止盈
TRAILING_PROFIT_THRESHOLD = 0.02  # 触发追踪止盈的收益率阈值（2%）
TRAILING_PROFIT_STEP = 0.005  # 追踪止盈回撤幅度（0.5%）

# ===== 全局变量 =====
current_direction = 0   # 当前持仓方向：1=多头，-1=空头，0=空仓
entry_price = 0         # 开仓价格
stop_loss_price = 0     # 止损价格
take_profit_price = 0   # 止盈价格
highest_since_entry = 0 # 入场后的最高价（用于多头追踪止盈）
lowest_since_entry = 0  # 入场后的最低价（用于空头追踪止盈）

# ===== Hull移动平均线相关函数 =====
def wma(series, period):
    """计算加权移动平均线"""
    weights = np.arange(1, period + 1)
    return series.rolling(period).apply(lambda x: np.sum(weights * x) / weights.sum(), raw=True)

def hma(series, period):
    """计算Hull移动平均线"""
    period = int(period)
    if period < 3:
        return series
    
    half_period = period // 2
    sqrt_period = int(np.sqrt(period))
    
    wma1 = wma(series, half_period)
    wma2 = wma(series, period)
    
    raw_hma = 2 * wma1 - wma2
    
    return wma(raw_hma, sqrt_period)

# ===== 策略开始 =====
print("开始运行Hull移动平均线期货策略...")

# 创建API实例
api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
            auth=TqAuth("快期账号", "快期密码"))

# 订阅合约的K线数据
klines = api.get_kline_serial(SYMBOL, 60 * 60 * 24)

# 创建目标持仓任务
target_pos = TargetPosTask(api, SYMBOL)

try:
    while True:
        # 等待更新
        api.wait_update()
        
        # 如果K线有更新
        if api.is_changing(klines.iloc[-1], "datetime"):
            # 确保有足够的数据计算指标
            if len(klines) < max(SHORT_HMA_PERIOD, LONG_HMA_PERIOD, ATR_PERIOD) + 10:
                continue
                
            # 计算短期和长期HMA
            klines['short_hma'] = hma(klines.close, SHORT_HMA_PERIOD)
            klines['long_hma'] = hma(klines.close, LONG_HMA_PERIOD)
            
            # 计算ATR用于止损设置
            atr_data = ATR(klines, ATR_PERIOD)
            
            # 获取最新数据
            current_price = float(klines.close.iloc[-1])
            current_short_hma = float(klines.short_hma.iloc[-1])
            current_long_hma = float(klines.long_hma.iloc[-1])
            current_atr = float(atr_data.atr.iloc[-1])
            
            # 获取前一个周期的数据
            prev_short_hma = float(klines.short_hma.iloc[-2])
            prev_long_hma = float(klines.long_hma.iloc[-2])
            
            # 输出调试信息
            print(f"价格: {current_price}, 短期HMA: {current_short_hma:.2f}, 长期HMA: {current_long_hma:.2f}")
            
            # ===== 交易逻辑 =====
            
            # 空仓状态 - 寻找开仓机会
            if current_direction == 0:
                # 多头开仓条件
                if (prev_short_hma <= prev_long_hma and current_short_hma > current_long_hma
                        and current_price > current_long_hma):
                    
                    print(f"多头开仓信号: 短期HMA上穿长期HMA")
                    
                    # 设置持仓和记录开仓价格
                    current_direction = 1
                    target_pos.set_target_volume(POSITION_SIZE)
                    entry_price = current_price
                    
                    # 设置止损价格
                    stop_loss_price = current_long_hma - STOP_LOSS_ATR * current_atr
                    
                    # 设置止盈价格
                    take_profit_price = entry_price * (1 + FIXED_TAKE_PROFIT_PCT)
                    
                    # 重置追踪止盈变量
                    highest_since_entry = entry_price
                    
                    print(f"多头开仓价格: {entry_price}, 止损: {stop_loss_price:.2f}, 止盈: {take_profit_price:.2f}")
                
                # 空头开仓条件
                elif (prev_short_hma >= prev_long_hma and current_short_hma < current_long_hma
                      and current_price < current_long_hma):
                    
                    print(f"空头开仓信号: 短期HMA下穿长期HMA")
                    
                    # 设置持仓和记录开仓价格
                    current_direction = -1
                    target_pos.set_target_volume(-POSITION_SIZE)
                    entry_price = current_price
                    
                    # 设置止损价格
                    stop_loss_price = current_long_hma + STOP_LOSS_ATR * current_atr
                    
                    # 设置止盈价格
                    take_profit_price = entry_price * (1 - FIXED_TAKE_PROFIT_PCT)
                    
                    # 重置追踪止盈变量
                    lowest_since_entry = entry_price
                    
                    print(f"空头开仓价格: {entry_price}, 止损: {stop_loss_price:.2f}, 止盈: {take_profit_price:.2f}")
            
            # 多头持仓 - 检查平仓条件
            elif current_direction == 1:
                # 更新入场后的最高价
                if current_price > highest_since_entry:
                    highest_since_entry = current_price
                
                # 计算固定止损
                fixed_stop_loss = entry_price * (1 - STOP_LOSS_ATR)
                
                # 更新追踪止损（只上移不下移）
                new_stop = current_short_hma - STOP_LOSS_ATR * current_atr
                if new_stop > stop_loss_price:
                    stop_loss_price = new_stop
                    print(f"更新多头止损: {stop_loss_price:.2f}")
                
                # 平仓条件1: 短期HMA下穿长期HMA
                if prev_short_hma >= prev_long_hma and current_short_hma < current_long_hma:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")
                
                # 平仓条件2: 价格跌破止损
                elif current_price < stop_loss_price or current_price < fixed_stop_loss:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止损: 价格={current_price}, 盈亏={profit_pct:.2f}%")
                
                # 平仓条件3: 价格达到止盈价格
                elif current_price >= take_profit_price:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止盈: 价格={current_price}, 盈亏={profit_pct:.2f}%")
            
            # 空头持仓 - 检查平仓条件
            elif current_direction == -1:
                # 更新入场后的最低价
                if current_price < lowest_since_entry or lowest_since_entry == 0:
                    lowest_since_entry = current_price
                
                # 计算固定止损
                fixed_stop_loss = entry_price * (1 + STOP_LOSS_ATR)
                
                # 更新追踪止损（只下移不上移）
                new_stop = current_short_hma + STOP_LOSS_ATR * current_atr
                if new_stop < stop_loss_price or stop_loss_price == 0:
                    stop_loss_price = new_stop
                    print(f"更新空头止损: {stop_loss_price:.2f}")
                
                # 平仓条件1: 短期HMA上穿长期HMA
                if prev_short_hma <= prev_long_hma and current_short_hma > current_long_hma:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")
                
                # 平仓条件2: 价格突破止损
                elif current_price > stop_loss_price or current_price > fixed_stop_loss:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止损: 价格={current_price}, 盈亏={profit_pct:.2f}%")
                
                # 平仓条件3: 价格达到止盈价格
                elif current_price <= take_profit_price:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止盈: 价格={current_price}, 盈亏={profit_pct:.2f}%")

except BacktestFinished as e:
    print("回测结束")
    api.close()
