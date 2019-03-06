#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

"""
tqsdk.ta_func 模块包含了一批用于技术指标计算的函数
"""

import pandas as pd
import numpy as np


def ma(series, n):
    """简单移动平均线"""
    ma_data = series.rolling(n).mean()
    return ma_data


def sma(series, n, m):
    """扩展指数加权移动平均"""
    sma_data = series.ewm(alpha=m / n, adjust=False).mean()
    return sma_data


def ema(series, n):
    """指数加权移动平均线"""
    ema_data = series.ewm(span=n, adjust=False).mean()
    return ema_data


def ema2(series, n):
    """线性加权移动平均 WMA"""
    weights = list(i for i in range(1, n + 1))  # 对应的权值列表

    def average(elements):
        return np.average(elements, weights=weights)

    ema2 = series.rolling(window=n).apply(average, raw=True)
    return ema2


def crossup(a, b):
    """向上穿越"""
    crossup_data = pd.Series(np.where((a > b) & (a.shift(1) <= b.shift(1)), 1, 0))
    return crossup_data


def crossdown(a, b):
    """向下穿越"""
    crossdown_data = pd.Series(np.where((a < b) & (a.shift(1) >= b.shift(1)), 1, 0))
    return crossdown_data


def count(cond, n):
    """统计n周期内中满足cond条件的周期数;
        如果n为0,则从第一个有效值开始统计
    """
    if n == 0:  # 从第一个有效值开始统计
        count_data = pd.Series(np.where(cond, 1, 0).cumsum())
    else:  # 统计每个n周期
        count_data = pd.Series(pd.Series(np.where(cond, 1, 0)).rolling(n).sum())
    return count_data


def trma(series, n):
    """三角移动平均"""
    if n % 2 == 0:
        n1 = int(n / 2)
        n2 = int(n / 2 + 1)
    else:
        n1 = n2 = int((n + 1) / 2)
    ma_half = ma(series, n1)
    trma_data = ma(ma_half, n2)
    return trma_data


def harmean(series, n):
    """调和平均值"""
    harmean_data = n / ((1 / series).rolling(n).sum())
    return harmean_data


def numpow(series, n, m):
    """自然数幂方和"""
    numpow_data = sum((n - i) ** m * series.shift(i) for i in range(n))
    return numpow_data


def abs(series):
    """获取series的绝对值"""
    abs_data = pd.Series(np.absolute(series))
    return abs_data


def min(series1, series2):
    """获取series1和series2中的最小值"""
    min_data = np.minimum(series1, series2)
    return min_data


def max(series1, series2):
    """获取series1和series2中的最大值"""
    max_data = np.maximum(series1, series2)
    return max_data


def median(series, n):
    """中位数: 求series在n个周期内居于中间的数值"""
    median_data = series.rolling(n).median()
    return median_data


def exist(cond, n):
    """判断n个周期内,是否有满足cond的条件"""
    exist_data = pd.Series(np.where(pd.Series(np.where(cond, 1, 0)).rolling(n).sum() > 0, 1, 0))
    return exist_data


def every(cond, n):
    """判断n周期内,是否一直满足cond条件"""
    every_data = pd.Series(np.where(pd.Series(np.where(cond, 1, 0)).rolling(n).sum() == n, 1, 0))
    return every_data


def hhv(series, n):
    """求series在n个周期内的最高值"""
    hhv_data = series.rolling(n).max()
    return hhv_data


def llv(series, n):
    """求在n个周期内的最小值"""
    llv_data = series.rolling(n).min()
    return llv_data


def avedev(series, n):
    """平均绝对偏差: 求series在n周期内的平均绝对偏差"""

    def mad(x):
        return np.fabs(x - x.mean()).mean()

    avedev_data = series.rolling(window=n).apply(mad, raw=True)
    return avedev_data
