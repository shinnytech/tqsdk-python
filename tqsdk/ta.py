#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

"""
tqsdk.ta 模块包含了一批常用的技术指标计算函数
"""

import numpy as np
import pandas as pd
import numba
import ta_func


def ATR(df, n):
    """平均真实波幅"""
    new_df = pd.DataFrame()
    pre_close = df["close"].shift(1)
    new_df["tr"] = np.where(df["high"] - df["low"] > np.absolute(pre_close - df["high"]),
                            np.where(df["high"] - df["low"] > np.absolute(pre_close - df["low"]),
                                     df["high"] - df["low"], np.absolute(pre_close - df["low"])),
                            np.where(np.absolute(pre_close - df["high"]) > np.absolute(pre_close - df["low"]),
                                     np.absolute(pre_close - df["high"]), np.absolute(pre_close - df["low"])))
    new_df["atr"] = ta_func.ma(new_df["tr"], n)
    return new_df


def BIAS(df, n):
    """乖离率"""
    ma1 = ta_func.ma(df["close"], n)
    new_df = pd.DataFrame(data=list((df["close"] - ma1) / ma1 * 100), columns=["bias"])
    return new_df


def BOLL(df, n, p):
    """布林线"""
    new_df = pd.DataFrame()
    mid = ta_func.ma(df["close"], n)
    std = df["close"].rolling(n).std()
    new_df["mid"] = mid
    new_df["top"] = mid + p * std
    new_df["bottom"] = mid - p * std
    return new_df


def DMI(df, n, m):
    """动向指标"""
    new_df = pd.DataFrame()
    new_df["atr"] = ATR(df, n)["atr"]
    pre_high = df["high"].shift(1)
    pre_low = df["low"].shift(1)
    hd = df["high"] - pre_high
    ld = pre_low - df["low"]
    admp = ta_func.ma(pd.Series(np.where((hd > 0) & (hd > ld), hd, 0)), n)
    admm = ta_func.ma(pd.Series(np.where((ld > 0) & (ld > hd), ld, 0)), n)
    new_df["pdi"] = pd.Series(np.where(new_df["atr"] > 0, admp / new_df["atr"] * 100, np.NaN)).ffill()
    new_df["mdi"] = pd.Series(np.where(new_df["atr"] > 0, admm / new_df["atr"] * 100, np.NaN)).ffill()
    ad = pd.Series(np.absolute(new_df["mdi"] - new_df["pdi"]) / (new_df["mdi"] + new_df["pdi"]) * 100)
    new_df["adx"] = ta_func.ma(ad, m)
    new_df["adxr"] = (new_df["adx"] + new_df["adx"].shift(m)) / 2
    return new_df


def KDJ(df, n, m1, m2):
    """随机指标"""
    new_df = pd.DataFrame()
    hv = df["high"].rolling(n).max()
    lv = df["low"].rolling(n).min()
    rsv = pd.Series(np.where(hv == lv, 0, (df["close"] - lv) / (hv - lv) * 100))
    new_df["k"] = ta_func.sma(rsv, m1, 1)
    new_df["d"] = ta_func.sma(new_df["k"], m2, 1)
    new_df["j"] = 3 * new_df["k"] - 2 * new_df["d"]
    return new_df


def MACD(df, short, long, m):
    """异同移动平均线"""
    new_df = pd.DataFrame()
    eshort = ta_func.ema(df["close"], short)
    elong = ta_func.ema(df["close"], long)
    new_df["diff"] = eshort - elong
    new_df["dea"] = ta_func.ema(new_df["diff"], m)
    new_df["bar"] = 2 * (new_df["diff"] - new_df["dea"])
    return new_df


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
    sar = _sar(df["open"].values, df["high"].values, df["low"].values, df["close"].values, range_high.values,
               range_low.values, n, step, max)
    new_df = pd.DataFrame(data=sar, columns=["sar"])
    return new_df


def WR(df, n):
    """威廉指标"""
    hn = df["high"].rolling(n).max()
    ln = df["low"].rolling(n).min()
    new_df = pd.DataFrame(data=list((hn - df["close"]) / (hn - ln) * (-100)), columns=["wr"])
    return new_df


