#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'

import numpy as np
from pandas import DataFrame

from tqsdk.datetime import _get_trading_timestamp, _get_trade_timestamp
from tqsdk.rangeset import _rangeset_head, _rangeset_slice, _rangeset_length

"""
检查参数类型
"""

from inspect import isfunction


def _check_volume_limit(min_volume, max_volume):
    if min_volume is not None and min_volume <= 0:
        raise Exception("最小下单手数(min_volume) %s 错误, 请检查 min_volume 是否填写正确" % min_volume)
    if max_volume is not None and max_volume <= 0:
        raise Exception("最大下单手数(max_volume) %s 错误, 请检查 max_volume 是否填写正确" % max_volume)
    if (min_volume is None and max_volume) or (max_volume is None and min_volume):
        raise Exception("最小下单手数(min_volume) %s 和 最大下单手数(max_volume) %s 必须用时填写" % (min_volume, max_volume))
    if min_volume and max_volume and min_volume > max_volume:
        raise Exception("最小下单手数(min_volume) %s ，最大下单手数(max_volume) %s 错误, 请检查 min_volume, max_volume 是否填写正确" % (
            min_volume, max_volume))
    return int(min_volume) if min_volume else None, int(max_volume) if max_volume else None


def _check_direction(direction):
    if direction not in ("BUY", "SELL"):
        raise Exception("下单方向(direction) %s 错误, 请检查 direction 参数是否填写正确" % direction)
    return direction


def _check_offset(offset):
    if offset not in ("OPEN", "CLOSE", "CLOSETODAY"):
        raise Exception("开平标志(offset) %s 错误, 请检查 offset 是否填写正确" % offset)
    return offset


def _check_offset_priority(offset_priority):
    if len(offset_priority.replace(",", "").replace("今", "", 1).replace("昨", "", 1).replace("开", "", 1)) > 0:
        raise Exception("开平仓顺序(offset_priority) %s 错误, 请检查 offset_priority 参数是否填写正确" % offset_priority)
    return offset_priority


def _check_volume(volume):
    _volume = int(volume)
    if _volume <= 0:
        raise Exception("下单手数(volume) %s 错误, 请检查 volume 是否填写正确" % volume)
    return _volume


def _check_price(price):
    if price in ("ACTIVE", "PASSIVE") or isfunction(price):
        return price
    else:
        raise Exception("下单方式(price) %s 错误, 请检查 price 参数是否填写正确" % price)


def _check_time_table(time_table: DataFrame):
    if not isinstance(time_table, DataFrame):
        raise Exception(f"time_table 参数应该是 pandas.DataFrame 类型")
    need_columns = {'price', 'target_pos', 'interval'} - set(time_table.columns)
    if need_columns:
        raise Exception(f"缺少必要的列 {need_columns}")
    if time_table.shape[0] > 0:
        if time_table['interval'].isnull().values.any() or np.where(time_table['interval'] < 0, True, False).any():
            raise Exception(f"interval 列必须为正数，请检查参数 {time_table['interval']}")
        if time_table['target_pos'].isnull().values.any() or not np.issubdtype(time_table['target_pos'].dtype, np.integer):
            raise Exception(f"target_pos 列必须为整数，请检查参数 {time_table['target_pos']}")
        if not (np.isin(time_table['price'], ('PASSIVE', 'ACTIVE', None)) | time_table['price'].apply(isfunction)).all():
            raise Exception(f"price 列必须为 ('PASSIVE', 'ACTIVE', None, Callable) 之一，请检查参数 {time_table['price']}")
    return time_table


def _get_deadline_from_interval(quote, interval):
    """将 interval （持续长度 seconds）列转换为 deadline（结束时间 nano_timestamp）"""
    # 当前交易日完整的交易时间段
    trading_timestamp = _get_trading_timestamp(quote, quote.datetime)
    trading_timestamp_nano_range = trading_timestamp['night'] + trading_timestamp['day']  # 当前交易日完整的交易时间段
    # 当前时间 行情时间
    current_timestamp_nano = _get_trade_timestamp(quote.datetime, float('nan'))
    if not trading_timestamp_nano_range[0][0] <= current_timestamp_nano < trading_timestamp_nano_range[-1][1]:
        raise Exception("当前时间不在指定的交易时间段内")
    deadline = []
    for index, value in interval.items():
        r = _rangeset_head(_rangeset_slice(trading_timestamp_nano_range, current_timestamp_nano), int(value * 1e9))
        if _rangeset_length(r) < int(value * 1e9):
            raise Exception("指定时间段超出当前交易日")
        deadline.append(r[-1][1])
        current_timestamp_nano = r[-1][1]
    return deadline
