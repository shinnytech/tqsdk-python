#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

import sys
import uuid
import asyncio
import functools
import contextlib
import logging
import time

from tqsdk import TqApi, TqSim, TargetPosTask, TqChan
# from tqsdk.tq.logger import WidgetLogger, log_task_exception



'''
TianQin内置策略基类
'''

class TqBase:
    """所有Tq中策略/指标的共同基类"""
    def __init__(self, api):
        self.api = api
        self.logger = logging.getLogger("TQ")
        self.desc_chan = TqChan(api)

    def on_start(self):
        pass

    def on_data(self):
        pass

    def set_desc(self, desc):
        self.desc_chan.send_nowait(desc)


# class TqGui(TqBase):
#     """自带Gui的策略/指标基类"""
#     def __init__(self):
#         TqBase.__init__(self)
#         self.init_gui()
#
#
# class TqComplexStrategy(TqBase):
#     """复杂策略, 超过一个合约或一个周期. 这类合约都自带一个GUI, 用于"""
#     def gui(self):
#         pass
#

class TqKlineStrategy(TqBase):
    """
    K线策略, 绑定一个合约和一个K线周期, 可能需要别的参数
    """
    SYMBOL = ""
    DURATION = 1

    def __init__(self, api, param_list):
        TqBase.__init__(self, api)
        for item in param_list:
            k, v = item
            self.__dict__[k] = v
        self.target_pos = TargetPosTask(self.api, self.SYMBOL)
        self.klines = self.api.get_kline_serial(self.SYMBOL, self.DURATION)
