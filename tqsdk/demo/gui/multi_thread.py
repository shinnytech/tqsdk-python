#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

import threading
import PySimpleGUI as sg
from tqsdk import TqApi, TargetPosTask

api = TqApi()
quote_a = api.get_quote("SHFE.rb1910")
quote_b = api.get_quote("SHFE.rb2001")


class WorkingThread(threading.Thread):
    def run(self):
        while True:
            api.wait_update()


# 创建新线程
wt = WorkingThread()
wt.start()

layout = [[sg.Text('rb1910'), sg.Text("99999", key="rb1910.last")],
          [sg.Text('rb2001'), sg.Text("99999", key="rb2001.last")],
          [sg.Text('spread'), sg.Text("99999", key="spread")],
          ]

window = sg.Window('价差显示', layout)

while True:  # Event Loop
    event, values = window.Read(timeout=1)
    if event is None or event == 'Exit':
        break
    window.Element('rb1910.last').Update(quote_a.last_price)
    window.Element('rb2001.last').Update(quote_b.last_price)
    window.Element('spread').Update(quote_b.last_price - quote_a.last_price)

window.Close()

