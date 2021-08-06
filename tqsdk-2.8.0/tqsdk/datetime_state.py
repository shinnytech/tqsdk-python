#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'


"""
时间帮助函数，根据回测/实盘获取不同的当前时间

模块内部创建使用
"""

import time


class TqDatetimeState:

    def __init__(self):
        self.data_ready = False  # 是否收到了第一个 mdhis_more_data
        self.tqsdk_backtest = {}

    def get_current_dt(self):
        """返回当前 nano timestamp"""
        if self.tqsdk_backtest:
            return self.tqsdk_backtest.get('current_dt')
        else:
            return int(time.time() * 1e9)

    def update_state(self, diff):
        self.tqsdk_backtest.update(diff.get('_tqsdk_backtest', {}))
        if not self.data_ready and diff.get('mdhis_more_data', True) is False:
            self.data_ready = True

