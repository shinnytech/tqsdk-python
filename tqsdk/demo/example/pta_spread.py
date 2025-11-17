#!/usr/bin/env python
# coding=utf-8
__author__ = "Chaos"

from datetime import date
from tqsdk import TqApi, TqAuth, TargetPosTask, TqBacktest, BacktestFinished
import numpy as np
import time

# === 用户参数 ===
# 合约参数
PF = "CZCE.PF409"      # 涤纶短纤期货合约
PTA = "CZCE.TA409"     # PTA期货合约
EG = "DCE.eg2409"      # 乙二醇期货合约
START_DATE = date(2024, 2, 1)   # 回测开始日期
END_DATE = date(2024, 4, 30)     # 回测结束日期

# 套利参数
LOOKBACK_DAYS = 30        # 计算历史价差的回溯天数
STD_THRESHOLD = 2.0       # 标准差阈值，超过此阈值视为套利机会
ORDER_VOLUME = 500         # 涤纶短纤的下单手数
CLOSE_THRESHOLD = 0.5     # 平仓阈值(标准差)

# 生产比例（可根据实际工艺调整）
PF_RATIO = 1
PTA_RATIO = 0.86
EG_RATIO = 0.34

# === 初始化API ===
api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
            auth=TqAuth("快期账号", "快期密码"))

# 获取合约行情和K线
pf_quote = api.get_quote(PF)
pta_quote = api.get_quote(PTA)
eg_quote = api.get_quote(EG)

pf_klines = api.get_kline_serial(PF, 60*60*24, LOOKBACK_DAYS)
pta_klines = api.get_kline_serial(PTA, 60*60*24, LOOKBACK_DAYS)
eg_klines = api.get_kline_serial(EG, 60*60*24, LOOKBACK_DAYS)

# 创建目标持仓任务
pf_pos = TargetPosTask(api, PF)
pta_pos = TargetPosTask(api, PTA)
eg_pos = TargetPosTask(api, EG)

# 获取合约乘数
pf_volume_multiple = pf_quote.volume_multiple
pta_volume_multiple = pta_quote.volume_multiple
eg_volume_multiple = eg_quote.volume_multiple

# 初始化状态变量
position_time = 0        # 建仓时间
in_position = False      # 是否有持仓
mean_spread = 0          # 历史价差均值
std_spread = 0           # 历史价差标准差

print(f"策略启动，监控合约: {PF}, {PTA}, {EG}")

# === 主循环 ===
try:
    # 初始计算历史统计值
    spreads = []
    for i in range(len(pf_klines) - 1):
        pf_price = pf_klines.close.iloc[i] * pf_volume_multiple * PF_RATIO
        pta_price = pta_klines.close.iloc[i] * pta_volume_multiple * PTA_RATIO
        eg_price = eg_klines.close.iloc[i] * eg_volume_multiple * EG_RATIO
        
        # 涤纶短纤生产利润 = 涤纶短纤价值 - (PTA成本 + EG成本)
        spread = pf_price - (pta_price + eg_price)
        spreads.append(spread)
    
    mean_spread = np.mean(spreads)
    std_spread = np.std(spreads)
    print(f"历史涤纶短纤利润均值: {mean_spread:.2f}, 标准差: {std_spread:.2f}")

    # 主循环
    while True:
        api.wait_update()
        
        # 当K线数据有变化时进行计算
        if api.is_changing(pf_klines) or api.is_changing(pta_klines) or api.is_changing(eg_klines):
            # 重新计算历史价差统计
            spreads = []
            for i in range(len(pf_klines) - 1):
                pf_price = pf_klines.close.iloc[i] * pf_volume_multiple * PF_RATIO
                pta_price = pta_klines.close.iloc[i] * pta_volume_multiple * PTA_RATIO
                eg_price = eg_klines.close.iloc[i] * eg_volume_multiple * EG_RATIO
                
                spread = pf_price - (pta_price + eg_price)
                spreads.append(spread)
            
            mean_spread = np.mean(spreads)
            std_spread = np.std(spreads)
            
            # 计算当前利润价差
            pf_price = pf_klines.close.iloc[-1] * pf_volume_multiple * PF_RATIO
            pta_price = pta_klines.close.iloc[-1] * pta_volume_multiple * PTA_RATIO
            eg_price = eg_klines.close.iloc[-1] * eg_volume_multiple * EG_RATIO
            
            current_spread = pf_price - (pta_price + eg_price)
            
            # 计算z-score (标准化的价差)
            z_score = (current_spread - mean_spread) / std_spread
            
            print(f"当前涤纶短纤利润: {current_spread:.2f}, Z-score: {z_score:.2f}")
            
            # 获取当前持仓
            pf_position = api.get_position(PF)
            pta_position = api.get_position(PTA)
            eg_position = api.get_position(EG)
            
            current_pf_pos = pf_position.pos_long - pf_position.pos_short
            current_pta_pos = pta_position.pos_long - pta_position.pos_short
            current_eg_pos = eg_position.pos_long - eg_position.pos_short
            
            # 计算实际下单手数（依据比例）
            pta_volume = int(ORDER_VOLUME * PTA_RATIO / PF_RATIO)
            eg_volume = int(ORDER_VOLUME * EG_RATIO / PF_RATIO)
            
            # === 交易信号判断 ===
            if not in_position:  # 如果没有持仓
                if z_score > STD_THRESHOLD:  # 利润显著高于均值
                    # 做空利润：卖出PF，买入PTA和EG
                    print(f"做空利润：卖出PF{ORDER_VOLUME}手，买入PTA{pta_volume}手和EG{eg_volume}手")
                    pf_pos.set_target_volume(-ORDER_VOLUME)
                    pta_pos.set_target_volume(pta_volume)
                    eg_pos.set_target_volume(eg_volume)
                    position_time = time.time()
                    in_position = True
                    
                elif z_score < -STD_THRESHOLD:  # 利润显著低于均值
                    # 做多利润：买入PF，卖出PTA和EG
                    print(f"做多利润：买入PF{ORDER_VOLUME}手，卖出PTA{pta_volume}手和EG{eg_volume}手")
                    pf_pos.set_target_volume(ORDER_VOLUME)
                    pta_pos.set_target_volume(-pta_volume)
                    eg_pos.set_target_volume(-eg_volume)
                    position_time = time.time()
                    in_position = True
            
            else:  # 如果已有持仓
                # 检查是否应当平仓
                if abs(z_score) < CLOSE_THRESHOLD:  # 利润回归正常
                    print("利润回归正常，平仓所有头寸")
                    pf_pos.set_target_volume(0)
                    pta_pos.set_target_volume(0)
                    eg_pos.set_target_volume(0)
                    in_position = False

                
                # 止损逻辑
                if (z_score > STD_THRESHOLD * 1.5 and current_pf_pos > 0) or \
                   (z_score < -STD_THRESHOLD * 1.5 and current_pf_pos < 0):
                    print("止损：利润向不利方向进一步偏离")
                    pf_pos.set_target_volume(0)
                    pta_pos.set_target_volume(0)
                    eg_pos.set_target_volume(0)
                    in_position = False

except BacktestFinished as e:
    print("回测结束")
    api.close()

