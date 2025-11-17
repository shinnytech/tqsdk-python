#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Chaos"

from datetime import date
import pandas as pd
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished
from tqsdk.ta import ATR, MA

# ===== 全局参数设置 =====
SYMBOL = "SHFE.au2306"
POSITION_SIZE = 30  # 每次交易手数
START_DATE = date(2023, 4, 10)  # 回测开始日期
END_DATE = date(2023, 4, 26)  # 回测结束日期

# 1小时K线
KLINE_PERIOD = 60 * 60

# 分形识别参数
FRACTAL_WINDOW = 2  # 分形窗口大小

# 确认指标参数
SHORT_MA_PERIOD = 6  # 短期MA周期
LONG_MA_PERIOD = 12  # 长期MA周期
VOLUME_PERIOD = 5  # 成交量平均周期
ATR_PERIOD = 10  # ATR计算周期

# 风控参数
ATR_MULTIPLIER = 1.2  # 止损ATR乘数
TP_RATIO = 1.8  # 止盈比例

# ===== 全局变量 =====
current_direction = 0  # 当前持仓方向：1=多头，-1=空头，0=空仓
entry_price = 0  # 开仓价格
stop_loss_price = 0  # 止损价格
take_profit_price = 0  # 止盈价格
last_bull_fractal = None  # 最近的牛市分形
last_bear_fractal = None  # 最近的熊市分形


# ===== 分形识别函数 =====
def identify_fractals(klines):
    """识别牛市和熊市分形"""
    bull_fractals = []  # 牛市分形列表 [(index, low_price, high_price), ...]
    bear_fractals = []  # 熊市分形列表 [(index, low_price, high_price), ...]

    # 至少需要2*FRACTAL_WINDOW+1个K线才能形成分形
    if len(klines) < 2 * FRACTAL_WINDOW + 1:
        return bull_fractals, bear_fractals

    # 遍历K线，寻找分形
    start_idx = max(FRACTAL_WINDOW, len(klines) - 20)
    end_idx = len(klines) - FRACTAL_WINDOW

    for i in range(start_idx, end_idx):
        # 牛市分形：中间K线的低点低于两侧K线的低点
        is_bull_fractal = True
        for j in range(1, FRACTAL_WINDOW + 1):
            if klines.low.iloc[i] >= klines.low.iloc[i - j] or klines.low.iloc[i] >= klines.low.iloc[i + j]:
                is_bull_fractal = False
                break

        if is_bull_fractal:
            bull_fractals.append((i, klines.low.iloc[i], klines.high.iloc[i]))

        # 熊市分形：中间K线的高点高于两侧K线的高点
        is_bear_fractal = True
        for j in range(1, FRACTAL_WINDOW + 1):
            if klines.high.iloc[i] <= klines.high.iloc[i - j] or klines.high.iloc[i] <= klines.high.iloc[i + j]:
                is_bear_fractal = False
                break

        if is_bear_fractal:
            bear_fractals.append((i, klines.low.iloc[i], klines.high.iloc[i]))

    return bull_fractals, bear_fractals


# ===== 策略开始 =====
print("开始运行基于分形的趋势突破期货策略...")
print(f"品种: {SYMBOL}, 回测周期: {START_DATE} 至 {END_DATE}")

# 创建API实例
api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
            auth=TqAuth("快期账号", "快期密码"))

# 订阅合约的K线数据
klines = api.get_kline_serial(SYMBOL, KLINE_PERIOD)  # 1小时K线

# 创建目标持仓任务
target_pos = TargetPosTask(api, SYMBOL)

