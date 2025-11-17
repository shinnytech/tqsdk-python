#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Chaos"

from datetime import date

import numpy as np
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished

# 参数设置
NEAR_CONTRACT = "CFFEX.IH2101"  # 近月合约
FAR_CONTRACT = "CFFEX.IH2102"  # 远月合约
K = 2  # 标准差倍数
WINDOW = 80  # 计算窗口
LOTS = 20  # 交易手数
START_DATE = date(2020, 12, 21)  # 回测开始日期
END_DATE = date(2021, 1, 15)  # 回测结束日期

# 创建API实例
api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
            auth=TqAuth("快期账号", "快期密码"))

# 订阅行情
near_quote = api.get_quote(NEAR_CONTRACT)
far_quote = api.get_quote(FAR_CONTRACT)
near_klines = api.get_kline_serial(NEAR_CONTRACT, 15 * 60, WINDOW * 2)  # 15分钟K线
far_klines = api.get_kline_serial(FAR_CONTRACT, 15 * 60, WINDOW * 2)

# 创建目标持仓任务
near_pos = TargetPosTask(api, NEAR_CONTRACT)
far_pos = TargetPosTask(api, FAR_CONTRACT)

# 持仓状态: 0-无持仓, 1-多价差(买近卖远), -1-空价差(卖近买远)
position_state = 0

print(f"策略启动: {NEAR_CONTRACT}-{FAR_CONTRACT} 跨期套利")
print(f"参数设置: K={K}倍标准差, 窗口={WINDOW}, 交易手数={LOTS}手")

try:
    while True:
        api.wait_update()

        # 检查K线是否更新
        if api.is_changing(near_klines) or api.is_changing(far_klines):
            # 确保有足够的数据
            if len(near_klines) < WINDOW or len(far_klines) < WINDOW:
                continue

            # 计算价差指标
            near_close = near_klines.close.iloc[-WINDOW:]
            far_close = far_klines.close.iloc[-WINDOW:]
            spread = near_close - far_close

            # 计算均值和标准差
            mean = np.mean(spread)
            std = np.std(spread)
            current_spread = near_quote.last_price - far_quote.last_price

            # 计算上下边界
            upper_bound = mean + K * std
            lower_bound = mean - K * std

            print(f"价差: {current_spread:.2f}, 均值: {mean:.2f}, "
                  f"上界: {upper_bound:.2f}, 下界: {lower_bound:.2f}")

            # 交易逻辑
            if position_state == 0:  # 无持仓状态
                if current_spread > upper_bound:  # 做空价差(卖近买远)
                    near_pos.set_target_volume(-LOTS)
                    far_pos.set_target_volume(LOTS)
                    position_state = -1
                    print(f"开仓: 卖出{LOTS}手{NEAR_CONTRACT}, 买入{LOTS}手{FAR_CONTRACT}")

                elif current_spread < lower_bound:  # 做多价差(买近卖远)
                    near_pos.set_target_volume(LOTS)
                    far_pos.set_target_volume(-LOTS)
                    position_state = 1
                    print(f"开仓: 买入{LOTS}手{NEAR_CONTRACT}, 卖出{LOTS}手{FAR_CONTRACT}")

            elif position_state == 1:  # 持有多价差
                if current_spread >= mean:  # 平仓获利
                    near_pos.set_target_volume(0)
                    far_pos.set_target_volume(0)
                    position_state = 0
                    print("平仓: 价差回到均值，平仓获利")

            elif position_state == -1:  # 持有空价差
                if current_spread <= mean:  # 平仓获利
                    near_pos.set_target_volume(0)
                    far_pos.set_target_volume(0)
                    position_state = 0
                    print("平仓: 价差回到均值，平仓获利")

except BacktestFinished as e:
    api.close()
    print("回测结束")

