#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from functools import reduce
from tqsdk import TqApi, TargetPosTask, TqSim
import tkinter as tk

#
# """
# 网格交易算法
# 参考: https://xueqiu.com/6027474589/59766858
# """
# # 网格计划参数:
# symbol = "DCE.jd1901"  # 合约代码
# start_price = 4047  # 起始价位
# grid_amount = 10  # 网格在多头、空头方向的格子(档位)数量
# grid_region_long = [0.005] * grid_amount  # 多头每格价格跌幅(网格密度)
# grid_region_short = [0.005] * grid_amount  # 空头每格价格涨幅(网格密度)
# grid_volume_long = [i for i in range(grid_amount + 1)]  # 多头每格交易手数
# grid_volume_short = [i for i in range(grid_amount + 1)]  # 空头每格交易手数
# grid_prices_long = [reduce(lambda p, r: p*(1-r), grid_region_long[:i], start_price) for i in range(grid_amount + 1)]  # 多头每格的触发价位列表
# grid_prices_short = [reduce(lambda p, r: p*(1+r), grid_region_short[:i], start_price) for i in range(grid_amount + 1)]  # 空头每格的触发价位列表
#
# print("起始价位:", start_price)
# print("多头每格交易量:", grid_volume_long)
# print("多头每格的价位:", grid_prices_long)
# print("空头每格的价位:", grid_prices_short)
#
# api = TqApi(TqSim())
# quote = api.get_quote(symbol)  # 行情数据
# target_pos = TargetPosTask(api, symbol)
# position = api.get_position(symbol)  # 持仓信息
#
#
# def wait_price(layer):
#     """等待行情最新价变动到其他档位,则进入下一档位或回退到上一档位; 如果从下一档位回退到当前档位,则设置为当前对应的持仓手数;
#         layer : 当前所在第几个档位层次; layer>0 表示多头方向, layer<0 表示空头方向
#     """
#     if layer > 0 or quote["last_price"] <= grid_prices_long[1]:  # 是多头方向
#         while True:
#             api.wait_update()
#             # 如果当前档位小于最大档位,并且最新价小于等于下一个档位的价格: 则设置为下一档位对应的手数后进入下一档位层次
#             if layer < grid_amount and quote["last_price"] <= grid_prices_long[layer + 1]:
#                 target_pos.set_target_volume(grid_volume_long[layer + 1])
#                 print("时间:", quote["datetime"], "最新价:", quote["last_price"], "进入: 多头第", layer + 1, "档")
#                 wait_price(layer + 1)
#                 # 从下一档位回退到当前档位后, 设置回当前对应的持仓手数
#                 target_pos.set_target_volume(grid_volume_long[layer + 1])
#             # 如果最新价大于当前档位的价格: 则回退到上一档位
#             if quote["last_price"] > grid_prices_long[layer]:
#                 print("时间:", quote["datetime"], "最新价:", quote["last_price"], "回退到: 多头第", layer, "档")
#                 return
#     elif layer < 0 or quote["last_price"] >= grid_prices_short[1]:  # 是空头方向
#         layer = -layer  # 转为正数便于计算
#         while True:
#             api.wait_update()
#             # 如果当前档位小于最大档位层次,并且最新价大于等于下一个档位的价格: 则设置为下一档位对应的持仓手数后进入下一档位层次
#             if layer < grid_amount and quote["last_price"] >= grid_prices_short[layer + 1]:
#                 target_pos.set_target_volume(-grid_volume_short[layer + 1])
#                 print("时间:", quote["datetime"], "最新价:", quote["last_price"], "进入: 空头第", layer + 1, "档")
#                 wait_price(-(layer + 1))
#                 # 从下一档位回退到当前档位后, 设置回当前对应的持仓手数
#                 target_pos.set_target_volume(-grid_volume_short[layer + 1])
#             # 如果最新价小于当前档位的价格: 则回退到上一档位
#             if quote["last_price"] < grid_prices_short[layer]:
#                 print("时间:", quote["datetime"], "最新价:", quote["last_price"], "回退到: 空头第", layer, "档")
#                 return
#
#
# while True:
#     api.wait_update()
#     wait_price(0)  # 从第0层开始进入网格
#     target_pos.set_target_volume(0)


class TqStrategy(tk.Frame):
    def __init__(self, manager):
        tk_master = tk.Tk()
        tk.Frame.__init__(self, tk_master)
        self.manager = manager
        self.pack()
        self.uis = []

    # def on_closing():
    #     if messagebox.askokcancel("Quit", "Do you want to quit?"):
    #         root.destroy()
    #
    # root.protocol("WM_DELETE_WINDOW", on_closing)
    # root.mainloop()

    def add_input(self, label=None, default_value="", cls=tk.Entry):
        v = tk.StringVar(value=default_value)
        tk_label = tk.Label(self, text=label)
        tk_label.pack()
        self.uis.append(tk_label)
        tk_edit = cls(self, textvariable=v)
        tk_edit.pack()
        self.uis.append(tk_edit)
        return v

    def run(self, api):
        raise NotImplementedError()


