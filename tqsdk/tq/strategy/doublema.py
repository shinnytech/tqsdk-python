#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

import talib
import numpy as np
from tqsdk import TargetPosTask
from tqsdk.tq.strategy.base import StrategyBase


class StrategyDoubleMA(StrategyBase):
    def __init__(self, api, desc, stg_id, desc_chan):
        StrategyBase.__init__(self, api, desc, stg_id, desc_chan)
        self.add_input("合约代码", "symbol", "SHFE.bu1906", str)
        self.add_input("短周期", "short", 30, int)
        self.add_input("长周期", "long", 60, int)
        self.add_switch()
        self.add_console()
        self.set_status()
        self.show()

    def get_desc(self):
        return "合约代码 %s, 短周期 %d, 长周期 %d" % (self.symbol, self.short, self.long)

    async def run_strategy(self):
        data_length = self.long + 2  # k线数据长度
        # "duration_seconds=60"为一分钟线, 日线的duration_seconds参数为: 24*60*60
        klines = self.api.get_kline_serial(self.symbol, duration_seconds=60, data_length=data_length)
        target_pos = TargetPosTask(self.api, self.symbol)

        try:
            async with self.api.register_update_notify() as update_chan:
                async for _ in update_chan:
                    if self.api.is_changing(klines[-1], "datetime"):  # 产生新k线:重新计算SMA
                        short_avg = talib.SMA(np.array(klines.close), timeperiod=self.short)  # 短周期
                        long_avg = talib.SMA(np.array(klines.close), timeperiod=self.long)  # 长周期
                        # 均线下穿，做空
                        if long_avg[-2] < short_avg[-2] and long_avg[-1] > short_avg[-1]:
                            target_pos.set_target_volume(-3)
                            print("均线下穿，做空")
                        # 均线上穿，做多
                        if short_avg[-2] < long_avg[-2] and short_avg[-1] > long_avg[-1]:
                            target_pos.set_target_volume(3)
                            print("均线上穿，做多")
        finally:
            target_pos.task.cancel()
