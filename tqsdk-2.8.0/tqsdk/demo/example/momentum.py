#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = "Ringo"

'''
价格动量 策略 (难度：初级)
参考: https://www.shinnytech.com/blog/momentum-strategy/
注: 该示例策略仅用于功能示范, 实盘时请根据自己的策略/经验进行修改
'''

from tqsdk import TqApi, TqAuth, TargetPosTask

# 设置指定合约,获取N条K线计算价格动量
SYMBOL = "SHFE.au2012"
N = 15

api = TqApi(auth=TqAuth("信易账户", "账户密码"))
klines = api.get_kline_serial(SYMBOL, 60 * 60 * 24, N)
quote = api.get_quote(SYMBOL)
target_pos = TargetPosTask(api, SYMBOL)
position = api.get_position(SYMBOL)


def AR(kline1):
    """价格动量函数AR，以前N-1日K线计算价格动量ar"""
    spread_ho = sum(kline1.high[:-1] - kline1.open[:-1])
    spread_oc = sum(kline1.open[:-1] - kline1.low[:-1])
    # spread_oc 为0时，设置为最小价格跳动值
    if spread_oc == 0:
        spread_oc = quote.price_tick
    ar = (spread_ho / spread_oc) * 100
    return ar


ar = AR(klines)
print("策略开始启动")

while True:
    api.wait_update()
    # 生成新K线时，重新计算价格动量值ar
    if api.is_changing(klines.iloc[-1], "datetime"):
        ar = AR(klines)
        print("价格动量是：", ar)
    # 每次最新价发生变动时，重新进行判断
    if api.is_changing(quote, "last_price"):
        # 开仓策略
        if position.pos_long == 0 and position.pos_short == 0:
            # 如果ar大于110并且小于150，开多仓
            if 110 < ar < 150:
                print("价值动量超过110，小于150，做多")
                target_pos.set_target_volume(100)
            # 如果ar大于50，小于90，开空仓
            elif 50 < ar < 90:
                print("价值动量大于50，小于90，做空")
                target_pos.set_target_volume(-100)

        # 止损策略，多头下当前ar值小于90则平仓止损，空头下当前ar值大于110则平仓止损
        elif (position.pos_long > 0 and ar < 90) or (position.pos_short > 0 and ar > 110):
            print("止损平仓")
            target_pos.set_target_volume(0)