class StrategyGridTrading(TqStrategy):
    desc = "网格交易算法"

    def __init__(self, manager):
        TqStrategy.__init__(self, manager)
        self.var_symbol = self.add_input('合约代码', default_value="DCE.jd1901")
        self.var_start_price = self.add_input('起始价位', default_value="4047")
        self.var_grid_amount = self.add_input('格子数量', default_value="10")  # 网格在多头、空头方向的格子(档位)数量
        # grid_region_long = [0.005] * grid_amount  # 多头每格价格跌幅(网格密度)
        # grid_region_short = [0.005] * grid_amount  # 空头每格价格涨幅(网格密度)
        # grid_volume_long = [i for i in range(grid_amount + 1)]  # 多头每格交易手数
        # grid_volume_short = [i for i in range(grid_amount + 1)]  # 空头每格交易手数
        # grid_prices_long = [reduce(lambda p, r: p * (1 - r), grid_region_long[:i], start_price) for i in
        #                     range(grid_amount + 1)]  # 多头每格的触发价位列表
        # grid_prices_short = [reduce(lambda p, r: p * (1 + r), grid_region_short[:i], start_price) for i in
        #                      range(grid_amount + 1)]  # 空头每格的触发价位列表
        instance = self.manager.create_instance(self, self.run)

    def get_desc(self):
        return "abcd"

    def run(self, api):
        self.symbol = "DCE.jd1901"  # 合约代码
        self.start_price = 4047  # 起始价位
        self.grid_amount = 10  # 网格在多头、空头方向的格子(档位)数量
        self.grid_region_long = [0.005] * self.grid_amount  # 多头每格价格跌幅(网格密度)
        self.grid_region_short = [0.005] * self.grid_amount  # 空头每格价格涨幅(网格密度)
        self.grid_volume_long = [i for i in range(self.grid_amount + 1)]  # 多头每格交易手数
        self.grid_volume_short = [i for i in range(self.grid_amount + 1)]  # 空头每格交易手数
        self.grid_prices_long = [reduce(lambda p, r: p * (1 - r), self.grid_region_long[:i], self.start_price) for i in range(self.grid_amount + 1)]  # 多头每格的触发价位列表
        self.grid_prices_short = [reduce(lambda p, r: p * (1 + r), self.grid_region_short[:i], self.start_price) for i in range(self.grid_amount + 1)]  # 空头每格的触发价位列表

        print("起始价位:", self.start_price)
        print("多头每格交易量:", self.grid_volume_long)
        print("多头每格的价位:", self.grid_prices_long)
        print("空头每格的价位:", self.grid_prices_short)

        self.api = api
        self.quote = api.get_quote(self.symbol)  # 行情数据
        self.target_pos = TargetPosTask(self.api, self.symbol)
        self.position = api.get_position(self.symbol)  # 持仓信息

        while True:
            self.api.wait_update()
            self.wait_price(0)  # 从第0层开始进入网格
            self.target_pos.set_target_volume(0)

    def wait_price(self, layer):
        """等待行情最新价变动到其他档位,则进入下一档位或回退到上一档位; 如果从下一档位回退到当前档位,则设置为当前对应的持仓手数;
            layer : 当前所在第几个档位层次; layer>0 表示多头方向, layer<0 表示空头方向
        """
        if layer > 0 or self.quote["last_price"] <= self.grid_prices_long[1]:  # 是多头方向
            while True:
                self.api.wait_update()
                # 如果当前档位小于最大档位,并且最新价小于等于下一个档位的价格: 则设置为下一档位对应的手数后进入下一档位层次
                if layer < self.grid_amount and self.quote["last_price"] <= self.grid_prices_long[layer + 1]:
                    self.target_pos.set_target_volume(self.grid_volume_long[layer + 1])
                    print("时间:", self.quote["datetime"], "最新价:", self.quote["last_price"], "进入: 多头第", layer + 1, "档")
                    self.wait_price(layer + 1)
                    # 从下一档位回退到当前档位后, 设置回当前对应的持仓手数
                    self.target_pos.set_target_volume(self.grid_volume_long[layer + 1])
                # 如果最新价大于当前档位的价格: 则回退到上一档位
                if self.quote["last_price"] > self.grid_prices_long[layer]:
                    print("时间:", self.quote["datetime"], "最新价:", self.quote["last_price"], "回退到: 多头第", layer, "档")
                    return
        elif layer < 0 or self.quote["last_price"] >= self.grid_prices_short[1]:  # 是空头方向
            layer = -layer  # 转为正数便于计算
            while True:
                self.api.wait_update()
                # 如果当前档位小于最大档位层次,并且最新价大于等于下一个档位的价格: 则设置为下一档位对应的持仓手数后进入下一档位层次
                if layer < self.grid_amount and self.quote["last_price"] >= self.grid_prices_short[layer + 1]:
                    self.target_pos.set_target_volume(-self.grid_volume_short[layer + 1])
                    print("时间:", self.quote["datetime"], "最新价:", self.quote["last_price"], "进入: 空头第", layer + 1, "档")
                    self.wait_price(-(layer + 1))
                    # 从下一档位回退到当前档位后, 设置回当前对应的持仓手数
                    self.target_pos.set_target_volume(-self.grid_volume_short[layer + 1])
                # 如果最新价小于当前档位的价格: 则回退到上一档位
                if self.quote["last_price"] < self.grid_prices_short[layer]:
                    print("时间:", self.quote["datetime"], "最新价:", self.quote["last_price"], "回退到: 空头第", layer, "档")
                    return
