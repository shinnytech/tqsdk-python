#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Chaos"

from datetime import date

import numpy as np
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished

# ===== 全局参数设置 =====
SYMBOL = "SHFE.au2306"  # 交易合约
POSITION_SIZE = 30  # 持仓手数
START_DATE = date(2023, 1, 15)  # 回测开始日期
END_DATE = date(2023, 5, 15)  # 回测结束日期

# VPT策略参数
VPT_MA_PERIOD = 14  # VPT均线周期
VOLUME_THRESHOLD = 1.5  # 成交量放大倍数阈值

print(f"开始回测 {SYMBOL} 的量价趋势(VPT)策略...")
print(f"参数: VPT均线周期={VPT_MA_PERIOD}, 成交量阈值={VOLUME_THRESHOLD}")

api = None
try:
    api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
                auth=TqAuth("快期账号", "快期密码"))

    # 订阅日K线数据
    klines = api.get_kline_serial(SYMBOL, 60 * 60 * 24)
    target_pos = TargetPosTask(api, SYMBOL)

    # 初始化交易状态
    position = 0  # 当前持仓
    entry_price = 0  # 入场价格
    vpt_values = []  # 存储VPT值

    while True:
        api.wait_update()

        if api.is_changing(klines):
            # 确保有足够的数据
            if len(klines) < VPT_MA_PERIOD + 1:
                continue

            # 计算VPT指标
            close = klines.close.values
            volume = klines.volume.values

            # 计算最新的VPT值
            if len(vpt_values) == 0:
                vpt_values.append(volume[-1])
            else:
                price_change_pct = (close[-1] - close[-2]) / close[-2]
                new_vpt = vpt_values[-1] + volume[-1] * price_change_pct
                vpt_values.append(new_vpt)

            # 保持VPT列表长度与K线数据同步
            if len(vpt_values) > len(klines):
                vpt_values.pop(0)

            # 计算VPT均线
            if len(vpt_values) >= VPT_MA_PERIOD:
                vpt_ma = np.mean(vpt_values[-VPT_MA_PERIOD:])

                # 获取当前价格和成交量数据
                current_price = float(close[-1])
                current_volume = float(volume[-1])
                avg_volume = np.mean(volume[-VPT_MA_PERIOD:-1])

                # 判断成交量是否放大
                volume_increased = current_volume > avg_volume * VOLUME_THRESHOLD

                # 交易信号判断
                vpt_trend_up = vpt_values[-1] > vpt_ma
                vpt_trend_down = vpt_values[-1] < vpt_ma

                # 交易逻辑
                if position == 0:  # 空仓
                    if vpt_trend_up and volume_increased and close[-1] > close[-2]:
                        position = POSITION_SIZE
                        entry_price = current_price
                        target_pos.set_target_volume(position)
                        print(f"开多仓: 价格={current_price:.2f}, VPT上穿均线")

                    elif vpt_trend_down and volume_increased and close[-1] < close[-2]:
                        position = -POSITION_SIZE
                        entry_price = current_price
                        target_pos.set_target_volume(position)
                        print(f"开空仓: 价格={current_price:.2f}, VPT下穿均线")

                elif position > 0:  # 持有多头
                    if vpt_trend_down and volume_increased:
                        profit_pct = (current_price / entry_price - 1) * 100
                        target_pos.set_target_volume(0)
                        print(f"平多仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")
                        position = 0
                        entry_price = 0

                elif position < 0:  # 持有空头
                    if vpt_trend_up and volume_increased:
                        profit_pct = (entry_price / current_price - 1) * 100
                        target_pos.set_target_volume(0)
                        print(f"平空仓: 价格={current_price:.2f}, 盈亏={profit_pct:.2f}%")
                        position = 0
                        entry_price = 0

except BacktestFinished as e:
    print(f"策略运行异常: {e}")
    api.close()