def RSI(df, n):
    """相对强弱指标"""
    lc = df["close"].shift(1)
    rsi = ta_func.sma(pd.Series(np.where(df["close"] - lc > 0, df["close"] - lc, 0)), n, 1) / \
          ta_func.sma(np.absolute(df["close"] - lc), n, 1) * 100
    new_df = pd.DataFrame(data=rsi, columns=["rsi"])
    return new_df


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
    new_df = pd.DataFrame(data=list(pd.Series(si).cumsum()), columns=["asi"])
    return new_df


def VR(df, n):
    """VR 容量比率"""
    lc = df["close"].shift(1)
    vr = pd.Series(np.where(df["close"] > lc, df["volume"], 0)).rolling(n).sum() / pd.Series(
        np.where(df["close"] <= lc, df["volume"], 0)).rolling(n).sum() * 100
    new_df = pd.DataFrame(data=list(vr), columns=["vr"])
    return new_df


def ARBR(df, n):
    """人气意愿指标"""
    new_df = pd.DataFrame()
    new_df["ar"] = (df["high"] - df["open"]).rolling(n).sum() / (df["open"] - df["low"]).rolling(n).sum() * 100
    new_df["br"] = pd.Series(
        np.where(df["high"] - df["close"].shift(1) > 0, df["high"] - df["close"].shift(1), 0)).rolling(
        n).sum() / pd.Series(
        np.where(df["close"].shift(1) - df["low"] > 0, df["close"].shift(1) - df["low"], 0)).rolling(n).sum() * 100
    return new_df


def DMA(df, short, long, m):
    """平均线差"""
    new_df = pd.DataFrame()
    new_df["ddd"] = ta_func.ma(df["close"], short) - ta_func.ma(df["close"], long)
    new_df["ama"] = ta_func.ma(new_df["ddd"], m)
    return new_df


def EXPMA(df, p1, p2):
    """指数加权移动平均线组合"""
    new_df = pd.DataFrame()
    new_df["ma1"] = ta_func.ema(df["close"], p1)
    new_df["ma2"] = ta_func.ema(df["close"], p2)
    return new_df


def CR(df, n, m):
    """CR能量"""
    new_df = pd.DataFrame()
    mid = (df["high"] + df["low"] + df["close"]) / 3
    new_df["cr"] = pd.Series(np.where(0 > df["high"] - mid.shift(1), 0, df["high"] - mid.shift(1))).rolling(
        n).sum() / pd.Series(np.where(0 > mid.shift(1) - df["low"], 0, mid.shift(1) - df["low"])).rolling(n).sum() * 100
    new_df["crma"] = ta_func.ma(new_df["cr"], m).shift(int(m / 2.5 + 1))
    return new_df


def CCI(df, n):
    """顺势指标"""
    typ = (df["high"] + df["low"] + df["close"]) / 3
    ma = ta_func.ma(typ, n)

    def mad(x):
        return np.fabs(x - x.mean()).mean()

    md = typ.rolling(window=n).apply(mad, raw=True)  # 平均绝对偏差
    new_df = pd.DataFrame(data=list((typ - ma) / (md * 0.015)), columns=["cci"])
    return new_df


def OBV(df):
    """能量潮"""
    lc = df["close"].shift(1)
    obv = (np.where(df["close"] > lc, df["volume"], np.where(df["close"] < lc, -df["volume"], 0))).cumsum()
    new_df = pd.DataFrame(data=obv, columns=["obv"])
    return new_df


def CDP(df, n):
    """逆势操作"""
    new_df = pd.DataFrame()
    pt = df["high"].shift(1) - df["low"].shift(1)
    cdp = (df["high"].shift(1) + df["low"].shift(1) + df["close"].shift(1)) / 3
    new_df["ah"] = ta_func.ma(cdp + pt, n)
    new_df["al"] = ta_func.ma(cdp - pt, n)
    new_df["nh"] = ta_func.ma(2 * cdp - df["low"], n)
    new_df["nl"] = ta_func.ma(2 * cdp - df["high"], n)
    return new_df


def HCL(df, n):
    """均线通道"""
    new_df = pd.DataFrame()
    new_df["mah"] = ta_func.ma(df["high"], n)
    new_df["mal"] = ta_func.ma(df["low"], n)
    new_df["mac"] = ta_func.ma(df["close"], n)
    return new_df


