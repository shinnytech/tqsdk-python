#!/usr/bin/env python
# coding=utf-8
__author__ = "Chaos"

from datetime import date

from tqsdk import TqApi, TqAuth, TargetPosTask, TqBacktest, BacktestFinished
import numpy as np
import time

# === 用户参数 ===
# 合约参数
LIVE_HOG = "DCE.lh2409"  # 生猪期货合约
CORN = "DCE.c2409"  # 玉米期货合约
SOYMEAL = "DCE.m2409"  # 豆粕期货合约
START_DATE = date(2023, 11, 1)  # 回测开始日期
END_DATE = date(2024, 3, 13)  # 回测结束日期

# 套利参数
LOOKBACK_DAYS = 30  # 计算历史价差的回溯天数
STD_THRESHOLD = 2.0  # 标准差阈值，超过此阈值视为套利机会
ORDER_VOLUME = 100  # 生猪的下单手数
CLOSE_THRESHOLD = 0.5  # 平仓阈值(标准差)

# 饲养利润价差比例 - 生产1吨生猪约需要3吨玉米和0.6吨豆粕
# 可根据实际养殖转化比调整
HOG_RATIO = 1
CORN_RATIO = 3
SOYMEAL_RATIO = 0.6

# === 初始化API ===
api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
            auth=TqAuth("快期账号", "快期密码"))

# 获取合约行情和K线
hog_quote = api.get_quote(LIVE_HOG)
corn_quote = api.get_quote(CORN)
meal_quote = api.get_quote(SOYMEAL)

hog_klines = api.get_kline_serial(LIVE_HOG, 60 * 60 * 24, LOOKBACK_DAYS)
corn_klines = api.get_kline_serial(CORN, 60 * 60 * 24, LOOKBACK_DAYS)
meal_klines = api.get_kline_serial(SOYMEAL, 60 * 60 * 24, LOOKBACK_DAYS)

# 创建目标持仓任务
hog_pos = TargetPosTask(api, LIVE_HOG)
corn_pos = TargetPosTask(api, CORN)
meal_pos = TargetPosTask(api, SOYMEAL)

# 获取合约乘数
hog_volume_multiple = hog_quote.volume_multiple
corn_volume_multiple = corn_quote.volume_multiple
meal_volume_multiple = meal_quote.volume_multiple

# 初始化状态变量
position_time = 0  # 建仓时间
in_position = False  # 是否有持仓
mean_spread = 0  # 历史价差均值
std_spread = 0  # 历史价差标准差

print(f"策略启动，监控合约: {LIVE_HOG}, {CORN}, {SOYMEAL}")

# === 主循环 ===
try:
    # 初始计算历史统计值
    spreads = []
    for i in range(len(hog_klines) - 1):
        hog_price = hog_klines.close.iloc[i] * hog_volume_multiple * HOG_RATIO
        corn_price = corn_klines.close.iloc[i] * corn_volume_multiple * CORN_RATIO
        meal_price = meal_klines.close.iloc[i] * meal_volume_multiple * SOYMEAL_RATIO

        # 饲养利润 = 生猪价值 - 饲料成本价值
        spread = hog_price - (corn_price + meal_price)
        spreads.append(spread)

    mean_spread = np.mean(spreads)
    std_spread = np.std(spreads)
    print(f"历史饲养利润均值: {mean_spread:.2f}, 标准差: {std_spread:.2f}")

    # 主循环
    while True:
        api.wait_update()

        # 当K线数据有变化时进行计算
        if api.is_changing(hog_klines) or api.is_changing(corn_klines) or api.is_changing(meal_klines):
            # 重新计算历史价差统计
            spreads = []
            for i in range(len(hog_klines) - 1):
                hog_price = hog_klines.close.iloc[i] * hog_volume_multiple * HOG_RATIO
                corn_price = corn_klines.close.iloc[i] * corn_volume_multiple * CORN_RATIO
                meal_price = meal_klines.close.iloc[i] * meal_volume_multiple * SOYMEAL_RATIO

                spread = hog_price - (corn_price + meal_price)
                spreads.append(spread)

            mean_spread = np.mean(spreads)
            std_spread = np.std(spreads)

            # 计算当前饲养利润价差
            hog_price = hog_klines.close.iloc[-1] * hog_volume_multiple * HOG_RATIO
            corn_price = corn_klines.close.iloc[-1] * corn_volume_multiple * CORN_RATIO
            meal_price = meal_klines.close.iloc[-1] * meal_volume_multiple * SOYMEAL_RATIO

            current_spread = hog_price - (corn_price + meal_price)

            # 计算z-score (标准化的价差)
            z_score = (current_spread - mean_spread) / std_spread

            print(f"当前饲养利润: {current_spread:.2f}, Z-score: {z_score:.2f}")

            # 获取当前持仓
            hog_position = api.get_position(LIVE_HOG)
            corn_position = api.get_position(CORN)
            meal_position = api.get_position(SOYMEAL)

            current_hog_pos = hog_position.pos_long - hog_position.pos_short
            current_corn_pos = corn_position.pos_long - corn_position.pos_short
            current_meal_pos = meal_position.pos_long - meal_position.pos_short

            # 计算实际下单手数（依据比例）
            corn_volume = int(ORDER_VOLUME * CORN_RATIO / HOG_RATIO)
            meal_volume = int(ORDER_VOLUME * SOYMEAL_RATIO / HOG_RATIO)

            # === 交易信号判断 ===
            if not in_position:  # 如果没有持仓
                if z_score > STD_THRESHOLD:  # 饲养利润显著高于均值
                    # 做空饲养利润：卖出生猪，买入玉米和豆粕
                    print(f"做空饲养利润：卖出生猪{ORDER_VOLUME}手，买入玉米{corn_volume}手和豆粕{meal_volume}手")
                    hog_pos.set_target_volume(-ORDER_VOLUME)
                    corn_pos.set_target_volume(corn_volume)
                    meal_pos.set_target_volume(meal_volume)
                    position_time = time.time()
                    in_position = True

                elif z_score < -STD_THRESHOLD:  # 饲养利润显著低于均值
                    # 做多饲养利润：买入生猪，卖出玉米和豆粕
                    print(f"做多饲养利润：买入生猪{ORDER_VOLUME}手，卖出玉米{corn_volume}手和豆粕{meal_volume}手")
                    hog_pos.set_target_volume(ORDER_VOLUME)
                    corn_pos.set_target_volume(-corn_volume)
                    meal_pos.set_target_volume(-meal_volume)
                    position_time = time.time()
                    in_position = True

            else:  # 如果已有持仓
                # 检查是否应当平仓
                if abs(z_score) < CLOSE_THRESHOLD:  # 饲养利润恢复正常
                    print("饲养利润回归正常水平，平仓所有头寸")
                    hog_pos.set_target_volume(0)
                    corn_pos.set_target_volume(0)
                    meal_pos.set_target_volume(0)
                    in_position = False

                # 止损逻辑
                if (z_score > STD_THRESHOLD * 1.5 and current_hog_pos > 0) or \
                        (z_score < -STD_THRESHOLD * 1.5 and current_hog_pos < 0):
                    print("止损：饲养利润向不利方向进一步偏离")
                    hog_pos.set_target_volume(0)
                    corn_pos.set_target_volume(0)
                    meal_pos.set_target_volume(0)
                    in_position = False

except BacktestFinished as e:
    print("回测结束")
    api.close()