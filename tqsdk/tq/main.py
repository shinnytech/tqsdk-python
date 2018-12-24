#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import uuid
import asyncio
import tkinter as tk
import tkinter.ttk as ttk

from tqsdk import TqApi, TqSim
from tqsdk.tq.blocks.split import ViewSplitOrder
from tqsdk.tq.strategy.grid_trading import StrategyGridTrading


class TqStrategyManager(tk.Frame):
    def __init__(self, tq_api):
        self.tk_master = tk.Tk()
        self.tk_master.title('TqStrategyManager')
        tk.Frame.__init__(self, self.tk_master)
        self.tq_api = tq_api
        self.pack()
        self.strategy_class_map = {}
        self.block_class_map = {}
        self.instance_map = {}

        self.tree = ttk.Treeview(self)
        self.tree["columns"] = ("备注")
        self.tree.column("备注", width=100)
        self.tree.heading("备注", text="备注")
        self.line_blocks = self.tree.insert("", 9999, "功能板块", text="功能板块")
        self.line_strategies = self.tree.insert("", 9999, "交易策略", text="交易策略")
        self.tree.bind('<Double-1>', self.on_tree_double_click)  # 绑定双击
        self.tree.pack()

        # self.button_create_instance = tk.Button(self, text="创建实例", command=self.create_instance)
        # self.button_create_instance.pack()

        self.add_view(ViewSplitOrder)
        self.add_stategy_class(StrategyGridTrading)

    def add_view(self, cls):
        self.block_class_map[cls.__name__] = cls
        self.tree.insert(self.line_blocks, "end", text=cls.__name__, values=(cls.desc))

    def add_stategy_class(self, cls):
        self.strategy_class_map[cls.__name__] = cls
        self.tree.insert(self.line_strategies, "end", text=cls.__name__, values=(cls.desc))

    def create_instance(self):
        print("create_instance")
        item = self.tree.selection()[0]
        item_text = self.tree.item(item, "text")
        block_cls = self.block_class_map.get(item_text, None)
        if block_cls:
            block_instance = self.instance_map.get(item_text)
            if not block_instance:
                block_instance = block_cls(self.tq_api)
                self.instance_map[item_text] = block_instance
            return
        strategy_class = self.strategy_class_map.get(item_text, None)
        if strategy_class:
            s = strategy_class(self.tq_api)
            instance_id = item_text + str(uuid.uuid4())
            self.instance_map[instance_id] = s
            self.tree.insert(item, 9999, text=instance_id, values=(s.get_instance_desc()))
            return

    def on_tree_double_click(self, event):
        print('双击', event)
        self.create_instance()

    def run(self):
        async def tk_updater():
            while True:
                self.tk_master.update()
                await asyncio.sleep(1.0 / 60)
        self.tq_api.create_task(tk_updater())
        while True:
            self.tq_api.wait_update()
            for t in self.instance_map.values():
                t.on_update()


if __name__ == "__main__":
    #创建
    tq_api = TqApi(TqSim())
    m = TqStrategyManager(tq_api)
    m.run()
