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
    """平均真实波幅"""
    pre_close = df["close"].shift(1)
    df["tr"] = np.where(df["high"] - df["low"] > np.absolute(pre_close - df["high"]),
                        np.where(df["high"] - df["low"] > np.absolute(pre_close - df["low"]), df["high"] - df["low"],
                                 np.absolute(pre_close - df["low"])),
                        np.where(np.absolute(pre_close - df["high"]) > np.absolute(pre_close - df["low"]),
                                 np.absolute(pre_close - df["high"]), np.absolute(pre_close - df["low"])))
    df["atr"] = MA(df["tr"], n)["ma"]
    return df


def BIAS(df, n1, n2, n3):
    """乖离率"""
    ma1 = MA(df["close"], n1)["ma"]
    ma2 = MA(df["close"], n2)["ma"]
    ma3 = MA(df["close"], n3)["ma"]
    df["bias1"] = (df["close"] - ma1) / ma1 * 100
    df["bias2"] = (df["close"] - ma2) / ma2 * 100
    df["bias3"] = (df["close"] - ma3) / ma3 * 100
    return df


def BOLL(df, n, p):
    """布林线"""
    mid = MA(df["close"], n)["ma"]
    std = df["close"].rolling(n).std()
    df["mid"] = mid
    df["top"] = mid + p * std
    df["bottom"] = mid - p * std
    return df


def DMI(df, n, m):
    """动向指标"""
    df = ATR(df, n)
    pre_high = df["high"].shift(1)
    pre_low = df["low"].shift(1)
    hd = df["high"] - pre_high
    ld = pre_low - df["low"]
    admp = MA(pd.Series(np.where((hd > 0) & (hd > ld), hd, 0)), n)["ma"]
    admm = MA(pd.Series(np.where((ld > 0) & (ld > hd), ld, 0)), n)["ma"]
    df["pdi"] = pd.Series(np.where(df["atr"] > 0, admp / df["atr"] * 100, np.NaN)).ffill()
    df["mdi"] = pd.Series(np.where(df["atr"] > 0, admm / df["atr"] * 100, np.NaN)).ffill()
    ad = pd.Series(np.absolute(df["mdi"] - df["pdi"]) / (df["mdi"] + df["pdi"]) * 100)
    df["adx"] = MA(ad, m)["ma"]
    df["adxr"] = (df["adx"] + df["adx"].shift(m)) / 2
    return df


def KDJ(df, n, m1, m2):
    """随机指标"""
    hv = df["high"].rolling(n).max()
    lv = df["low"].rolling(n).min()
    rsv = pd.Series(np.where(hv == lv, 0, (df["close"] - lv) / (hv - lv) * 100))
    df["k"] = SMA(rsv, m1, 1)["sma"]  # SMA
    df["d"] = SMA(df["k"], m2, 1)["sma"]  # SMA
    df["j"] = 3 * df["k"] - 2 * df["d"]
    return df


def MACD(df, short, long, m):
    """异同移动平均线"""
    eshort = EMA(df["close"], short)["ema"]  # EMA
    elong = EMA(df["close"], long)["ema"]  # EMA
    df["diff"] = eshort - elong
    df["dea"] = EMA(df["diff"], m)["ema"]  # EMA
    df["bar"] = 2 * (df["diff"] - df["dea"])
    return df


@numba.njit
def _sar(open, high, low, close, range_high, range_low, n, step, maximum):
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
    """抛物转向"""
    range_high = df["high"].rolling(n - 1).max()
    range_low = df["low"].rolling(n - 1).min()
    df["sar"] = _sar(df["open"].values, df["high"].values, df["low"].values, df["close"].values, range_high.values,
                     range_low.values, n, step, max)
    return df


def WR(df, n):
    """威廉指标"""
    hn = df["high"].rolling(n).max()
    ln = df["low"].rolling(n).min()
    df["wr"] = (hn - df["close"]) / (hn - ln) * (-100)
    return df