def ENV(df, n, k):
    """包略线 (Envelopes)"""
    new_df = pd.DataFrame()
    new_df["upper"] = ta_func.ma(df["close"], n) * (1 + k / 100)
    new_df["lower"] = ta_func.ma(df["close"], n) * (1 - k / 100)
    return new_df


def MIKE(df, n):
    """麦克指标"""
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
    """瀑布线"""
    pb = (ta_func.ema(df["close"], m) + ta_func.ma(df["close"], m * 2) + ta_func.ma(df["close"], m * 4)) / 3
    new_df = pd.DataFrame(data=list(pb), columns=["pb"])
    return new_df


def BBI(df, n1, n2, n3, n4):
    """多空指数"""
    bbi = (ta_func.ma(df["close"], n1) + ta_func.ma(df["close"], n2) + ta_func.ma(df["close"], n3) + ta_func.ma(
        df["close"], n4)) / 4
    new_df = pd.DataFrame(data=list(bbi), columns=["bbi"])
    return new_df


def DKX(df, m):
    """多空线"""
    new_df = pd.DataFrame()
    a = (3 * df["close"] + df["high"] + df["low"] + df["open"]) / 6
    new_df["b"] = (20 * a + 19 * a.shift(1) + 18 * a.shift(2) + 17 * a.shift(3) + 16 * a.shift(4) + 15 * a.shift(
        5) + 14 * a.shift(6)
                   + 13 * a.shift(7) + 12 * a.shift(8) + 11 * a.shift(9) + 10 * a.shift(10) + 9 * a.shift(
                11) + 8 * a.shift(
                12) + 7 * a.shift(13) + 6 * a.shift(14) + 5 * a.shift(15) + 4 * a.shift(16) + 3 * a.shift(
                17) + 2 * a.shift(18) + a.shift(20)
                   ) / 210
    new_df["d"] = ta_func.ma(new_df["b"], m)
    return new_df


def BBIBOLL(df, n, m):
    """多空布林线"""
    new_df = pd.DataFrame()
    new_df["bbiboll"] = (ta_func.ma(df["close"], 3) + ta_func.ma(df["close"], 6) + ta_func.ma(df["close"],
                                                                                              12) + ta_func.ma(
        df["close"], 24)) / 4
    new_df["upr"] = new_df["bbiboll"] + m * new_df["bbiboll"].rolling(n).std()
    new_df["dwn"] = new_df["bbiboll"] - m * new_df["bbiboll"].rolling(n).std()
    return new_df


def ADTM(df, n, m):
    """动态买卖气指标"""
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
    new_df["adtmma"] = ta_func.ma(new_df["adtm"], m)
    return new_df


def B3612(df):
    """三减六日乖离率"""
    new_df = pd.DataFrame()
    new_df["b36"] = ta_func.ma(df["close"], 3) - ta_func.ma(df["close"], 6)
    new_df["b612"] = ta_func.ma(df["close"], 6) - ta_func.ma(df["close"], 12)
    return new_df


def DBCD(df, n, m, t):
    """异同离差乖离率"""
    new_df = pd.DataFrame()
    bias = (df["close"] - ta_func.ma(df["close"], n)) / ta_func.ma(df["close"], n)
    dif = bias - bias.shift(m)
    new_df["dbcd"] = ta_func.sma(dif, t, 1)
    new_df["mm"] = ta_func.ma(new_df["dbcd"], 5)
    return new_df


def DDI(df, n, n1, m, m1):
    """方向标准离差指数"""
    new_df = pd.DataFrame()
    tr = np.where(np.absolute(df["high"] - df["high"].shift(1)) > np.absolute(df["low"] - df["low"].shift(1)),
                  np.absolute(df["high"] - df["high"].shift(1)), np.absolute(df["low"] - df["low"].shift(1)))
    dmz = np.where((df["high"] + df["low"]) <= (df["high"].shift(1) + df["low"].shift(1)), 0, tr)
    dmf = np.where((df["high"] + df["low"]) >= (df["high"].shift(1) + df["low"].shift(1)), 0, tr)
    diz = pd.Series(dmz).rolling(n).sum() / (pd.Series(dmz).rolling(n).sum() + pd.Series(dmf).rolling(n).sum())
    dif = pd.Series(dmf).rolling(n).sum() / (pd.Series(dmf).rolling(n).sum() + pd.Series(dmz).rolling(n).sum())
    new_df["ddi"] = diz - dif
    new_df["addi"] = ta_func.sma(new_df["ddi"], n1, m)
    new_df["ad"] = ta_func.ma(new_df["addi"], m1)
    return new_df


