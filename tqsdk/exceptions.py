#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

class BacktestFinished(Exception):
    """回测结束会抛出此例外"""
    def __init__(self):
        message = "回测结束"
        super().__init__(message)