def RSI(df, n1, n2):
    """相对强弱指标"""
    lc = df["close"].shift(1)  # 前一日的收盘价
    df["rsi1"] = SMA(pd.Series(np.where(df["close"] - lc > 0, df["close"] - lc, 0)), n1, 1)["sma"] / \
                 SMA(np.absolute(df["close"] - lc), n1, 1)["sma"] * 100
    df["rsi2"] = SMA(pd.Series(np.where(df["close"] - lc > 0, df["close"] - lc, 0)), n2, 1)["sma"] / \
                 SMA(np.absolute(df["close"] - lc), n2, 1)["sma"] * 100
    return df


def ASI(df):
    """振动升降指标"""
    lc = df["close"].shift(1)  # 上一交易日的收盘价
    aa = np.absolute(df["high"] - lc)
    bb = np.absolute(df["low"] - lc)
    cc = np.absolute(df["high"] - df["low"].shift(1))
    dd = np.absolute(lc - df["open"].shift(1))
    r = np.where((aa > bb) & (aa > cc), aa + bb / 2 + dd / 4,
                 np.where((bb > cc) & (bb > aa), bb + aa / 2 + dd / 4, cc + dd / 4))
    x = df["close"] - lc + (df["close"] - df["open"]) / 2 + lc - df["open"].shift(1)
    si = np.where(r == 0, 0, 16 * x / r * np.where(aa > bb, aa, bb))
    df["asi"] = pd.Series(si).cumsum()
    return df


def VR(df, n):
    """VR 容量比率"""
    lc = df["close"].shift(1)  # 上一交易日的收盘价
    df["vr"] = pd.DataFrame(np.where(df["close"] > lc, df["volume"], 0)).rolling(n).sum() / pd.DataFrame(
        np.where(df["close"] <= lc, df["volume"], 0)).rolling(n).sum() * 100
    return df


def ARBR(df, n):
    """人气意愿指标"""
    df["ar"] = (df["high"] - df["open"]).rolling(n).sum() / (df["open"] - df["low"]).rolling(n).sum() * 100
    df["br"] = pd.Series(np.where(df["high"] - df["close"].shift(1) > 0, df["high"] - df["close"].shift(1), 0)).rolling(
        n).sum() / pd.Series(
        np.where(df["close"].shift(1) - df["low"] > 0, df["close"].shift(1) - df["low"], 0)).rolling(n).sum() * 100
    return df


def DMA(df, short, long, m):
    """平均线差"""
    df["ddd"] = MA(df["close"], short)["ma"] - MA(df["close"], long)["ma"]
    df["ama"] = MA(df["ddd"], m)["ma"]
    return df


def EXPMA(df, p1, p2, p3, p4):
    """指数加权移动平均线组合"""
    df["ma1"] = EMA(df["close"], p1)["ema"]  # EMA
    df["ma2"] = EMA(df["close"], p2)["ema"]
    df["ma3"] = EMA(df["close"], p3)["ema"]
    df["ma4"] = EMA(df["close"], p4)["ema"]
    return df


def CR(df, n, m1, m2, m3, m4):
    """CR能量"""
    mid = (df["high"] + df["low"] + df["close"]) / 3
    df["cr"] = pd.Series(np.where(0 > df["high"] - mid.shift(1), 0, df["high"] - mid.shift(1))).rolling(
        n).sum() / pd.Series(np.where(0 > mid.shift(1) - df["low"], 0, mid.shift(1) - df["low"])).rolling(n).sum() * 100
    df["crma1"] = MA(df["cr"], m1)["ma"].shift(int(m1 / 2.5 + 1))
    df["crma2"] = MA(df["cr"], m2)["ma"].shift(int(m2 / 2.5 + 1))
    df["crma3"] = MA(df["cr"], m3)["ma"].shift(int(m3 / 2.5 + 1))
    df["crma4"] = MA(df["cr"], m4)["ma"].shift(int(m4 / 2.5 + 1))
    return df


def CCI(df, n):
    """顺势指标"""
    typ = (df["high"] + df["low"] + df["close"]) / 3
    ma = MA(typ, n)["ma"]  # 简单平均

    def mad(x):
        return np.fabs(x - x.mean()).mean()

    md = typ.rolling(window=n).apply(mad, raw=True)  # 平均绝对偏差
    df["cci"] = (typ - ma) / (md * 0.015)
    return df


