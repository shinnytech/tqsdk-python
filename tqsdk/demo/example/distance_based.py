#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Chaos'

from tqsdk import TqApi, TqAuth, TargetPosTask, TqBacktest, BacktestFinished
from datetime import date, datetime
import numpy as np

# === 全局参数 ===
SYMBOL1 = "SHFE.rb2305"
SYMBOL2 = "SHFE.hc2305"
WINDOW = 30
K_THRESHOLD = 2.0
CLOSE_THRESHOLD = 0.5
MAX_HOLD_DAYS = 10
STOP_LOSS_PCT = 0.05
POSITION_LOTS1 = 200      # 合约1固定手数
POSITION_RATIO = 1.0     # 合约2与合约1的数量比例

# === 全局变量 ===
price_data1, price_data2 = [], []
position_long = False
position_short = False
entry_price1 = 0
entry_price2 = 0
position_time = None
trade_ratio = 1
entry_spread = 0
trade_count = 0
win_count = 0
total_profit = 0

# === API初始化 ===
api = TqApi(backtest=TqBacktest(start_dt=date(2023, 2, 1),end_dt=date(2023, 4, 27)),
            auth=TqAuth("快期账号", "快期密码")
)
quote1 = api.get_quote(SYMBOL1)
quote2 = api.get_quote(SYMBOL2)
klines1 = api.get_kline_serial(SYMBOL1, 24*60*60)
klines2 = api.get_kline_serial(SYMBOL2, 24*60*60)
target_pos1 = TargetPosTask(api, SYMBOL1)
target_pos2 = TargetPosTask(api, SYMBOL2)

print(f"策略开始运行，交易品种: {SYMBOL1} 和 {SYMBOL2}")

try:
    while True:
        api.wait_update()
        if api.is_changing(klines1.iloc[-1], "datetime") or api.is_changing(klines2.iloc[-1], "datetime"):
            price_data1.append(klines1.iloc[-1]["close"])
            price_data2.append(klines2.iloc[-1]["close"])
            if len(price_data1) <= WINDOW:
                continue
            if len(price_data1) > WINDOW:
                price_data1 = price_data1[-WINDOW:]
                price_data2 = price_data2[-WINDOW:]
            data1 = np.array(price_data1)
            data2 = np.array(price_data2)
            norm1 = (data1 - np.mean(data1)) / np.std(data1)
            norm2 = (data2 - np.mean(data2)) / np.std(data2)
            spread = norm1 - norm2
            mean_spread = np.mean(spread)
            std_spread = np.std(spread)
            current_spread = spread[-1]
            price_ratio = quote2.last_price / quote1.last_price
            trade_ratio = round(price_ratio * POSITION_RATIO, 2)
            position_lots2 = int(POSITION_LOTS1 * trade_ratio)
            current_time = datetime.fromtimestamp(klines1.iloc[-1]["datetime"] / 1e9)

            # === 平仓逻辑 ===
            if position_long or position_short:
                days_held = (current_time - position_time).days
                if position_long:
                    current_profit = (quote1.last_price - entry_price1) * POSITION_LOTS1 - (quote2.last_price - entry_price2) * position_lots2
                else:
                    current_profit = (entry_price1 - quote1.last_price) * POSITION_LOTS1 - (entry_price2 - quote2.last_price) * position_lots2
                profit_pct = current_profit / (entry_price1 * POSITION_LOTS1)
                close_by_mean = abs(current_spread - mean_spread) < CLOSE_THRESHOLD * std_spread
                close_by_time = days_held >= MAX_HOLD_DAYS
                close_by_stop = profit_pct <= -STOP_LOSS_PCT
                if close_by_mean or close_by_time or close_by_stop:
                    target_pos1.set_target_volume(0)
                    target_pos2.set_target_volume(0)
                    trade_count += 1
                    if profit_pct > 0:
                        win_count += 1
                    total_profit += current_profit
                    reason = "均值回归" if close_by_mean else "时间限制" if close_by_time else "止损"
                    print(f"平仓 - {reason}, 盈亏: {profit_pct:.2%}, 持仓天数: {days_held}")
                    position_long = False
                    position_short = False

            # === 开仓逻辑 ===
            else:
                if current_spread < mean_spread - K_THRESHOLD * std_spread:
                    target_pos1.set_target_volume(POSITION_LOTS1)
                    target_pos2.set_target_volume(-position_lots2)
                    position_long = True
                    position_time = current_time
                    entry_price1 = quote1.last_price
                    entry_price2 = quote2.last_price
                    entry_spread = current_spread
                    print(f"开仓 - 多价差, 合约1: {POSITION_LOTS1}手, 合约2: {-position_lots2}手, 比例: {trade_ratio}")
                elif current_spread > mean_spread + K_THRESHOLD * std_spread:
                    target_pos1.set_target_volume(-POSITION_LOTS1)
                    target_pos2.set_target_volume(position_lots2)
                    position_short = True
                    position_time = current_time
                    entry_price1 = quote1.last_price
                    entry_price2 = quote2.last_price
                    entry_spread = current_spread
                    print(f"开仓 - 空价差, 合约1: {-POSITION_LOTS1}手, 合约2: {position_lots2}手, 比例: {trade_ratio}")

        # 每日统计
        if api.is_changing(klines1.iloc[-1], "datetime"):
            account = api.get_account()
            print(f"日期: {current_time.date()}, 账户权益: {account.balance:.2f}, 可用资金: {account.available:.2f}")
            if trade_count > 0:
                print(f"交易统计 - 总交易: {trade_count}, 胜率: {win_count/trade_count:.2%}, 总盈亏: {total_profit:.2f}")

except BacktestFinished as e:
    print("回测结束")
    api.close()

