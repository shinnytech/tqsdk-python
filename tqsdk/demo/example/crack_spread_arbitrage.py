#!/usr/bin/env python
# coding=utf-8
"""
裂解价差均值回归策略
基于原油及其主要炼化产品之间的价格关系在短期内可能偏离其长期均衡水平，并最终回归的假设
"""

from tqsdk import TqApi, TqAuth, TqKq, TargetPosTask, TqBacktest, BacktestFinished
from datetime import date
import numpy as np
import time

# === 用户参数 ===
# 合约参数
CRUDE_OIL = "SHFE.sc2406"  # 原油期货合约
GASOLINE = "SHFE.fu2406"   # 燃料油期货合约
DIESEL = "INE.nr2406"      # 柴油期货合约

# 回测参数
START_DATE = date(2023, 11, 1)  # 回测开始日期
END_DATE = date(2024, 4, 1)     # 回测结束日期

# 裂解比例 - 3:2:1 裂解价差
OIL_RATIO = 3        # 原油比例
GAS_RATIO = 2        # 汽油比例
DIESEL_RATIO = 1     # 柴油比例

# 套利参数
LOOKBACK_DAYS = 60         # 计算历史价差的回溯天数
DEVIATION_THRESHOLD = 1.5  # 偏离阈值（标准差倍数）
OIL_LOTS = 5               # 原油交易手数
CLOSE_AT_MEAN = True       # 是否在价差回归到均值时平仓
MAX_HOLDING_DAYS = 10      # 最大持仓天数

# === 初始化API ===
api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
            auth=TqAuth("你的天勤账号", "你的天勤密码"))

# 获取合约行情和K线
crude_quote = api.get_quote(CRUDE_OIL)
gasoline_quote = api.get_quote(GASOLINE)
diesel_quote = api.get_quote(DIESEL)

crude_klines = api.get_kline_serial(CRUDE_OIL, 60*60*24, LOOKBACK_DAYS)
gasoline_klines = api.get_kline_serial(GASOLINE, 60*60*24, LOOKBACK_DAYS)
diesel_klines = api.get_kline_serial(DIESEL, 60*60*24, LOOKBACK_DAYS)

# 创建目标持仓任务
crude_pos = TargetPosTask(api, CRUDE_OIL)
gasoline_pos = TargetPosTask(api, GASOLINE)
diesel_pos = TargetPosTask(api, DIESEL)

# 获取合约乘数
crude_volume_multiple = crude_quote.volume_multiple
gasoline_volume_multiple = gasoline_quote.volume_multiple
diesel_volume_multiple = diesel_quote.volume_multiple

# 计算汽油和柴油的交易手数（基于原油手数和裂解比例）
GAS_LOTS = round(GAS_RATIO / OIL_RATIO * OIL_LOTS)
DIESEL_LOTS = round(DIESEL_RATIO / OIL_RATIO * OIL_LOTS)

# 初始化状态变量
position_time = 0  # 建仓时间
in_position = False  # 是否有持仓
last_trade_direction = ""  # 上次交易方向 "BUY_SPREAD" 或 "SELL_SPREAD"
mean_spread = 0  # 历史价差均值
std_spread = 0  # 历史价差标准差

print(f"裂解价差套利策略启动")
print(f"监控合约: 原油({CRUDE_OIL}) - {OIL_LOTS}手, 汽油({GASOLINE}) - {GAS_LOTS}手, 柴油({DIESEL}) - {DIESEL_LOTS}手")
print(f"裂解比例: {OIL_RATIO}:{GAS_RATIO}:{DIESEL_RATIO}")

