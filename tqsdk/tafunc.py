#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

"""
tqsdk.tafunc 模块包含了一批用于技术指标计算的函数
"""

import pandas as pd
import numpy as np


def ref(series, n):
    """
    简单移动: 求series序列位移n个周期的结果

    例:
        pre_close = ref(klines.close, 1)     # 将收盘价序列右移一位, 得到昨收盘序列
        change = klines.close - pre_close    # 收盘价序列 - 昨收盘序列, 得到涨跌序列
    """
    m = series.shift(n)
    return m


def std(series, n):
    """
    标准差: 求series序列每n个周期的标准差

    例:
        s = std(klines.close)
    """
    m = series.rolling(n).std()
    return m


def ma(series, n):
    """
    简单移动平均线: 求series序列在n个周期内的简单移动平均

    计算公式:
        ma(x, 5) = (x(1) + x(2) + x(3) + x(4) + x(5)) / 5

    例:
        ma5 = tafunc.ma(df["close"], 5)  # 求5周期收盘价的简单移动平均

    注:
        1. n包含当前k线
        2. 简单移动平均线将设定周期内的值取平均值, 其中各元素的权重都相等
        3. n为0的情况下, 或当n为有效值但当前的k线数不足n根, 函数返回空值
    """
    ma_data = series.rolling(n).mean()
    return ma_data


def sma(series, n, m):
    """
    扩展指数加权移动平均: 求series的n个周期内的扩展指数加权移动平均, m为权重

    计算公式:
        sma(x, n, m) = sma(x, n, m).shift(1) * (n - m) / n + x(n) * m / n

    例:
        sma = tafunc.sma(df["close"], 5, 2)

    注:
        n为0或空值的情况下, 或当n为有效值但当前的k线数不足n根, 函数返回空值
    """
    sma_data = series.ewm(alpha=m / n, adjust=False).mean()
    return sma_data


def ema(series, n):
    """
    指数加权移动平均线: 求series序列n周期的指数加权移动平均(平滑移动平均)

    计算公式:
        ema(x, n) = 2 * x / (n + 1) + (n - 1) * ema(x, n).shift(1) / (n + 1)

    例:
        ema = tafunc.ema(df["close"], 5)  # 求收盘价5周期指数加权移动平均值

    注:
        1. n包含当前k线
        2. 对距离当前较近的k线赋予了较大的权重
        4. n为0或空值的情况下, 或当n为有效值但当前的k线数不足n根, 函数返回空值
    """
    ema_data = series.ewm(span=n, adjust=False).mean()
    return ema_data


def ema2(series, n):
    """
    线性加权移动平均: 求n周期series值的线性加权移动平均 (也称WMA)

    计算公式:
        ema2(x, n) = [n * x(0) + (n - 1) * x(1) + (x - 2) * x(2) + ... + 1 * x(n - 1)] / [n + (n - 1) + (n - 2) + ... + 1]

    例:
        ema2 = tafunc.ema2(df["close"], 5)  # 求收盘价在5个周期的线性加权移动平均值

    注:
        1. n包含当前k线
        2. n为0或空值的情况下, 或当n为有效值但当前的k线数不足n根, 函数返回空值
    """
    weights = list(i for i in range(1, n + 1))  # 对应的权值列表

    def average(elements):
        return np.average(elements, weights=weights)

    ema2 = series.rolling(window=n).apply(average, raw=True)
    return ema2


def crossup(a, b):
    """
    向上穿越: 表当a从下方向上穿过b, 成立返回1, 否则返回0

    例:
        crossup = tafunc.crossup(tafunc.ma(df["close"], 5), tafunc.ma(df["close"], 10))
    """
    crossup_data = pd.Series(np.where((a > b) & (a.shift(1) <= b.shift(1)), 1, 0))
    return crossup_data


def crossdown(a, b):
    """
    向下穿越: 表示当a从上方向下穿b，成立返回1, 否则返回0

    例:
        crossdown = tafunc.crossdown(tafunc.ma(df["close"], 5), tafunc.ma(df["close"], 10))
    """
    crossdown_data = pd.Series(np.where((a < b) & (a.shift(1) >= b.shift(1)), 1, 0))
    return crossdown_data


def count(cond, n):
    """
    统计n周期中满足cond条件的周期数

    例:
        统计从申请到的行情数据以来到当前这段时间内, 5周期均线上穿10周期均线的次数:
        count = tafunc.count(tafunc.crossup(tafunc.ma(df["close"], 5), tafunc.ma(df["close"], 10)), 0)

    注:
        1. n包含当前k线
        2. 如果n为0, 则从第一个有效值开始统计
        4. n为空值时返回值为空值
    """
    if n == 0:  # 从第一个有效值开始统计
        count_data = pd.Series(np.where(cond, 1, 0).cumsum())
    else:  # 统计每个n周期
        count_data = pd.Series(pd.Series(np.where(cond, 1, 0)).rolling(n).sum())
    return count_data


def trma(series, n):
    """
    三角移动平均: 求series在n个周期的三角移动平均值

    计算方法:
        三角移动平均线公式, 是采用算数移动平均, 并且对第一个移动平均线再一次应用算数移动平均

    例:
        trma = tafunc.trma(df["close"], 10)

    注:
        1. n包含当前k线
        2. n为0或空值的情况下, 或当n为有效值但当前的k线数不足n根, 函数返回空值
    """
    if n % 2 == 0:
        n1 = int(n / 2)
        n2 = int(n / 2 + 1)
    else:
        n1 = n2 = int((n + 1) / 2)
    ma_half = ma(series, n1)
    trma_data = ma(ma_half, n2)
    return trma_data


