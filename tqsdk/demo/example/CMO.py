#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Chaos"

from datetime import date
import numpy as np
import pandas as pd
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished
from tqsdk.ta import ATR

# ===== 全局参数设置 =====
SYMBOL = "DCE.c2309"  # 玉米期货合约
POSITION_SIZE = 500  # 基础持仓手数
START_DATE = date(2023, 2, 1)  # 回测开始日期
END_DATE = date(2023, 7, 31)  # 回测结束日期

# CMO参数设置
CMO_PERIOD = 6  # CMO计算周期
SIGNAL_PERIOD = 4  # CMO信号线周期
CMO_SLOPE_PERIOD = 2  # CMO斜率计算周期
OVERBOUGHT_THRESHOLD = 50  # 超买阈值
OVERSOLD_THRESHOLD = -50  # 超卖阈值
SMA_PERIOD = 10  # 趋势确认移动平均线周期

# 止损止盈参数
FIXED_STOP_LOSS_PCT = 0.008  # 固定止损百分比(0.8%)
TAKE_PROFIT_PCT = 0.015  # 止盈百分比(1.5%)
ATR_STOP_MULTIPLIER = 2.0  # ATR止损乘数
MAX_HOLDING_DAYS = 10  # 最大持仓天数

# ===== 全局变量 =====
current_direction = 0   # 当前持仓方向：1=多头，-1=空头，0=空仓
entry_price = 0         # 开仓价格
stop_loss_price = 0     # 止损价格
take_profit_price = 0   # 止盈价格
entry_date = None       # 开仓日期
entry_position = 0      # 开仓数量

# ===== CMO指标计算函数 =====
def calculate_cmo(close_prices, period=14):
    """计算钱德动量震荡指标(CMO)"""
    delta = close_prices.diff()
    
    # 分离上涨和下跌
    up_sum = np.zeros_like(delta)
    down_sum = np.zeros_like(delta)
    
    # 填充上涨和下跌数组
    up_sum[delta > 0] = delta[delta > 0]
    down_sum[delta < 0] = -delta[delta < 0]  # 注意要取绝对值
    
    # 计算上涨和下跌的滚动总和
    up_rolling_sum = pd.Series(up_sum).rolling(period).sum()
    down_rolling_sum = pd.Series(down_sum).rolling(period).sum()
    
    # 计算CMO值
    cmo = 100 * ((up_rolling_sum - down_rolling_sum) / (up_rolling_sum + down_rolling_sum))
    
    return cmo