def KD(df, n, m1, m2):
    """随机指标"""
    new_df = pd.DataFrame()
    hv = df["high"].rolling(n).max()
    lv = df["low"].rolling(n).min()
    rsv = pd.Series(np.where(hv == lv, 0, (df["close"] - lv) / (hv - lv) * 100))
    new_df["k"] = ta_func.sma(rsv, m1, 1)
    new_df["d"] = ta_func.sma(new_df["k"], m2, 1)
    return new_df


def LWR(df, n, m):
    """威廉指标"""
    hv = df["high"].rolling(n).max()
    lv = df["low"].rolling(n).min()
    rsv = pd.Series(np.where(hv == lv, 0, (df["close"] - hv) / (hv - lv) * 100))
    new_df = pd.DataFrame(data=list(ta_func.sma(rsv, m, 1)), columns=["lwr"])
    return new_df


def MASS(df, n1, n2):
    """梅斯线"""
    ema1 = ta_func.ema(df["high"] - df["low"], n1)
    ema2 = ta_func.ema(ema1, n1)
    new_df = pd.DataFrame(data=list((ema1 / ema2).rolling(n2).sum()), columns=["mass"])
    return new_df


def MFI(df, n):
    """资金流量指标"""
    typ = (df["high"] + df["low"] + df["close"]) / 3
    mr = pd.Series(np.where(typ > typ.shift(1), typ * df["volume"], 0)).rolling(n).sum() / pd.Series(
        np.where(typ < typ.shift(1), typ * df["volume"], 0)).rolling(n).sum()
    new_df = pd.DataFrame(data=list(100 - (100 / (1 + mr))), columns=["mfi"])
    return new_df


def MI(df, n):
    """动量指标"""
    new_df = pd.DataFrame()
    new_df["a"] = df["close"] - df["close"].shift(n)
    new_df["mi"] = ta_func.sma(new_df["a"], n, 1)
    return new_df


def MICD(df, n, n1, n2):
    """异同离差动力指数"""
    new_df = pd.DataFrame()
    mi = df["close"] - df["close"].shift(1)
    ami = ta_func.sma(mi, n, 1)
    new_df["dif"] = ta_func.ma(ami.shift(1), n1) - ta_func.ma(ami.shift(1), n2)
    new_df["micd"] = ta_func.sma(new_df["dif"], 10, 1)
    return new_df


def MTM(df, n, n1):
    """MTM动力指标"""
    new_df = pd.DataFrame()
    new_df["mtm"] = df["close"] - df["close"].shift(n)
    new_df["mtmma"] = ta_func.ma(new_df["mtm"], n1)
    return new_df


def PRICEOSC(df, long, short):
    """价格震荡指数 Price Oscillator"""
    ma_s = ta_func.ma(df["close"], short)
    ma_l = ta_func.ma(df["close"], long)
    new_df = pd.DataFrame(data=list((ma_s - ma_l) / ma_s * 100), columns=["priceosc"])
    return new_df


def PSY(df, n, m):
    """心理线"""
    new_df = pd.DataFrame()
    new_df["psy"] = ta_func.count(df["close"] > df["close"].shift(1), n) / n * 100
    new_df["psyma"] = ta_func.ma(new_df["psy"], m)
    return new_df


def QHLSR(df):
    """阻力指标"""
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
    """变化率指数"""
    rc = df["close"] / df["close"].shift(n)
    new_df = pd.DataFrame(data=list(ta_func.sma(rc.shift(1), n, 1)), columns=["arc"])
    return new_df


def RCCD(df, n, n1, n2):
    """异同离差变化率指数"""
    new_df = pd.DataFrame()
    rc = df["close"] / df["close"].shift(n)
    arc = ta_func.sma(rc.shift(1), n, 1)
    new_df["dif"] = ta_func.ma(arc.shift(1), n1) - ta_func.ma(arc.shift(1), n2)
    new_df["rccd"] = ta_func.sma(new_df["dif"], n, 1)
    return new_df


