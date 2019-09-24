"""
t90.py - 本示例程序演示如何用程序在天勤的行情图上绘图
"""

from tqsdk import TqApi, TqSim

api = TqApi()

# 获取 cu1910 和 cu1911 的日线数据
klines = api.get_kline_serial("SHFE.cu1910", 86400)
klines2 = api.get_kline_serial("SHFE.cu1911", 86400)

# 算出 cu1911 - cu1910 的价差，并以折线型态显示在副图
klines["dif"] = klines2["close"] - klines["close"]
klines["dif.board"] = "DIF"
klines["dif.color"] = 0xFF00FF00
klines["dif.width"] = 3

# 在附图画出 cu1911 的K线
klines["cu1911.open"] = klines2["open"]
klines["cu1911.high"] = klines2["high"]
klines["cu1911.low"] = klines2["low"]
klines["cu1911.close"] = klines2["close"]
klines["cu1911.board"] = "B2"

# 给主图最后5根K线加一个方框
api.draw_box(klines, x1=-5, y1=klines.iloc[-5]["close"], x2=-1, y2=klines.iloc[-1]["close"], width=1, color=0xFF0000FF, bg_color=0x8000FF00)

# 在主图最后一根K线的最高处标一个"最高"文字
indic = -1
value = klines["high"].iloc[-1]
api.draw_text(klines, "最高", x=indic, y=value, color=0xFF00FF00)

api.close()
