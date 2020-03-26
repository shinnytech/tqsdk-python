#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

"""
tqsdk.ta 模块包含了一批常用的技术指标计算函数
(函数返回值类型保持为 pandas.Dataframe)
"""

import math
import numpy as np
import pandas as pd
from tqsdk import tafunc


def ATR(df, n):
    """
    平均真实波幅

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 平均真实波幅的周期

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 分别是"tr"和"atr", 分别代表真实波幅和平均真实波幅

    Example::

        # 获取 CFFEX.IF1903 合约的平均真实波幅
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import ATR

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        atr = ATR(klines, 14)
        print(atr.tr)  # 真实波幅
        print(atr.atr)  # 平均真实波幅

        # 预计的输出是这样的:
        [..., 143.0, 48.0, 80.0, ...]
        [..., 95.20000000000005, 92.0571428571429, 95.21428571428575, ...]
    """
    new_df = pd.DataFrame()
    pre_close = df["close"].shift(1)
    new_df["tr"] = np.where(df["high"] - df["low"] > np.absolute(pre_close - df["high"]),
                            np.where(df["high"] - df["low"] > np.absolute(pre_close - df["low"]),
                                     df["high"] - df["low"], np.absolute(pre_close - df["low"])),
                            np.where(np.absolute(pre_close - df["high"]) > np.absolute(pre_close - df["low"]),
                                     np.absolute(pre_close - df["high"]), np.absolute(pre_close - df["low"])))
    new_df["atr"] = tafunc.ma(new_df["tr"], n)
    return new_df


def BIAS(df, n):
    """
    乖离率

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 移动平均的计算周期

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"bias", 代表计算出来的乖离率值

    Example::

        # 获取 CFFEX.IF1903 合约的乖离率
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import BIAS

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        bias = BIAS(klines, 6)
        print(list(bias["bias"]))  # 乖离率

        # 预计的输出是这样的:
        [..., 2.286835533357118, 2.263301549041151, 0.7068445823271412, ...]
    """
    ma1 = tafunc.ma(df["close"], n)
    new_df = pd.DataFrame(data=list((df["close"] - ma1) / ma1 * 100), columns=["bias"])
    return new_df


def BOLL(df, n, p):
    """
    布林线

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

        p (int): 计算参数p

    Returns:
        pandas.DataFrame: 返回的dataframe包含3列, 分别是"mid", "top"和"bottom", 分别代表布林线的中、上、下轨

    Example::

        # 获取 CFFEX.IF1903 合约的布林线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import BOLL

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        boll=BOLL(klines, 26, 2)
        print(list(boll["mid"]))
        print(list(boll["top"]))
        print(list(boll["bottom"]))

        # 预计的输出是这样的:
        [..., 3401.338461538462, 3425.600000000001, 3452.3230769230777, ...]
        [..., 3835.083909752222, 3880.677579320277, 3921.885406954584, ...]
        [..., 2967.593013324702, 2970.5224206797247, 2982.760746891571, ...]
    """
    new_df = pd.DataFrame()
    mid = tafunc.ma(df["close"], n)
    std = df["close"].rolling(n).std()
    new_df["mid"] = mid
    new_df["top"] = mid + p * std
    new_df["bottom"] = mid - p * std
    return new_df


def DMI(df, n, m):
    """
    动向指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

        m (int): 周期m

    Returns:
        pandas.DataFrame: 返回的DataFrame包含5列, 是"atr", "pdi", "mdi", "adx"和"adxr", 分别代表平均真实波幅, 上升方向线, 下降方向线, 趋向平均值以及评估数值

    Example::

        # 获取 CFFEX.IF1903 合约的动向指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import DMI

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        dmi=DMI(klines, 14, 6)
        print(list(dmi["atr"]))
        print(list(dmi["pdi"]))
        print(list(dmi["mdi"]))
        print(list(dmi["adx"]))
        print(list(dmi["adxr"]))

        # 预计的输出是这样的:
        [..., 95.20000000000005, 92.0571428571429, 95.21428571428575, ...]
        [..., 51.24549819927972, 46.55493482309126, 47.14178544636161, ...]
        [..., 6.497599039615802, 6.719428926132791, 6.4966241560389655, ...]
        [..., 78.80507786697127, 76.8773544355082, 75.11662664555287, ...]
        [..., 70.52493837227118, 73.28531799111778, 74.59341569051983, ...]
    """
    new_df = pd.DataFrame()
    new_df["atr"] = ATR(df, n)["atr"]
    pre_high = df["high"].shift(1)
    pre_low = df["low"].shift(1)
    hd = df["high"] - pre_high
    ld = pre_low - df["low"]
    admp = tafunc.ma(pd.Series(np.where((hd > 0) & (hd > ld), hd, 0)), n)
    admm = tafunc.ma(pd.Series(np.where((ld > 0) & (ld > hd), ld, 0)), n)
    new_df["pdi"] = pd.Series(np.where(new_df["atr"] > 0, admp / new_df["atr"] * 100, np.NaN)).ffill()
    new_df["mdi"] = pd.Series(np.where(new_df["atr"] > 0, admm / new_df["atr"] * 100, np.NaN)).ffill()
    ad = pd.Series(np.absolute(new_df["mdi"] - new_df["pdi"]) / (new_df["mdi"] + new_df["pdi"]) * 100)
    new_df["adx"] = tafunc.ma(ad, m)
    new_df["adxr"] = (new_df["adx"] + new_df["adx"].shift(m)) / 2
    return new_df


def KDJ(df, n, m1, m2):
    """
    随机指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

        m1 (int): 参数m1

        m2 (int): 参数m2

    Returns:
        pandas.DataFrame: 返回的DataFrame包含3列, 是"k", "d"和"j", 分别代表计算出来的K值, D值和J值

    Example::

        # 获取 CFFEX.IF1903 合约的随机指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import KDJ

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        kdj = KDJ(klines, 9, 3, 3)
        print(list(kdj["k"]))
        print(list(kdj["d"]))
        print(list(kdj["j"]))

        # 预计的输出是这样的:
        [..., 80.193148635668, 81.83149521546302, 84.60665654726242, ...]
        [..., 82.33669997171852, 82.16829838630002, 82.98108443995415, ...]
        [..., 77.8451747299365, 75.90604596356695, 81.15788887378903, ...]
    """
    new_df = pd.DataFrame()
    hv = df["high"].rolling(n).max()
    lv = df["low"].rolling(n).min()
    rsv = pd.Series(np.where(hv == lv, 0, (df["close"] - lv) / (hv - lv) * 100))
    new_df["k"] = tafunc.sma(rsv, m1, 1)
    new_df["d"] = tafunc.sma(new_df["k"], m2, 1)
    new_df["j"] = 3 * new_df["k"] - 2 * new_df["d"]
    return new_df


def MACD(df, short, long, m):
    """
    异同移动平均线

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        short (int): 短周期

        long (int): 长周期

        m (int): 移动平均线的周期

    Returns:
        pandas.DataFrame: 返回的DataFrame包含3列, 是"diff", "dea"和"bar", 分别代表离差值, DIFF的指数加权移动平均线, MACD的柱状线

        (注: 因 DataFrame 有diff()函数，因此获取到此指标后："diff"字段使用 macd["diff"] 方式来取值，而非 macd.diff )

    Example::

        # 获取 CFFEX.IF1903 合约的异同移动平均线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import MACD

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        macd = MACD(klines, 12, 26, 9)
        print(list(macd["diff"]))
        print(list(macd["dea"]))
        print(list(macd["bar"]))

        # 预计的输出是这样的:
        [..., 149.58313904045826, 155.50790712365142, 160.27622505636737, ...]
        [..., 121.46944573796466, 128.27713801510203, 134.6769554233551, ...]
        [..., 56.2273866049872, 54.46153821709879, 51.19853926602451, ...]
    """
    new_df = pd.DataFrame()
    eshort = tafunc.ema(df["close"], short)
    elong = tafunc.ema(df["close"], long)
    new_df["diff"] = eshort - elong
    new_df["dea"] = tafunc.ema(new_df["diff"], m)
    new_df["bar"] = 2 * (new_df["diff"] - new_df["dea"])
    return new_df


# @numba.njit
def _sar(open, high, low, close, range_high, range_low, n, step, maximum):
    n = max(np.sum(np.isnan(range_high)), np.sum(np.isnan(range_low))) + 2
    sar = np.empty_like(close)
    sar[:n] = np.NAN
    af = 0
    ep = 0
    trend = 1 if (close[n] - open[n]) > 0 else -1
    if trend == 1:
        sar[n] = min(range_low[n - 2], low[n - 1])
    else:
        sar[n] = max(range_high[n - 2], high[n - 1])
    for i in range(n, len(sar)):
        if i != n:
            if abs(trend) > 1:
                sar[i] = sar[i - 1] + af * (ep - sar[i - 1])
            elif trend == 1:
                sar[i] = min(range_low[i - 2], low[i - 1])
            elif trend == -1:
                sar[i] = max(range_high[i - 2], high[i - 1])
        if trend > 0:
            if sar[i - 1] > low[i]:
                ep = low[i]
                af = step
                trend = -1
            else:
                ep = high[i]
                af = min(af + step, maximum) if ep > range_high[i - 1] else af
                trend += 1
        else:
            if sar[i - 1] < high[i]:
                ep = high[i]
                af = step
                trend = 1
            else:
                ep = low[i]
                af = min(af + step, maximum) if ep < range_low[i - 1] else af
                trend -= 1
    return sar