def ROC(df, n, m):
    """变动速率"""
    new_df = pd.DataFrame()
    new_df["roc"] = (df["close"] - df['close'].shift(n)) / df["close"].shift(n) * 100
    new_df["rocma"] = ta_func.ma(new_df["roc"], m)
    return new_df


def SLOWKD(df, n, m1, m2, m3):
    """慢速KD"""
    new_df = pd.DataFrame()
    rsv = (df["close"] - df["low"].rolling(n).min()) / \
          (df["high"].rolling(n).max() - df["low"].rolling(n).min()) * 100
    fastk = ta_func.sma(rsv, m1, 1)
    new_df["k"] = ta_func.sma(fastk, m2, 1)
    new_df["d"] = ta_func.sma(new_df["k"], m3, 1)
    return new_df


def SRDM(df, n):
    """动向速度比率"""
    new_df = pd.DataFrame()
    dmz = np.where((df["high"] + df["low"]) <= (df["high"].shift(1) + df["low"].shift(1)), 0,
                   np.where(np.absolute(df["high"] - df["high"].shift(1)) > np.absolute(df["low"] - df["low"].shift(1)),
                            np.absolute(df["high"] - df["high"].shift(1)), np.absolute(df["low"] - df["low"].shift(1))))
    dmf = np.where((df["high"] + df["low"]) >= (df["high"].shift(1) + df["low"].shift(1)), 0,
                   np.where(np.absolute(df["high"] - df["high"].shift(1)) > np.absolute(df["low"] - df["low"].shift(1)),
                            np.absolute(df["high"] - df["high"].shift(1)), np.absolute(df["low"] - df["low"].shift(1))))
    admz = ta_func.ma(pd.Series(dmz), 10)
    admf = ta_func.ma(pd.Series(dmf), 10)
    new_df["srdm"] = np.where(admz > admf, (admz - admf) / admz, np.where(admz == admf, 0, (admz - admf) / admf))
    new_df["asrdm"] = ta_func.sma(new_df["srdm"], n, 1)
    return new_df


def SRMI(df, n):
    """MI修正指标"""
    new_df = pd.DataFrame()
    new_df["a"] = np.where(df["close"] < df["close"].shift(n),
                           (df["close"] - df["close"].shift(n)) / df["close"].shift(n),
                           np.where(df["close"] == df["close"].shift(n), 0,
                                    (df["close"] - df["close"].shift(n)) / df["close"]))
    new_df["mi"] = ta_func.sma(new_df["a"], n, 1)
    return new_df


def ZDZB(df, n1, n2, n3):
    """筑底指标"""
    new_df = pd.DataFrame()
    a = pd.Series(np.where(df["close"] >= df["close"].shift(1), 1, 0)).rolling(n1).sum() / pd.Series(
        np.where(df["close"] < df["close"].shift(1), 1, 0)).rolling(n1).sum()
    new_df["b"] = ta_func.ma(a, n2)
    new_df["d"] = ta_func.ma(a, n3)
    return new_df


def DPO(df, n, m):
    """区间震荡线"""
    dpo = df["close"] - (ta_func.ma(df["close"], 20)).shift(11)
    new_df = pd.DataFrame(data=list(dpo), columns=["dpo"])
    return new_df


def LON(df):
    """长线指标"""
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
    new_df["ma1"] = ta_func.ma(new_df["lon"], 10)
    return new_df


def SHORT(df):
    """短线指标"""
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
    new_df["ma1"] = ta_func.ma(new_df["short"], 10)
    return new_df


def MV(df, n, m):
    """均量线"""
    new_df = pd.DataFrame()
    new_df["mv1"] = ta_func.sma(df["volume"], n, 1)
    new_df["mv2"] = ta_func.sma(df["volume"], m, 1)
    return new_df


def WAD(df, n, m):
    """威廉多空力度线"""
    new_df = pd.DataFrame()
    new_df["a"] = np.absolute(np.where(df["close"] > df["close"].shift(1),
                                       df["close"] - np.where(df["close"].shift(1) < df["low"], df["close"].shift(1),
                                                              df["low"]),
                                       np.where(df["close"] < df["close"].shift(1), df["close"] - np.where(
                                           df["close"].shift(1) > df["high"], df["close"].shift(1), df["high"]),
                                                0)).cumsum())
    new_df["b"] = ta_func.sma(new_df["a"], n, 1)
    new_df["e"] = ta_func.sma(new_df["a"], m, 1)
    return new_df


