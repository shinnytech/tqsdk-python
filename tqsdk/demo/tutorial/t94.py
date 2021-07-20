#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

from tqsdk import TqApi, TqAuth

'''
画图示例: 在附图中画K线
注意: 画图示例中用到的数据不含有实际意义，请根据自己的实际策略情况进行修改
'''

api = TqApi(web_gui=True, auth=TqAuth("信易账户", "账户密码"))
klines = api.get_kline_serial("SHFE.rb2104", 86400)
klines2 = api.get_kline_serial("SHFE.rb2105", 86400)

while True:
    # 将画图代码放在循环中即可使图像随着行情推进而更新
    # 在附图画出 rb2105 的K线: 需要将open、high、log、close的数据都设置正确
    klines["rb2105.open"] = klines2["open"]
    klines["rb2105.high"] = klines2["high"]
    klines["rb2105.low"] = klines2["low"]
    klines["rb2105.close"] = klines2["close"]
    klines["rb2105.board"] = "B2"
    api.wait_update()
