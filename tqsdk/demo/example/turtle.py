#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

'''
海龟策略 (难度：中级)
参考: https://www.shinnytech.com/blog/turtle/
注: 该示例策略仅用于功能示范, 实盘时请根据自己的策略/经验进行修改
'''

import json
import time
from tqsdk import TqApi, TqAuth, TargetPosTask
from tqsdk.ta import ATR


class Turtle:
    def __init__(self, symbol, account=None, auth=None, donchian_channel_open_position=20,
                 donchian_channel_stop_profit=10,
                 atr_day_length=20, max_risk_ratio=0.5):
        self.account = account  # 交易账号
        self.auth = auth  # 信易账户
        self.symbol = symbol  # 合约代码
        self.donchian_channel_open_position = donchian_channel_open_position  # 唐奇安通道的天数周期(开仓)
        self.donchian_channel_stop_profit = donchian_channel_stop_profit  # 唐奇安通道的天数周期(止盈)
        self.atr_day_length = atr_day_length  # ATR计算所用天数
        self.max_risk_ratio = max_risk_ratio  # 最高风险度
        self.state = {
            "position": 0,  # 本策略净持仓数(正数表示多头，负数表示空头，0表示空仓)
            "last_price": float("nan"),  # 上次调仓价
        }

        self.n = 0  # 平均真实波幅(N值)
        self.unit = 0  # 买卖单位
        self.donchian_channel_high = 0  # 唐奇安通道上轨
        self.donchian_channel_low = 0  # 唐奇安通道下轨

        self.api = TqApi(self.account, auth=self.auth)
        self.quote = self.api.get_quote(self.symbol)
        # 由于ATR是路径依赖函数，因此使用更长的数据序列进行计算以便使其值稳定下来
        kline_length = max(donchian_channel_open_position + 1, donchian_channel_stop_profit + 1, atr_day_length * 5)
        self.klines = self.api.get_kline_serial(self.symbol, 24 * 60 * 60, data_length=kline_length)
        self.account = self.api.get_account()
        self.target_pos = TargetPosTask(self.api, self.symbol)

    def recalc_paramter(self):
        # 平均真实波幅(N值)
        self.n = ATR(self.klines, self.atr_day_length)["atr"].iloc[-1]
        # 买卖单位
        self.unit = int((self.account.balance * 0.01) / (self.quote.volume_multiple * self.n))
        # 唐奇安通道上轨：前N个交易日的最高价
        self.donchian_channel_high = max(self.klines.high[-self.donchian_channel_open_position - 1:-1])
        # 唐奇安通道下轨：前N个交易日的最低价
        self.donchian_channel_low = min(self.klines.low[-self.donchian_channel_open_position - 1:-1])
        print("唐其安通道上下轨: %f, %f" % (self.donchian_channel_high, self.donchian_channel_low))
        return True

    def set_position(self, pos):
        self.state["position"] = pos
        self.state["last_price"] = self.quote["last_price"]
        self.target_pos.set_target_volume(self.state["position"])

    def try_open(self):
        """开仓策略"""
        while self.state["position"] == 0:
            self.api.wait_update()
            if self.api.is_changing(self.klines.iloc[-1], "datetime"):  # 如果产生新k线,则重新计算唐奇安通道及买卖单位
                self.recalc_paramter()
            if self.api.is_changing(self.quote, "last_price"):
                print("最新价: %f" % self.quote.last_price)
                if self.quote.last_price > self.donchian_channel_high:  # 当前价>唐奇安通道上轨，买入1个Unit；(持多仓)
                    print("当前价>唐奇安通道上轨，买入1个Unit(持多仓): %d 手" % self.unit)
                    self.set_position(self.state["position"] + self.unit)
                elif self.quote.last_price < self.donchian_channel_low:  # 当前价<唐奇安通道下轨，卖出1个Unit；(持空仓)
                    print("当前价<唐奇安通道下轨，卖出1个Unit(持空仓): %d 手" % self.unit)
                    self.set_position(self.state["position"] - self.unit)

    def try_close(self):
        """交易策略"""
        while self.state["position"] != 0:
            self.api.wait_update()
            if self.api.is_changing(self.quote, "last_price"):
                print("最新价: ", self.quote.last_price)
                if self.state["position"] > 0:  # 持多单
                    # 加仓策略: 如果是多仓且行情最新价在上一次建仓（或者加仓）的基础上又上涨了0.5N，就再加一个Unit的多仓,并且风险度在设定范围内(以防爆仓)
                    if self.quote.last_price >= self.state[
                        "last_price"] + 0.5 * self.n and self.account.risk_ratio <= self.max_risk_ratio:
                        print("加仓:加1个Unit的多仓")
                        self.set_position(self.state["position"] + self.unit)
                    # 止损策略: 如果是多仓且行情最新价在上一次建仓（或者加仓）的基础上又下跌了2N，就卖出全部头寸止损
                    elif self.quote.last_price <= self.state["last_price"] - 2 * self.n:
                        print("止损:卖出全部头寸")
                        self.set_position(0)
                    # 止盈策略: 如果是多仓且行情最新价跌破了10日唐奇安通道的下轨，就清空所有头寸结束策略,离场
                    if self.quote.last_price <= min(self.klines.low[-self.donchian_channel_stop_profit - 1:-1]):
                        print("止盈:清空所有头寸结束策略,离场")
                        self.set_position(0)

                elif self.state["position"] < 0:  # 持空单
                    # 加仓策略: 如果是空仓且行情最新价在上一次建仓（或者加仓）的基础上又下跌了0.5N，就再加一个Unit的空仓,并且风险度在设定范围内(以防爆仓)
                    if self.quote.last_price <= self.state[
                        "last_price"] - 0.5 * self.n and self.account.risk_ratio <= self.max_risk_ratio:
                        print("加仓:加1个Unit的空仓")
                        self.set_position(self.state["position"] - self.unit)
                    # 止损策略: 如果是空仓且行情最新价在上一次建仓（或者加仓）的基础上又上涨了2N，就平仓止损
                    elif self.quote.last_price >= self.state["last_price"] + 2 * self.n:
                        print("止损:卖出全部头寸")
                        self.set_position(0)
                    # 止盈策略: 如果是空仓且行情最新价升破了10日唐奇安通道的上轨，就清空所有头寸结束策略,离场
                    if self.quote.last_price >= max(self.klines.high[-self.donchian_channel_stop_profit - 1:-1]):
                        print("止盈:清空所有头寸结束策略,离场")
                        self.set_position(0)

    def strategy(self):
        """海龟策略"""
        print("等待K线及账户数据...")
        deadline = time.time() + 5
        while not self.recalc_paramter():
            if not self.api.wait_update(deadline=deadline):
                raise Exception("获取数据失败，请确认行情连接正常并已经登录交易账户")
        while True:
            self.try_open()
            self.try_close()


turtle = Turtle("SHFE.au2006")
print("策略开始运行")
try:
    turtle.state = json.load(open("turtle_state.json", "r"))  # 读取数据: 本策略目标净持仓数,上一次开仓价
except FileNotFoundError:
    pass
print("当前持仓数: %d, 上次调仓价: %f" % (turtle.state["position"], turtle.state["last_price"]))
try:
    turtle.strategy()
finally:
    turtle.api.close()
    json.dump(turtle.state, open("turtle_state.json", "w"))  # 保存数据