def SAR(df, n, step, max):
    """
    抛物线指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): SAR的周期n

        step (float): 步长

        max (float): 极值

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"sar", 代表计算出来的SAR值

    Example::

        # 获取 CFFEX.IF1903 合约的抛物线指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import SAR

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        sar=SAR(klines, 4, 0.02, 0.2)
        print(list(sar["sar"]))


        # 预计的输出是这样的:
        [..., 3742.313604622293, 3764.5708836978342, 3864.4, ...]
    """
    range_high = df["high"].rolling(n - 1).max()
    range_low = df["low"].rolling(n - 1).min()
    sar = _sar(df["open"].values, df["high"].values, df["low"].values, df["close"].values, range_high.values,
               range_low.values, n, step, max)
    new_df = pd.DataFrame(data=sar, columns=["sar"])
    return new_df


def WR(df, n):
    """
    威廉指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"wr", 代表计算出来的威廉指标

    Example::

        # 获取 CFFEX.IF1903 合约的威廉指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import WR

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        wr = WR(klines, 14)
        print(list(wr["wr"]))

        # 预计的输出是这样的:
        [..., -12.843029637760672, -8.488840102451537, -16.381322957198407, ...]
    """
    hn = df["high"].rolling(n).max()
    ln = df["low"].rolling(n).min()
    new_df = pd.DataFrame(data=list((hn - df["close"]) / (hn - ln) * (-100)), columns=["wr"])
    return new_df


def RSI(df, n):
    """
    相对强弱指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"rsi", 代表计算出来的相对强弱指标

    Example::

        # 获取 CFFEX.IF1903 合约的相对强弱指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import RSI

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        rsi = RSI(klines, 7)
        print(list(rsi["rsi"]))

        # 预计的输出是这样的:
        [..., 80.21169825630794, 81.57315806032297, 72.34968324924667, ...]
    """
    lc = df["close"].shift(1)
    rsi = tafunc.sma(pd.Series(np.where(df["close"] - lc > 0, df["close"] - lc, 0)), n, 1) / \
          tafunc.sma(np.absolute(df["close"] - lc), n, 1) * 100
    new_df = pd.DataFrame(data=rsi, columns=["rsi"])
    return new_df


def ASI(df):
    """
    振动升降指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"asi", 代表计算出来的振动升降指标

    Example::

        # 获取 CFFEX.IF1903 合约的振动升降指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import ASI

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        asi = ASI(klines)
        print(list(asi["asi"]))


        # 预计的输出是这样的:
        [..., -4690.587005986468, -4209.182816350308, -4699.742010304962, ...]
    """
    lc = df["close"].shift(1)  # 上一交易日的收盘价
    aa = np.absolute(df["high"] - lc)
    bb = np.absolute(df["low"] - lc)
    cc = np.absolute(df["high"] - df["low"].shift(1))
    dd = np.absolute(lc - df["open"].shift(1))
    r = np.where((aa > bb) & (aa > cc), aa + bb / 2 + dd / 4,
                 np.where((bb > cc) & (bb > aa), bb + aa / 2 + dd / 4, cc + dd / 4))
    x = df["close"] - lc + (df["close"] - df["open"]) / 2 + lc - df["open"].shift(1)
    si = np.where(r == 0, 0, 16 * x / r * np.where(aa > bb, aa, bb))
    new_df = pd.DataFrame(data=list(pd.Series(si).cumsum()), columns=["asi"])
    return new_df


def VR(df, n):
    """
    VR 容量比率

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"vr", 代表计算出来的VR

    Example::

        # 获取 CFFEX.IF1903 合约的VR
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import VR

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        vr = VR(klines, 26)
        print(list(vr["vr"]))


        # 预计的输出是这样的:
        [..., 150.1535316212112, 172.2897559521652, 147.04236342791924, ...]
    """
    lc = df["close"].shift(1)
    vr = pd.Series(np.where(df["close"] > lc, df["volume"], 0)).rolling(n).sum() / pd.Series(
        np.where(df["close"] <= lc, df["volume"], 0)).rolling(n).sum() * 100
    new_df = pd.DataFrame(data=list(vr), columns=["vr"])
    return new_df


def ARBR(df, n):
    """
    人气意愿指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"ar"和"br" , 分别代表人气指标和意愿指标

    Example::

        # 获取 CFFEX.IF1903 合约的人气意愿指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import ARBR

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        arbr = ARBR(klines, 26)
        print(list(arbr["ar"]))
        print(list(arbr["br"]))


        # 预计的输出是这样的:
        [..., 183.5698517817721, 189.98732572877034, 175.08802816901382, ...]
        [..., 267.78549382716034, 281.567546278062, 251.08041091037902, ...]
    """
    new_df = pd.DataFrame()
    new_df["ar"] = (df["high"] - df["open"]).rolling(n).sum() / (df["open"] - df["low"]).rolling(n).sum() * 100
    new_df["br"] = pd.Series(
        np.where(df["high"] - df["close"].shift(1) > 0, df["high"] - df["close"].shift(1), 0)).rolling(
        n).sum() / pd.Series(
        np.where(df["close"].shift(1) - df["low"] > 0, df["close"].shift(1) - df["low"], 0)).rolling(n).sum() * 100
    return new_df


def DMA(df, short, long, m):
    """
    平均线差

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        short (int): 短周期

        long (int): 长周期

        m (int): 计算周期m

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"ddd"和"ama", 分别代表长短周期均值的差和ddd的简单移动平均值

    Example::

        # 获取 CFFEX.IF1903 合约的平均线差
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import DMA

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        dma = DMA(klines, 10, 50, 10)
        print(list(dma["ddd"]))
        print(list(dma["ama"]))


        # 预计的输出是这样的:
        [..., 409.2520000000022, 435.68000000000166, 458.3360000000025, ...]
        [..., 300.64360000000147, 325.0860000000015, 349.75200000000166, ...]
    """
    new_df = pd.DataFrame()
    new_df["ddd"] = tafunc.ma(df["close"], short) - tafunc.ma(df["close"], long)
    new_df["ama"] = tafunc.ma(new_df["ddd"], m)
    return new_df


def EXPMA(df, p1, p2):
    """
    指数加权移动平均线组合

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        p1 (int): 周期1

        p2 (int): 周期2

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"ma1"和"ma2", 分别代表指数加权移动平均线1和指数加权移动平均线2

    Example::

        # 获取 CFFEX.IF1903 合约的指数加权移动平均线组合
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import EXPMA

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        expma = EXPMA(klines, 5, 10)
        print(list(expma["ma1"]))
        print(list(expma["ma2"]))


        # 预计的输出是这样的:
        [..., 3753.679549224137, 3784.6530328160916, 3792.7020218773946, ...]
        [..., 3672.4492964832566, 3704.113060759028, 3723.1470497119317, ...]
    """
    new_df = pd.DataFrame()
    new_df["ma1"] = tafunc.ema(df["close"], p1)
    new_df["ma2"] = tafunc.ema(df["close"], p2)
    return new_df


def CR(df, n, m):
    """
    CR能量

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

        m (int): 周期m

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"cr"和"crma", 分别代表CR值和CR值的简单移动平均值

    Example::

        # 获取 CFFEX.IF1903 合约的CR能量
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import CR

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        cr = CR(klines, 26, 5)
        print(list(cr["cr"]))
        print(list(cr["crma"]))


        # 预计的输出是这样的:
        [..., 291.5751884671343, 316.71058105671943, 299.50578748862046, ...]
        [..., 316.01257308163747, 319.3545725665982, 311.8275184876805, ...]
    """
    new_df = pd.DataFrame()
    mid = (df["high"] + df["low"] + df["close"]) / 3
    new_df["cr"] = pd.Series(np.where(0 > df["high"] - mid.shift(1), 0, df["high"] - mid.shift(1))).rolling(
        n).sum() / pd.Series(np.where(0 > mid.shift(1) - df["low"], 0, mid.shift(1) - df["low"])).rolling(n).sum() * 100
    new_df["crma"] = tafunc.ma(new_df["cr"], m).shift(int(m / 2.5 + 1))
    return new_df


def CCI(df, n):
    """
    顺势指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"cci", 代表计算出来的CCI值

    Example::

        # 获取 CFFEX.IF1903 合约的顺势指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import CCI

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        cci = CCI(klines, 14)
        print(list(cci["cci"]))


        # 预计的输出是这样的:
        [..., 98.13054698810375, 93.57661788413617, 77.8671380173813, ...]
    """
    typ = (df["high"] + df["low"] + df["close"]) / 3
    ma = tafunc.ma(typ, n)

    def mad(x):
        return np.fabs(x - x.mean()).mean()

    md = typ.rolling(window=n).apply(mad, raw=True)  # 平均绝对偏差
    new_df = pd.DataFrame(data=list((typ - ma) / (md * 0.015)), columns=["cci"])
    return new_df


