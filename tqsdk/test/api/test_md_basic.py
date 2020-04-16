#!/usr/bin/env python
#  -*- coding: utf-8 -*-
import json
import os
import random
import unittest
from datetime import datetime
from tqsdk.test.api.helper import MockInsServer, MockServer
from tqsdk import TqApi, TqBacktest


class TestMdBasic(unittest.TestCase):
    """
    测试TqApi行情相关函数基本功能, 以及TqApi与行情服务器交互是否符合设计预期

    注：
    1. 在本地运行测试用例前需设置运行环境变量(Environment variables), 保证api中dict及set等类型的数据序列在每次运行时元素顺序一致: PYTHONHASHSEED=32
    2. 若测试用例中调用了会使用uuid的功能函数时（如insert_order()会使用uuid生成order_id）,
        则：在生成script文件时及测试用例中都需设置 TqApi.RD = random.Random(x), 以保证两次生成的uuid一致, x取值范围为0-2^32
    3. 對盤中的測試用例（即非回測）：因为TqSim模拟交易 Order 的 insert_date_time 和 Trade 的 trade_date_time 不是固定值，所以改为判断范围。
        盘中时：self.assertAlmostEqual(1575292560005832000 / 1e9, order1.insert_date_time / 1e9, places=1)
        回测时：self.assertEqual(1575291600000000000, order1.insert_date_time)
    """

    def setUp(self):
        # self.ins = MockInsServer(5000)
        self.mock = MockServer()
        # self.tq = WebsocketServer(5300)
        self.ins_url_2019_07_03 = "https://openmd.shinnytech.com/t/md/symbols/2019-07-03.json"
        self.md_url = "ws://127.0.0.1:5100/"
        self.td_url = "ws://127.0.0.1:5200/"

    def tearDown(self):
        # self.ins.close()
        self.mock.close()

    # 获取行情测试

    # @unittest.skip("无条件跳过")
    def test_get_quote_normal(self):
        """
        获取行情报价

        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_md_basic_get_quote_normal.script.lzma"))
        # 获取行情
        api = TqApi(_ins_url=self.ins_url_2019_07_03, _td_url=self.td_url, _md_url=self.md_url)
        q = api.get_quote("SHFE.cu1909")
        self.assertEqual(q.datetime, "2019-09-16 14:59:59.999500")
        self.assertEqual(q.ask_price1, 47650.0)
        self.assertEqual(q.ask_volume1, 10)
        self.assertEqual(q.bid_price1, 47570.0)
        self.assertEqual(q.bid_volume1, 5)
        self.assertEqual(q.last_price, 47580.0)
        self.assertEqual(q.highest, 47860.0)
        self.assertEqual(q.lowest, 47580.0)
        self.assertEqual(q.open, 47860.0)
        self.assertEqual(q.close, 47580.0)
        self.assertEqual(q.average, 47732.35)
        self.assertEqual(q.volume, 9020)
        self.assertEqual(q.amount, 2152729000.0)
        self.assertEqual(q.open_interest, 6940)
        self.assertEqual(q.settlement, 47730.0)
        self.assertEqual(q.upper_limit, 49650.0)
        self.assertEqual(q.lower_limit, 44920)
        self.assertEqual(q.pre_open_interest, 13260)
        self.assertEqual(q.pre_settlement, 47290.0)
        self.assertEqual(q.pre_close, 47590.0)
        self.assertEqual(q.price_tick, 10)
        self.assertEqual(q.price_decs, 0)
        self.assertEqual(q.volume_multiple, 5)
        self.assertEqual(q.max_limit_order_volume, 500)
        self.assertEqual(q.max_market_order_volume, 0)
        self.assertEqual(q.min_limit_order_volume, 0)
        self.assertEqual(q.min_market_order_volume, 0)
        self.assertEqual(q.underlying_symbol, "")
        self.assertTrue(q.strike_price != q.strike_price)  # 判定nan
        self.assertEqual(q.expired, False)
        self.assertEqual(q.ins_class, "FUTURE")
        self.assertEqual(q.margin, 16233.000000000002)
        self.assertEqual(q.commission, 11.594999999999999)
        self.assertEqual(repr(q.trading_time.day),
                         "[['09:00:00', '10:15:00'], ['10:30:00', '11:30:00'], ['13:30:00', '15:00:00']]")
        self.assertEqual(repr(q.trading_time.night), "[['21:00:00', '25:00:00']]")

        self.assertEqual(q.expire_datetime, 1568617200.0)
        self.assertEqual(q.delivery_month, 9)
        self.assertEqual(q.delivery_year, 2019)
        self.assertEqual(q.instrument_id, "SHFE.cu1909")
        self.assertEqual(q.ask_price2, 47730.0)
        self.assertEqual(q.ask_volume2, 10)
        self.assertEqual(q.ask_price3, 47990.0)
        self.assertEqual(q.ask_volume3, 5)
        self.assertEqual(q.ask_price4, 49250.0)
        self.assertEqual(q.ask_volume4, 50)
        self.assertEqual(q.ask_price5 != q.ask_price5, True)  # 判断nan
        self.assertEqual(q.ask_volume5, 0)
        self.assertEqual(q.bid_price2, 46560.0)
        self.assertEqual(q.bid_volume2, 100)
        self.assertEqual(q.bid_price3, 45650.0)
        self.assertEqual(q.bid_volume3, 270)
        self.assertEqual(q.bid_price4, 44920.0)
        self.assertEqual(q.bid_volume4, 5)
        self.assertEqual(q.bid_price5 != q.bid_price5, True)
        self.assertEqual(q.bid_volume5, 0)

        # 其他取值方式
        self.assertEqual(q["pre_close"], 47590.0)
        self.assertEqual(q.get("pre_settlement"), 47290.0)
        self.assertEqual(q.get("highest"), 47860.0)
        self.assertEqual(q.get("lowest"), 47580.0)
        self.assertEqual(q["open"], 47860.0)
        self.assertEqual(q["close"], 47580.0)
        # 报错测试
        self.assertRaises(Exception, api.get_quote, "SHFE.au1999")
        self.assertRaises(KeyError, q.__getitem__, "ask_price6")

        api.close()

    def test_get_kline_serial(self):
        """
        获取K线数据
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_md_basic_get_kline_serial.script.lzma"))

        # 测试: 获取K线数据
        TqApi.RD = random.Random(1)
        api = TqApi(_ins_url=self.ins_url_2019_07_03, _td_url=self.td_url, _md_url=self.md_url)
        klines = api.get_kline_serial("SHFE.cu1909", 10)
        self.assertEqual(klines.iloc[-1].close, 47580.0)
        self.assertEqual(klines.iloc[-1].id, 660788)
        self.assertEqual(klines.iloc[-2].id, 660787)
        self.assertEqual(klines.iloc[-1].datetime, 1.56861719e+18)
        self.assertEqual(klines.iloc[-1].open, 47580)
        self.assertEqual(klines.iloc[-1].volume, 0.0)
        self.assertEqual(klines.iloc[-1].open_oi, 6940.0)
        self.assertEqual(klines.iloc[-1].duration, 10)
        # 其他取值方式
        self.assertEqual(klines.duration.iloc[-1], 10)
        self.assertEqual(klines.iloc[-1]["duration"], 10)
        self.assertEqual(klines["duration"].iloc[-1], 10)
        # 报错测试
        self.assertRaises(Exception, api.get_kline_serial, "SHFE.au1999", 10)
        self.assertRaises(AttributeError, klines.iloc[-1].__getattribute__, "dur")
        self.assertRaises(KeyError, klines.iloc[-1].__getitem__, "dur")
        api.close()

    def test_get_tick_serial(self):
        """
        获取tick数据
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_md_basic_get_tick_serial.script.lzma"))

        # 测试: 获取tick数据
        TqApi.RD = random.Random(2)
        api = TqApi(_ins_url=self.ins_url_2019_07_03, _td_url=self.td_url, _md_url=self.md_url)
        ticks = api.get_tick_serial("SHFE.cu1909")
        self.assertEqual(ticks.iloc[-1].id, 2822951.0)
        self.assertEqual(ticks.iloc[-1].datetime, 1.5686171999995e+18)
        self.assertEqual(ticks.iloc[-1].last_price, 47580)
        self.assertEqual(ticks.iloc[-1].average, 47732.3516)
        self.assertEqual(ticks.iloc[-1].highest, 47860)
        self.assertEqual(ticks.iloc[-1].lowest, 47580)
        self.assertEqual(ticks.iloc[-1].ask_price1, 47650)
        self.assertEqual(ticks.iloc[-1].ask_volume1, 10)
        self.assertEqual(ticks.iloc[-1].bid_price1, 47570)
        self.assertEqual(ticks.iloc[-1].bid_volume1, 5)
        self.assertEqual(ticks.iloc[-1].volume, 9020)
        self.assertEqual(ticks.iloc[-1].amount, 2152729000.0)
        self.assertEqual(ticks.iloc[-1].open_interest, 6940)
        self.assertEqual(ticks.iloc[-1].duration, 0)
        # 其他调用方式
        self.assertEqual(ticks.open_interest.iloc[-1], 6940)
        self.assertEqual(ticks["open_interest"].iloc[-2], 6940)
        self.assertEqual(ticks.iloc[-1]["ask_price1"], 47650)
        # 报错测试
        self.assertRaises(Exception, api.get_tick_serial, "SHFE.au1999")
        self.assertRaises(AttributeError, ticks.iloc[-1].__getattribute__, "dur")
        self.assertRaises(KeyError, ticks.iloc[-1].__getitem__, "dur")

        api.close()
