#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

import json
import talib
from tqsdk.api import *
from tqsdk.lib import TargetPosTask

'''
海龟策略
'''
class Turtle:
    def __init__(self, account_id, symbol, donchian_channel_open_position=20, donchian_channel_stop_profit=10, atr_day_length=20):
        self.account_id = account_id
        self.symbol = symbol  # 合约代码
        self.donchian_channel_open_position = donchian_channel_open_position  # 唐奇安通道的天数周期(开仓)
        self.donchian_channel_stop_profit = donchian_channel_stop_profit  # 唐奇安通道的天数周期(止盈)
        self.atr_day_length = atr_day_length  # ATR计算所用天数
        self.state = {
            "position": 0,  # 本策略净持仓数(正数表示多头，负数表示空头，0表示空仓)
            "last_price": float("nan"),  # 上次调仓价
        }

        self.n = 0
        self.unit = 0
        self.donchian_channel_high = 0
        self.donchian_channel_low = 0

        self.api = TqApi(self.account_id)
        self.quote = self.api.get_quote(self.symbol)
        # 由于ATR是路径依赖函数，因此使用更长的数据序列进行计算以便使其值稳定下来
        kline_length = max(donchian_channel_open_position + 1, donchian_channel_stop_profit + 1, atr_day_length * 5)
        self.klines = self.api.get_kline_serial(self.symbol, 24 * 60 * 60, data_length=kline_length)
        self.account = self.api.get_account()
        self.target_pos = TargetPosTask(self.api, self.symbol, init_pos=self.state["position"])

    def recalc_paramter(self):
        try:
            df = self.klines.to_dataframe()
            # 本交易日的平均真实波幅(N值)
            self.n = talib.ATR(df["high"], df["low"], df["close"], timeperiod=self.atr_day_length).iloc[-1]
            # 买卖单位
            self.unit = int((self.account["balance"] * 0.01) / (self.quote["volume_multiple"] * self.n))
            print('atr:', self.n, "  unit:", self.unit)

            # 唐奇安通道上轨：前N个交易日的最高价
            self.donchian_channel_high = max(self.klines.high[-self.donchian_channel_open_position - 1:-1])
            # 唐奇安通道下轨：前N个交易日的最低价
            self.donchian_channel_low = min(self.klines.low[-self.donchian_channel_open_position - 1:-1])
            print("唐其安通道上下轨:", self.donchian_channel_high, self.donchian_channel_low)
        except Exception:  # 若尚未接收到数据, 即数据为NaN, 则在ATR或unit计算时会报错
            return False
        return True

    def set_position(self, pos):
        self.state["position"] = pos
        self.state["last_price"] = self.quote["last_price"]
        self.target_pos.set_target_volume(self.state["position"])

    def try_open(self):
        """开仓策略"""
        while self.state["position"] == 0:
            self.api.wait_update()
            if self.api.is_changing(self.klines[-1], "datetime"):  # 如果产生新k线,则重新计算唐奇安通道及买卖单位
                self.recalc_paramter()
            if self.api.is_changing(self.quote, "last_price"):
                print("最新价: ", self.quote["last_price"])
                if self.quote["last_price"] > self.donchian_channel_high:  # 当前价>唐奇安通道上轨，买入1个Unit；(持多仓)
                    print("当前价>唐奇安通道上轨，买入1个Unit(持多仓):", self.unit, "手")
                    self.set_position(self.state["position"] + self.unit)
                elif self.quote["last_price"] < self.donchian_channel_low:  # 当前价<唐奇安通道下轨，卖出1个Unit；(持空仓)
                    print("当前价<唐奇安通道下轨，卖出1个Unit(持空仓):", self.unit, "手")
                    self.set_position(self.state["position"] - self.unit)

    def try_close(self):
        """交易策略"""
        while self.state["position"] != 0:
            self.api.wait_update()
            if self.api.is_changing(self.quote, "last_price"):
                print("最新价: ", self.quote["last_price"])

                if self.state["position"] > 0:  # 持多单
                    # 加仓策略: 如果是多仓且资产的价格在上一次建仓（或者加仓）的基础上又上涨了0.5N，就再加一个Unit的多仓
                    if self.quote["last_price"] >= self.state["last_price"] + 0.5 * self.n:
                        print("加仓:加1个Unit的多仓")
                        self.set_position(self.state["position"] + self.unit)
                    # 止损策略: 如果是多仓且资产的价格在上一次建仓（或者加仓）的基础上又下跌了2N，就卖出全部头寸止损
                    elif self.quote["last_price"] <= self.state["last_price"] - 2 * self.n:
                        print("止损:卖出全部头寸")
                        self.set_position(0)
                    # 止盈策略: 如果是多仓且当前资产价格跌破了10日唐奇安通道的下轨，就清空所有头寸结束策略,离场
                    if self.quote["last_price"] <= min(self.klines.low[-self.donchian_channel_stop_profit - 1:-1]):
                        print("止盈:清空所有头寸结束策略,离场")
                        self.set_position(0)

                elif self.state["position"] < 0:  # 持空单
                    # 加仓策略: 如果是空仓且资产的价格在上一次建仓（或者加仓）的基础上又下跌了0.5N，就再加一个Unit的空仓
                    if self.quote["last_price"] <= self.state["last_price"] - 0.5 * self.n:
                        print("加仓:加1个Unit的空仓")
                        self.set_position(self.state["position"] - self.unit)
                    # 止损策略: 如果是空仓且资产的价格在上一次建仓（或者加仓）的基础上又上涨了2N，就平仓止损
                    elif self.quote["last_price"] >= self.state["last_price"] + 2 * self.n:
                        print("止损:卖出全部头寸")
                        self.set_position(0)
                    # 止盈策略: 如果是空仓且当前资产价格升破了10日唐奇安通道的上轨，就清空所有头寸结束策略,离场
                    if self.quote["last_price"] >= max(self.klines.high[-self.donchian_channel_stop_profit - 1:-1]):
                        print("止盈:清空所有头寸结束策略,离场")
                        self.set_position(0)

    def strategy(self):
        """海龟策略"""
        print("等待K线及账户数据...")
        deadline = time.time()+5
        while not self.recalc_paramter():
            if not self.api.wait_update(deadline=deadline):
                raise Exception("获取数据失败，请确认行情连接正常并已经登录交易账户")
        while True:
            self.try_open()
            self.try_close()


if __name__ == "__main__":
    turtle = Turtle("SIM", "SHFE.au1812")
    try:
        turtle.state = json.load(open("turtle_state.json", "r"))  # 读取数据: 本策略目标净持仓数,上一次开仓价
    except FileNotFoundError:
        pass
    print("当前持仓数:", turtle.state["position"], "  上次调仓价:", turtle.state["last_price"])
    try:
        turtle.strategy()
    finally:
        turtle.api.close()
        json.dump(turtle.state, open("turtle_state.json", "w"))  # 保存数据