def OBV(df):
    """
    能量潮

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"obv", 代表计算出来的OBV值

    Example::

        # 获取 CFFEX.IF1903 合约的能量潮
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import OBV

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        obv = OBV(klines)
        print(list(obv["obv"]))


        # 预计的输出是这样的:
        [..., 267209, 360351, 264476, ...]
    """
    lc = df["close"].shift(1)
    obv = (np.where(df["close"] > lc, df["volume"], np.where(df["close"] < lc, -df["volume"], 0))).cumsum()
    new_df = pd.DataFrame(data=obv, columns=["obv"])
    return new_df


def CDP(df, n):
    """
    逆势操作

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含4列, 是"ah", "al", "nh", "nl", 分别代表最高值, 最低值, 近高值, 近低值

    Example::

        # 获取 CFFEX.IF1903 合约的逆势操作指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import CDP

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        cdp = CDP(klines, 3)
        print(list(cdp["ah"]))
        print(list(cdp["al"]))
        print(list(cdp["nh"]))
        print(list(cdp["nl"]))


        # 预计的输出是这样的:
        [..., 3828.244444444447, 3871.733333333336, 3904.37777777778, ...]
        [..., 3656.64444444444, 3698.3999999999955, 3734.9111111111065, ...]
        [..., 3743.8888888888837, 3792.3999999999946, 3858.822222222217, ...]
        [..., 3657.2222222222213, 3707.6666666666656, 3789.955555555554, ...]
    """
    new_df = pd.DataFrame()
    pt = df["high"].shift(1) - df["low"].shift(1)
    cdp = (df["high"].shift(1) + df["low"].shift(1) + df["close"].shift(1)) / 3
    new_df["ah"] = tafunc.ma(cdp + pt, n)
    new_df["al"] = tafunc.ma(cdp - pt, n)
    new_df["nh"] = tafunc.ma(2 * cdp - df["low"], n)
    new_df["nl"] = tafunc.ma(2 * cdp - df["high"], n)
    return new_df


def HCL(df, n):
    """
    均线通道

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含3列, 是"mah", "mal", "mac", 分别代表最高价的移动平均线, 最低价的移动平均线以及收盘价的移动平均线

    Example::

        # 获取 CFFEX.IF1903 合约的均线通道指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import HCL

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        hcl = HCL(klines, 10)
        print(list(hcl["mah"]))
        print(list(hcl["mal"]))
        print(list(hcl["mac"]))


        # 预计的输出是这样的:
        [..., 3703.5400000000022, 3743.2800000000025, 3778.300000000002, ...]
        [..., 3607.339999999999, 3643.079999999999, 3677.579999999999, ...]
        [..., 3666.1600000000008, 3705.8600000000006, 3741.940000000001, ...]
    """
    new_df = pd.DataFrame()
    new_df["mah"] = tafunc.ma(df["high"], n)
    new_df["mal"] = tafunc.ma(df["low"], n)
    new_df["mac"] = tafunc.ma(df["close"], n)
    return new_df


def ENV(df, n, k):
    """
    包略线 (Envelopes)

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

        k (float): 参数k

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"upper", "lower", 分别代表上线和下线

    Example::

        # 获取 CFFEX.IF1903 合约的包略线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import ENV

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        env = ENV(klines, 14, 6)
        print(list(env["upper"]))
        print(list(env["lower"]))


        # 预计的输出是这样的:
        [..., 3842.2122857142863, 3876.7531428571433, 3893.849428571429, ...]
        [..., 3407.244857142857, 3437.875428571429, 3453.036285714286, ...]
    """
    new_df = pd.DataFrame()
    new_df["upper"] = tafunc.ma(df["close"], n) * (1 + k / 100)
    new_df["lower"] = tafunc.ma(df["close"], n) * (1 - k / 100)
    return new_df


def MIKE(df, n):
    """
    麦克指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含6列, 是"wr", "mr", "sr", "ws", "ms", "ss", 分别代表初级压力价,中级压力,强力压力,初级支撑,中级支撑和强力支撑

    Example::

        # 获取 CFFEX.IF1903 合约的麦克指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import MIKE

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        mike = MIKE(klines, 12)
        print(list(mike["wr"]))
        print(list(mike["mr"]))
        print(list(mike["sr"]))
        print(list(mike["ws"]))
        print(list(mike["ms"]))
        print(list(mike["ss"]))


        # 预计的输出是这样的:
        [..., 4242.4, 4203.333333333334, 3986.266666666666, ...]
        [..., 4303.6, 4283.866666666667, 4175.333333333333, ...]
        [..., 4364.8, 4364.4, 4364.4, ...]
        [..., 3770.5999999999995, 3731.9333333333343, 3514.866666666666, ...]
        [..., 3359.9999999999995, 3341.066666666667, 3232.533333333333, ...]
        [..., 2949.3999999999996, 2950.2, 2950.2, ...]
    """
    new_df = pd.DataFrame()
    typ = (df["high"] + df["low"] + df["close"]) / 3
    ll = df["low"].rolling(n).min()
    hh = df["high"].rolling(n).max()
    new_df["wr"] = typ + (typ - ll)
    new_df["mr"] = typ + (hh - ll)
    new_df["sr"] = 2 * hh - ll
    new_df["ws"] = typ - (hh - typ)
    new_df["ms"] = typ - (hh - ll)
    new_df["ss"] = 2 * ll - hh
    return new_df


def PUBU(df, m):
    """
    瀑布线

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        m (int): 周期m

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"pb", 代表计算出的瀑布线

    Example::

        # 获取 CFFEX.IF1903 合约的瀑布线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import PUBU

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        pubu = PUBU(klines, 4)
        print(list(pubu["pb"]))


        # 预计的输出是这样的:
        [..., 3719.087702972829, 3728.9326217836974, 3715.7537397368856, ...]
    """
    pb = (tafunc.ema(df["close"], m) + tafunc.ma(df["close"], m * 2) + tafunc.ma(df["close"], m * 4)) / 3
    new_df = pd.DataFrame(data=list(pb), columns=["pb"])
    return new_df


def BBI(df, n1, n2, n3, n4):
    """
    多空指数

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n1 (int): 周期n1

        n2 (int): 周期n2

        n3 (int): 周期n3

        n4 (int): 周期n4

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"bbi", 代表计算出的多空指标

    Example::

        # 获取 CFFEX.IF1903 合约的多空指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import BBI

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        bbi = BBI(klines, 3, 6, 12, 24)
        print(list(bbi["bbi"]))


        # 预计的输出是这样的:
        [..., 3679.841666666668, 3700.9645833333348, 3698.025000000002, ...]
    """
    bbi = (tafunc.ma(df["close"], n1) + tafunc.ma(df["close"], n2) + tafunc.ma(df["close"], n3) + tafunc.ma(
        df["close"], n4)) / 4
    new_df = pd.DataFrame(data=list(bbi), columns=["bbi"])
    return new_df


def DKX(df, m):
    """
    多空线

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        m (int): 周期m

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"b", "d", 分别代表计算出来的DKX指标及DKX的m日简单移动平均值

    Example::

        # 获取 CFFEX.IF1903 合约的多空线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import DKX

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        dkx = DKX(klines, 10)
        print(list(dkx["b"]))
        print(list(dkx["d"]))


        # 预计的输出是这样的:
        [..., 3632.081746031746, 3659.4501587301593, 3672.744761904762, ...]
        [..., 3484.1045714285706, 3516.1797301587294, 3547.44857142857, ...]
    """
    new_df = pd.DataFrame()
    a = (3 * df["close"] + df["high"] + df["low"] + df["open"]) / 6
    new_df["b"] = (20 * a + 19 * a.shift(1) + 18 * a.shift(2) + 17 * a.shift(3) + 16 * a.shift(4) + 15 * a.shift(
        5) + 14 * a.shift(6)
                   + 13 * a.shift(7) + 12 * a.shift(8) + 11 * a.shift(9) + 10 * a.shift(10) + 9 * a.shift(
                11) + 8 * a.shift(
                12) + 7 * a.shift(13) + 6 * a.shift(14) + 5 * a.shift(15) + 4 * a.shift(16) + 3 * a.shift(
                17) + 2 * a.shift(18) + a.shift(20)
                   ) / 210
    new_df["d"] = tafunc.ma(new_df["b"], m)
    return new_df


def BBIBOLL(df, n, m):
    """
    多空布林线

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 参数n

        m (int): 参数m

    Returns:
        pandas.DataFrame: 返回的DataFrame包含3列, 是"bbiboll", "upr", "dwn", 分别代表多空布林线, 压力线和支撑线

    Example::

        # 获取 CFFEX.IF1903 合约的多空布林线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import BBIBOLL

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        bbiboll=BBIBOLL(klines,10,3)
        print(list(bbiboll["bbiboll"]))
        print(list(bbiboll["upr"]))
        print(list(bbiboll["dwn"]))


        # 预计的输出是这样的:
        [..., 3679.841666666668, 3700.9645833333348, 3698.025000000002, ...]
        [..., 3991.722633271389, 3991.796233444868, 3944.7721466057383, ...]
        [..., 3367.960700061947, 3410.1329332218015, 3451.2778533942655, ...]
    """
    new_df = pd.DataFrame()
    new_df["bbiboll"] = (tafunc.ma(df["close"], 3) + tafunc.ma(df["close"], 6) + tafunc.ma(df["close"],
                                                                                           12) + tafunc.ma(
        df["close"], 24)) / 4
    new_df["upr"] = new_df["bbiboll"] + m * new_df["bbiboll"].rolling(n).std()
    new_df["dwn"] = new_df["bbiboll"] - m * new_df["bbiboll"].rolling(n).std()
    return new_df


