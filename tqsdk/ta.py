#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

"""
tqsdk.ta 模块包含了一批常用的技术指标计算函数
"""

import numpy as np
import pandas as pd
import numba


def ATR(df, n):
    pre_close = df["close"].shift(1)
    df["tr"] = np.maximum.reduce([df["high"] - df["low"], np.absolute(pre_close - df["high"]), np.absolute(pre_close - df["low"])])
    df["atr"] = df["tr"].rolling(n).mean()
    return df


def BIAS(df, n):
    ma = df["close"].rolling(n).mean()
    df["bias"] = (df["close"] - ma) / ma * 100
    return df


def BOLL(df, n, p):
    """
    布林线.

    Args:
        df (numpy.dataframe): dataframe格式的K线序列

        n: 布林线周期

        p: 布林线p值

    Returns:
        numpy.dataframe: 返回的dataframe包含2个列, 分别是 "top" 和 "bottom", 分别代表布林线的上下轨

    Example::

        # 获取 SHFE.cu1812 合约的布林线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import BOLL

        api = TqApi(TqSim())
        klines = api.get_kline_serial("SHFE.cu1812", 60)
        boll = BOLL(klines.to_dataframe(), 20, 0.1)

        print(boll["top"], boll["bottom"]) # 布林线上下轨序列

        #以上代码将输出
        [..., ..., ..., ...]
        [..., ..., ..., ...]
        ...
    """
    mid = df["close"].rolling(n).mean()
    std = df["close"].rolling(n).std()
    df["top"] = mid + p * std
    df["bottom"] = mid - p * std
    return df


def DMI(df, n, m):
    df = ATR(df, n)
    pre_high = df["high"].shift(1)
    pre_low = df["low"].shift(1)
    hd = df["high"] - pre_high
    ld = pre_low - df["low"]
    admp = pd.Series(np.where((hd > 0) & (hd > ld),  hd, 0)).rolling(n).mean()
    admm = pd.Series(np.where((ld > 0) & (ld > hd),  ld, 0)).rolling(n).mean()

    df["pdi"] = pd.Series(np.where(df["atr"] > 0, admp / df["atr"] * 100, np.NaN)).ffill()
    df["mdi"] = pd.Series(np.where(df["atr"] > 0, admm / df["atr"] * 100, np.NaN)).ffill()
    ad = pd.Series(np.absolute(df["mdi"]-df["pdi"]) / (df["mdi"]+df["pdi"]) * 100)
    df["adx"] = ad.rolling(m).mean()
    df["adxr"] = (df["adx"] + df["adx"].shift(m-1)) / 2
    return df


def KDJ(df, n, m1, m2):
    hv = df["high"].rolling(n).max()
    lv = df["low"].rolling(n).min()
    rsv = pd.Series(np.where(hv == lv, 0, (df["close"] - lv) / (hv -lv) *100))
    df["k"] = rsv.ewm(com=m1, adjust=False).mean() #SMA
    df["d"] = df["k"].ewm(com=m2, adjust=False).mean() # SMA
    df["j"] = 3*df["k"] - 2*df["d"]
    return df


def MA(df, n):
    df["ma"] = df["close"].rolling(n).mean()
    return df


def MACD(df, short, long, m):
    eshort = df["close"].ewm(span=short, adjust=False).mean() #EMA
    elong = df["close"].ewm(span=long, adjust=False).mean() #EMA
    df["diff"] = eshort - elong
    df["dea"] = df["diff"].ewm(span=m, adjust=False).mean() #EMA
    df["bar"] = 2 * (df["diff"] - df["dea"])
    return df


@numba.njit
def _sar(open, high, low, close, range_high, range_low, n, step, maximum):
    sar = np.empty_like(close)
    sar[:n] = np.NAN
    af = 0
    ep = 0
    trend =  1 if (close[n] - open[n]) > 0 else -1
    if trend == 1:
        sar[n] = min(range_low[n-2], low[n-1])
    else:
        sar[n] = max(range_high[n-2], high[n-1])
    for i in range(n, len(sar)):
        if i != n:
            if abs(trend) > 1:
                sar[i] = sar[i-1] + af * (ep - sar[i-1])
            elif trend == 1:
                sar[i] = min(range_low[i-2], low[i-1])
            elif trend == -1:
                sar[i] = max(range_high[i-2], high[i-1])
        if trend > 0:
            if sar[i-1] > low[i]:
                ep = low[i]
                af = step
                trend = -1
            else:
                ep = high[i]
                af = min(af + step, maximum) if ep > range_high[i-1] else af
                trend += 1
        else:
            if sar[i-1] < high[i]:
                ep = high[i]
                af = step
                trend = 1
            else:
                ep = low[i]
                af = min(af + step, maximum) if ep < range_low[i-1] else af
                trend -= 1
    return sar


def SAR(df, n, step, max):
    range_high = df["high"].rolling(n-1).max()
    range_low = df["low"].rolling(n-1).min()
    df["sar"] = _sar(df["open"].values,df["high"].values,df["low"].values,df["close"].values,range_high.values,range_low.values, n, step, max)
    return df

