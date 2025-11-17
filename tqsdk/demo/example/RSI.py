#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Chaos"

from datetime import date
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished
from tqsdk.ta import RSI
from tqsdk.tafunc import time_to_str

# ===== 全局参数设置 =====
SYMBOL = "DCE.a2101"
POSITION_SIZE = 500  # 每次交易手数
START_DATE = date(2020, 4, 20)  # 回测开始日期
END_DATE = date(2020, 11, 20)  # 回测结束日期

# RSI参数
RSI_PERIOD = 6  # RSI计算周期，
OVERBOUGHT_THRESHOLD = 65  # 超买阈值
OVERSOLD_THRESHOLD = 35  # 超卖阈值

# 风控参数
STOP_LOSS_PERCENT = 0.01  # 止损百分比
TIME_STOP_DAYS = 10  # 缩短时间止损天数

# ===== 全局变量 =====
current_direction = 0  # 当前持仓方向：1=多头，-1=空头，0=空仓
entry_price = 0  # 开仓价格
stop_loss_price = 0  # 止损价格
entry_date = None  # 开仓日期
was_overbought = False  # 是否曾进入超买区域
was_oversold = False  # 是否曾进入超卖区域

# ===== 策略开始 =====
print("开始运行RSI超买/超卖反转策略...")

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
            if len(klines) < RSI_PERIOD + 10:
                continue

            # 使用天勤的RSI函数计算
            rsi = RSI(klines, RSI_PERIOD)
            current_rsi = float(rsi.iloc[-1].iloc[0])
            previous_rsi = float(rsi.iloc[-2].iloc[0])

            # 更新超买/超卖状态
            if previous_rsi > OVERBOUGHT_THRESHOLD:
                was_overbought = True
            if previous_rsi < OVERSOLD_THRESHOLD:
                was_oversold = True

            # 获取最新数据
            current_price = float(klines.close.iloc[-1])
            current_timestamp = klines.datetime.iloc[-1]
            current_datetime = time_to_str(current_timestamp)  # 使用time_to_str转换时间

            # 打印当前状态
            print(f"日期: {current_datetime}, 价格: {current_price:.2f}, RSI: {current_rsi:.2f}")

            # ===== 交易逻辑 =====

            # 空仓状态 - 寻找开仓机会
            if current_direction == 0:
                # 多头开仓条件：RSI从超卖区域回升
                if was_oversold and previous_rsi < OVERSOLD_THRESHOLD and current_rsi > OVERSOLD_THRESHOLD:
                    current_direction = 1
                    target_pos.set_target_volume(POSITION_SIZE)
                    entry_price = current_price
                    stop_loss_price = entry_price * (1 - STOP_LOSS_PERCENT)
                    entry_date = current_timestamp  # 存储时间戳
                    print(f"多头开仓: 价格={entry_price:.2f}, 止损={stop_loss_price:.2f}")
                    was_oversold = False  # 重置超卖状态

                # 空头开仓条件：RSI从超买区域回落
                elif was_overbought and previous_rsi > OVERBOUGHT_THRESHOLD and current_rsi < OVERBOUGHT_THRESHOLD:
                    current_direction = -1
                    target_pos.set_target_volume(-POSITION_SIZE)
                    entry_price = current_price
                    stop_loss_price = entry_price * (1 + STOP_LOSS_PERCENT)
                    entry_date = current_timestamp  # 存储时间戳
                    print(f"空头开仓: 价格={entry_price:.2f}, 止损={stop_loss_price:.2f}")
                    was_overbought = False  # 重置超买状态

            # 多头持仓 - 检查平仓条件
            elif current_direction == 1:
                # 止损条件
                if current_price <= stop_loss_price:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止损平仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")

                # 止盈条件：RSI进入超买区域
                elif current_rsi > OVERBOUGHT_THRESHOLD:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止盈平仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")

                # 时间止损
                elif (current_timestamp - entry_date) / (60 * 60 * 24) >= TIME_STOP_DAYS:  # 计算天数差
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头时间止损: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")

            # 空头持仓 - 检查平仓条件
            elif current_direction == -1:
                # 止损条件
                if current_price >= stop_loss_price:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止损平仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")

                # 止盈条件：RSI进入超卖区域
                elif current_rsi < OVERSOLD_THRESHOLD:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止盈平仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")

                # 时间止损
                elif (current_timestamp - entry_date) / (60 * 60 * 24) >= TIME_STOP_DAYS:  # 计算天数差
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头时间止损: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")

except BacktestFinished as e:
    print("回测结束")
    api.close()