def ADTM(df, n, m):
    """
    动态买卖气指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

        m (int): 周期m

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"adtm", "adtmma", 分别代表计算出来的ADTM指标及其M日的简单移动平均

    Example::

        # 获取 CFFEX.IF1903 合约的动态买卖气指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import ADTM

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        adtm = ADTM(klines, 23, 8)
        print(list(adtm["adtm"]))
        print(list(adtm["adtmma"]))


        # 预计的输出是这样的:
        [..., 0.8404011965511171, 0.837919942816297, 0.8102215868477481, ...]
        [..., 0.83855483869397, 0.8354743499113684, 0.8257261282040207, ...]
    """
    new_df = pd.DataFrame()
    dtm = np.where(df["open"] < df["open"].shift(1), 0,
                   np.where(df["high"] - df["open"] > df["open"] - df["open"].shift(1), df["high"] - df["open"],
                            df["open"] - df["open"].shift(1)))
    dbm = np.where(df["open"] >= df["open"].shift(1), 0,
                   np.where(df["open"] - df["low"] > df["open"] - df["open"].shift(1), df["open"] - df["low"],
                            df["open"] - df["open"].shift(1)))
    stm = pd.Series(dtm).rolling(n).sum()
    sbm = pd.Series(dbm).rolling(n).sum()
    new_df["adtm"] = np.where(stm > sbm, (stm - sbm) / stm, np.where(stm == sbm, 0, (stm - sbm) / sbm))
    new_df["adtmma"] = tafunc.ma(new_df["adtm"], m)
    return new_df


def B3612(df):
    """
    三减六日乖离率

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"b36", "b612", 分别代表收盘价的3日移动平均线与6日移动平均线的乖离值及收盘价的6日移动平均线与12日移动平均线的乖离值

    Example::

        # 获取 CFFEX.IF1903 合约的三减六日乖离率
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import B3612

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        b3612=B3612(klines)
        print(list(b3612["b36"]))
        print(list(b3612["b612"]))


        # 预计的输出是这样的:
        [..., 57.26666666667188, 44.00000000000546, -5.166666666660603, ...]
        [..., 99.28333333333285, 88.98333333333221, 69.64999999999918, ...]
    """
    new_df = pd.DataFrame()
    new_df["b36"] = tafunc.ma(df["close"], 3) - tafunc.ma(df["close"], 6)
    new_df["b612"] = tafunc.ma(df["close"], 6) - tafunc.ma(df["close"], 12)
    return new_df


def DBCD(df, n, m, t):
    """
    异同离差乖离率

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

        m (int): 参数m

        t (int): 参数t

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"dbcd", "mm", 分别代表离差值及其简单移动平均值

    Example::

        # 获取 CFFEX.IF1903 合约的异同离差乖离率
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import DBCD

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        dbcd=DBCD(klines, 5, 16, 76)
        print(list(dbcd["dbcd"]))
        print(list(dbcd["mm"]))


        # 预计的输出是这样的:
        [..., 0.0038539724453411045, 0.0034209659500908517, 0.0027130669520015094, ...]
        [..., 0.003998499673401192, 0.003864353204606074, 0.0035925052896395872, ...]
    """
    new_df = pd.DataFrame()
    bias = (df["close"] - tafunc.ma(df["close"], n)) / tafunc.ma(df["close"], n)
    dif = bias - bias.shift(m)
    new_df["dbcd"] = tafunc.sma(dif, t, 1)
    new_df["mm"] = tafunc.ma(new_df["dbcd"], 5)
    return new_df


def DDI(df, n, n1, m, m1):
    """
    方向标准离差指数

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

        n1 (int): 参数n1

        m (int): 参数m

        m1 (int): 周期m1

    Returns:
        pandas.DataFrame: 返回的DataFrame包含3列, 是"ddi", "addi", "ad", 分别代表DIZ与DIF的差值, DDI的加权平均, ADDI的简单移动平均

    Example::

        # 获取 CFFEX.IF1903 合约的方向标准离差指数
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import DDI

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        ddi = DDI(klines, 13, 30, 10, 5)
        print(list(ddi["ddi"]))
        print(list(ddi["addi"]))
        print(list(ddi["ad"]))


        # 预计的输出是这样的:
        [..., 0.6513560804899388, 0.6129178985672046, 0.40480202190395936, ...]
        [..., 0.6559570156346113, 0.6416106432788091, 0.5626744361538593, ...]
        [..., 0.6960565490556135, 0.6765004585407994, 0.6455063893920429, ...]
    """
    new_df = pd.DataFrame()
    tr = np.where(np.absolute(df["high"] - df["high"].shift(1)) > np.absolute(df["low"] - df["low"].shift(1)),
                  np.absolute(df["high"] - df["high"].shift(1)), np.absolute(df["low"] - df["low"].shift(1)))
    dmz = np.where((df["high"] + df["low"]) <= (df["high"].shift(1) + df["low"].shift(1)), 0, tr)
    dmf = np.where((df["high"] + df["low"]) >= (df["high"].shift(1) + df["low"].shift(1)), 0, tr)
    diz = pd.Series(dmz).rolling(n).sum() / (pd.Series(dmz).rolling(n).sum() + pd.Series(dmf).rolling(n).sum())
    dif = pd.Series(dmf).rolling(n).sum() / (pd.Series(dmf).rolling(n).sum() + pd.Series(dmz).rolling(n).sum())
    new_df["ddi"] = diz - dif
    new_df["addi"] = tafunc.sma(new_df["ddi"], n1, m)
    new_df["ad"] = tafunc.ma(new_df["addi"], m1)
    return new_df


def KD(df, n, m1, m2):
    """
    随机指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

        m1 (int): 参数m1

        m2 (int): 参数m2

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"k", "d", 分别代表计算出来的K值与D值

    Example::

        # 获取 CFFEX.IF1903 合约的随机指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import KD

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        kd = KD(klines, 9, 3, 3)
        print(list(kd["k"]))
        print(list(kd["d"]))


        # 预计的输出是这样的:
        [..., 84.60665654726242, 80.96145249909222, 57.54863147922147, ...]
        [..., 82.98108443995415, 82.30787379300017, 74.05479302174061, ...]
    """
    new_df = pd.DataFrame()
    hv = df["high"].rolling(n).max()
    lv = df["low"].rolling(n).min()
    rsv = pd.Series(np.where(hv == lv, 0, (df["close"] - lv) / (hv - lv) * 100))
    new_df["k"] = tafunc.sma(rsv, m1, 1)
    new_df["d"] = tafunc.sma(new_df["k"], m2, 1)
    return new_df


def LWR(df, n, m):
    """
    威廉指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

        m (int): 参数m

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"lwr", 代表计算出来的威廉指标

    Example::

        # 获取 CFFEX.IF1903 合约的威廉指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import LWR

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        lwr = LWR(klines, 9, 3)
        print(list(lwr["lwr"]))


        # 预计的输出是这样的:
        [..., -15.393343452737565, -19.03854750090778, -42.45136852077853, ...]
    """
    hv = df["high"].rolling(n).max()
    lv = df["low"].rolling(n).min()
    rsv = pd.Series(np.where(hv == lv, 0, (df["close"] - hv) / (hv - lv) * 100))
    new_df = pd.DataFrame(data=list(tafunc.sma(rsv, m, 1)), columns=["lwr"])
    return new_df


def MASS(df, n1, n2):
    """
    梅斯线

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n1 (int): 周期n1

        n2 (int): 周期n2

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"mass", 代表计算出来的梅斯线指标

    Example::

        # 获取 CFFEX.IF1903 合约的梅斯线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import MASS

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        mass = MASS(klines, 9, 25)
        print(list(mass["mass"]))


        # 预计的输出是这样的:
        [..., 27.478822053291733, 27.485710830466964, 27.561223922342652, ...]
    """
    ema1 = tafunc.ema(df["high"] - df["low"], n1)
    ema2 = tafunc.ema(ema1, n1)
    new_df = pd.DataFrame(data=list((ema1 / ema2).rolling(n2).sum()), columns=["mass"])
    return new_df


def MFI(df, n):
    """
    资金流量指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"mfi", 代表计算出来的MFI指标

    Example::

        # 获取 CFFEX.IF1903 合约的资金流量指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import MFI

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        mfi = MFI(klines, 14)
        print(list(mfi["mfi"]))


        # 预计的输出是这样的:
        [..., 73.47968487105688, 70.2250476611595, 62.950450871062266, ...]
    """
    typ = (df["high"] + df["low"] + df["close"]) / 3
    mr = pd.Series(np.where(typ > typ.shift(1), typ * df["volume"], 0)).rolling(n).sum() / pd.Series(
        np.where(typ < typ.shift(1), typ * df["volume"], 0)).rolling(n).sum()
    new_df = pd.DataFrame(data=list(100 - (100 / (1 + mr))), columns=["mfi"])
    return new_df


