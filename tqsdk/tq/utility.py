#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'


import sys
import datetime
from PyQt5.QtWidgets import (QDialog, QWidget, QPushButton,
    QHBoxLayout, QVBoxLayout, QApplication, QLabel, QLineEdit, QDateTimeEdit)
from PyQt5.QtCore import pyqtSlot


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


def input_param(param_list):
    if not param_list:
        return param_list
    app = QApplication(sys.argv)
    dialog = ParamDialog(param_list, False)
    if not dialog.exec():
        return None
    return dialog.params


def input_param_backtest(param_list):
    app = QApplication(sys.argv)
    dialog = ParamDialog(param_list, True)
    if not dialog.exec():
        return None, None, None
    return dialog.params, dialog.bk_left, dialog.bk_right


if __name__ == "__main__":
    ds = input_param_backtest([("A", 10)])
    print(4, ds)