try:
    while True:
        # 等待更新
        api.wait_update()

        # 如果K线更新
        if api.is_changing(klines.iloc[-1], "datetime"):
            # 确保有足够的数据计算指标
            if len(klines) < max(SHORT_MA_PERIOD, LONG_MA_PERIOD, ATR_PERIOD) + 5:
                print(f"数据不足，当前K线数量: {len(klines)}")
                continue

            # 计算确认指标
            klines["short_ma"] = MA(klines, SHORT_MA_PERIOD).ma
            klines["long_ma"] = MA(klines, LONG_MA_PERIOD).ma
            klines["volume_avg"] = klines.volume.rolling(VOLUME_PERIOD).mean().fillna(0)
            atr = ATR(klines, ATR_PERIOD).atr

            # 识别分形
            bull_fractals, bear_fractals = identify_fractals(klines)

            # 更新最近的分形
            if bull_fractals:
                last_bull_fractal = bull_fractals[-1]
                print(
                    f"发现新牛市分形: 索引={last_bull_fractal[0]}, 低点={last_bull_fractal[1]}, 高点={last_bull_fractal[2]}")

            if bear_fractals:
                last_bear_fractal = bear_fractals[-1]
                print(
                    f"发现新熊市分形: 索引={last_bear_fractal[0]}, 低点={last_bear_fractal[1]}, 高点={last_bear_fractal[2]}")

            # 获取当前价格和指标数据
            current_price = float(klines.close.iloc[-1])
            current_volume = float(klines.volume.iloc[-1])
            current_short_ma = float(klines.short_ma.iloc[-1])
            current_long_ma = float(klines.long_ma.iloc[-1])
            current_volume_avg = float(klines.volume_avg.iloc[-1] if not pd.isna(klines.volume_avg.iloc[-1]) else 0)
            current_atr = float(atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0)

            # 确定当前趋势
            uptrend = current_short_ma > current_long_ma
            downtrend = current_short_ma < current_long_ma

            # 输出当前状态
            current_time = pd.to_datetime(klines.datetime.iloc[-1], unit='ns')
            print(f"时间: {current_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"价格: {current_price}, ATR: {current_atr:.2f}")
            print(f"短期MA: {current_short_ma:.2f}, 长期MA: {current_long_ma:.2f}")
            print(f"趋势方向: {'上升' if uptrend else '下降' if downtrend else '盘整'}")
            print(f"当前成交量: {current_volume}, 平均成交量: {current_volume_avg:.2f}")

            # ===== 交易逻辑 =====

            # 空仓状态 - 寻找开仓机会
            if current_direction == 0:
                # 多头入场信号
                if (last_bull_fractal and
                        last_bull_fractal[0] < len(klines) - 1 and  # 确认分形不是最新K线
                        current_price > last_bull_fractal[2] and  # 价格突破牛市分形高点
                        uptrend):  # 上升趋势确认

                    current_direction = 1
                    entry_price = current_price
                    target_pos.set_target_volume(POSITION_SIZE)

                    # 设置止损和止盈
                    stop_loss_price = last_bull_fractal[1] - current_atr * ATR_MULTIPLIER
                    take_profit_price = entry_price + (entry_price - stop_loss_price) * TP_RATIO

                    print(f"多头开仓: 价格={entry_price}, 止损={stop_loss_price:.2f}, 止盈={take_profit_price:.2f}")

                # 空头入场信号
                elif (last_bear_fractal and
                      last_bear_fractal[0] < len(klines) - 1 and  # 确认分形不是最新K线
                      current_price < last_bear_fractal[1] and  # 价格跌破熊市分形低点
                      downtrend):  # 下降趋势确认

                    current_direction = -1
                    entry_price = current_price
                    target_pos.set_target_volume(-POSITION_SIZE)

                    # 设置止损和止盈
                    stop_loss_price = last_bear_fractal[2] + current_atr * ATR_MULTIPLIER
                    take_profit_price = entry_price - (stop_loss_price - entry_price) * TP_RATIO

                    print(f"空头开仓: 价格={entry_price}, 止损={stop_loss_price:.2f}, 止盈={take_profit_price:.2f}")

            # 多头持仓 - 检查平仓条件
            elif current_direction == 1:
                # 1. 止损条件
                if current_price <= stop_loss_price:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止损平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")

                # 2. 止盈条件
                elif current_price >= take_profit_price:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止盈平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")

                # 3. 价格跌破短期MA
                elif current_price < current_short_ma:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头MA平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")

                # 4. 出现新的熊市分形且价格跌破该分形的低点
                elif (last_bear_fractal and
                      last_bear_fractal[0] > klines.index[-10] and  # 确保是较新的分形
                      current_price < last_bear_fractal[1]):
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头分形反转平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")

            # 空头持仓 - 检查平仓条件
            elif current_direction == -1:
                # 1. 止损条件
                if current_price >= stop_loss_price:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止损平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")

                # 2. 止盈条件
                elif current_price <= take_profit_price:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止盈平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")

                # 3. 价格突破短期MA
                elif current_price > current_short_ma:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头MA平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")

                # 4. 出现新的牛市分形且价格突破该分形的高点
                elif (last_bull_fractal and
                      last_bull_fractal[0] > klines.index[-10] and  # 确保是较新的分形
                      current_price > last_bull_fractal[2]):
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头分形反转平仓: 价格={current_price}, 盈亏={profit_pct:.2f}%")

except BacktestFinished as e:
    print("回测结束")
    api.close()