def OBV(df):
    """能量潮"""
    lc = df["close"].shift(1)
    df["obv"] = (np.where(df["close"] > lc, df["volume"], np.where(df["close"] < lc, -df["volume"], 0))).cumsum()
    return df


def CDP(df, n):
    """逆势操作"""
    pt = df["high"].shift(1) - df["low"].shift(1)
    cdp = (df["high"].shift(1) + df["low"].shift(1) + df["close"].shift(1)) / 3
    df["ah"] = MA(cdp + pt, n)["ma"]
    df["al"] = MA(cdp - pt, n)["ma"]
    df["nh"] = MA(2 * cdp - df["low"], n)["ma"]
    df["nl"] = MA(2 * cdp - df["high"], n)["ma"]

    return df


def HCL(df, n):
    """均线通道"""
    df["mah"] = MA(df["high"], n)["ma"]
    df["mal"] = MA(df["low"], n)["ma"]
    df["mac"] = MA(df["close"], n)["ma"]
    return df


def ENV(df, n, k):
    """包略线 (Envelopes)"""
    df["upper"] = MA(df["close"], n)["ma"] * (1 + k / 100)
    df["lower"] = MA(df["close"], n)["ma"] * (1 - k / 100)
    return df


def MIKE(df, n):
    """麦克指标"""
    typ = (df["high"] + df["low"] + df["close"]) / 3
    ll = df["low"].rolling(n).min()
    hh = df["high"].rolling(n).max()
    df["wr"] = typ + (typ - ll)
    df["mr"] = typ + (hh - ll)
    df["sr"] = 2 * hh - ll
    df["ws"] = typ - (hh - typ)
    df["ms"] = typ - (hh - ll)
    df["ss"] = 2 * ll - hh
    return df


def PUBU(df, m1, m2, m3, m4, m5, m6):
    """瀑布线"""
    df["pb1"] = (EMA(df["close"], m1)["ema"] + MA(df["close"], m1 * 2)["ma"] + MA(df["close"], m1 * 4)["ma"]) / 3
    df["pb2"] = (EMA(df["close"], m2)["ema"] + MA(df["close"], m2 * 2)["ma"] + MA(df["close"], m2 * 4)["ma"]) / 3
    df["pb3"] = (EMA(df["close"], m3)["ema"] + MA(df["close"], m3 * 2)["ma"] + MA(df["close"], m3 * 4)["ma"]) / 3
    df["pb4"] = (EMA(df["close"], m4)["ema"] + MA(df["close"], m4 * 2)["ma"] + MA(df["close"], m4 * 4)["ma"]) / 3
    df["pb5"] = (EMA(df["close"], m5)["ema"] + MA(df["close"], m5 * 2)["ma"] + MA(df["close"], m5 * 4)["ma"]) / 3
    df["pb6"] = (EMA(df["close"], m6)["ema"] + MA(df["close"], m6 * 2)["ma"] + MA(df["close"], m6 * 4)["ma"]) / 3
    return df


def BBI(df, n1, n2, n3, n4):
    """多空指数"""
    df["bbi"] = (MA(df["close"], n1)["ma"] + MA(df["close"], n2)["ma"] + MA(df["close"], n3)["ma"] +
                 MA(df["close"], n4)["ma"]) / 4
    return df


def DKX(df, m):
    """多空线"""
    a = (3 * df["close"] + df["high"] + df["low"] + df["open"]) / 6
    df["b"] = (20 * a + 19 * a.shift(1) + 18 * a.shift(2) + 17 * a.shift(3) + 16 * a.shift(4) + 15 * a.shift(
        5) + 14 * a.shift(6)
               + 13 * a.shift(7) + 12 * a.shift(8) + 11 * a.shift(9) + 10 * a.shift(10) + 9 * a.shift(11) + 8 * a.shift(
                12) + 7 * a.shift(13) + 6 * a.shift(14) + 5 * a.shift(15) + 4 * a.shift(16) + 3 * a.shift(
                17) + 2 * a.shift(18) + a.shift(20)
               ) / 210
    df["d"] = MA(df["b"], m)["ma"]
    return df