def MI(df, n):
    """
    动量指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 参数n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"a", "mi", 分别代表当日收盘价与N日前收盘价的差值以及MI值

    Example::

        # 获取 CFFEX.IF1903 合约的动量指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import MI

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        mi = MI(klines, 12)
        print(list(mi["a"]))
        print(list(mi["mi"]))


        # 预计的输出是这样的:
        [..., 399.1999999999998, 370.8000000000002, 223.5999999999999, ...]
        [..., 293.2089214076506, 299.67484462367975, 293.3352742383731, ...]
    """
    new_df = pd.DataFrame()
    new_df["a"] = df["close"] - df["close"].shift(n)
    new_df["mi"] = tafunc.sma(new_df["a"], n, 1)
    return new_df


def MICD(df, n, n1, n2):
    """
    异同离差动力指数

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 参数n

        n1 (int): 周期n1

        n2 (int): 周期n2

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"dif", "micd", 代表离差值和MICD指标

    Example::

        # 获取 CFFEX.IF1903 合约的异同离差动力指数
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import MICD

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        micd = MICD(klines, 3, 10, 20)
        print(list(micd["dif"]))
        print(list(micd["micd"]))


        # 预计的输出是这样的:
        [..., 6.801483500680234, 6.700989000453493, 6.527326000302342, ...]
        [..., 6.2736377238314684, 6.3163728514936714, 6.3374681663745385, ...]
    """
    new_df = pd.DataFrame()
    mi = df["close"] - df["close"].shift(1)
    ami = tafunc.sma(mi, n, 1)
    new_df["dif"] = tafunc.ma(ami.shift(1), n1) - tafunc.ma(ami.shift(1), n2)
    new_df["micd"] = tafunc.sma(new_df["dif"], 10, 1)
    return new_df


def MTM(df, n, n1):
    """
    MTM动力指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

        n1 (int): 周期n1

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"mtm", "mtmma", 分别代表MTM值和MTM的简单移动平均值

    Example::

        # 获取 CFFEX.IF1903 合约的动力指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import MTM

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        mtm = MTM(klines, 6, 6)
        print(list(mtm["mtm"]))
        print(list(mtm["mtmma"]))


        # 预计的输出是这样的:
        [..., 144.79999999999973, 123.60000000000036, -4.200000000000273, ...]
        [..., 198.5666666666667, 177.96666666666678, 139.30000000000004, ...]
    """
    new_df = pd.DataFrame()
    new_df["mtm"] = df["close"] - df["close"].shift(n)
    new_df["mtmma"] = tafunc.ma(new_df["mtm"], n1)
    return new_df


def PRICEOSC(df, long, short):
    """
    价格震荡指数 Price Oscillator

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        long (int): 长周期

        short (int): 短周期

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"priceosc", 代表计算出来的价格震荡指数

    Example::

        # 获取 CFFEX.IF1903 合约的价格震荡指数
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import PRICEOSC

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        priceosc = PRICEOSC(klines, 26, 12)
        print(list(priceosc["priceosc"]))


        # 预计的输出是这样的:
        [..., 5.730468338384374, 5.826866231225718, 5.776959240989803, ...]
    """
    ma_s = tafunc.ma(df["close"], short)
    ma_l = tafunc.ma(df["close"], long)
    new_df = pd.DataFrame(data=list((ma_s - ma_l) / ma_s * 100), columns=["priceosc"])
    return new_df


def PSY(df, n, m):
    """
    心理线

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

        m (int): 周期m

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"psy", "psyma", 分别代表心理线和心理线的简单移动平均

    Example::

        # 获取 CFFEX.IF1903 合约的心理线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import PSY

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        psy = PSY(klines, 12, 6)
        print(list(psy["psy"]))
        print(list(psy["psyma"]))


        # 预计的输出是这样的:
        [..., 58.333333333333336, 58.333333333333336, 50.0, ...]
        [..., 54.16666666666671, 54.16666666666671, 54.16666666666671, ...]
    """
    new_df = pd.DataFrame()
    new_df["psy"] = tafunc.count(df["close"] > df["close"].shift(1), n) / n * 100
    new_df["psyma"] = tafunc.ma(new_df["psy"], m)
    return new_df


def QHLSR(df):
    """
    阻力指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"qhl5", "qhl10", 分别代表计算出来的QHL5值和QHL10值

    Example::

        # 获取 CFFEX.IF1903 合约的阻力指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import QHLSR

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        ndf = QHLSR(klines)
        print(list(ndf["qhl5"]))
        print(list(ndf["qhl10"]))


        # 预计的输出是这样的:
        [..., 0.9512796890171819, 1.0, 0.8061319699743583, 0.36506038490240567, ...]
        [..., 0.8192641975527878, 0.7851545532504415, 0.5895613967067044, ...]
    """
    new_df = pd.DataFrame()
    qhl = (df["close"] - df["close"].shift(1)) - (df["volume"] - df["volume"].shift(1)) * (
            df["high"].shift(1) - df["low"].shift(1)) / df["volume"].shift(1)
    a = pd.Series(np.where(qhl > 0, qhl, 0)).rolling(5).sum()
    e = pd.Series(np.where(qhl > 0, qhl, 0)).rolling(10).sum()
    b = np.absolute(pd.Series(np.where(qhl < 0, qhl, 0)).rolling(5).sum())
    f = np.absolute(pd.Series(np.where(qhl < 0, qhl, 0)).rolling(10).sum())
    d = a / (a + b)
    g = e / (e + f)
    new_df["qhl5"] = np.where(pd.Series(np.where(qhl > 0, 1, 0)).rolling(5).sum() == 5, 1,
                              np.where(pd.Series(np.where(qhl < 0, 1, 0)).rolling(5).sum() == 5, 0, d))
    new_df["qhl10"] = g
    return new_df


def RC(df, n):
    """
    变化率指数

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 参数n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"arc", 代表计算出来的变化率指数

    Example::

        # 获取 CFFEX.IF1903 合约的变化率指数
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import RC

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        rc = RC(klines, 50)
        print(list(rc["arc"]))


        # 预计的输出是这样的:
        [..., 1.011782057069131, 1.0157160672001329, 1.019680175228899, ...]
    """
    rc = df["close"] / df["close"].shift(n)
    new_df = pd.DataFrame(data=list(tafunc.sma(rc.shift(1), n, 1)), columns=["arc"])
    return new_df


def RCCD(df, n, n1, n2):
    """
    异同离差变化率指数

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 参数n

        n1 (int): 周期n1

        n2 (int): 周期n2

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"dif", "rccd", 分别代表离差值和异同离差变化率指数

    Example::

        # 获取 CFFEX.IF1903 合约的异同离差变化率指数
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import RCCD

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        rccd = RCCD(klines, 10, 21, 28)
        print(list(rccd["dif"]))
        print(list(rccd["rccd"]))


        # 预计的输出是这样的:
        [..., 0.007700543190044096, 0.007914865667604465, 0.008297381119103608, ...]
        [..., 0.007454465277084111, 0.007500505316136147, 0.0075801928964328935, ...]
    """
    new_df = pd.DataFrame()
    rc = df["close"] / df["close"].shift(n)
    arc = tafunc.sma(rc.shift(1), n, 1)
    new_df["dif"] = tafunc.ma(arc.shift(1), n1) - tafunc.ma(arc.shift(1), n2)
    new_df["rccd"] = tafunc.sma(new_df["dif"], n, 1)
    return new_df


def ROC(df, n, m):
    """
    变动速率

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 参数n

        m (int): 周期m

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"roc", "rocma", 分别代表ROC值和ROC的简单移动平均值

    Example::

        # 获取 CFFEX.IF1903 合约的变动速率
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import ROC

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        roc = ROC(klines, 24, 20)
        print(list(roc["roc"]))
        print(list(roc["rocma"]))


        # 预计的输出是这样的:
        [..., 21.389800555415288, 19.285937989351712, 15.183443085606768, ...]
        [..., 14.597071588550435, 15.223202630466648, 15.537530180238516, ...]
    """
    new_df = pd.DataFrame()
    new_df["roc"] = (df["close"] - df['close'].shift(n)) / df["close"].shift(n) * 100
    new_df["rocma"] = tafunc.ma(new_df["roc"], m)
    return new_df


def SLOWKD(df, n, m1, m2, m3):
    """
    慢速KD

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 周期n

        m1 (int): 参数m1

        m2 (int): 参数m2

        m3 (int): 参数m3

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"k", "d", 分别代表K值和D值

    Example::

        # 获取 CFFEX.IF1903 合约的慢速KD
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import SLOWKD

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        slowkd = SLOWKD(klines, 9, 3, 3, 3)
        print(list(slowkd["k"]))
        print(list(slowkd["d"]))


        # 预计的输出是这样的:
        [..., 82.98108443995415, 82.30787379300017, 74.05479302174061, ...]
        [..., 83.416060393041, 83.04666485969405, 80.0493742470429, ...]
    """
    new_df = pd.DataFrame()
    rsv = (df["close"] - df["low"].rolling(n).min()) / \
          (df["high"].rolling(n).max() - df["low"].rolling(n).min()) * 100
    fastk = tafunc.sma(rsv, m1, 1)
    new_df["k"] = tafunc.sma(fastk, m2, 1)
    new_df["d"] = tafunc.sma(new_df["k"], m3, 1)
    return new_df