def AD(df):
    """累积/派发指标 Accumulation/Distribution"""
    ad = (((df["close"] - df["low"]) - (df["high"] - df["close"])) / (df["high"] - df["low"]) * df[
        "volume"]).cumsum()
    new_df = pd.DataFrame(data=list(ad), columns=["ad"])
    return new_df


def CCL(df):
    """持仓异动"""
    ccl = np.where(df["close"] > df["close"].shift(1),
                   np.where(df["close_oi"] > df["close_oi"].shift(1), "多头增仓", "空头减仓"),
                   np.where(df["close_oi"] > df["close_oi"].shift(1), "空头增仓", "多头减仓"))
    # color = np.where(df["close"] > df["close"].shift(1), "红", "绿")  # 1表示红色, 0表示绿色
    # position = np.where(df["close_oi"] > df["close_oi"].shift(1), "上", "下")  # 1表示零轴之上, 0表示零轴之下
    new_df = pd.DataFrame(data=list(ccl), columns=["ccl"])
    return new_df


def CJL(df):
    """成交量"""
    new_df = pd.DataFrame()
    new_df["vol"] = df["volume"]  # 成交量
    new_df["opid"] = df["close_oi"]  # 持仓量
    return new_df


def OPI(df):
    """持仓量"""
    opi = df["close_oi"]
    new_df = pd.DataFrame(data=list(opi), columns=["opi"])
    return new_df


def PVT(df):
    """价量趋势指数"""
    pvt = ((df["close"] - df["close"].shift(1)) / df["close"].shift(1) * df["volume"]).cumsum()
    new_df = pd.DataFrame(data=list(pvt), columns=["pvt"])
    return new_df


def VOSC(df, short, long):
    """移动平均成交量指标 Volume Oscillator"""
    vosc = (ta_func.ma(df["volume"], short) - ta_func.ma(df["volume"], long)) / ta_func.ma(df["volume"], short) * 100
    new_df = pd.DataFrame(data=list(vosc), columns=["vosc"])
    return new_df


def VROC(df, n):
    """量变动速率"""
    vroc = (df["volume"] - df["volume"].shift(n)) / df["volume"].shift(n) * 100
    new_df = pd.DataFrame(data=list(vroc), columns=["vroc"])
    return new_df


def VRSI(df, n):
    """量相对强弱"""
    vrsi = ta_func.sma(
        pd.Series(np.where(df["volume"] - df["volume"].shift(1) > 0, df["volume"] - df["volume"].shift(1), 0)), n,
        1) / ta_func.sma(np.absolute(df["volume"] - df["volume"].shift(1)), n, 1) * 100
    new_df = pd.DataFrame(data=list(vrsi), columns=["vrsi"])
    return new_df


def WVAD(df):
    """威廉变异离散量"""
    wvad = (df["close"] - df["open"]) / (df["high"] - df["low"]) * df["volume"]
    new_df = pd.DataFrame(data=list(wvad), columns=["wvad"])
    return new_df


def MA(df, n):
    """简单移动平均线"""
    new_df = pd.DataFrame(data=list(ta_func.ma(df["close"], n)), columns=["ma"])
    return new_df


def SMA(df, n, m):
    """扩展指数加权移动平均"""
    new_df = pd.DataFrame(data=list(ta_func.sma(df["close"], n, m)), columns=["sma"])
    return new_df


def EMA(df, n):
    """指数加权移动平均线"""
    new_df = pd.DataFrame(data=list(ta_func.ema(df["close"], n)), columns=["ema"])
    return new_df


def EMA2(df, n):
    """线性加权移动平均 WMA"""
    new_df = pd.DataFrame(data=list(ta_func.ema2(df["close"], n)), columns=["ema2"])
    return new_df


def TRMA(df, n):
    """三角移动平均线"""
    new_df = pd.DataFrame(data=list(ta_func.trma(df["close"], n)), columns=["trma"])
    return new_df
