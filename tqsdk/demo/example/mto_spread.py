#!/usr/bin/env python
# coding=utf-8
__author__ = "Chaos"

from datetime import date
from tqsdk import TqApi, TqAuth, TargetPosTask, TqBacktest, BacktestFinished
import numpy as np
import time

# === 用户参数 ===
# 合约参数
MA = "CZCE.MA409"      # 甲醇期货合约
L = "DCE.l2409"        # 聚乙烯期货合约
PP = "DCE.pp2409"      # 聚丙烯期货合约
START_DATE = date(2023, 11, 1)   # 回测开始日期
END_DATE = date(2024, 4, 30)     # 回测结束日期

# 套利参数
LOOKBACK_DAYS = 30        # 计算历史价差的回溯天数
STD_THRESHOLD = 2.0       # 标准差阈值，超过此阈值视为套利机会
ORDER_VOLUME = 100         # 聚乙烯的下单手数
CLOSE_THRESHOLD = 0.5     # 平仓阈值(标准差)

# 生产比例（可根据实际工艺调整）
MA_RATIO = 3      # 生产1吨烯烃消耗3吨甲醇
L_RATIO = 1       # 产出1吨聚乙烯
PP_RATIO = 1      # 产出1吨聚丙烯

# === 初始化API ===
api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
            auth=TqAuth("快期账号", "快期密码"))

# 获取合约行情和K线
ma_quote = api.get_quote(MA)
l_quote = api.get_quote(L)
pp_quote = api.get_quote(PP)

ma_klines = api.get_kline_serial(MA, 60*60*24, LOOKBACK_DAYS)
l_klines = api.get_kline_serial(L, 60*60*24, LOOKBACK_DAYS)
pp_klines = api.get_kline_serial(PP, 60*60*24, LOOKBACK_DAYS)

# 创建目标持仓任务
ma_pos = TargetPosTask(api, MA)
l_pos = TargetPosTask(api, L)
pp_pos = TargetPosTask(api, PP)

# 获取合约乘数
ma_volume_multiple = ma_quote.volume_multiple
l_volume_multiple = l_quote.volume_multiple
pp_volume_multiple = pp_quote.volume_multiple

# 初始化状态变量
position_time = 0        # 建仓时间
in_position = False      # 是否有持仓
mean_spread = 0          # 历史价差均值
std_spread = 0           # 历史价差标准差

print(f"策略启动，监控合约: {MA}, {L}, {PP}")

# === 主循环 ===
try:
    # 初始计算历史统计值
    spreads = []
    for i in range(len(ma_klines) - 1):
        ma_price = ma_klines.close.iloc[i] * ma_volume_multiple * MA_RATIO
        l_price = l_klines.close.iloc[i] * l_volume_multiple * L_RATIO
        pp_price = pp_klines.close.iloc[i] * pp_volume_multiple * PP_RATIO
        
        # MTO利润 = (L价值 + PP价值) - MA成本
        spread = (l_price + pp_price) - ma_price
        spreads.append(spread)
    
    mean_spread = np.mean(spreads)
    std_spread = np.std(spreads)
    print(f"历史MTO利润均值: {mean_spread:.2f}, 标准差: {std_spread:.2f}")

    # 主循环
    while True:
        api.wait_update()
        
        # 当K线数据有变化时进行计算
        if api.is_changing(ma_klines) or api.is_changing(l_klines) or api.is_changing(pp_klines):
            # 重新计算历史价差统计
            spreads = []
            for i in range(len(ma_klines) - 1):
                ma_price = ma_klines.close.iloc[i] * ma_volume_multiple * MA_RATIO
                l_price = l_klines.close.iloc[i] * l_volume_multiple * L_RATIO
                pp_price = pp_klines.close.iloc[i] * pp_volume_multiple * PP_RATIO
                
                spread = (l_price + pp_price) - ma_price
                spreads.append(spread)
            
            mean_spread = np.mean(spreads)
            std_spread = np.std(spreads)
            
            # 计算当前利润价差
            ma_price = ma_klines.close.iloc[-1] * ma_volume_multiple * MA_RATIO
            l_price = l_klines.close.iloc[-1] * l_volume_multiple * L_RATIO
            pp_price = pp_klines.close.iloc[-1] * pp_volume_multiple * PP_RATIO
            
            current_spread = (l_price + pp_price) - ma_price
            
            # 计算z-score (标准化的价差)
            z_score = (current_spread - mean_spread) / std_spread
            
            print(f"当前MTO利润: {current_spread:.2f}, Z-score: {z_score:.2f}")
            
            # 获取当前持仓
            ma_position = api.get_position(MA)
            l_position = api.get_position(L)
            pp_position = api.get_position(PP)
            
            current_ma_pos = ma_position.pos_long - ma_position.pos_short
            current_l_pos = l_position.pos_long - l_position.pos_short
            current_pp_pos = pp_position.pos_long - pp_position.pos_short
            
            # 计算实际下单手数（依据比例）
            ma_volume = int(ORDER_VOLUME * MA_RATIO / L_RATIO)
            # L和PP按同等手数下单
            
            # === 交易信号判断 ===
            if not in_position:  # 如果没有持仓
                if z_score > STD_THRESHOLD:  # 利润显著高于均值
                    # 做空利润：卖出L和PP，买入MA
                    print(f"做空利润：卖出L{ORDER_VOLUME}手和PP{ORDER_VOLUME}手，买入MA{ma_volume}手")
                    l_pos.set_target_volume(-ORDER_VOLUME)
                    pp_pos.set_target_volume(-ORDER_VOLUME)
                    ma_pos.set_target_volume(ma_volume)
                    position_time = time.time()
                    in_position = True
                    
                elif z_score < -STD_THRESHOLD:  # 利润显著低于均值
                    # 做多利润：买入L和PP，卖出MA
                    print(f"做多利润：买入L{ORDER_VOLUME}手和PP{ORDER_VOLUME}手，卖出MA{ma_volume}手")
                    l_pos.set_target_volume(ORDER_VOLUME)
                    pp_pos.set_target_volume(ORDER_VOLUME)
                    ma_pos.set_target_volume(-ma_volume)
                    position_time = time.time()
                    in_position = True
            
            else:  # 如果已有持仓
                # 检查是否应当平仓
                if abs(z_score) < CLOSE_THRESHOLD:  # 利润回归正常
                    print("利润回归正常，平仓所有头寸")
                    l_pos.set_target_volume(0)
                    pp_pos.set_target_volume(0)
                    ma_pos.set_target_volume(0)
                    in_position = False
                
                # 止损逻辑
                if (z_score > STD_THRESHOLD * 1.5 and current_l_pos < 0) or \
                   (z_score < -STD_THRESHOLD * 1.5 and current_l_pos > 0):
                    print("止损：利润向不利方向进一步偏离")
                    l_pos.set_target_volume(0)
                    pp_pos.set_target_volume(0)
                    ma_pos.set_target_volume(0)
                    in_position = False

except BacktestFinished as e:
    print("回测结束")
    api.close()