def BBIBOLL(df, n, m):
    """多空布林线"""
    df["bbiboll"] = (MA(df["close"], 3)["ma"] + MA(df["close"], 6)["ma"] + MA(df["close"], 12)["ma"] +
                     MA(df["close"], 24)["ma"]) / 4
    df["upr"] = df["bbiboll"] + m * df["bbiboll"].rolling(n).std()
    df["dwn"] = df["bbiboll"] - m * df["bbiboll"].rolling(n).std()
    return df


def ADTM(df, n, m):
    """动态买卖气指标"""
    dtm = np.where(df["open"] < df["open"].shift(1), 0,
                   np.where(df["high"] - df["open"] > df["open"] - df["open"].shift(1), df["high"] - df["open"],
                            df["open"] - df["open"].shift(1)))
    dbm = np.where(df["open"] >= df["open"].shift(1), 0,
                   np.where(df["open"] - df["low"] > df["open"] - df["open"].shift(1), df["open"] - df["low"],
                            df["open"] - df["open"].shift(1)))
    stm = pd.Series(dtm).rolling(n).sum()
    sbm = pd.Series(dbm).rolling(n).sum()
    df["adtm"] = np.where(stm > sbm, (stm - sbm) / stm, np.where(stm == sbm, 0, (stm - sbm) / sbm))
    df["adtmma"] = MA(df["adtm"], m)["ma"]
    return df


def B3612(df):
    """三减六日乖离率"""
    df["b36"] = MA(df["close"], 3)["ma"] - MA(df["close"], 6)["ma"]
    df["b612"] = MA(df["close"], 6)["ma"] - MA(df["close"], 12)["ma"]
    return df


def DBCD(df, n, m, t):
    """异同离差乖离率"""
    bias = (df["close"] - MA(df["close"], n)["ma"]) / MA(df["close"], n)["ma"]
    dif = bias - bias.shift(m)
    df["dbcd"] = SMA(dif, t, 1)["sma"]  # SMA
    df["mm"] = MA(df["dbcd"], 5)["ma"]
    return df


def DDI(df, n, n1, m, m1):
    """方向标准离差指数"""
    tr = np.where(np.absolute(df["high"] - df["high"].shift(1)) > np.absolute(df["low"] - df["low"].shift(1)),
                  np.absolute(df["high"] - df["high"].shift(1)), np.absolute(df["low"] - df["low"].shift(1)))
    dmz = np.where((df["high"] + df["low"]) <= (df["high"].shift(1) + df["low"].shift(1)), 0, tr)
    dmf = np.where((df["high"] + df["low"]) >= (df["high"].shift(1) + df["low"].shift(1)), 0, tr)
    diz = pd.Series(dmz).rolling(n).sum() / (pd.Series(dmz).rolling(n).sum() + pd.Series(dmf).rolling(n).sum())
    dif = pd.Series(dmf).rolling(n).sum() / (pd.Series(dmf).rolling(n).sum() + pd.Series(dmz).rolling(n).sum())
    df["ddi"] = diz - dif
    df["addi"] = SMA(df["ddi"], n1, m)["sma"]
    df["ad"] = MA(df["addi"], m1)["ma"]
    return df


def KD(df, n, m1, m2):
    """随机指标"""
    hv = df["high"].rolling(n).max()
    lv = df["low"].rolling(n).min()
    rsv = pd.Series(np.where(hv == lv, 0, (df["close"] - lv) / (hv - lv) * 100))
    df["k"] = SMA(rsv, m1, 1)["sma"]
    df["d"] = SMA(df["k"], m2, 1)["sma"]
    return df


def LWR(df, n, m1, m2):
    """威廉指标"""
    hv = df["high"].rolling(n).max()
    lv = df["low"].rolling(n).min()
    rsv = pd.Series(np.where(hv == lv, 0, (df["close"] - hv) / (hv - lv) * 100))
    df["lwr1"] = SMA(rsv, m1, 1)["sma"]
    df["lwr2"] = SMA(df["lwr1"], m2, 1)["sma"]
    return df


