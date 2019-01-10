#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk import TargetPosTask
from tqsdk.tq.strategy.base import StrategyBase


class StrategyDualThrust(StrategyBase):
    def __init__(self, api, desc, stg_id, desc_chan):
        StrategyBase.__init__(self, api, desc, stg_id, desc_chan)
        self.add_input("合约代码", "symbol", "SHFE.rb1901", str)
        self.add_input("天数", "Nday", 5, int)
        self.add_input("上轨K值", "K1", 0.2, float)
        self.add_input("下轨K值", "K2", 0.2, float)
        self.add_switch()
        self.add_console()
        self.set_status()
        self.show()

    def get_desc(self):
        return "合约代码 %s, 天数 %d, 上轨K值 %f, 下轨K值 %f" % (self.symbol, self.Nday, self.K1, self.K2)

    async def run_strategy(self):
        quote = self.api.get_quote(self.symbol)
        klines = self.api.get_kline_serial(self.symbol, 24 * 60 * 60)  # 86400使用日线
        target_pos = TargetPosTask(self.api, self.symbol)
        buy_line, sell_line = self.dual_thrust(quote, klines)  # 获取上下轨

        try:
            async with self.api.register_update_notify() as update_chan:
                async for _ in update_chan:
                    if self.api.is_changing(klines[-1], "datetime") or self.api.is_changing(quote, "open"):  # 新产生一根日线或开盘价发生变化: 重新计算上下轨
                        buy_line, sell_line = self.dual_thrust(quote, klines)
                    if self.api.is_changing(quote, "last_price"):
                        print("最新价变化", quote["last_price"], end=':')
                        if quote["last_price"] > buy_line:  # 高于上轨
                            print("高于上轨,目标持仓 多头3手")
                            target_pos.set_target_volume(3)  # 交易
                        elif quote["last_price"] < sell_line:  # 低于下轨
                            print("低于下轨,目标持仓 空头3手")
                            target_pos.set_target_volume(-3)  # 交易
                        else:
                            print('未穿越上下轨,不调整持仓')
        finally:
            target_pos.task.cancel()

    def dual_thrust(self, quote, klines):
        current_open = quote["open"]
        HH = max(klines.high[-self.Nday - 1:-1])  # N日最高价的最高价
        HC = max(klines.close[-self.Nday - 1:-1])  # N日收盘价的最高价
        LC = min(klines.close[-self.Nday - 1:-1])  # N日收盘价的最低价
        LL = min(klines.low[-self.Nday - 1:-1])  # N日最低价的最低价
        range = max(HH - LC, HC - LL)
        buy_line = current_open + range * self.K1  # 上轨
        sell_line = current_open - range * self.K2  # 下轨

        print("当前开盘价:", current_open, "\n上轨:", buy_line, "\n下轨:", sell_line)
        return buy_line, sell_line