# ===== 策略开始 =====
print("开始运行钱德动量震荡指标(CMO)期货策略...")

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
            if len(klines) < max(CMO_PERIOD, SIGNAL_PERIOD, SMA_PERIOD) + 10:
                continue
            
            # 计算CMO及相关指标
            klines['cmo'] = calculate_cmo(klines.close, CMO_PERIOD)
            klines['cmo_signal'] = klines['cmo'].rolling(SIGNAL_PERIOD).mean()  # CMO信号线
            klines['cmo_slope'] = klines['cmo'].diff(CMO_SLOPE_PERIOD)  # CMO斜率
            klines['sma'] = klines.close.rolling(SMA_PERIOD).mean()  # 趋势确认SMA
            
            # 计算ATR用于动态止损
            atr_data = ATR(klines, 14)
            
            # 获取最新数据和前一个交易日数据
            current_price = float(klines.close.iloc[-1])
            current_datetime = pd.to_datetime(klines.datetime.iloc[-1], unit='ns')
            current_cmo = float(klines.cmo.iloc[-1])
            current_cmo_signal = float(klines.cmo_signal.iloc[-1])
            current_cmo_slope = float(klines.cmo_slope.iloc[-1])
            current_sma = float(klines.sma.iloc[-1])
            current_atr = float(atr_data.atr.iloc[-1])
            
            prev_price = float(klines.close.iloc[-2])
            prev_cmo = float(klines.cmo.iloc[-2])
            prev_cmo_signal = float(klines.cmo_signal.iloc[-2])
            
            # 输出调试信息
            print(f"日期: {current_datetime.strftime('%Y-%m-%d')}, 价格: {current_price}, CMO: {current_cmo:.2f}, 信号线: {current_cmo_signal:.2f}, 斜率: {current_cmo_slope:.2f}")
            
            # ===== 交易逻辑 =====
            
            # 空仓状态 - 寻找开仓机会
            if current_direction == 0:
                # 计算多头开仓信号
                # 信号1: 超卖反弹
                long_signal1 = prev_cmo < OVERSOLD_THRESHOLD and current_cmo > OVERSOLD_THRESHOLD and current_price > current_sma and current_cmo_slope > 0
                
                # 信号2: 信号线交叉
                long_signal2 = prev_cmo < prev_cmo_signal and current_cmo > current_cmo_signal and current_price > current_sma and current_cmo > -30
                
                # 信号3: 零轴交叉
                long_signal3 = prev_cmo < 0 and current_cmo > 0 and current_price > current_sma and prev_cmo < -10
                
                # 计算空头开仓信号
                # 信号1: 超买回落
                short_signal1 = prev_cmo > OVERBOUGHT_THRESHOLD and current_cmo < OVERBOUGHT_THRESHOLD and current_price < current_sma and current_cmo_slope < 0
                
                # 信号2: 信号线交叉
                short_signal2 = prev_cmo > prev_cmo_signal and current_cmo < current_cmo_signal and current_price < current_sma and current_cmo < 30
                
                # 信号3: 零轴交叉
                short_signal3 = prev_cmo > 0 and current_cmo < 0 and current_price < current_sma and prev_cmo > 10
                
                # 多头开仓条件
                if long_signal1 or long_signal2 or long_signal3:
                    # 确定信号强度和头寸规模
                    signal_strength = 1
                    # 多个信号同时满足时增加头寸
                    if sum([long_signal1, long_signal2, long_signal3]) > 1:
                        signal_strength = 1.5
                    # 极端CMO值时减少头寸
                    if abs(current_cmo) > 80:
                        signal_strength = 0.7
                    
                    # 设置持仓方向和规模
                    current_direction = 1
                    position_size = round(POSITION_SIZE * signal_strength)
                    entry_position = position_size
                    target_pos.set_target_volume(position_size)
                    
                    # 记录开仓信息
                    entry_price = current_price
                    entry_date = current_datetime
                    
                    # 设置止损价格
                    atr_stop = entry_price - ATR_STOP_MULTIPLIER * current_atr
                    fixed_stop = entry_price * (1 - FIXED_STOP_LOSS_PCT)
                    stop_loss_price = max(atr_stop, fixed_stop)  # 取较严格的止损
                    
                    # 设置止盈价格
                    take_profit_price = entry_price * (1 + TAKE_PROFIT_PCT)
                    
                    # 记录信号类型
                    signal_type = ""
                    if long_signal1: signal_type += "超卖反弹 "
                    if long_signal2: signal_type += "信号线上穿 "
                    if long_signal3: signal_type += "零轴上穿 "
                    
                    print(f"多头开仓: 价格={entry_price}, 手数={position_size}, 信号={signal_type}, 止损={stop_loss_price:.2f}, 止盈={take_profit_price:.2f}")
                
                # 空头开仓条件
                elif short_signal1 or short_signal2 or short_signal3:
                    # 确定信号强度和头寸规模
                    signal_strength = 1
                    # 多个信号同时满足时增加头寸
                    if sum([short_signal1, short_signal2, short_signal3]) > 1:
                        signal_strength = 1.5
                    # 极端CMO值时减少头寸
                    if abs(current_cmo) > 80:
                        signal_strength = 0.7
                    
                    # 设置持仓方向和规模
                    current_direction = -1
                    position_size = round(POSITION_SIZE * signal_strength)
                    entry_position = position_size
                    target_pos.set_target_volume(-position_size)
                    
                    # 记录开仓信息
                    entry_price = current_price
                    entry_date = current_datetime
                    
                    # 设置止损价格
                    atr_stop = entry_price + ATR_STOP_MULTIPLIER * current_atr
                    fixed_stop = entry_price * (1 + FIXED_STOP_LOSS_PCT)
                    stop_loss_price = min(atr_stop, fixed_stop)  # 取较严格的止损
                    
                    # 设置止盈价格
                    take_profit_price = entry_price * (1 - TAKE_PROFIT_PCT)
                    
                    # 记录信号类型
                    signal_type = ""
                    if short_signal1: signal_type += "超买回落 "
                    if short_signal2: signal_type += "信号线下穿 "
                    if short_signal3: signal_type += "零轴下穿 "
                    
                    print(f"空头开仓: 价格={entry_price}, 手数={position_size}, 信号={signal_type}, 止损={stop_loss_price:.2f}, 止盈={take_profit_price:.2f}")
            
            # 多头持仓 - 检查平仓条件
            elif current_direction == 1:
                # 计算持仓天数
                holding_days = (current_datetime - entry_date).days
                
                # 3. 基于CMO信号平仓
                if (prev_cmo > prev_cmo_signal and current_cmo < current_cmo_signal and current_cmo > 30):
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头信号平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%, 持仓天数={holding_days}, 原因=动量减弱")
                
                # 4. 反向信号产生
                elif (prev_cmo > OVERBOUGHT_THRESHOLD and current_cmo < OVERBOUGHT_THRESHOLD and current_cmo_slope < 0) or \
                     (prev_cmo > prev_cmo_signal and current_cmo < current_cmo_signal and current_price < current_sma) or \
                     (prev_cmo > 0 and current_cmo < 0 and prev_cmo > 10):
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头反向平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%, 持仓天数={holding_days}, 原因=反向信号")

            
            # 空头持仓 - 检查平仓条件
            elif current_direction == -1:
                # 计算持仓天数
                holding_days = (current_datetime - entry_date).days

                
                # 3. 基于CMO信号平仓
                if (prev_cmo < prev_cmo_signal and current_cmo > current_cmo_signal and current_cmo < -30):
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头信号平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%, 持仓天数={holding_days}, 原因=动量减弱")
                
                # 4. 反向信号产生
                elif (prev_cmo < OVERSOLD_THRESHOLD and current_cmo > OVERSOLD_THRESHOLD and current_cmo_slope > 0) or \
                     (prev_cmo < prev_cmo_signal and current_cmo > current_cmo_signal and current_price > current_sma) or \
                     (prev_cmo < 0 and current_cmo > 0 and prev_cmo < -10):
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头反向平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%, 持仓天数={holding_days}, 原因=反向信号")


except BacktestFinished as e:
    print("回测结束")
    api.close()