def MASS(df, n1, n2):
    """梅斯线"""
    ema1 = EMA(df["high"] - df["low"], n1)["ema"]
    ema2 = EMA(ema1, n1)["ema"]
    df["mass"] = (ema1 / ema2).rolling(n2).sum()
    return df


def MFI(df, n):
    """资金流量指标"""
    typ = (df["high"] + df["low"] + df["close"]) / 3
    mr = pd.Series(np.where(typ > typ.shift(1), typ * df["volume"], 0)).rolling(n).sum() / pd.Series(
        np.where(typ < typ.shift(1), typ * df["volume"], 0)).rolling(n).sum()
    df["mfi"] = 100 - (100 / (1 + mr))
    return df


def MI(df, n):
    """动量指标"""
    df["a"] = df["close"] - df["close"].shift(n)
    df["mi"] = SMA(df["a"], n, 1)["sma"]
    return df


def MICD(df, n, n1, n2):
    """异同离差动力指数"""
    mi = df["close"] - df["close"].shift(1)
    ami = SMA(mi, n, 1)["sma"]
    df["dif"] = MA(ami.shift(1), n1)["ma"] - MA(ami.shift(1), n2)["ma"]
    df["micd"] = SMA(df["dif"], 10, 1)["sma"]
    return df


def MTM(df, n, n1):
    """MTM动力指标"""
    df["mtm"] = df["close"] - df["close"].shift(n)
    df["mtmma"] = MA(df["mtm"], n1)["ma"]
    return df


def PRICEOSC(df, long, short):
    """价格震荡指数 Price Oscillator"""
    ma_s = MA(df["close"], short)["ma"]
    ma_l = MA(df["close"], long)["ma"]
    df["priceosc"] = (ma_s - ma_l) / ma_s * 100
    return df


def PSY(df, n, m):
    """心理线"""
    df["psy"] = COUNT(df["close"] > df["close"].shift(1), n)["count"] / n * 100
    df["psyma"] = MA(df["psy"], m)["ma"]
    return df


def QHLSR(df):
    """阻力指标"""
    qhl = (df["close"] - df["close"].shift(1)) - (df["volume"] - df["volume"].shift(1)) * (
            df["high"].shift(1) - df["low"].shift(1)) / df["volume"].shift(1)
    a = pd.Series(np.where(qhl > 0, qhl, 0)).rolling(5).sum()
    e = pd.Series(np.where(qhl > 0, qhl, 0)).rolling(10).sum()
    b = np.absolute(pd.Series(np.where(qhl < 0, qhl, 0)).rolling(5).sum())
    f = np.absolute(pd.Series(np.where(qhl < 0, qhl, 0)).rolling(10).sum())
    d = a / (a + b)
    g = e / (e + f)
    df["qhl5"] = np.where(pd.Series(np.where(qhl > 0, 1, 0)).rolling(5).sum() == 5, 1,
                          np.where(pd.Series(np.where(qhl < 0, 1, 0)).rolling(5).sum() == 5, 0, d))
    df["qhl10"] = g
    return df


def RC(df, n):
    """变化率指数"""
    rc = df["close"] / df["close"].shift(n)
    df["arc"] = SMA(rc.shift(1), n, 1)["sma"]
    return df


def RCCD(df, n, n1, n2):
    """异同离差变化率指数"""
    rc = df["close"] / df["close"].shift(n)
    arc = SMA(rc.shift(1), n, 1)["sma"]
    df["dif"] = MA(arc.shift(1), n1)["ma"] - MA(arc.shift(1), n2)["ma"]
    df["rccd"] = SMA(df["dif"], n, 1)["sma"]
    return df


def ROC(df, n, m):
    """变动速率"""
    df["roc"] = (df["close"] - df['close'].shift(n)) / df["close"].shift(n) * 100
    df["rocma"] = MA(df["roc"], m)["ma"]
    return df


