#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import uuid
import time
import threading
import queue
import tkinter as tk
import tkinter.ttk as ttk

from tqsdk import TqApi, TqSim
from tqsdk.tq.blocks.split import ViewSplitOrder
from tqsdk.tq.strategy.grid_trading import StrategyGridTrading


class StrategyExit(Exception):
    """策略结束会抛出此例外"""
    pass

class TqStrategyManager(tk.Frame):
    def __init__(self, tq_api):
        self.tk_master = tk.Tk()
        self.tk_master.title('TqStrategyManager')
        tk.Frame.__init__(self, self.tk_master)
        self.tq_api = tq_api
        self.pack()
        self.strategy_class_map = {}
        self.block_class_map = {}
        self.instances = {}

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
        if block_cls and not [instance for instance in self.instances.values() if instance["instance_id"] == item_text]:
            self._init_instance(item_text, block_cls())
            return
        strategy_class = self.strategy_class_map.get(item_text, None)
        if strategy_class:
            s = strategy_class()
            id = item_text + str(uuid.uuid4())
            self.tree.insert(item, 9999, text=id, values=(s.get_instance_desc()))
            self._init_instance(id, s)
            return

    def _init_instance(self, instance_id, strategy):
        t = threading.Thread(target=self._run_instance)
        self.instances[t] = {
            "instance_id": instance_id,
            "strategy": strategy,
            "run_queue": queue.Queue(),  # run信号,0未更新，1有更新，-1停止
            "exception": None,
        }
        self.instances[t]["run_queue"].put(0)
        t.start()
        self.instances[t]["run_queue"].join()

    def _run_instance(self):
        instance = self.instances[threading.current_thread()]
        instance["run_queue"].get()
        try:
            instance["strategy"].run(self.tq_api)
        except Exception as e:
            instance["exception"] = e
        else:
            instance["exception"] = StrategyExit()
        finally:
            instance["run_queue"].task_done()

    def on_tree_double_click(self, event):
        print('双击', event)
        self.create_instance()

    def _wait_update(self, deadline = None):
        # 由子线程调用
        instance = self.instances[threading.current_thread()]
        instance["run_queue"].task_done()
        while True:
            run = instance["run_queue"].get()
            if run == -1:
                raise StrategyExit
            elif run == 0:
                if deadline is not None and deadline > time.time():
                    return False
                else:
                    instance["run_queue"].task_done()
                    continue
            else:
                return True

    def run(self):
        org_wait_update = self.tq_api.wait_update
        self.tq_api.wait_update = self._wait_update
        while True:
            self.tk_master.update()
            deadline = time.time() + 1.0 / 60
            updated = org_wait_update(deadline = deadline)
            removed = []
            for t, instance in self.instances.items():
                if instance["exception"] is not None:
                    removed.append(t)
                    continue
                instance["run_queue"].put(1 if updated else 0)
                instance["run_queue"].join()
            for t in removed:
                t.join()
                #@todo: show self.instances[t]["exception"]
                del self.instances[t]


if __name__ == "__main__":
    #创建
    tq_api = TqApi(TqSim())
    m = TqStrategyManager(tq_api)
    m.run()
