"""
t90.py - 本示例程序演示如何用程序在天勤的行情图上绘图
"""

import numpy as np
from tqsdk import TqApi

api = TqApi()

# 获取 cu1905 和 cu1906 的日线数据
klines = api.get_kline_serial("SHFE.cu1905", 86400)
klines2 = api.get_kline_serial("SHFE.cu1906", 86400)

# 算出 cu1906 - cu1905 的价差，并以折线型态显示在副图
klines["dif"] = klines2["close"] - klines["close"]
klines["dif.board"] = "DIF"
klines["dif.color"] = 0xFF00FF00
klines["dif.width"] = 3

# 在附图画出 cu1906 的K线
klines["cu1906.open"] = klines2["open"]
klines["cu1906.high"] = klines2["high"]
klines["cu1906.low"] = klines2["low"]
klines["cu1906.close"] = klines2["close"]
klines["cu1906.board"] = "B2"

# 给主图最后5根K线加一个方框
klines["sig.type"] = np.empty(len(klines), dtype=object)
klines["sig.x1"] = np.empty(len(klines))
klines["sig.x2"] = np.empty(len(klines))
klines["sig.y1"] = np.empty(len(klines))
klines["sig.y2"] = np.empty(len(klines))
klines["sig.color"] = np.full(len(klines), 0xFF0000FF)
klines["sig.bg_color"] = np.full(len(klines), 0x8000FF00)
klines.loc[klines.index[-1], ("sig.type", "sig.x1", "sig.x2", "sig.y1", "sig.y2")] = ("DRAW_BOX", klines["id"].iloc[-5], klines["id"].iloc[-1], klines["close"].iloc[-5], klines["close"].iloc[-1])

# 在主图最近K线的最低处标一个"最低"文字
is_lowest = klines["low"] == klines["low"].min()
klines["lowest"] = np.where(is_lowest, "测试413423", None)
klines["lowest.type"] = np.where(is_lowest, "TEXT", None)
klines["lowest.y"] = np.where(is_lowest, klines["low"], np.nan)
klines["lowest.color"] = np.where(is_lowest, 0xFF00FF00, 0)

api.close()