def SLOWKD(df, n, m1, m2, m3):
    """慢速KD"""
    rsv = (df["close"] - df["low"].rolling(n).min()) / \
          (df["high"].rolling(n).max() - df["low"].rolling(n).min()) * 100
    fastk = SMA(rsv, m1, 1)["sma"]
    df["k"] = SMA(fastk, m2, 1)["sma"]
    df["d"] = SMA(df["k"], m3, 1)["sma"]
    return df


def SRDM(df, n):
    """动向速度比率"""
    dmz = np.where((df["high"] + df["low"]) <= (df["high"].shift(1) + df["low"].shift(1)), 0,
                   np.where(np.absolute(df["high"] - df["high"].shift(1)) > np.absolute(df["low"] - df["low"].shift(1)),
                            np.absolute(df["high"] - df["high"].shift(1)), np.absolute(df["low"] - df["low"].shift(1))))
    dmf = np.where((df["high"] + df["low"]) >= (df["high"].shift(1) + df["low"].shift(1)), 0,
                   np.where(np.absolute(df["high"] - df["high"].shift(1)) > np.absolute(df["low"] - df["low"].shift(1)),
                            np.absolute(df["high"] - df["high"].shift(1)), np.absolute(df["low"] - df["low"].shift(1))))
    admz = MA(pd.Series(dmz), 10)["ma"]
    admf = MA(pd.Series(dmf), 10)["ma"]
    df["srdm"] = np.where(admz > admf, (admz - admf) / admz, np.where(admz == admf, 0, (admz - admf) / admf))
    df["asrdm"] = SMA(df["srdm"], n, 1)["sma"]
    return df


def SRMI(df, n):
    """MI修正指标"""
    df["a"] = np.where(df["close"] < df["close"].shift(n), (df["close"] - df["close"].shift(n)) / df["close"].shift(n),
                       np.where(df["close"] == df["close"].shift(n), 0,
                                (df["close"] - df["close"].shift(n)) / df["close"]))
    df["mi"] = SMA(df["a"], n, 1)["sma"]
    return df


def ZDZB(df, n1, n2, n3):
    """筑底指标"""
    a = pd.Series(np.where(df["close"] >= df["close"].shift(1), 1, 0)).rolling(n1).sum() / pd.Series(
        np.where(df["close"] < df["close"].shift(1), 1, 0)).rolling(n1).sum()
    df["b"] = MA(a, n2)["ma"]
    df["d"] = MA(a, n3)["ma"]
    return df


def DPO(df, n, m):
    """区间震荡线"""
    df["dpo"] = df["close"] - (MA(df["close"], 20)["ma"]).shift(11)
    return df


def LON(df):
    """长线指标"""
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
    df["lon"] = res1.cumsum()
    df["ma1"] = MA(df["lon"], 10)["ma"]
    return df


def SHORT(df):
    """短线指标"""
    tb = np.where(df["high"] > df["close"].shift(1),
                  df["high"] - df["close"].shift(1) + df["close"] - df["low"],
                  df["close"] - df["low"])
    ts = np.where(df["close"].shift(1) > df["low"],
                  df["close"].shift(1) - df["low"] + df["high"] - df["close"],
                  df["high"] - df["close"])
    vol1 = (tb - ts) * df["volume"] / (tb + ts) / 10000
    vol10 = vol1.ewm(alpha=0.1, adjust=False).mean()  # DMA 动态均值
    vol11 = vol1.ewm(alpha=0.05, adjust=False).mean()  # DMA
    df["short"] = vol10 - vol11
    df["ma1"] = MA(df["short"], 10)["ma"]
    return df


def MV(df, n, m):
    """均量线"""
    df["mv1"] = SMA(df["volume"], n, 1)["sma"]  # SMA
    df["mv2"] = SMA(df["volume"], m, 1)["sma"]  # SMA
    return df


