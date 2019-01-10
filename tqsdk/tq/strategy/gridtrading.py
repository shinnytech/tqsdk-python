#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from functools import reduce
from tqsdk import TargetPosTask
from tqsdk.tq.strategy.base import StrategyBase


class StrategyGridTrading(StrategyBase):
    def __init__(self, api, desc, stg_id, desc_chan):
        StrategyBase.__init__(self, api, desc, stg_id, desc_chan)
        self.add_input("合约代码", "symbol", "DCE.jd1905", str)
        self.add_input("起始价位", "start_price", 4047, float)
        self.add_input("格子数量", "grid_amount", 10, int)
        self.add_input("每格涨跌幅", "grid_gap", 0.05, float)
        self.add_switch()
        self.add_console()
        self.set_status()
        self.show()

    def get_desc(self):
        return "合约代码 %s, 起始价位 %f, 格子数量 %d, 每格涨跌幅 %f" % (self.symbol, self.start_price, self.grid_amount, self.grid_gap)

    async def run_strategy(self):
        self.grid_region_long = [self.grid_gap] * self.grid_amount  # 多头每格价格跌幅(网格密度)
        self.grid_region_short = [self.grid_gap] * self.grid_amount  # 空头每格价格涨幅(网格密度)
        self.grid_volume_long = [i for i in range(self.grid_amount + 1)]  # 多头每格交易手数
        self.grid_volume_short = [i for i in range(self.grid_amount + 1)]  # 空头每格交易手数
        self.grid_prices_long = [reduce(lambda p, r: p * (1 - r), self.grid_region_long[:i], self.start_price) for i in range(self.grid_amount + 1)]  # 多头每格的触发价位列表
        self.grid_prices_short = [reduce(lambda p, r: p * (1 + r), self.grid_region_short[:i], self.start_price) for i in range(self.grid_amount + 1)]  # 空头每格的触发价位列表

        print("起始价位:", self.start_price)
        print("多头每格交易量:", self.grid_volume_long)
        print("多头每格的价位:", self.grid_prices_long)
        print("空头每格的价位:", self.grid_prices_short)

        self.quote = self.api.get_quote(self.symbol)  # 行情数据
        self.target_pos = TargetPosTask(self.api, self.symbol)
        self.position = self.api.get_position(self.symbol)  # 持仓信息

        try:
            async with self.api.register_update_notify() as update_chan:
                async for _ in update_chan:
                    await self.wait_price(0)  # 从第0层开始进入网格
                    self.target_pos.set_target_volume(0)
        finally:
            self.target_pos.task.cancel()

    async def wait_price(self, layer):
        """等待行情最新价变动到其他档位,则进入下一档位或回退到上一档位; 如果从下一档位回退到当前档位,则设置为当前对应的持仓手数;
            layer : 当前所在第几个档位层次; layer>0 表示多头方向, layer<0 表示空头方向
        """
        if layer > 0 or self.quote["last_price"] <= self.grid_prices_long[1]:  # 是多头方向
            async with self.api.register_update_notify() as update_chan:
                async for _ in update_chan:
                    # 如果当前档位小于最大档位,并且最新价小于等于下一个档位的价格: 则设置为下一档位对应的手数后进入下一档位层次
                    if layer < self.grid_amount and self.quote["last_price"] <= self.grid_prices_long[layer + 1]:
                        self.target_pos.set_target_volume(self.grid_volume_long[layer + 1])
                        print("时间:", self.quote["datetime"], "最新价:", self.quote["last_price"], "进入: 多头第", layer + 1, "档")
                        await self.wait_price(layer + 1)
                        # 从下一档位回退到当前档位后, 设置回当前对应的持仓手数
                        self.target_pos.set_target_volume(self.grid_volume_long[layer + 1])
                    # 如果最新价大于当前档位的价格: 则回退到上一档位
                    if self.quote["last_price"] > self.grid_prices_long[layer]:
                        print("时间:", self.quote["datetime"], "最新价:", self.quote["last_price"], "回退到: 多头第", layer, "档")
                        return
        elif layer < 0 or self.quote["last_price"] >= self.grid_prices_short[1]:  # 是空头方向
            layer = -layer  # 转为正数便于计算
            async with self.api.register_update_notify() as update_chan:
                async for _ in update_chan:
                    # 如果当前档位小于最大档位层次,并且最新价大于等于下一个档位的价格: 则设置为下一档位对应的持仓手数后进入下一档位层次
                    if layer < self.grid_amount and self.quote["last_price"] >= self.grid_prices_short[layer + 1]:
                        self.target_pos.set_target_volume(-self.grid_volume_short[layer + 1])
                        print("时间:", self.quote["datetime"], "最新价:", self.quote["last_price"], "进入: 空头第", layer + 1, "档")
                        await self.wait_price(-(layer + 1))
                        # 从下一档位回退到当前档位后, 设置回当前对应的持仓手数
                        self.target_pos.set_target_volume(-self.grid_volume_short[layer + 1])
                    # 如果最新价小于当前档位的价格: 则回退到上一档位
                    if self.quote["last_price"] < self.grid_prices_short[layer]:
                        print("时间:", self.quote["datetime"], "最新价:", self.quote["last_price"], "回退到: 空头第", layer, "档")
                        return
