#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import asyncio
import logging
import functools
from PyQt5.QtWidgets import (QLabel, QLineEdit, QPushButton, QFormLayout, QVBoxLayout, QWidget, QTextBrowser)
from tqsdk.tq.logger import WidgetLogger, log_task_exception


class StrategyBase(QWidget):
    def __init__(self, api, desc, stg_id, desc_chan):
        QWidget.__init__(self)
        self.logger = logging.getLogger("Strategy.%s.%s" % (desc, stg_id))
        self.logger.setLevel(logging.INFO)
        self.api = api
        self.desc = desc
        self.stg_id = stg_id
        self.desc_chan = desc_chan
        self.quit = asyncio.Future(loop=api.loop)
        self.task = None
        self.entry = []
        self.resize(500, 300)
        self.main_layout = QVBoxLayout()
        self.form = QWidget()
        self.form_layout = QFormLayout()
        self.form.setLayout(self.form_layout)
        self.main_layout.addWidget(self.form)
        self.setLayout(self.main_layout)

    def closeEvent(self, event):
        if not self.quit.done():
            self.quit.set_result(True)

    def add_input(self, desc, name, default, type):
        def text_changed(self, name, value):
            try:
                setattr(self, name, type(value))
            except:
                pass
        edit = QLineEdit()
        edit.textChanged.connect(functools.partial(text_changed, self, name))
        self.form_layout.addRow(QLabel(desc), edit)
        self.entry.append(edit)
        edit.setText(str(default))
        return edit

    def add_switch(self):
        self.switch = QPushButton("启动", self)
        self.switch.clicked.connect(self.on_switch)
        self.main_layout.addWidget(self.switch)

    def add_console(self):
        self.console = QTextBrowser(self)
        wh = WidgetLogger(self.console)
        wh.setLevel(logging.INFO)
        wh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(wh)
        self.main_layout.addWidget(self.console)

    def get_desc(self):
        raise NotImplementedError

    def set_status(self):
        if self.task:
            status = "执行中 - %s" % (self.get_desc())
        else:
            status = "已停止"
        self.setWindowTitle(self.desc + " " + status)
        self.desc_chan.send_nowait(status)

    def on_switch(self):
        if self.task:
            for e in self.entry:
                e.setDisabled(False)
            self.switch.setText("启动")
            self.task.cancel()
            self.task = None
            self.logger.info("策略已停止")
        else:
            for e in self.entry:
                e.setDisabled(True)
            self.switch.setText("停止")
            self.task = self.api.create_task(self.run_strategy())
            self.task.add_done_callback(self.on_task_done)
            self.task.add_done_callback(functools.partial(log_task_exception, self.logger, self.desc + ":" + self.stg_id))
            self.logger.info("启动策略: %s", self.get_desc())
        self.set_status()

    def on_task_done(self, task):
        if task == self.task:
            self.on_switch()

    async def run_ui(self):
        try:
            await self.quit
        finally:
            if self.task:
                self.task.cancel()
                self.task = None
            for h in self.logger.handlers.copy():
                self.logger.removeHandler(h)
            self.close()

    async def run_strategy(self):
        raise NotImplementedError

async def Strategy(stg, api, desc, stg_id, desc_chan):
    await stg(api, desc, stg_id, desc_chan).run_ui()