def WAD(df, n, m):
    """威廉多空力度线"""
    df["a"] = np.absolute(np.where(df["close"] > df["close"].shift(1),
                                   df["close"] - np.where(df["close"].shift(1) < df["low"], df["close"].shift(1),
                                                          df["low"]), np.where(df["close"] < df["close"].shift(1),
                                                                               df["close"] - np.where(
                                                                                   df["close"].shift(1) > df["high"],
                                                                                   df["close"].shift(1), df["high"]),
                                                                               0)).cumsum())
    df["b"] = SMA(df["a"], n, 1)["sma"]
    df["e"] = SMA(df["a"], m, 1)["sma"]
    return df


def AD(df):
    """累积/派发指标 Accumulation/Distribution"""
    df["ad"] = (((df["close"] - df["low"]) - (df["high"] - df["close"])) / (df["high"] - df["low"]) * df[
        "volume"]).cumsum()
    return df


def CCL(df):
    """持仓异动"""
    ccl = np.where(df["close"] > df["close"].shift(1),
                   np.where(df["close_oi"] > df["close_oi"].shift(1), "多头增仓", "空头减仓"),
                   np.where(df["close_oi"] > df["close_oi"].shift(1), "空头增仓", "多头减仓"))
    # color = np.where(df["close"] > df["close"].shift(1), "红", "绿")  # 1表示红色, 0表示绿色
    # position = np.where(df["close_oi"] > df["close_oi"].shift(1), "上", "下")  # 1表示零轴之上, 0表示零轴之下
    df["ccl"] = ccl
    return df


def CJL(df):
    """成交量"""
    df["vol"] = df["volume"]  # 成交量
    df["opid"] = df["close_oi"]  # 持仓量
    return df


def OPI(df):
    """持仓量"""
    df["opi"] = df["close_oi"]
    return df


def PVT(df):
    """价量趋势指数"""
    df["pvt"] = ((df["close"] - df["close"].shift(1)) / df["close"].shift(1) * df["volume"]).cumsum()
    return df


def VOSC(df, short, long):
    """移动平均成交量指标 Volume Oscillator"""
    df["vosc"] = (MA(df["volume"], short)["ma"] - MA(df["volume"], long)["ma"]) / MA(df["volume"], short)["ma"] * 100
    return df


def VROC(df, n):
    """量变动速率"""
    df["vroc"] = (df["volume"] - df["volume"].shift(n)) / df["volume"].shift(n) * 100
    return df


def VRSI(df, n):
    """量相对强弱"""
    df["vrsi"] = \
        SMA(pd.Series(np.where(df["volume"] - df["volume"].shift(1) > 0, df["volume"] - df["volume"].shift(1), 0)), n,
            1)[
            "sma"] / SMA(np.absolute(df["volume"] - df["volume"].shift(1)), n, 1)["sma"] * 100
    return df


def WVAD(df):
    """威廉变异离散量"""
    df["wvad"] = (df["close"] - df["open"]) / (df["high"] - df["low"]) * df["volume"]
    return df


def MA(df, n):
    """简单移动平均线"""
    if not isinstance(df, pd.DataFrame):
        ma = list(df.rolling(n).mean())  #
        df = pd.DataFrame(data=ma, columns=["ma"])
    else:
        df["ma"] = df["close"].rolling(n).mean()  #
    return df


def SMA(df, n, m):
    """扩展指数加权移动平均"""
    if not isinstance(df, pd.DataFrame):
        sma = list(df.ewm(alpha=m / n, adjust=False).mean())
        df = pd.DataFrame(data=sma, columns=["sma"])
    else:
        df["sma"] = df["close"].ewm(alpha=m / n, adjust=False).mean()
    return df


def EMA(df, n):
    """指数加权移动平均线"""
    if not isinstance(df, pd.DataFrame):
        ema = list(df.ewm(span=n, adjust=False).mean())
        df = pd.DataFrame(data=ema, columns=["ema"])
    else:
        df["ema"] = df["close"].ewm(span=n, adjust=False).mean()
    return df


def CROSSUP(a, b):
    """向上穿越"""
    df = pd.DataFrame(data=np.where((a > b) & (a.shift(1) <= b.shift(1)), 1, 0), columns=["crossup"])
    return df


def CROSSDOWN(a, b):
    """向下穿越"""
    df = pd.DataFrame(data=np.where((a < b) & (a.shift(1) >= b.shift(1)), 1, 0), columns=["crossdown"])
    return df


