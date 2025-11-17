#!/usr/bin/env python
# coding=utf-8
__author__ = "Chaos"

from datetime import date

from tqsdk import TqApi, TqAuth, TargetPosTask, TqBacktest, BacktestFinished
import numpy as np
import time

# === 用户参数 ===
# 合约参数
SOYBEAN = "DCE.a2409"    # 大豆期货合约
SOYMEAL = "DCE.m2409"    # 豆粕期货合约
SOYOIL = "DCE.y2409"     # 豆油期货合约
START_DATE = date(2023, 11, 1)   # 回测开始日期
END_DATE = date(2024, 4, 30)     # 回测结束日期

# 套利参数
LOOKBACK_DAYS = 30       # 计算历史价差的回溯天数
STD_THRESHOLD = 2.0      # 标准差阈值，超过此阈值视为套利机会
ORDER_VOLUME = 500        # 大豆的下单手数
CLOSE_THRESHOLD = 0.5    # 平仓阈值(标准差)

# 压榨价差比例 - 1吨大豆压榨可得约0.785吨豆粕和0.18吨豆油
# 为了简化，使用10:8:2的整数比例
BEAN_RATIO = 10
MEAL_RATIO = 8
OIL_RATIO = 2

# === 初始化API ===
api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
            auth=TqAuth("快期账号", "快期密码"))

# 获取合约行情和K线
bean_quote = api.get_quote(SOYBEAN)
meal_quote = api.get_quote(SOYMEAL)
oil_quote = api.get_quote(SOYOIL)

bean_klines = api.get_kline_serial(SOYBEAN, 60*60*24, LOOKBACK_DAYS)
meal_klines = api.get_kline_serial(SOYMEAL, 60*60*24, LOOKBACK_DAYS)
oil_klines = api.get_kline_serial(SOYOIL, 60*60*24, LOOKBACK_DAYS)

# 创建目标持仓任务
bean_pos = TargetPosTask(api, SOYBEAN)
meal_pos = TargetPosTask(api, SOYMEAL)
oil_pos = TargetPosTask(api, SOYOIL)

# 获取合约乘数
bean_volume_multiple = bean_quote.volume_multiple
meal_volume_multiple = meal_quote.volume_multiple
oil_volume_multiple = oil_quote.volume_multiple

# 初始化状态变量
position_time = 0        # 建仓时间
in_position = False      # 是否有持仓
mean_spread = 0          # 历史价差均值
std_spread = 0           # 历史价差标准差

print(f"策略启动，监控合约: {SOYBEAN}, {SOYMEAL}, {SOYOIL}")

# === 主循环 ===
try:
    # 初始计算历史统计值
    spreads = []
    for i in range(len(bean_klines) - 1):
        bean_price = bean_klines.close.iloc[i] * bean_volume_multiple * BEAN_RATIO
        meal_price = meal_klines.close.iloc[i] * meal_volume_multiple * MEAL_RATIO
        oil_price = oil_klines.close.iloc[i] * oil_volume_multiple * OIL_RATIO
        
        # 压榨价差 = (豆粕价值 + 豆油价值) - 大豆价值
        spread = (meal_price + oil_price) - bean_price
        spreads.append(spread)
    
    mean_spread = np.mean(spreads)
    std_spread = np.std(spreads)
    print(f"历史压榨价差均值: {mean_spread:.2f}, 标准差: {std_spread:.2f}")

    # 主循环
    while True:
        api.wait_update()
        
        # 当K线数据有变化时进行计算
        if api.is_changing(bean_klines) or api.is_changing(meal_klines) or api.is_changing(oil_klines):
            # 重新计算历史价差统计
            spreads = []
            for i in range(len(bean_klines) - 1):
                bean_price = bean_klines.close.iloc[i] * bean_volume_multiple * BEAN_RATIO
                meal_price = meal_klines.close.iloc[i] * meal_volume_multiple * MEAL_RATIO
                oil_price = oil_klines.close.iloc[i] * oil_volume_multiple * OIL_RATIO
                
                spread = (meal_price + oil_price) - bean_price
                spreads.append(spread)
            
            mean_spread = np.mean(spreads)
            std_spread = np.std(spreads)
            
            # 计算当前压榨价差
            bean_price = bean_klines.close.iloc[-1] * bean_volume_multiple * BEAN_RATIO
            meal_price = meal_klines.close.iloc[-1] * meal_volume_multiple * MEAL_RATIO
            oil_price = oil_klines.close.iloc[-1] * oil_volume_multiple * OIL_RATIO
            
            current_spread = (meal_price + oil_price) - bean_price
            
            # 计算z-score (标准化的价差)
            z_score = (current_spread - mean_spread) / std_spread
            
            print(f"当前压榨价差: {current_spread:.2f}, Z-score: {z_score:.2f}")
            
            # 获取当前持仓
            bean_position = api.get_position(SOYBEAN)
            meal_position = api.get_position(SOYMEAL)
            oil_position = api.get_position(SOYOIL)
            
            current_bean_pos = bean_position.pos_long - bean_position.pos_short
            current_meal_pos = meal_position.pos_long - meal_position.pos_short
            current_oil_pos = oil_position.pos_long - oil_position.pos_short
            
            # 计算实际下单手数（依据比例）
            meal_volume = int(ORDER_VOLUME * MEAL_RATIO / BEAN_RATIO)
            oil_volume = int(ORDER_VOLUME * OIL_RATIO / BEAN_RATIO)
            
            # === 交易信号判断 ===
            if not in_position:  # 如果没有持仓
                if z_score > STD_THRESHOLD:  # 价差显著高于均值，压榨利润偏高
                    # 卖出压榨价差：买入大豆，卖出豆粕和豆油
                    print(f"卖出压榨价差：买入大豆{ORDER_VOLUME}手，卖出豆粕{meal_volume}手和豆油{oil_volume}手")
                    bean_pos.set_target_volume(ORDER_VOLUME)
                    meal_pos.set_target_volume(-meal_volume)
                    oil_pos.set_target_volume(-oil_volume)
                    position_time = time.time()
                    in_position = True
                    
                elif z_score < -STD_THRESHOLD:  # 价差显著低于均值，压榨利润偏低
                    # 买入压榨价差：卖出大豆，买入豆粕和豆油
                    print(f"买入压榨价差：卖出大豆{ORDER_VOLUME}手，买入豆粕{meal_volume}手和豆油{oil_volume}手")
                    bean_pos.set_target_volume(-ORDER_VOLUME)
                    meal_pos.set_target_volume(meal_volume)
                    oil_pos.set_target_volume(oil_volume)
                    position_time = time.time()
                    in_position = True
            
            else:  # 如果已有持仓
                # 检查是否应当平仓
                if abs(z_score) < CLOSE_THRESHOLD:  # 价差恢复正常
                    print("价差恢复正常，平仓所有头寸")
                    bean_pos.set_target_volume(0)
                    meal_pos.set_target_volume(0)
                    oil_pos.set_target_volume(0)
                    in_position = False
                
                # 也可以添加止损逻辑
                if (z_score > STD_THRESHOLD * 1.5 and current_bean_pos > 0) or \
                   (z_score < -STD_THRESHOLD * 1.5 and current_bean_pos < 0):
                    print("止损：价差向不利方向进一步偏离")
                    bean_pos.set_target_volume(0)
                    meal_pos.set_target_volume(0)
                    oil_pos.set_target_volume(0)
                    in_position = False

except BacktestFinished as e:
    print("回测结束")
    api.close()
