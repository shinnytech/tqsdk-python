#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

import json
from datetime import datetime
from tqsdk import TqApi, TqBacktest


def test_get_quote_normal_backtest():
    """
    回测获取行情报价

    """
    # 获取行情
    api = TqApi(backtest=TqBacktest(datetime(2019, 10, 15), datetime(2019, 10, 16)),
                _ins_url="https://openmd.shinnytech.com/t/md/symbols/2019-07-03.json")
    quote = api.get_quote("SHFE.cu2001")
    quote_data = {k: v for k, v in quote.items()}
    quote_data["trading_time"] = {k: v for k, v in quote_data["trading_time"].items()}

    assert json.dumps(quote_data, sort_keys=True) == \
           '{"amount": NaN, "ask_price1": 47070.0, "ask_price2": NaN, "ask_price3": NaN, "ask_price4": NaN, "ask_price5": NaN, "ask_volume1": 1, "ask_volume2": 0, "ask_volume3": 0, "ask_volume4": 0, "ask_volume5": 0, "average": NaN, "bid_price1": 47050.0, "bid_price2": NaN, "bid_price3": NaN, "bid_price4": NaN, "bid_price5": NaN, "bid_volume1": 1, "bid_volume2": 0, "bid_volume3": 0, "bid_volume4": 0, "bid_volume5": 0, "close": NaN, "commission": 11.594999999999999, "datetime": "2019-10-14 23:59:59.999999", "delivery_month": 1, "delivery_year": 2020, "expire_datetime": 1579071600.0, "expired": false, "highest": NaN, "ins_class": "FUTURE", "instrument_id": "SHFE.cu2001", "last_price": 47060.0, "lower_limit": NaN, "lowest": NaN, "margin": 16233.000000000002, "max_limit_order_volume": 500, "max_market_order_volume": 0, "min_limit_order_volume": 0, "min_market_order_volume": 0, "open": NaN, "open_interest": 45357, "pre_close": NaN, "pre_open_interest": 0, "pre_settlement": NaN, "price_decs": 0, "price_tick": 10, "settlement": NaN, "strike_price": NaN, "trading_time": {"day": [["09:00:00", "10:15:00"], ["10:30:00", "11:30:00"], ["13:30:00", "15:00:00"]], "night": [["21:00:00", "25:00:00"]]}, "underlying_symbol": "", "upper_limit": NaN, "volume": 0, "volume_multiple": 5}'

    # 其他取值方式
    assert quote["pre_close"] != quote.pre_close
    assert quote.get("pre_settlement") != quote.pre_settlement
    assert quote.get("highest") != quote.highest
    assert quote.get("lowest") != quote.lowest
    assert quote["open"] != quote.open
    assert quote["close"] != quote.close
    api.close()
