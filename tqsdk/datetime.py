#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

"""
包含有关时间处理的功能函数
"""


def _get_trading_day_start_time(trading_day):
    """给定交易日, 获得交易日起始时间"""
    begin_mark = 631123200000000000  # 1990-01-01
    start_time = trading_day - 21600000000000  # 6小时
    week_day = (start_time - begin_mark) // 86400000000000 % 7
    if week_day >= 5:
        start_time -= 86400000000000 * (week_day - 4)
    return start_time


def _get_trading_day_end_time(trading_day):
    """给定交易日, 获得交易日结束时间"""
    return trading_day + 64799999999999  # 18小时


def _get_trading_day_from_timestamp(timestamp):
    """给定时间, 获得其所属的交易日"""
    begin_mark = 631123200000000000  # 1990-01-01
    days = (timestamp - begin_mark) // 86400000000000  # 自 1990-01-01 以来的天数
    if (timestamp - begin_mark) % 86400000000000 >= 64800000000000:  # 大于18点, 天数+1
        days += 1
    week_day = days % 7
    if week_day >= 5:  # 如果是周末则移到星期一
        days += 7 - week_day
    return begin_mark + days * 86400000000000
