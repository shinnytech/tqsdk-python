#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

"""
网格交易策略
参考: https://www.shinnytech.com/blog/grid-trading/
注: 该示例策略仅用于功能示范, 实盘时请根据自己的策略/经验进行修改
"""

from functools import reduce
from contextlib import closing
from tqsdk import TqApi, TqAuth, TargetPosTask

# 网格计划参数:
symbol = "DCE.jd2011"  # 合约代码
start_price = 4247  # 起始价位
grid_amount = 10  # 网格在多头、空头方向的格子(档位)数量
grid_region_long = [0.005] * grid_amount  # 多头每格价格跌幅(网格密度)
grid_region_short = [0.005] * grid_amount  # 空头每格价格涨幅(网格密度)
grid_volume_long = [1] * grid_amount  # 多头每格交易手数
grid_volume_short = [-1] * grid_amount  # 空头每格交易手数
grid_prices_long = [reduce(lambda p, r: p*(1-r), grid_region_long[:i], start_price) for i in range(grid_amount + 1)]  # 多头每格的触发价位列表, 第一个元素为起始价位
grid_prices_short = [reduce(lambda p, r: p*(1+r), grid_region_short[:i], start_price) for i in range(grid_amount + 1)]  # 空头每格的触发价位列表, 第一个元素为起始价位

print("起始价位:", start_price)
print("多头每格交易量:", grid_volume_long)
print("多头每格的价位:", grid_prices_long)
print("空头每格的价位:", grid_prices_short)

api = TqApi(auth=TqAuth("信易账户", "账户密码"))
quote = api.get_quote(symbol)  # 行情数据
target_pos = TargetPosTask(api, symbol)
target_volume = 0  # 目标持仓手数


async def price_watcher(open_price, close_price, volume):
    """该task在价格触发开仓价时开仓，触发平仓价时平仓"""
    global target_volume
    async with api.register_update_notify(quote) as update_chan:  # 当 quote 有更新时会发送通知到 update_chan 上
        while True:
            async for _ in update_chan:  # 当从 update_chan 上收到行情更新通知时判断是否触发开仓条件
                if (volume > 0 and quote.last_price <= open_price) or (volume < 0 and quote.last_price >= open_price):
                    break
            target_volume += volume
            target_pos.set_target_volume(target_volume)
            print("时间:", quote.datetime, "最新价:", quote.last_price, "开仓", volume, "手", "总仓位:", target_volume, "手")
            async for _ in update_chan:  # 当从 update_chan 上收到行情更新通知时判断是否触发平仓条件
                if (volume > 0 and quote.last_price > close_price) or (volume < 0 and quote.last_price < close_price):
                    break
            target_volume -= volume
            target_pos.set_target_volume(target_volume)
            print("时间:", quote.datetime, "最新价:", quote.last_price, "平仓", volume, "手", "总仓位:", target_volume, "手")


for i in range(grid_amount):
    api.create_task(price_watcher(grid_prices_long[i+1], grid_prices_long[i], grid_volume_long[i]))
    api.create_task(price_watcher(grid_prices_short[i+1], grid_prices_short[i], grid_volume_short[i]))

with closing(api):
    while True:
        api.wait_update()
