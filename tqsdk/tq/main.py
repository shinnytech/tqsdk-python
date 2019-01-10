#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import sys
import uuid
import asyncio
import functools
import contextlib
import logging
import time

from PyQt5.QtWidgets import (QApplication, QVBoxLayout, QGroupBox, QTreeWidgetItem, QWidget,
                             QMainWindow, QTreeWidget, QAction, QTextBrowser)
from PyQt5.QtCore import Qt
from quamash import QEventLoop
from tqsdk import TqApi, TqChan
from tqsdk.tq.logger import WidgetLogger, log_task_exception
from tqsdk.tq.strategy.base import Strategy
from tqsdk.tq.strategy.doublema import StrategyDoubleMA
from tqsdk.tq.strategy.dualthrust import StrategyDualThrust
from tqsdk.tq.strategy.gridtrading import StrategyGridTrading
from tqsdk.tq.strategy.rbreaker import StrategyRBreaker
from tqsdk.tq.strategy.vwap import StrategyVWAP


class TqStrategyManager(QMainWindow):
    def __init__(self, api):
        QMainWindow.__init__(self)
        self.logger = logging.getLogger("TqStrategyManager")  # 调试信息输出
        self.logger.setLevel(logging.INFO)
        self.setWindowTitle("TqStrategyManager")
        self.resize(700, 500)
        self.api = api
        self.stgs = {}

        self.new_stg_menu = self.menuBar().addMenu("新建策略")
        self.new_help_menu = self.menuBar().addMenu("帮助")
        act = QAction("使用说明书", self)
        #act.triggered.connect(self.on_manual)
        self.new_help_menu.addAction(act)
        act = QAction("关于", self)
        #act.triggered.connect(self.on_about)
        self.new_help_menu.addAction(act)

        window_layout = QVBoxLayout()
        tree_box = QGroupBox("策略列表")
        tree_layout = QVBoxLayout()
        self.tree = QTreeWidget(self)
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["策略名称", "ID", "状态"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        tree_layout.addWidget(self.tree)
        tree_box.setLayout(tree_layout)
        window_layout.addWidget(tree_box)

        console_box = QGroupBox("操作日志")
        console_layout = QVBoxLayout()
        self.console = QTextBrowser(self)
        wh = WidgetLogger(self.console)
        wh.setLevel(logging.INFO)
        wh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(wh)
        console_layout.addWidget(self.console)
        console_box.setLayout(console_layout)
        window_layout.addWidget(console_box)

        self.add_stg_template(functools.partial(Strategy, StrategyVWAP), "大单拆分")
        self.add_stg_template(functools.partial(Strategy, StrategyDoubleMA), "双均线策略")
        self.add_stg_template(functools.partial(Strategy, StrategyDualThrust), "DualThrust策略")
        self.add_stg_template(functools.partial(Strategy, StrategyGridTrading), "网格交易策略")
        self.add_stg_template(functools.partial(Strategy, StrategyRBreaker), "R-Breaker策略")

        centralWidget = QWidget()
        centralWidget.setLayout(window_layout)
        self.setCentralWidget(centralWidget)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.show()

    def add_stg_template(self, template, desc):
        act = QAction(desc, self)
        act.triggered.connect(functools.partial(self.create_stg, template, desc))
        self.new_stg_menu.addAction(act)
        self.logger.info("初始化 %s 策略完成", desc)

    def create_stg(self, template, desc):
        stg_id = str(uuid.uuid4())
        item = QTreeWidgetItem(self.tree)
        item.setText(0, desc)
        item.setText(1, stg_id)
        item.setText(2, "")
        self.tree.addTopLevelItem(item)
        stg = {
            "stg_id": stg_id,
            "item": item,
            "task": self.api.create_task(self._run_template(template, desc, stg_id, item))
        }
        self.stgs[stg_id] = stg
        stg["task"].add_done_callback(functools.partial(self._on_stg_done, desc, stg_id, item))
        stg["task"].add_done_callback(functools.partial(log_task_exception, self.logger, desc + ":" + stg_id))
        self.logger.info("创建 %s:%s 完成", desc, stg_id)

    def _on_stg_done(self, desc, stg_id, item, task):
        self.logger.info("%s:%s 执行结束", desc, stg_id)
        self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
        del self.stgs[stg_id]

    def _stop_stg(self, task):
        task.cancel()

    async def _update_stg_desc(self, item, desc_chan):
        async for desc in desc_chan:
            item.setText(2, desc)

    async def _run_template(self, template, desc, stg_id, item):
        desc_chan = TqChan(self.api)
        try:
            self.api.create_task(self._update_stg_desc(item, desc_chan))
            await template(self.api, desc, stg_id, desc_chan)
        finally:
            await desc_chan.close()

    def run(self):
        while self.isVisible():
            self.api.wait_update(deadline=time.time()+0.1)


if __name__ == "__main__":
    #创建
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    api = TqApi(sys.argv[1], loop=loop)
    with contextlib.closing(api):
        m = TqStrategyManager(api)
        m.run()
