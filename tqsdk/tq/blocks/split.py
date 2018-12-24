#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk import TqApi, TargetPosTask
import tkinter as tk


class TqView(tk.Frame):
    def __init__(self, tq_api):
        tk_master = tk.Tk()
        tk.Frame.__init__(self, tk_master)
        self.api = tq_api
        self.pack()
        self.uis = []
        self.button_start = tk.Button(self, text="开始", command=self.on_start)
        self.button_start.pack()
        self.button_stop = tk.Button(self, text="停止", command=self.on_stop)
        self.button_stop.pack()

    def add_input(self, label=None, default_value="", cls=tk.Entry):
        v = tk.StringVar(value=default_value)
        tk_label = tk.Label(self, text=label)
        tk_label.pack()
        self.uis.append(tk_label)
        tk_edit = cls(self, textvariable=v)
        tk_edit.pack()
        self.uis.append(tk_edit)
        return v

    def on_update(self):
        raise NotImplementedError()

    def on_start(self):
        raise NotImplementedError()

    def on_stop(self):
        raise NotImplementedError()


class ViewSplitOrder(TqView):
    desc = "大单拆分工具"

    def __init__(self, tq_api):
        TqView.__init__(self, tq_api)
        self.running = False
        self.var_symbol = self.add_input('合约代码', default_value="SHFE.cu1901")
        self.var_direction = self.add_input('方向', default_value="BUY")
        self.var_offset = self.add_input('开平', default_value="OPEN")
        self.var_total_volume = self.add_input('总下单手数', default_value="100")
        self.var_batch_volume = self.add_input('最大单笔手数', default_value="5")
        self.var_price_range_low = self.add_input('价格范围', default_value="10")
        self.var_price_range_high = self.add_input('价格范围', default_value="100000")
        self.label_bid_price = tk.Label(self, text='买价')
        self.label_bid_price.pack()
        self.label_ask_price = tk.Label(self, text='卖价')
        self.label_ask_price.pack()
        self.label_finished_volume = tk.Label(self, text='已成交')
        self.label_finished_volume.pack()

    def on_start(self):
        print("start")
        self.symbol = self.var_symbol.get()
        self.direction = self.var_direction.get()
        self.offset = self.var_offset.get()
        self.total_volume = int(self.var_total_volume.get())
        self.batch_volume = int(self.var_batch_volume.get())
        self.price_range_min = float(self.var_price_range_low.get())
        self.price_range_max = float(self.var_price_range_high.get())
        self.quote = self.api.get_quote(self.symbol)
        self.order = None
        self.finished_volume = 0
        self.traded_cost = 0
        self.traded_volume = 0
        if self.direction == "BUY":
            self.price_field = "bid_price1"
        else:
            self.price_field = "ask_price1"
        self.running = True

    def on_stop(self):
        print("stop")
        self.running = False

    def update_ui(self):
        print("update_ui")
        self.label_bid_price.config(text=self.quote["bid_price1"])
        self.label_ask_price.config(text=self.quote["ask_price1"])
        self.label_finished_volume.config(text=self.finished_volume)

    def on_update(self):
        if not self.running:
            return
        if self.finished_volume >= self.total_volume:
            return
        self.update_ui()
        if self.order and self.api.is_changing(self.quote):
            self.api.cancel_order(self.order)
        if self.order and self.order["status"] == "FINISHED":
            trade_volume = self.order["volume_orign"] - self.order["volume_left"]
            self.traded_cost += self.order["limit_price"] * trade_volume
            self.traded_volume += trade_volume
            self.order = None
        if self.order is None and self.price_range_min <= self.quote[self.price_field] <= self.price_range_max:
            volume = min(self.total_volume - self.finished_volume, self.batch_volume)
            self.order = self.api.insert_order(self.symbol, self.direction, self.offset, volume,
                                               self.quote[self.price_field])


