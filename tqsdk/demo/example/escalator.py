#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = "Ringo"

'''
自动扶梯 策略 (难度：初级)
参考: https://www.shinnytech.com/blog/escalator/
注: 该示例策略仅用于功能示范, 实盘时请根据自己的策略/经验进行修改
'''

from tqsdk import TqApi, TqAuth, TargetPosTask
from tqsdk.ta import MA

# 设置合约
SYMBOL = "SHFE.rb2012"
# 设置均线长短周期
MA_SLOW, MA_FAST = 8, 40

api = TqApi(auth=TqAuth("信易账户", "账户密码"))
klines = api.get_kline_serial(SYMBOL, 60 * 60 * 24)
quote = api.get_quote(SYMBOL)
position = api.get_position(SYMBOL)
target_pos = TargetPosTask(api, SYMBOL)


# K线收盘价在这根K线波动范围函数


def kline_range(num):
    kl_range = (klines.iloc[num].close - klines.iloc[num].low) / \
               (klines.iloc[num].high - klines.iloc[num].low)
    return kl_range


# 获取长短均线值
def ma_caculate(klines):
    ma_slow = MA(klines, MA_SLOW).iloc[-1].ma
    ma_fast = MA(klines, MA_FAST).iloc[-1].ma
    return ma_slow, ma_fast


ma_slow, ma_fast = ma_caculate(klines)
print("慢速均线为%.2f,快速均线为%.2f" % (ma_slow, ma_fast))

while True:
    api.wait_update()
    # 每次k线更新，重新计算快慢均线
    if api.is_changing(klines.iloc[-1], "datetime"):
        ma_slow, ma_fast = ma_caculate(klines)
        print("慢速均线为%.2f,快速均线为%.2f" % (ma_slow, ma_fast))

    if api.is_changing(quote, "last_price"):
        # 开仓判断
        if position.pos_long == 0 and position.pos_short == 0:
            # 计算前后两根K线在当时K线范围波幅
            kl_range_cur = kline_range(-2)
            kl_range_pre = kline_range(-3)
            # 开多头判断，最近一根K线收盘价在短期均线和长期均线之上，前一根K线收盘价位于K线波动范围底部25%，最近这根K线收盘价位于K线波动范围顶部25%
            if klines.iloc[-2].close > max(ma_slow, ma_fast) and kl_range_pre <= 0.25 and kl_range_cur >= 0.75:
                print("最新价为:%.2f 开多头" % quote.last_price)
                target_pos.set_target_volume(100)

            # 开空头判断，最近一根K线收盘价在短期均线和长期均线之下，前一根K线收盘价位于K线波动范围顶部25%，最近这根K线收盘价位于K线波动范围底部25%
            elif klines.iloc[-2].close < min(ma_slow, ma_fast) and kl_range_pre >= 0.75 and kl_range_cur <= 0.25:
                print("最新价为:%.2f 开空头" % quote.last_price)
                target_pos.set_target_volume(-100)
            else:
                print("最新价位:%.2f ，未满足开仓条件" % quote.last_price)

        # 多头持仓止损策略
        elif position.pos_long > 0:
            # 在两根K线较低点减一跳，进行多头止损
            kline_low = min(klines.iloc[-2].low, klines.iloc[-3].low)
            if klines.iloc[-1].close <= kline_low - quote.price_tick:
                print("最新价为:%.2f,进行多头止损" % (quote.last_price))
                target_pos.set_target_volume(0)
            else:
                print("多头持仓，当前价格 %.2f,多头离场价格%.2f" %
                      (quote.last_price, kline_low - quote.price_tick))

        # 空头持仓止损策略
        elif position.pos_short > 0:
            # 在两根K线较高点加一跳，进行空头止损
            kline_high = max(klines.iloc[-2].high, klines.iloc[-3].high)
            if klines.iloc[-1].close >= kline_high + quote.price_tick:
                print("最新价为:%.2f 进行空头止损" % quote.last_price)
                target_pos.set_target_volume(0)
            else:
                print("空头持仓，当前价格 %.2f,空头离场价格%.2f" %
                      (quote.last_price, kline_high + quote.price_tick))