def harmean(series, n):
    """
    调和平均值: 求series在n个周期内的调和平均值

    计算方法:
        harmean(x, 5) = 1 / [(1 / x(1) + 1 / x(2) + 1 / x(3) + 1 / x(4) + 1 / x(5)) / 5]

    例:
        harmean = tafunc.harmean(df["close"], 5)  # 求5周期收盘价的调和平均值

    注:
        1. n包含当前k线
        2. 调和平均值与倒数的简单平均值互为倒数
        3. 当n为有效值, 但当前的k线数不足n根, 函数返回空值
        4. series或n为0或空值的情况下, 函数返回空值
    """
    harmean_data = n / ((1 / series).rolling(n).sum())
    return harmean_data


def numpow(series, n, m):
    """
    自然数幂方和

    计算方法:
        numpow(x, n, m) = n ^ m * x + (n - 1) ^ m * x.shift(1) + (n - 2) ^ m * x.shift(2) + ... + 2 ^ m * x.shift(n - 2) + 1 ^ m * x.shift(n - 1)

    例:
        numpow = tafunc.numpow(df["close"], 5, 2)
    """
    numpow_data = sum((n - i) ** m * series.shift(i) for i in range(n))
    return numpow_data


def abs(series):
    """
    获取series的绝对值

    例:
        abs = tafunc.abs(series)

    注:
        正数的绝对值是它本身, 负数的绝对值是它的相反数, 0的绝对值还是0
    """
    abs_data = pd.Series(np.absolute(series))
    return abs_data


def min(series1, series2):
    """
    获取series1和series2中的最小值

    例:
        min = tafunc.min(series1, series2)
    """
    min_data = np.minimum(series1, series2)
    return min_data


def max(series1, series2):
    """
    获取series1和series2中的最大值

    例:
        max = tafunc.max(series1, series2)
    """
    max_data = np.maximum(series1, series2)
    return max_data


def median(series, n):
    """
    中位数: 求series在n个周期内居于中间的数值

    例1:
        median3 = tafunc.median(df["close"], 3)
        假设最近3日的收盘价为2727, 2754, 2748, 那么当前median(df["close"], 3)的返回值是2748
    例2:
        median4 = tafunc.median(df["open"], 4)
        假设最近4日的开盘价为2752, 2743, 2730, 2728, 那么当前median(df["open"], 4)的返回值是2736.5

    注:
        n个周期内所有series排序后, 若n为奇数, 则选择第(n + 1) / 2个为中位数, 若n为偶数, 则中位数是(n / 2)以及(n / 2 + 1)的平均数
    """
    median_data = series.rolling(n).median()
    return median_data


def exist(cond, n):
    """
    判断n个周期内, 是否有满足cond的条件, 若满足则值为1, 不满足为0

    例:
        exist = tafunc.exist(df["close"] > df["high"].shift(1), 4)  # 表示4个周期中是否存在收盘价大于前一个周期的最高价, 存在返回1, 不存在则返回0
    """
    exist_data = pd.Series(np.where(pd.Series(np.where(cond, 1, 0)).rolling(n).sum() > 0, 1, 0))
    return exist_data


def every(cond, n):
    """
    判断n个周期内, 是否一直满足cond条件, 若满足则值为1, 不满足为0

    例:
        every = tafunc.every(tafunc.ma(df["close"], 3) > tafunc.ma(df["close"], 5), 4)  # 表示在4周期内, 3周期的简单移动平均是否一直大于5周期的简单移动平均

    注:
        n包含当前k线
    """
    every_data = pd.Series(np.where(pd.Series(np.where(cond, 1, 0)).rolling(n).sum() == n, 1, 0))
    return every_data


def hhv(series, n):
    """
    求series在n个周期内的最高值

    例:
        hhv = tafunc.hhv(df["high"], 4)  # 求4个周期最高价的最大值, 即4周期高点(包含当前k线)

    注:
        n包含当前k线
    """
    hhv_data = series.rolling(n).max()
    return hhv_data


def llv(series, n):
    """
    求在n个周期内的最小值

    例:
        llv = tafunc.llv(df["low"], 5)  # 求5根k线最低点(包含当前k线)

    注:
        n包含当前k线
    """
    llv_data = series.rolling(n).min()
    return llv_data


def avedev(series, n):
    """
    平均绝对偏差: 求series在n周期内的平均绝对偏差

    算法:
        计算avedev(df["close"],3)在最近一根K线上的值:
        (abs(df["close"] - (df["close"] + df["close"].shift(1) + df["close"].shift(2)) / 3) + abs(
        df["close"].shift(1) - (df["close"] + df["close"].shift(1) + df["close"].shift(2)) / 3) + abs(
        df["close"].shift(2) - (df["close"] + df["close"].shift(1) + df["close"].shift(2)) / 3)) / 3

    例:
        计算收盘价在5周期内的平均绝对偏差, 表示5个周期内每个周期的收盘价与5周期收盘价的平均值的差的绝对值的平均值, 判断收盘价与其均值的偏离程度:
        avedev = tafunc.avedev(df["close"], 5)

    注:
        1. 包含当前k线
        2. n为0时, 该函数返回空值
    """

    def mad(x):
        return np.fabs(x - x.mean()).mean()

    avedev_data = series.rolling(window=n).apply(mad, raw=True)
    return avedev_data
