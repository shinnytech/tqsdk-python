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
        self.block_template_map = {}
        self.strategy_template_map = {}
        self.classes = {}
        self.instances = {}

        self.tree = ttk.Treeview(self)
        self.tree["columns"] = ("备注")
        self.tree.column("备注", width=100)
        self.tree.heading("备注", text="备注")
        self.line_blocks = self.tree.insert("", 9999, "功能板块", text="功能板块")
        self.line_strategies = self.tree.insert("", 9999, "交易策略", text="交易策略")
        self.tree.bind('<Double-1>', self.on_tree_double_click)  # 绑定双击
        self.tree.pack()

        self.add_view(ViewSplitOrder)
        self.add_stategy_class(StrategyGridTrading)

    def add_view(self, template):
        self.block_template_map[template.__name__] = template
        self.tree.insert(self.line_blocks, "end", text=template.__name__, values=(template.desc))

    def add_stategy_class(self, template):
        self.strategy_template_map[template.__name__] = template
        self.tree.insert(self.line_strategies, "end", text=template.__name__, values=(template.desc))

    def on_tree_double_click(self, event):
        print('双击', event)
        self.create_class()

    def create_class(self):
        print("create_class")
        item = self.tree.selection()[0]
        item_text = self.tree.item(item, "text")
        block_template = self.block_template_map.get(item_text, None)
        if block_template and not item_text in self.classes:
            return self._init_class(item_text, block_template(self))
        strategy_template = self.strategy_template_map.get(item_text, None)
        if strategy_template:
            id = item_text + str(uuid.uuid4())
            cls = strategy_template(self)
            self.tree.insert(item, 9999, text=id, values=(cls.get_desc()))
            return self._init_class(id, cls)

    def _init_class(self, class_id, cls):
        self.classes[class_id] = {
            "class_id": class_id,
            "class": cls,
            "instances": [],
        }
        return cls

    def remove_class(self, cls):
        for id, c in self.classes.items():
            if c["class"] is cls:
                for instance in c["instances"]:
                    self.stop_instance(instance)
                del self.classes[id]
                return

    def create_instance(self, cls, func):
        print("create_instance")
        t = threading.Thread(target=self._run_instance)
        instance = {
            "strategy": func,
            "run_queue": queue.Queue(),  # run信号,0未更新，1有更新，-1停止
            "exception": None,
        }
        for c in self.classes.values():
            if c["class"] is cls:
                c["instances"].append(instance)
        self.instances[t] = instance
        t.start()
        self._sched_instance(instance, 0)
        return instance

    def _run_instance(self):
        instance = self.instances[threading.current_thread()]
        instance["run_queue"].get()
        try:
            instance["strategy"](self.tq_api)
        except Exception as e:
            instance["exception"] = e
        else:
            instance["exception"] = StrategyExit()
        finally:
            instance["run_queue"].task_done()

    def _sched_instance(self, instance, run):
        instance["run_queue"].put(run)
        instance["run_queue"].join()
        if instance["exception"] is not None:
            #@todo: show self.instances[t]["exception"]
            for t, i in self.instances.items():
                if i is instance:
                    t.join()
                    del self.instances[t]
                    break
            for c in self.classes.values():
                c["instances"] = [i for i in c["instances"] if i is not instance]

    def stop_instance(self, instance):
        self._sched_instance(instance, -1)

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
            run = 1 if org_wait_update(deadline = deadline) else 0
            for instance in list(self.instances.values()):
                self._sched_instance(instance, run)


if __name__ == "__main__":
    #创建
    tq_api = TqApi(TqSim())
    m = TqStrategyManager(tq_api)
    m.run()
