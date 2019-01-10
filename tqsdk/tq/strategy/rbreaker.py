#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk import TargetPosTask
from tqsdk.tq.strategy.base import StrategyBase


class StrategyRBreaker(StrategyBase):
    def __init__(self, api, desc, stg_id, desc_chan):
        StrategyBase.__init__(self, api, desc, stg_id, desc_chan)
        self.add_input("合约代码", "symbol", "SHFE.au1812", str)
        self.add_input("止损点", "stop_loss_price", 10, float)
        self.add_switch()
        self.add_console()
        self.set_status()
        self.show()

    def get_desc(self):
        return "合约代码 %s, 止损点 %f" % (self.symbol, self.stop_loss_price)

    async def run_strategy(self):
        quote = self.api.get_quote(self.symbol)
        klines = self.api.get_kline_serial(self.symbol, 24*60*60)  # 86400: 使用日线
        position = self.api.get_position(self.symbol)
        target_pos = TargetPosTask(self.api, self.symbol)
        target_pos_value = position["volume_long"] - position["volume_short"]  # 目标净持仓数
        open_position_price = position["open_price_long"] if target_pos_value > 0 else position["open_price_short"]  # 开仓价
        pivot, bBreak, sSetup, sEnter, bEnter, bSetup, sBreak = self.get_index_line(klines)  # 七条标准线

        try:
            async with self.api.register_update_notify() as update_chan:
                while True:
                    target_pos.set_target_volume(target_pos_value)
                    await update_chan.recv()
                    if self.api.is_changing(klines[-1], "datetime"):  # 产生新k线,则重新计算7条指标线
                        pivot, bBreak, sSetup, sEnter, bEnter, bSetup, sBreak = self.get_index_line(klines)

                    '''交易规则'''
                    if self.api.is_changing(quote, "last_price"):
                        print("最新价: ", quote["last_price"])

                        # 开仓价与当前行情价之差大于止损点则止损
                        if (target_pos_value > 0 and open_position_price - quote["last_price"] >= self.stop_loss_price) or\
                            (target_pos_value < 0 and quote["last_price"] - open_position_price >= self.stop_loss_price):
                            target_pos_value = 0  # 平仓

                        # 反转:
                        if target_pos_value > 0:  # 多头持仓
                            if quote["highest"] > sSetup and quote["last_price"] < sEnter:
                                # 多头持仓,当日内最高价超过观察卖出价后，
                                # 盘中价格出现回落，且进一步跌破反转卖出价构成的支撑线时，
                                # 采取反转策略，即在该点位反手做空
                                print("多头持仓,当日内最高价超过观察卖出价后跌破反转卖出价: 反手做空")
                                target_pos_value = -3  # 做空
                                open_position_price = quote["last_price"]
                        elif target_pos_value < 0:  # 空头持仓
                            if quote["lowest"] < bSetup and quote["last_price"] > bEnter:
                                # 空头持仓，当日内最低价低于观察买入价后，
                                # 盘中价格出现反弹，且进一步超过反转买入价构成的阻力线时，
                                # 采取反转策略，即在该点位反手做多
                                print("空头持仓,当日最低价低于观察买入价后超过反转买入价: 反手做多")
                                target_pos_value = 3  # 做多
                                open_position_price = quote["last_price"]

                        # 突破:
                        elif target_pos_value == 0:  # 空仓条件
                            if quote["last_price"] > bBreak:
                                # 在空仓的情况下，如果盘中价格超过突破买入价，
                                # 则采取趋势策略，即在该点位开仓做多
                                print("空仓,盘中价格超过突破买入价: 开仓做多")
                                target_pos_value = 3  # 做多
                                open_position_price = quote["last_price"]
                            elif quote["last_price"] < sBreak:
                                # 在空仓的情况下，如果盘中价格跌破突破卖出价，
                                # 则采取趋势策略，即在该点位开仓做空
                                print("空仓,盘中价格跌破突破卖出价: 开仓做空")
                                target_pos_value = -3  # 做空
                                open_position_price = quote["last_price"]
        finally:
            target_pos.task.cancel()

    def get_index_line(self, klines):
        '''计算指标线'''
        high = klines[-2]["high"]  # 前一日的最高价
        low = klines[-2]["low"]  # 前一日的最低价
        close = klines[-2]["close"]  # 前一日的收盘价

        pivot = (high + low + close) / 3  # 枢轴点
        bBreak = high + 2 * (pivot - low)  # 突破买入价
        sSetup = pivot + (high - low)  # 观察卖出价
        sEnter = 2 * pivot - low  # 反转卖出价
        bEnter = 2 * pivot - high  # 反转买入价
        bSetup = pivot - (high - low)  # 观察买入价
        sBreak = low - 2 * (high - pivot)  # 突破卖出价

        print("已计算新标志线: ", "\n枢轴点", pivot, "\n突破买入价", bBreak, "\n观察卖出价", sSetup,
              "\n反转卖出价", sEnter, "\n反转买入价", bEnter, "\n观察买入价", bSetup, "\n突破卖出价", sBreak)
        return pivot, bBreak, sSetup, sEnter, bEnter, bSetup, sBreak