def SRDM(df, n):
    """
    动向速度比率

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 参数n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"srdm", "asrdm", 分别代表计算出来的SRDM值和SRDM值的加权移动平均值

    Example::

        # 获取 CFFEX.IF1903 合约的动向速度比率
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import SRDM

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        srdm = SRDM(klines, 30)
        print(list(srdm["srdm"]))
        print(list(srdm["asrdm"]))


        # 预计的输出是这样的:
        [..., 0.7865067466266866, 0.7570567713288928, 0.5528619528619526, ...]
        [..., 0.45441550541510667, 0.4645035476122329, 0.4674488277872236, ...]
    """
    new_df = pd.DataFrame()
    dmz = np.where((df["high"] + df["low"]) <= (df["high"].shift(1) + df["low"].shift(1)), 0,
                   np.where(np.absolute(df["high"] - df["high"].shift(1)) > np.absolute(df["low"] - df["low"].shift(1)),
                            np.absolute(df["high"] - df["high"].shift(1)), np.absolute(df["low"] - df["low"].shift(1))))
    dmf = np.where((df["high"] + df["low"]) >= (df["high"].shift(1) + df["low"].shift(1)), 0,
                   np.where(np.absolute(df["high"] - df["high"].shift(1)) > np.absolute(df["low"] - df["low"].shift(1)),
                            np.absolute(df["high"] - df["high"].shift(1)), np.absolute(df["low"] - df["low"].shift(1))))
    admz = tafunc.ma(pd.Series(dmz), 10)
    admf = tafunc.ma(pd.Series(dmf), 10)
    new_df["srdm"] = np.where(admz > admf, (admz - admf) / admz, np.where(admz == admf, 0, (admz - admf) / admf))
    new_df["asrdm"] = tafunc.sma(new_df["srdm"], n, 1)
    return new_df


def SRMI(df, n):
    """
    MI修正指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 参数n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"a", "mi", 分别代表A值和MI值

    Example::

        # 获取 CFFEX.IF1903 合约的MI修正指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import SRMI

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        srmi = SRMI(klines, 9)
        print(list(srmi["a"]))
        print(list(srmi["mi"]))


        # 预计的输出是这样的:
        [..., 0.10362397961836425, 0.07062591892459567, -0.03341929372138309, ...]
        [..., 0.07583104758041452, 0.0752526999519902, 0.06317803398828206, ...]
    """
    new_df = pd.DataFrame()
    new_df["a"] = np.where(df["close"] < df["close"].shift(n),
                           (df["close"] - df["close"].shift(n)) / df["close"].shift(n),
                           np.where(df["close"] == df["close"].shift(n), 0,
                                    (df["close"] - df["close"].shift(n)) / df["close"]))
    new_df["mi"] = tafunc.sma(new_df["a"], n, 1)
    return new_df


def ZDZB(df, n1, n2, n3):
    """
    筑底指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n1 (int): 周期n1

        n2 (int): 周期n2

        n3 (int): 周期n3

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"b", "d", 分别代表A值的n2周期简单移动平均和A值的n3周期简单移动平均

    Example::

        # 获取 CFFEX.IF1903 合约的筑底指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import ZDZB

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        zdzb = ZDZB(klines, 50, 5, 20)
        print(list(zdzb["b"]))
        print(list(zdzb["d"]))


        # 预计的输出是这样的:
        [..., 1.119565217391305, 1.1376811594202905, 1.155797101449276, ...]
        [..., 1.0722350515828771, 1.091644989471076, 1.1077480490523965, ...]
    """
    new_df = pd.DataFrame()
    a = pd.Series(np.where(df["close"] >= df["close"].shift(1), 1, 0)).rolling(n1).sum() / pd.Series(
        np.where(df["close"] < df["close"].shift(1), 1, 0)).rolling(n1).sum()
    new_df["b"] = tafunc.ma(a, n2)
    new_df["d"] = tafunc.ma(a, n3)
    return new_df


def DPO(df):
    """
    区间震荡线

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"dpo", 代表计算出来的DPO指标

    Example::

        # 获取 CFFEX.IF1903 合约的区间震荡线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import DPO

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        dpo = DPO(klines)
        print(list(dpo["dpo"]))


        # 预计的输出是这样的:
        [..., 595.4100000000021, 541.8300000000017, 389.7200000000016, ...]
    """
    dpo = df["close"] - (tafunc.ma(df["close"], 20)).shift(11)
    new_df = pd.DataFrame(data=list(dpo), columns=["dpo"])
    return new_df


def LON(df):
    """
    长线指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"lon", "ma1", 分别代表长线指标和长线指标的10周期简单移动平均值

    Example::

        # 获取 CFFEX.IF1903 合约的长线指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import LON

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        lon = LON(klines)
        print(list(lon["lon"]))
        print(list(lon["ma1"]))


        # 预计的输出是这样的:
        [..., 6.419941948913239, 6.725451135494827, 6.483546043406369, ...]
        [..., 4.366625464410439, 4.791685949556344, 5.149808865745246, ...]
    """
    new_df = pd.DataFrame()
    tb = np.where(df["high"] > df["close"].shift(1),
                  df["high"] - df["close"].shift(1) + df["close"] - df["low"],
                  df["close"] - df["low"])
    ts = np.where(df["close"].shift(1) > df["low"],
                  df["close"].shift(1) - df["low"] + df["high"] - df["close"],
                  df["high"] - df["close"])

    vol1 = (tb - ts) * df["volume"] / (tb + ts) / 10000
    vol10 = vol1.ewm(alpha=0.1, adjust=False).mean()  # DMA 动态均值
    vol11 = vol1.ewm(alpha=0.05, adjust=False).mean()  # DMA
    res1 = vol10 - vol11
    new_df["lon"] = res1.cumsum()
    new_df["ma1"] = tafunc.ma(new_df["lon"], 10)
    return new_df


def SHORT(df):
    """
    短线指标

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"short", "ma1", 分别代表短线指标和短线指标的10周期简单移动平均值

    Example::

        # 获取 CFFEX.IF1903 合约的短线指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import SHORT

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        short = SHORT(klines)
        print(list(short["short"]))
        print(list(short["ma1"]))


        # 预计的输出是这样的:
        [..., 0.6650139934614072, 0.3055091865815881, -0.24190509208845834, ...]
        [..., 0.41123378999608917, 0.42506048514590444, 0.35812291618890224, ...]
    """
    new_df = pd.DataFrame()
    tb = np.where(df["high"] > df["close"].shift(1),
                  df["high"] - df["close"].shift(1) + df["close"] - df["low"],
                  df["close"] - df["low"])
    ts = np.where(df["close"].shift(1) > df["low"],
                  df["close"].shift(1) - df["low"] + df["high"] - df["close"],
                  df["high"] - df["close"])
    vol1 = (tb - ts) * df["volume"] / (tb + ts) / 10000
    vol10 = vol1.ewm(alpha=0.1, adjust=False).mean()  # DMA 动态均值
    vol11 = vol1.ewm(alpha=0.05, adjust=False).mean()  # DMA
    new_df["short"] = vol10 - vol11
    new_df["ma1"] = tafunc.ma(new_df["short"], 10)
    return new_df


def MV(df, n, m):
    """
    均量线

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 参数n

        m (int): 参数m

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"mv1", "mv2", 分别代表均量线1和均量线2

    Example::

        # 获取 CFFEX.IF1903 合约的均量线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import MV

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        mv = MV(klines, 10, 20)
        print(list(mv["mv1"]))
        print(list(mv["mv2"]))


        # 预计的输出是这样的:
        [..., 69851.39419881169, 72453.75477893051, 75423.57930103746, ...]
        [..., 49044.75870654942, 51386.27077122195, 53924.557232660845, ...]
    """
    new_df = pd.DataFrame()
    new_df["mv1"] = tafunc.sma(df["volume"], n, 1)
    new_df["mv2"] = tafunc.sma(df["volume"], m, 1)
    return new_df


def WAD(df, n, m):
    """
    威廉多空力度线

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 参数n

        m (int): 参数m

    Returns:
        pandas.DataFrame: 返回的DataFrame包含3列, 是"a", "b", "e", 分别代表A/D值,A/D值n周期的以1为权重的移动平均, A/D值m周期的以1为权重的移动平均

    Example::

        # 获取 CFFEX.IF1903 合约的威廉多空力度线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import WAD

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        wad = WAD(klines, 10, 30)
        print(list(wad["a"]))
        print(list(wad["b"]))
        print(list(wad["e"]))


        # 预计的输出是这样的:
        [..., 90.0, 134.79999999999973, 270.4000000000001, ...]
        [..., 344.4265821851701, 323.46392396665306, 318.1575315699878, ...]
        [..., 498.75825781872277, 486.626315891432, 479.41877202838424, ...]
    """
    new_df = pd.DataFrame()
    new_df["a"] = np.absolute(np.where(df["close"] > df["close"].shift(1),
                                       df["close"] - np.where(df["close"].shift(1) < df["low"], df["close"].shift(1),
                                                              df["low"]),
                                       np.where(df["close"] < df["close"].shift(1), df["close"] - np.where(
                                           df["close"].shift(1) > df["high"], df["close"].shift(1), df["high"]),
                                                0)).cumsum())
    new_df["b"] = tafunc.sma(new_df["a"], n, 1)
    new_df["e"] = tafunc.sma(new_df["a"], m, 1)
    return new_df


