#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Chaos"

from datetime import date
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished
from tqsdk.tafunc import time_to_str
from tqsdk.ta import CCI

# ===== 全局参数设置 =====
SYMBOL = "SHFE.au2406"  # 黄金期货主力合约
POSITION_SIZE = 50  # 每次交易手数
START_DATE = date(2023, 9, 20)  # 回测开始日期
END_DATE = date(2024, 2, 28)  # 回测结束日期

# CCI参数
CCI_PERIOD = 10  # CCI计算周期
CCI_UPPER = 100  # CCI上轨
CCI_LOWER = -100  # CCI下轨
STOP_LOSS_PERCENT = 0.01  # 止损比例

# ===== 全局变量 =====
current_direction = 0  # 当前持仓方向：1=多头，-1=空头，0=空仓
entry_price = 0  # 开仓价格
stop_loss_price = 0  # 止损价格
last_cci_state = 0  # 上一次CCI状态：1=高于上轨，-1=低于下轨，0=中间区域

# ===== 策略开始 =====
print("开始运行CCI均值回归策略...")

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
            if len(klines) < CCI_PERIOD + 10:
                continue
            
            # 计算CCI
            cci_series = CCI(klines, CCI_PERIOD)
            cci = cci_series.iloc[-1].item()  # 使用item()方法获取标量值
            current_price = klines.close.iloc[-1].item()  # 同样使用item()方法
            
            # 确定当前CCI状态
            current_cci_state = 0
            if cci > CCI_UPPER:
                current_cci_state = 1
            elif cci < CCI_LOWER:
                current_cci_state = -1
            
            # 获取最新数据
            current_timestamp = klines.datetime.iloc[-1]
            current_datetime = time_to_str(current_timestamp)
            
            # 打印当前状态
            print(f"日期: {current_datetime}, 价格: {current_price:.2f}, CCI: {cci:.2f}")
            
            # ===== 交易逻辑 =====
            
            # 空仓状态 - 寻找开仓机会
            if current_direction == 0:
                # 多头开仓条件：CCI从下轨上穿
                if last_cci_state == -1 and current_cci_state == 0:
                    current_direction = 1
                    target_pos.set_target_volume(POSITION_SIZE)
                    entry_price = current_price
                    stop_loss_price = entry_price * (1 - STOP_LOSS_PERCENT)
                    print(f"多头开仓: 价格={entry_price:.2f}, 止损价={stop_loss_price:.2f}")
                
                # 空头开仓条件：CCI从上轨下穿
                elif last_cci_state == 1 and current_cci_state == 0:
                    current_direction = -1
                    target_pos.set_target_volume(-POSITION_SIZE)
                    entry_price = current_price
                    stop_loss_price = entry_price * (1 + STOP_LOSS_PERCENT)
                    print(f"空头开仓: 价格={entry_price:.2f}, 止损价={stop_loss_price:.2f}")
            
            # 多头持仓 - 检查平仓条件
            elif current_direction == 1:
                # 止盈条件：CCI从上轨下穿
                if last_cci_state == 1 and current_cci_state == 0:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止盈平仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")
                
                # 止损条件：价格跌破止损价
                elif current_price < stop_loss_price:
                    loss_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"多头止损平仓: 价格={current_price:.2f}, 亏损={loss_pct:.2f}%")
            
            # 空头持仓 - 检查平仓条件
            elif current_direction == -1:
                # 止盈条件：CCI从下轨上穿
                if last_cci_state == -1 and current_cci_state == 0:
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止盈平仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")
                
                # 止损条件：价格突破止损价
                elif current_price > stop_loss_price:
                    loss_pct = (current_price - entry_price) / entry_price * 100
                    target_pos.set_target_volume(0)
                    current_direction = 0
                    print(f"空头止损平仓: 价格={current_price:.2f}, 亏损={loss_pct:.2f}%")
            
            # 更新上一次CCI状态
            last_cci_state = current_cci_state

except BacktestFinished as e:
    print("回测结束")
    api.close()