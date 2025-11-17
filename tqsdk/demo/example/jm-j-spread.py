#!/usr/bin/env python
# coding=utf-8
__author__ = "Chaos"

from datetime import date
from tqsdk import TqApi, TqAuth, TargetPosTask, TqBacktest, BacktestFinished
import numpy as np
import time

# === 用户参数 ===
# 合约参数
J = "DCE.j2409"  # 焦炭期货合约
JM = "DCE.jm2409"  # 焦煤期货合约
START_DATE = date(2023, 11, 1)  # 回测开始日期
END_DATE = date(2024, 4, 30)  # 回测结束日期

# 套利参数
LOOKBACK_DAYS = 30  # 计算历史价差的回溯天数
STD_THRESHOLD = 2.0  # 标准差阈值，超过此阈值视为套利机会
ORDER_VOLUME = 50  # 焦炭的下单手数
CLOSE_THRESHOLD = 0.5  # 平仓阈值(标准差)

# 配比参数（可根据实际工艺调整）
J_RATIO = 10  # 10手焦炭
JM_RATIO = 22  # 22手焦煤（约1.32配比）

# === 初始化API ===
api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
            auth=TqAuth("快期账号", "快期密码"))

# 获取合约行情和K线
j_quote = api.get_quote(J)
jm_quote = api.get_quote(JM)

j_klines = api.get_kline_serial(J, 60 * 60 * 24, LOOKBACK_DAYS)
jm_klines = api.get_kline_serial(JM, 60 * 60 * 24, LOOKBACK_DAYS)

# 创建目标持仓任务
j_pos = TargetPosTask(api, J)
jm_pos = TargetPosTask(api, JM)

# 获取合约乘数
j_volume_multiple = j_quote.volume_multiple
jm_volume_multiple = jm_quote.volume_multiple

# 初始化状态变量
position_time = 0  # 建仓时间
in_position = False  # 是否有持仓
mean_spread = 0  # 历史价差均值
std_spread = 0  # 历史价差标准差

print(f"策略启动，监控合约: {J}, {JM}")

# === 主循环 ===
try:
    # 初始计算历史统计值
    spreads = []
    for i in range(len(j_klines) - 1):
        j_value = j_klines.close.iloc[i] * j_volume_multiple * J_RATIO
        jm_value = jm_klines.close.iloc[i] * jm_volume_multiple * JM_RATIO
        spread = j_value - jm_value
        spreads.append(spread)

    mean_spread = np.mean(spreads)
    std_spread = np.std(spreads)
    print(f"历史炼焦利润均值: {mean_spread:.2f}, 标准差: {std_spread:.2f}")

    # 主循环
    while True:
        api.wait_update()

        # 当K线数据有变化时进行计算
        if api.is_changing(j_klines) or api.is_changing(jm_klines):
            # 重新计算历史价差统计
            spreads = []
            for i in range(len(j_klines) - 1):
                j_value = j_klines.close.iloc[i] * j_volume_multiple * J_RATIO
                jm_value = jm_klines.close.iloc[i] * jm_volume_multiple * JM_RATIO
                spread = j_value - jm_value
                spreads.append(spread)

            mean_spread = np.mean(spreads)
            std_spread = np.std(spreads)

            # 计算当前炼焦利润价差
            j_value = j_klines.close.iloc[-1] * j_volume_multiple * J_RATIO
            jm_value = jm_klines.close.iloc[-1] * jm_volume_multiple * JM_RATIO
            current_spread = j_value - jm_value

            # 计算z-score (标准化的价差)
            z_score = (current_spread - mean_spread) / std_spread

            print(f"当前炼焦利润: {current_spread:.2f}, Z-score: {z_score:.2f}")

            # 获取当前持仓
            j_position = api.get_position(J)
            jm_position = api.get_position(JM)

            current_j_pos = j_position.pos_long - j_position.pos_short
            current_jm_pos = jm_position.pos_long - jm_position.pos_short

            # === 交易信号判断 ===
            if not in_position:
                if z_score > STD_THRESHOLD:
                    # 做空炼焦利润：卖出焦炭，买入焦煤
                    print(f"做空炼焦利润：卖出焦炭{ORDER_VOLUME}手，买入焦煤{int(ORDER_VOLUME * JM_RATIO / J_RATIO)}手")
                    j_pos.set_target_volume(-ORDER_VOLUME)
                    jm_pos.set_target_volume(int(ORDER_VOLUME * JM_RATIO / J_RATIO))
                    position_time = time.time()
                    in_position = True
                elif z_score < -STD_THRESHOLD:
                    # 做多炼焦利润：买入焦炭，卖出焦煤
                    print(f"做多炼焦利润：买入焦炭{ORDER_VOLUME}手，卖出焦煤{int(ORDER_VOLUME * JM_RATIO / J_RATIO)}手")
                    j_pos.set_target_volume(ORDER_VOLUME)
                    jm_pos.set_target_volume(-int(ORDER_VOLUME * JM_RATIO / J_RATIO))
                    position_time = time.time()
                    in_position = True

            else:  # 如果已有持仓
                # 检查是否应当平仓
                if abs(z_score) < CLOSE_THRESHOLD:  # 利润回归正常
                    print("利润回归正常，平仓所有头寸")
                    j_pos.set_target_volume(0)
                    jm_pos.set_target_volume(0)
                    in_position = False
                # 止损逻辑
                if (z_score > STD_THRESHOLD * 1.5 and current_j_pos < 0) or \
                        (z_score < -STD_THRESHOLD * 1.5 and current_j_pos > 0):
                    print("止损：利润向不利方向进一步偏离")
                    j_pos.set_target_volume(0)
                    jm_pos.set_target_volume(0)
                    in_position = False

except BacktestFinished as e:
    print("回测结束")
    api.close()