def AD(df):
    """
    累积/派发指标 Accumulation/Distribution

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"ad", 代表计算出来的累积/派发指标

    Example::

        # 获取 CFFEX.IF1903 合约的累积/派发指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import AD

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        ad = AD(klines)
        print(list(ad["ad"]))


        # 预计的输出是这样的:
        [..., 146240.57181105542, 132822.950945916, 49768.15024044845, ...]
    """
    ad = (((df["close"] - df["low"]) - (df["high"] - df["close"])) / (df["high"] - df["low"]) * df[
        "volume"]).cumsum()
    new_df = pd.DataFrame(data=list(ad), columns=["ad"])
    return new_df


def CCL(df):
    """
    持仓异动

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"ccl", 代表计算出来的持仓异动指标

    Example::

        # 获取 CFFEX.IF1903 合约的持仓异动指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import CCL

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        ccl = CCL(klines)
        print(list(ccl["ccl"]))


        # 预计的输出是这样的:
        [..., '多头增仓', '多头减仓', '空头增仓', ...]
    """
    ccl = np.where(df["close"] > df["close"].shift(1),
                   np.where(df["close_oi"] > df["close_oi"].shift(1), "多头增仓", "空头减仓"),
                   np.where(df["close_oi"] > df["close_oi"].shift(1), "空头增仓", "多头减仓"))
    # color = np.where(df["close"] > df["close"].shift(1), "红", "绿")  # 1表示红色, 0表示绿色
    # position = np.where(df["close_oi"] > df["close_oi"].shift(1), "上", "下")  # 1表示零轴之上, 0表示零轴之下
    new_df = pd.DataFrame(data=list(ccl), columns=["ccl"])
    return new_df


def CJL(df):
    """
    成交量

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

    Returns:
        pandas.DataFrame: 返回的DataFrame包含2列, 是"vol", "opid", 分别代表成交量和持仓量

    Example::

        # 获取 CFFEX.IF1903 合约的成交量
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import CJL

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        ndf = CJL(klines)
        print(list(ndf["vol"]))
        print(list(ndf["opid"]))


        # 预计的输出是这样的:
        [..., 93142, 95875, 102152, ...]
        [..., 69213, 66414, 68379, ...]
    """
    new_df = pd.DataFrame()
    new_df["vol"] = df["volume"]  # 成交量
    new_df["opid"] = df["close_oi"]  # 持仓量
    return new_df


def OPI(df):
    """
    持仓量

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"opi", 代表持仓量

    Example::

        # 获取 CFFEX.IF1903 合约的持仓量
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import OPI

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        opi = OPI(klines)
        print(list(opi["opi"]))


        # 预计的输出是这样的:
        [..., 69213, 66414, 68379, ...]
    """
    opi = df["close_oi"]
    new_df = pd.DataFrame(data=list(opi), columns=["opi"])
    return new_df


def PVT(df):
    """
    价量趋势指数

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"pvt", 代表计算出来的价量趋势指数

    Example::

        # 获取 CFFEX.IF1903 合约的价量趋势指数
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import PVT

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        pvt = PVT(klines)
        print(list(pvt["pvt"]))


        # 预计的输出是这样的:
        [..., 13834.536889431965, 12892.3866788564, 9255.595248484618, ...]
    """
    pvt = ((df["close"] - df["close"].shift(1)) / df["close"].shift(1) * df["volume"]).cumsum()
    new_df = pd.DataFrame(data=list(pvt), columns=["pvt"])
    return new_df


def VOSC(df, short, long):
    """
    移动平均成交量指标 Volume Oscillator

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        short (int): 短周期

        long (int): 长周期

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"vosc", 代表计算出来的移动平均成交量指标

    Example::

        # 获取 CFFEX.IF1903 合约的移动平均成交量指标
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import VOSC

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        vosc = VOSC(klines, 12, 26)
        print(list(vosc["vosc"]))


        # 预计的输出是这样的:
        [..., 38.72537848731668, 36.61748077024136, 35.4059127302802, ...]
    """
    vosc = (tafunc.ma(df["volume"], short) - tafunc.ma(df["volume"], long)) / tafunc.ma(df["volume"], short) * 100
    new_df = pd.DataFrame(data=list(vosc), columns=["vosc"])
    return new_df


def VROC(df, n):
    """
    量变动速率

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 参数n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"vroc", 代表计算出来的量变动速率

    Example::

        # 获取 CFFEX.IF1903 合约的量变动速率
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import VROC

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        vroc = VROC(klines, 12)
        print(list(vroc["vroc"]))


        # 预计的输出是这样的:
        [..., 41.69905854184833, 74.03274443327598, 3.549394666873177, ...]
    """
    vroc = (df["volume"] - df["volume"].shift(n)) / df["volume"].shift(n) * 100
    new_df = pd.DataFrame(data=list(vroc), columns=["vroc"])
    return new_df


def VRSI(df, n):
    """
    量相对强弱

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 参数n

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"vrsi", 代表计算出来的量相对强弱指标

    Example::

        # 获取 CFFEX.IF1903 合约的量相对强弱
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import VRSI

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        vrsi = VRSI(klines, 6)
        print(list(vrsi["vrsi"]))


        # 预计的输出是这样的:
        [..., 59.46573277427041, 63.3447660581749, 45.21081537920358, ...]
    """
    vrsi = tafunc.sma(
        pd.Series(np.where(df["volume"] - df["volume"].shift(1) > 0, df["volume"] - df["volume"].shift(1), 0)), n,
        1) / tafunc.sma(np.absolute(df["volume"] - df["volume"].shift(1)), n, 1) * 100
    new_df = pd.DataFrame(data=list(vrsi), columns=["vrsi"])
    return new_df


def WVAD(df):
    """
    威廉变异离散量

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"wvad", 代表计算出来的威廉变异离散量

    Example::

        # 获取 CFFEX.IF1903 合约的威廉变异离散量
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import WVAD

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        wvad = WVAD(klines)
        print(list(wvad["wvad"]))


        # 预计的输出是这样的:
        [..., -32690.203562340674, -42157.968253968385, 32048.182305630264, ...]
    """
    wvad = (df["close"] - df["open"]) / (df["high"] - df["low"]) * df["volume"]
    new_df = pd.DataFrame(data=list(wvad), columns=["wvad"])
    return new_df


def MA(df, n):
    """
    简单移动平均线

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 简单移动平均线的周期

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"ma", 代表计算出来的简单移动平均线

    Example::

        # 获取 CFFEX.IF1903 合约的简单移动平均线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import MA

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        ma = MA(klines, 30)
        print(list(ma["ma"]))


        # 预计的输出是这样的:
        [..., 3436.300000000001, 3452.8733333333344, 3470.5066666666676, ...]
    """
    new_df = pd.DataFrame(data=list(tafunc.ma(df["close"], n)), columns=["ma"])
    return new_df


def SMA(df, n, m):
    """
    扩展指数加权移动平均

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 扩展指数加权移动平均的周期

        m (int): 扩展指数加权移动平均的权重

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"sma", 代表计算出来的扩展指数加权移动平均线

    Example::

        # 获取 CFFEX.IF1903 合约的扩展指数加权移动平均线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import SMA

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        sma = SMA(klines, 5, 2)
        print(list(sma["sma"]))


        # 预计的输出是这样的:
        [..., 3803.9478653510914, 3751.648719210655, 3739.389231526393, ...]
    """
    new_df = pd.DataFrame(data=list(tafunc.sma(df["close"], n, m)), columns=["sma"])
    return new_df


def EMA(df, n):
    """
    指数加权移动平均线

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 指数加权移动平均线的周期

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"ema", 代表计算出来的指数加权移动平均线

    Example::

        # 获取 CFFEX.IF1903 合约的指数加权移动平均线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import EMA

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        ema = EMA(klines, 10)
        print(list(ema["ema"]))


        # 预计的输出是这样的:
        [..., 3723.1470497119317, 3714.065767946126, 3715.3265374104667, ...]
    """
    new_df = pd.DataFrame(data=list(tafunc.ema(df["close"], n)), columns=["ema"])
    return new_df


def EMA2(df, n):
    """
    线性加权移动平均 WMA

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 线性加权移动平均的周期

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"ema2", 代表计算出来的线性加权移动平均线

    Example::

        # 获取 CFFEX.IF1903 合约的线性加权移动平均线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import EMA2

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        ema2 = EMA2(klines, 10)
        print(list(ema2["ema2"]))


        # 预计的输出是这样的:
        [..., 3775.832727272727, 3763.334545454546, 3757.101818181818, ...]
    """
    new_df = pd.DataFrame(data=list(tafunc.ema2(df["close"], n)), columns=["ema2"])
    return new_df


