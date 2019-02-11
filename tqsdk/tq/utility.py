#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'


import os
import sys
import importlib
import inspect
import datetime
from PyQt5.QtWidgets import (QDialog, QWidget, QPushButton,
    QHBoxLayout, QVBoxLayout, QApplication, QLabel, QLineEdit, QDateTimeEdit)
from PyQt5.QtCore import pyqtSlot
from tqsdk.tq.tqbase import TqBase, TqKlineStrategy


class ParamDialog(QDialog):
    def __init__(self, param_list, backtest=False):
        super().__init__()
        self.vbox = QVBoxLayout()
        self.vbox.addStretch(1)
        self.inputs = []
        self.backtest = backtest
        if self.backtest:
            self.input_bk_left = self.add_input("回测起点", datetime.date(2018, 5, 1))
            self.input_bk_right = self.add_input("回测终点", datetime.date(2018, 5, 2))
        for k, v in param_list:
            qle = self.add_input(k, v)
            self.inputs.append([qle, k, v])

    def add_input(self, k, v):
        lbl = QLabel(self)
        lbl.setText(k)
        self.vbox.addWidget(lbl)
        if isinstance(v, datetime.date):
            qle = QDateTimeEdit(self)
            qle.setDate(v)
            qle.setDisplayFormat("yyyy.MM.dd");
            qle.setCalendarPopup(True)
        else:
            qle = QLineEdit(self)
            qle.setText(str(v))
        self.vbox.addWidget(qle)
        return qle

    def exec(self):
        okButton = QPushButton("OK")
        okButton.clicked.connect(self.on_ok)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.on_cancel)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(okButton)
        hbox.addWidget(cancelButton)
        self.vbox.addLayout(hbox)

        self.setLayout(self.vbox)
        self.setGeometry(300, 300, 300, 150)
        self.setWindowTitle('请输入参数')
        return super().exec()

    @pyqtSlot()
    def on_ok(self):
        self.params = []
        for editor, k, v in self.inputs:
            if isinstance(v, datetime.date):
                self.params.append([k, editor.date().toPyDate()])
            elif isinstance(v, int):
                self.params.append([k, int(editor.text())])
            else:
                self.params.append([k, editor.text()])
        if self.backtest:
            self.bk_left = self.input_bk_left.date().toPyDate()
            self.bk_right = self.input_bk_right.date().toPyDate()
        self.accept()

    @pyqtSlot()
    def on_cancel(self):
        self.close()


def input_param(classT):
    param_list = []
    mms = inspect.getmembers(classT)
    for k, v in mms:
        if k.upper() != k:
            continue
        param_list.append([k, v])
    app = QApplication(sys.argv)
    dialog = ParamDialog(param_list, False)
    if not dialog.exec():
        return None
    return dialog.params


def input_param_backtest(classT):
    param_list = []
    mms = inspect.getmembers(classT)
    for k, v in mms:
        if k.upper() != k:
            continue
        param_list.append([k, v])
    app = QApplication(sys.argv)
    dialog = ParamDialog(param_list, True)
    if not dialog.exec():
        return None, None, None
    return dialog.params, dialog.bk_left, dialog.bk_right


def load_strategy_file(file_full_path):
    #加载策略文件
    # execfile("/home/el/foo2/mylib.py")
    file_path, file_name = os.path.split(file_full_path)
    sys.path.insert(0, file_path)
    module_name = file_name[:-3]
    t_module = importlib.import_module(module_name)
    for name, obj in inspect.getmembers(t_module):
        if inspect.isclass(obj) and issubclass(obj, TqBase):
            return obj
    return None


if __name__ == "__main__":
    class Demo(TqKlineStrategy):
        '''
        Demo String
        '''
        N = 100 #comment N

    ds = input_param_backtest(Demo)
    print(4, ds)