def COUNT(cond, n):
    """统计n周期内中满足cond条件的周期数;
        如果n为0,则从第一个有效值开始统计
    """
    if n == 0:  # 从第一个有效值开始统计
        df = pd.DataFrame(data=np.where(cond, 1, 0).cumsum(), columns=["count"])
    else:  # 统计每个n周期
        df = pd.DataFrame(data=pd.Series(np.where(cond, 1, 0)).rolling(n).sum(), columns=["count"])
    return df


def EMA2(df, n):
    """线性加权移动平均 WMA"""
    weights = list(i for i in range(1, n + 1))  # 对应的权值列表

    def average(elements):
        return np.average(elements, weights=weights)

    if not isinstance(df, pd.DataFrame):
        ema2 = df.rolling(window=n).apply(average, raw=True)
        df = pd.DataFrame(data=list(ema2), columns=["ema2"])
    else:
        df["ema2"] = df["close"].rolling(window=n).apply(average, raw=True)
    return df


def TRMA(df, n):
    """三角移动平均线"""
    if n % 2 == 0:
        n1 = int(n / 2)
        n2 = int(n / 2 + 1)
    else:
        n1 = n2 = int((n + 1) / 2)

    if not isinstance(df, pd.DataFrame):
        ma_half = MA(df, n1)["ma"]
        trma = MA(ma_half, n2)["ma"]
        df = pd.DataFrame(data=list(trma), columns=["trma"])
    else:
        ma_half = MA(df["close"], n1)["ma"]
        df["trma"] = MA(ma_half, n2)["ma"]
    return df


def HARMEAN(series, n):
    """调和平均值"""
    harmean = n / ((1 / series).rolling(n).sum())
    df = pd.DataFrame(data=list(harmean), columns=["harmean"])
    return df


def NUMPOW(series, n, m):
    """自然数幂方和"""
    numpow = sum((n - i) ** m * series.shift(i) for i in range(n))
    df = pd.DataFrame(data=list(numpow), columns=["numpow"])
    return df


def ABS(series):
    """获取series的绝对值"""
    df = pd.DataFrame(data=list(np.absolute(series)), columns=["abs"])
    return df


def MIN(series1, series2):
    """获取series1和series2中的最小值"""
    min = np.minimum(series1, series2)
    df = pd.DataFrame(data=min, columns=["min"])
    return df


def MAX(series1, series2):
    """获取series1和series2中的最大值"""
    max = np.maximum(series1, series2)
    df = pd.DataFrame(data=max, columns=["max"])
    return df


def MEDIAN(series, n):
    """中位数: 求series在n个周期内居于中间的数值"""
    median = series.rolling(n).median()
    df = pd.DataFrame(data=list(median), columns=["median"])
    return df


def EXIST(cond, n):
    """判断n个周期内,是否有满足cond的条件"""
    exist = np.where(pd.Series(np.where(cond, 1, 0)).rolling(n).sum() > 0, 1, 0)
    df = pd.DataFrame(data=list(exist), columns=["exist"])
    return df


def EVERY(cond, n):
    """判断n周期内,是否一直满足cond条件"""
    every = np.where(pd.Series(np.where(cond, 1, 0)).rolling(n).sum() == n, 1, 0)
    df = pd.DataFrame(data=list(every), columns=["every"])
    return df


def HHV(series, n):
    """求series在n个周期内的最高值"""
    df = pd.DataFrame(data=list(series.rolling(n).max()), columns=["hhv"])
    return df


def LLV(series, n):
    """求在n个周期内的最小值"""
    df = pd.DataFrame(data=list(series.rolling(n).min()), columns=["llv"])
    return df


def AVEDEV(series, n):
    """平均绝对偏差: 求series在n周期内的平均绝对偏差"""

    def mad(x):
        return np.fabs(x - x.mean()).mean()

    avedev = series.rolling(window=n).apply(mad, raw=True)
    df = pd.DataFrame(data=list(avedev), columns=["avedev"])
    return df