def TRMA(df, n):
    """
    三角移动平均线

    Args:
        df (pandas.DataFrame): Dataframe格式的K线序列

        n (int): 三角移动平均线的周期

    Returns:
        pandas.DataFrame: 返回的DataFrame包含1列, 是"trma", 代表计算出来的三角移动平均线

    Example::

        # 获取 CFFEX.IF1903 合约的三角移动平均线
        from tqsdk import TqApi, TqSim
        from tqsdk.ta import TRMA

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1903", 24 * 60 * 60)
        trma = TRMA(klines, 10)
        print(list(trma["trma"]))

        # 预计的输出是这样的:
        [..., 341.366666666669, 3759.160000000002, 3767.7533333333354, ...]
    """
    new_df = pd.DataFrame(data=list(tafunc.trma(df["close"], n)), columns=["trma"])
    return new_df


def BS_VALUE(df, quote=None, r=0.025, v=None):
    """
    期权 BS 模型理论价格

    Args:
        df (pandas.DataFrame): 需要计算理论价的期权对应标的合约的 K 线序列，Dataframe 格式

        quote (tqsdk.objs.Quote): 需要计算理论价的期权对象，如果不是期权类型的对象或者该期权对应的标的合约 df 序列中合约，则返回序列值全为 nan

        r (float): 无风险利率

        v (float | pandas.Series): 波动率，默认使用 df 中的 close 序列计算波动率

    Returns:
        pandas.DataFrame: 返回的 DataFrame 包含 1 列, 是 "bs_price", 代表计算出来的期权理论价格, 与参数 df 行数相同

    Example1::

        from tqsdk import TqApi
        from tqsdk.ta import OPTION_BS_PRICE

        api = TqApi()
        quote = api.get_quote("SHFE.cu2006C43000")
        klines = api.get_kline_serial("SHFE.cu2006", 24 * 60 * 60, 30)
        bs_serise = BS_VALUE(klines, quote, 0.025)
        print(list(bs_serise["bs_price"]))
        api.close()

        # 预计的输出是这样的:
        [..., 3036.698780158862, 2393.333388624822, 2872.607833620801]


    Example2::

        from tqsdk import TqApi
        from tqsdk.ta import OPTION_BS_PRICE
        from tqsdk.tafunc import get_his_volatility

        api = TqApi()
        ks = api.get_kline_serial("SHFE.cu2006", 24 * 60 * 60, 30)
        v = get_his_volatility(ks, api.get_quote("SHFE.cu2006"))
        print("历史波动率:", v)

        quote = api.get_quote("SHFE.cu2006C43000")
        bs_serise = BS_VALUE(ks, quote, 0.025, v)
        print(list(bs_serise["bs_price"]))
        api.close()

        # 预计的输出是这样的:
        [..., 3036.698780158862, 2393.333388624822, 2872.607833620801]
    """
    if not (quote and quote.ins_class.endswith("OPTION") and quote.underlying_symbol == df["symbol"][0]):
        return pd.DataFrame(df.where(df["close"] < 0), columns=["bs_price"])
    if v is None:
        v = tafunc._get_volatility(df["close"], df["duration"], quote.trading_time, float('nan'))
        if math.isnan(v):
            return pd.DataFrame(df.where(df["close"] < 0), columns=["bs_price"])
    o = 1 if quote.option_class == "CALL" else -1
    t = tafunc._get_t_series(df["datetime"], df["duration"], quote)
    return pd.DataFrame(data=list(tafunc.get_bs_price(df["close"], quote.strike_price, r, v, t, o)),
                        columns=["bs_price"])


def OPTION_GREEKS(df, quote=None, r=0.025, v=None):
    """
    期权希腊指标

    Args:
        df (pandas.DataFrame): 期权合约及对应标的合约组成的 K 线序列, Dataframe 格式

        quote (tqsdk.objs.Quote): 期权对象，如果不是期权类型的对象或者与 df 中期权合约不同，则返回序列值全为 nan

        r (float): 无风险利率

        v (float | pandas.Series): 波动率, 默认使用隐含波动率

    Returns:
        pandas.DataFrame: 返回的 DataFrame 包含 5 列, 分别是 "delta", "theta", "gamma", "vega", "rho", 与参数 df 行数相同

    Example::

        from tqsdk import TqApi
        from tqsdk.ta import OPTION_GREEKS

        api = TqApi()
        quote = api.get_quote("SHFE.cu2006C44000")
        klines = api.get_kline_serial(["SHFE.cu2006C44000", "SHFE.cu2006"], 24 * 60 * 60, 30)
        greeks = OPTION_GREEKS(klines, quote, 0.025)
        print(list(greeks["delta"]))
        print(list(greeks["theta"]))
        print(list(greeks["gamma"]))
        print(list(greeks["vega"]))
        print(list(greeks["rho"]))

    """
    if not (quote and quote.ins_class.endswith("OPTION") and quote.instrument_id == df["symbol"][0]
            and quote.underlying_symbol == df["symbol1"][0]):
        return pd.DataFrame(df.where(df["close1"] < 0), columns=["delta", "theta", "gamma", "vega", "rho"])
    o = 1 if quote.option_class == "CALL" else -1
    t = tafunc._get_t_series(df["datetime"], df["duration"], quote)  # 到期时间
    if v is None:
        his_v = tafunc._get_volatility(df["close1"], df["duration"], quote.trading_time, 0.3)
        v = tafunc.get_impv(df["close1"], df["close"], quote.strike_price, r, his_v, t, o)
    d1 = tafunc._get_d1(df["close1"], quote.strike_price, r, v, t)
    new_df = pd.DataFrame()
    new_df["delta"] = tafunc.get_delta(df["close1"], quote.strike_price, r, v, t, o, d1)
    new_df["theta"] = tafunc.get_theta(df["close1"], quote.strike_price, r, v, t, o, d1)
    new_df["gamma"] = tafunc.get_gamma(df["close1"], quote.strike_price, r, v, t, d1)
    new_df["vega"] = tafunc.get_vega(df["close1"], quote.strike_price, r, v, t, d1)
    new_df["rho"] = tafunc.get_rho(df["close1"], quote.strike_price, r, v, t, o, d1)
    return new_df


def OPTION_VALUE(df, quote=None):
    """
    期权内在价值，时间价值

    Args:
        df (pandas.DataFrame): 期权合约及对应标的合约组成的 K 线序列, Dataframe 格式

        quote (tqsdk.objs.Quote): 期权对象，如果不是期权类型的对象或者与 df 中期权合约不同，则返回序列值全为 nan

    Returns:
        pandas.DataFrame: 返回的 DataFrame 包含 2 列, 是 "intrins" 和 "time", 代表内在价值和时间价值, 与参数 df 行数相同

    Example::

        from tqsdk import TqApi
        from tqsdk.ta import OPTION_VALUE

        api = TqApi()
        quote = api.get_quote("SHFE.cu2006C43000")
        klines = api.get_kline_serial(["SHFE.cu2006C43000", "SHFE.cu2006"], 24 * 60 * 60, 30)
        values = OPTION_VALUE(klines, quote)
        print(list(values["intrins"]))
        print(list(values["time"]))
        api.close()
    """
    if not (quote and quote.ins_class.endswith("OPTION") and quote.instrument_id == df["symbol"][0]
            and quote.underlying_symbol == df["symbol1"][0]):
        return pd.DataFrame(df.where(df["close1"] < 0), columns=["intrins", "time"])
    o = 1 if quote.option_class == "CALL" else -1
    new_df = pd.DataFrame()
    intrins = o * (df["close1"] - quote.strike_price)
    new_df["intrins"] = pd.Series(np.where(intrins > 0.0, intrins, 0.0))
    new_df["time"] = pd.Series(df["close"] - new_df["intrins"])
    return new_df


def OPTION_IMPV(df, quote=None, r=0.025, init_v=None):
    """
    计算期权隐含波动率

    Args:
        df (pandas.DataFrame): 期权合约及对应标的合约组成的 K 线序列, Dataframe 格式

        quote (tqsdk.objs.Quote): 期权对象，如果不是期权类型的对象或者与 df 中期权合约不同，则返回序列值全为 nan

        r (float): 无风险利率

        init_v (float): 初始对波动率的估计

    Returns:
        pandas.DataFrame: 返回的 DataFrame 包含 1 列, 是 "impv", 与参数 df 行数相同

    Example::

        from tqsdk import TqApi
        from tqsdk.ta import OPTION_IMPV

        api = TqApi()
        quote = api.get_quote("SHFE.cu2006C50000")
        klines = api.get_kline_serial(["SHFE.cu2006C50000", "SHFE.cu2006"], 24 * 60 * 60, 20)
        impv = OPTION_IMPV(klines, quote, 0.025)
        print(list(impv["impv"] * 100))
    """
    if not (quote and quote.ins_class.endswith("OPTION") and quote.instrument_id == df["symbol"][0]
            and quote.underlying_symbol == df["symbol1"][0]):
        return pd.DataFrame(df.where(df["close1"] < 0), columns=["impv"])
    if init_v is None:
        init_v = tafunc._get_volatility(df["close1"], df["duration"], quote.trading_time, 0.3)
    o = 1 if quote.option_class == "CALL" else -1
    t = tafunc._get_t_series(df["datetime"], df["duration"], quote)  # 到期时间
    return pd.DataFrame(
        data=list(tafunc.get_impv(df["close1"], df["close"], quote.strike_price, r, init_v, t, o)),
        columns=["impv"])