# === 主循环 ===
try:
    # 初始计算历史统计值
    spreads = []
    for i in range(len(crude_klines) - 1):
        crude_price = crude_klines.close.iloc[i] * crude_volume_multiple * OIL_RATIO
        gasoline_price = gasoline_klines.close.iloc[i] * gasoline_volume_multiple * GAS_RATIO
        diesel_price = diesel_klines.close.iloc[i] * diesel_volume_multiple * DIESEL_RATIO
        
        # 裂解价差 = (汽油价值 + 柴油价值) - 原油价值
        spread = (gasoline_price + diesel_price) - crude_price
        spreads.append(spread)
    
    mean_spread = np.mean(spreads)
    std_spread = np.std(spreads)
    print(f"历史裂解价差 - 均值: {mean_spread:.2f}, 标准差: {std_spread:.2f}")

    # 主循环
    while True:
        api.wait_update()
        
        # 当K线数据有变化时进行计算
        if api.is_changing(crude_klines) or api.is_changing(gasoline_klines) or api.is_changing(diesel_klines):
            # 重新计算历史价差统计
            spreads = []
            for i in range(len(crude_klines) - 1):
                crude_price = crude_klines.close.iloc[i] * crude_volume_multiple * OIL_RATIO
                gasoline_price = gasoline_klines.close.iloc[i] * gasoline_volume_multiple * GAS_RATIO
                diesel_price = diesel_klines.close.iloc[i] * diesel_volume_multiple * DIESEL_RATIO
                
                spread = (gasoline_price + diesel_price) - crude_price
                spreads.append(spread)
            
            mean_spread = np.mean(spreads)
            std_spread = np.std(spreads)
            
            # 计算当前裂解价差
            crude_price = crude_klines.close.iloc[-1] * crude_volume_multiple * OIL_RATIO
            gasoline_price = gasoline_klines.close.iloc[-1] * gasoline_volume_multiple * GAS_RATIO
            diesel_price = diesel_klines.close.iloc[-1] * diesel_volume_multiple * DIESEL_RATIO
            
            current_spread = (gasoline_price + diesel_price) - crude_price
            
            # 计算z-score (标准化的价差)
            z_score = (current_spread - mean_spread) / std_spread
            
            print(f"当前裂解价差: {current_spread:.2f}, Z-score: {z_score:.2f}, 均值: {mean_spread:.2f}")
            
            # 获取当前持仓
            crude_position = api.get_position(CRUDE_OIL)
            gasoline_position = api.get_position(GASOLINE)
            diesel_position = api.get_position(DIESEL)
            
            current_crude_pos = crude_position.pos_long - crude_position.pos_short
            current_gasoline_pos = gasoline_position.pos_long - gasoline_position.pos_short
            current_diesel_pos = diesel_position.pos_long - diesel_position.pos_short
            
            # === 交易信号判断 ===
            if not in_position:  # 如果没有持仓
                if z_score > DEVIATION_THRESHOLD:  # 价差显著高于均值
                    # 卖出裂解价差：卖出原油，买入汽油和柴油
                    print(f"信号: 卖出裂解价差 (Z-score: {z_score:.2f})")
                    print(f"操作: 卖出原油{OIL_LOTS}手，买入汽油{GAS_LOTS}手，买入柴油{DIESEL_LOTS}手")
                    crude_pos.set_target_volume(-OIL_LOTS)
                    gasoline_pos.set_target_volume(GAS_LOTS)
                    diesel_pos.set_target_volume(DIESEL_LOTS)
                    position_time = time.time()
                    in_position = True
                    last_trade_direction = "SELL_SPREAD"
                    
                elif z_score < -DEVIATION_THRESHOLD:  # 价差显著低于均值
                    # 买入裂解价差：买入原油，卖出汽油和柴油
                    print(f"信号: 买入裂解价差 (Z-score: {z_score:.2f})")
                    print(f"操作: 买入原油{OIL_LOTS}手，卖出汽油{GAS_LOTS}手，卖出柴油{DIESEL_LOTS}手")
                    crude_pos.set_target_volume(OIL_LOTS)
                    gasoline_pos.set_target_volume(-GAS_LOTS)
                    diesel_pos.set_target_volume(-DIESEL_LOTS)
                    position_time = time.time()
                    in_position = True
                    last_trade_direction = "BUY_SPREAD"
            
            elif in_position:  # 如果已有持仓
                # 检查是否应当平仓
                if CLOSE_AT_MEAN:  # 在价差回归均值时平仓
                    if (last_trade_direction == "BUY_SPREAD" and current_spread >= mean_spread) or \
                       (last_trade_direction == "SELL_SPREAD" and current_spread <= mean_spread):
                        print(f"信号: 价差回归均值，平仓所有头寸")
                        print(f"当前价差: {current_spread:.2f}, 均值: {mean_spread:.2f}")
                        crude_pos.set_target_volume(0)
                        gasoline_pos.set_target_volume(0)
                        diesel_pos.set_target_volume(0)
                        in_position = False
                else:  # 在价差回归（穿过阈值）时平仓
                    if (last_trade_direction == "BUY_SPREAD" and z_score >= 0) or \
                       (last_trade_direction == "SELL_SPREAD" and z_score <= 0):
                        print(f"信号: 价差穿过均值，平仓所有头寸")
                        print(f"当前价差: {current_spread:.2f}, Z-score: {z_score:.2f}")
                        crude_pos.set_target_volume(0)
                        gasoline_pos.set_target_volume(0)
                        diesel_pos.set_target_volume(0)
                        in_position = False
                
                # 持仓时间监控
                position_duration = (time.time() - position_time) / (60*60*24)  # 天数
                if position_duration > MAX_HOLDING_DAYS:  # 持仓超过最大天数
                    print(f"警告: 持仓时间已超过{MAX_HOLDING_DAYS}天 ({position_duration:.1f}天)")
                    print(f"强制平仓所有头寸")
                    crude_pos.set_target_volume(0)
                    gasoline_pos.set_target_volume(0)
                    diesel_pos.set_target_volume(0)
                    in_position = False

except BacktestFinished as e:
    print("回测结束")
    api.close()
except KeyboardInterrupt:
    print("用户中断程序执行")
    api.close()
    print("策略已停止运行") 