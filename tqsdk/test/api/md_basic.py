#!/usr/bin/env python
#  -*- coding: utf-8 -*-
import random
import unittest
import time
from tqsdk.test.api.helper import MockInsServer, MockServer
from tqsdk import TqApi


class TestMdBasic(unittest.TestCase):
    """
    行情部分基本功能测试.

    测试TqApi行情相关函数, 以及TqApi与行情服务器交互是否符合设计预期
    """

    def setUp(self):
        self.ins = MockInsServer(5000)
        self.mock = MockServer()
        # self.tq = WebsocketServer(5300)
        self.ins_url = "https://openmd.shinnytech.com/t/md/symbols/2019-07-03.json"
        self.md_url = "ws://127.0.0.1:5100/"
        self.td_url = "ws://127.0.0.1:5200/"

    def tearDown(self):

        self.ins.close()
        self.mock.close()

    # 获取行情测试

    # @unittest.skip("无条件跳过")
    def test_get_quote_normal(self):
        """
        获取行情报价

        """
        # 预设服务器端响应
        self.mock.run("test_md_basic_get_quote_normal.script")
        # 获取行情
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        q = api.get_quote("SHFE.cu1901")
        self.assertEqual(str(q),
                         "{'datetime': '2019-01-15 14:59:59.999500', 'ask_price1': 47000.0, 'ask_volume1': 10, 'bid_price1': 46800.0, 'bid_volume1': 20, 'last_price': 46940.0, 'highest': 47060.0, 'lowest': 46700.0, 'open': 46750.0, 'close': 46940.0, 'average': 46888.1, 'volume': 3210, 'amount': 752554000.0, 'open_interest': 2150, 'settlement': 46880.0, 'upper_limit': 49350.0, 'lower_limit': 44650.0, 'pre_open_interest': 4100, 'pre_settlement': 47000.0, 'pre_close': 46850.0, 'price_tick': 10, 'price_decs': 0, 'volume_multiple': 5, 'max_limit_order_volume': 500, 'max_market_order_volume': 0, 'min_limit_order_volume': 0, 'min_market_order_volume': 0, 'underlying_symbol': '', 'strike_price': nan, 'change': nan, 'change_percent': nan, 'expired': True, 'margin': 16233.000000000002, 'commission': 11.594999999999999, 'instrument_id': 'SHFE.cu1901'}")
        self.assertEqual(q.datetime, "2019-01-15 14:59:59.999500")
        self.assertEqual(q.ask_price1, 47000.0)
        self.assertEqual(q.ask_volume1, 10)
        self.assertEqual(q.bid_price1, 46800.0)
        self.assertEqual(q.bid_volume1, 20)
        self.assertEqual(q.last_price, 46940.0)
        self.assertEqual(q.highest, 47060.0)
        self.assertEqual(q.lowest, 46700.0)
        self.assertEqual(q.open, 46750.0)
        self.assertEqual(q.close, 46940.0)
        self.assertEqual(q.average, 46888.1)
        self.assertEqual(q.volume, 3210)
        self.assertEqual(q.amount, 752554000.0)
        self.assertEqual(q.open_interest, 2150)
        self.assertEqual(q.settlement, 46880.0)
        self.assertEqual(q.upper_limit, 49350.0)
        self.assertEqual(q.lower_limit, 44650)
        self.assertEqual(q.pre_open_interest, 4100)
        self.assertEqual(q.pre_settlement, 47000.0)
        self.assertEqual(q.pre_close, 46850.0)
        # 其他取值方式
        self.assertEqual(q["pre_close"], 46850.0)
        self.assertEqual(q.get("pre_settlement"), 47000.0)
        self.assertEqual(q.get("highest"), 47060.0)
        self.assertEqual(q.get("lowest"), 46700.0)
        self.assertEqual(q["open"], 46750.0)
        self.assertEqual(q["close"], 46940.0)
        # 报错测试
        self.assertRaises(Exception, api.get_quote, "SHFE.au1999")
        self.assertRaises(KeyError, q.__getitem__, "ask_price3")

        api.close()

    # @unittest.skip("无条件跳过")
    def test_get_kline_serial(self):
        """
        获取K线数据
        """
        # 预设服务器端响应
        self.mock.run("test_md_basic_get_kline_serial.script")

        # 测试: 获取K线数据
        TqApi.RD = random.Random(1)
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        klines = api.get_kline_serial("SHFE.cu1909", 10)
        self.assertEqual(klines.iloc[-1].close, 47260.0)
        self.assertEqual(klines.iloc[-1].id, 656648.0)
        self.assertEqual(klines.iloc[-2].id, 656647)
        self.assertEqual(klines.iloc[-1].datetime, 1.56818519e+18)
        self.assertEqual(klines.iloc[-1].open, 47260.0)
        self.assertEqual(klines.iloc[-1].volume, 0.0)
        self.assertEqual(klines.iloc[-1].open_oi, 27380.0)
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

    # @unittest.skip("无条件跳过")
    def test_get_tick_serial(self):
        """
        获取tick数据
        """
        # 预设服务器端响应
        self.mock.run("test_md_basic_get_tick_serial.script")

        # 测试: 获取tick数据
        TqApi.RD = random.Random(2)
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        ticks = api.get_tick_serial("SHFE.cu1909")
        self.assertEqual(ticks.iloc[-1].id, 2820074.0)
        self.assertEqual(ticks.iloc[-1].datetime, 1.5682567835e+18)
        self.assertEqual(ticks.iloc[-1].last_price, 47300.0)
        self.assertEqual(ticks.iloc[-1].average, 47225.7656)
        self.assertEqual(ticks.iloc[-1].highest, 47300)
        self.assertEqual(ticks.iloc[-1].lowest, 47050)
        self.assertEqual(ticks.iloc[-1].ask_price1, 47360)
        self.assertEqual(ticks.iloc[-1].ask_volume1, 25)
        self.assertEqual(ticks.iloc[-1].bid_price1, 47300)
        self.assertEqual(ticks.iloc[-1].bid_volume1, 30)
        self.assertEqual(ticks.iloc[-1].volume, 11520)
        self.assertEqual(ticks.iloc[-1].amount, 2720204000.0)
        self.assertEqual(ticks.iloc[-1].open_interest, 20670.0)
        self.assertEqual(ticks.iloc[-1].duration, 0)
        # 其他调用方式
        self.assertEqual(ticks.open_interest.iloc[-1], 20670.0)
        self.assertEqual(ticks["open_interest"].iloc[-2], 20670.0)
        self.assertEqual(ticks.iloc[-1]["ask_price1"], 47360.0)
        # 报错测试
        self.assertRaises(Exception, api.get_tick_serial, "SHFE.au1999")
        self.assertRaises(AttributeError, ticks.iloc[-1].__getattribute__, "dur")
        self.assertRaises(KeyError, ticks.iloc[-1].__getitem__, "dur")

        api.close()

    # 模拟交易测试

    @unittest.skip("无条件跳过")
    def test_insert_order(self):
        """
        下单
        """
        # 预设服务器端响应
        self.mock.run("test_td_basic_insert_order_simulate.script")
        # 测试: 模拟账户下单
        TqApi.RD = random.Random(2)
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url, debug="testttt.log")
        order1 = api.insert_order("DCE.jd2001", "BUY", "OPEN", 1)
        order2 = api.insert_order("SHFE.cu2001", "BUY", "OPEN", 2, limit_price=47550)

        while order1.status == "ALIVE" or order2.status == "ALIVE":
            api.wait_update()

        self.assertEqual(order1.order_id, "d95bafc8f2a4d27bdcf4bb99f4bea973")
        self.assertEqual(order1.direction, "BUY")
        self.assertEqual(order1.offset, "OPEN")
        self.assertEqual(order1.volume_orign, 1)
        self.assertEqual(order1.volume_left, 0)
        self.assertEqual(order1.limit_price != order1.limit_price, True)  # 判断nan
        self.assertEqual(order1.price_type, "ANY")
        self.assertEqual(order1.volume_condition, "ANY")
        self.assertEqual(order1.insert_date_time, 631123200000000000)
        self.assertEqual(order1.status, "FINISHED")
        for k, v in order1.trade_records.items():  # 模拟交易为一次性全部成交
            self.assertEqual(str(v),
                             "{'order_id': 'd95bafc8f2a4d27bdcf4bb99f4bea973', 'trade_id': 'd95bafc8f2a4d27bdcf4bb99f4bea973|1', 'exchange_trade_id': 'd95bafc8f2a4d27bdcf4bb99f4bea973|1', 'exchange_id': 'DCE', 'instrument_id': 'jd2001', 'direction': 'BUY', 'offset': 'OPEN', 'price': 4439.0, 'volume': 1, 'trade_date_time': 1568271599999500000, 'symbol': 'DCE.jd2001', 'user_id': 'TQSIM', 'commission': 6.122999999999999}")

        self.assertEqual(order2.order_id, "5c6e433715ba2bdd177219d30e7a269f")
        self.assertEqual(order2.direction, "BUY")
        self.assertEqual(order2.offset, "OPEN")
        self.assertEqual(order2.volume_orign, 2)
        self.assertEqual(order2.volume_left, 0)
        self.assertEqual(order2.limit_price, 47550.0)
        self.assertEqual(order2.price_type, "LIMIT")
        self.assertEqual(order2.volume_condition, "ANY")
        self.assertEqual(order2.insert_date_time, 631123200000000000)
        self.assertEqual(order2.status, "FINISHED")
        for k, v in order2.trade_records.items():  # 模拟交易为一次性全部成交
            self.assertEqual(str(v),
                             "{'order_id': '5c6e433715ba2bdd177219d30e7a269f', 'trade_id': '5c6e433715ba2bdd177219d30e7a269f|2', 'exchange_trade_id': '5c6e433715ba2bdd177219d30e7a269f|2', 'exchange_id': 'SHFE', 'instrument_id': 'cu2001', 'direction': 'BUY', 'offset': 'OPEN', 'price': 47550.0, 'volume': 2, 'trade_date_time': 1568271599999500000, 'symbol': 'SHFE.cu2001', 'user_id': 'TQSIM', 'commission': 23.189999999999998}")

        api.close()

    # @unittest.skip("无条件跳过")
    def test_cancel_order(self):
        """
        撤单
        """
        # 预设服务器端响应
        self.mock.run("test_td_basic_cancel_order_simulate.script")
        # 测试: 模拟账户
        TqApi.RD = random.Random(2)
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)

        order1 = api.insert_order("DCE.jd2001", "BUY", "OPEN", 1, limit_price=4560)
        order2 = api.insert_order("SHFE.cu2001", "BUY", "OPEN", 2, limit_price=47600)
        api.wait_update()

        self.assertEqual("ALIVE", order1.status)
        self.assertEqual("ALIVE", order2.status)

        api.cancel_order(order1)
        api.cancel_order(order2.order_id)
        api.wait_update()

        self.assertEqual("FINISHED", order1.status)
        self.assertEqual("FINISHED", order2.status)

        api.close()

    # @unittest.skip("无条件跳过")
    def test_get_account(self):
        """
        获取账户资金信息
        """
        # 预设服务器端响应
        self.mock.run("test_td_basic_get_account.script")
        # 测试: 获取数据
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        account = api.get_account()

        self.assertEqual(str(account),
                         "{'currency': 'CNY', 'pre_balance': 10000000.0, 'static_balance': 10000000.0, 'balance': 10000000.0, 'available': 10000000.0, 'float_profit': 0.0, 'position_profit': 0.0, 'close_profit': 0.0, 'frozen_margin': 0.0, 'margin': 0.0, 'frozen_commission': 0.0, 'commission': 0.0, 'frozen_premium': 0.0, 'premium': 0.0, 'deposit': 0.0, 'withdraw': 0.0, 'risk_ratio': 0.0}")
        self.assertEqual(account.currency, "CNY")
        self.assertEqual(account.pre_balance, 10000000.0)
        self.assertEqual(10000000.0, account.balance)
        self.assertEqual(0.0, account["commission"])
        self.assertEqual(0.0, account["margin"])
        self.assertEqual(0.0, account.position_profit)
        api.close()

    # @unittest.skip("无条件跳过")
    def test_get_position(self):
        """
        获取持仓
        """
        # 预设服务器端响应
        self.mock.run("test_td_basic_get_position.script")
        # 测试: 获取数据
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        order1 = api.insert_order("DCE.jd2001", "BUY", "OPEN", 1, limit_price=4592)
        order2 = api.insert_order("DCE.jd2001", "BUY", "OPEN", 3)
        order3 = api.insert_order("DCE.jd2001", "SELL", "OPEN", 3)

        while order1.status == "ALIVE" or order2.status == "ALIVE" or order3.status == "ALIVE":
            api.wait_update()
        position = api.get_position("DCE.jd2001")
        self.assertEqual(
            "{'exchange_id': 'DCE', 'instrument_id': 'jd2001', 'pos_long_his': 0, 'pos_long_today': 4, 'pos_short_his': 0, 'pos_short_today': 3, 'volume_long_today': 4, 'volume_long_his': 0, 'volume_long': 4, 'volume_long_frozen_today': 0, 'volume_long_frozen_his': 0, 'volume_long_frozen': 0, 'volume_short_today': 3, 'volume_short_his': 0, 'volume_short': 3, 'volume_short_frozen_today': 0, 'volume_short_frozen_his': 0, 'volume_short_frozen': 0, 'open_price_long': 4592.0, 'open_price_short': 4591.0, 'open_cost_long': 183680.0, 'open_cost_short': 137730.0, 'position_price_long': 4592.0, 'position_price_short': 4591.0, 'position_cost_long': 183680.0, 'position_cost_short': 137730.0, 'float_profit_long': 0.0, 'float_profit_short': -30.0, 'float_profit': -30.0, 'position_profit_long': 0.0, 'position_profit_short': -30.0, 'position_profit': -30.0, 'margin_long': 11429.6, 'margin_short': 8572.2, 'margin': 20001.800000000003, 'symbol': 'DCE.jd2001', 'last_price': 4592.0}",
            str(position))

        self.assertEqual(1, position.pos)
        self.assertEqual(4, position.pos_long)
        self.assertEqual(3, position.pos_short)
        self.assertEqual(position.exchange_id, "DCE")
        self.assertEqual(position.instrument_id, "jd2001")
        self.assertEqual(position.pos_long_his, 0)
        self.assertEqual(position.pos_long_today, 4)
        self.assertEqual(position.pos_short_his, 0)
        self.assertEqual(position.pos_short_today, 3)
        self.assertEqual(position.volume_long_today, 4)
        self.assertEqual(position.volume_long_his, 0)
        self.assertEqual(position.volume_long, 4)
        self.assertEqual(position.volume_long_frozen_today, 0)
        self.assertEqual(position.volume_long_frozen_his, 0)
        self.assertEqual(position.volume_long_frozen, 0)
        self.assertEqual(position.volume_short_today, 3)
        self.assertEqual(position.volume_short_his, 0)
        self.assertEqual(position.volume_short, 3)
        self.assertEqual(position.volume_short_frozen_today, 0)
        self.assertEqual(position.volume_short_frozen_his, 0)
        self.assertEqual(position.volume_short_frozen, 0)
        self.assertEqual(position.open_price_long, 4592.0)
        self.assertEqual(position.open_price_short, 4591.0)
        self.assertEqual(position.open_cost_long, 183680.0)
        self.assertEqual(position.open_cost_short, 137730.0)
        self.assertEqual(position.position_price_long, 4592.0)
        self.assertEqual(position.position_price_short, 4591.0)
        self.assertEqual(position.position_cost_long, 183680.0)
        self.assertEqual(position.position_cost_short, 137730.0)
        self.assertEqual(position.float_profit_long, 0.0)
        self.assertEqual(position.float_profit_short, -30.0)
        self.assertEqual(position.float_profit, -30.0)
        self.assertEqual(position.position_profit_long, 0.0)
        self.assertEqual(position.position_profit_short, -30.0)
        self.assertEqual(position.position_profit, -30.0)
        self.assertEqual(position.margin_long, 11429.6)
        self.assertEqual(position.margin_short, 8572.2)
        self.assertEqual(position.margin, 20001.800000000003)
        self.assertEqual(position.symbol, "DCE.jd2001")
        self.assertEqual(position.last_price, 4592.0)

        # 其他取值方式测试
        self.assertEqual(position["pos_long_today"], 4)
        self.assertEqual(position["pos_short_today"], 3)
        self.assertEqual(position["volume_long_his"], 0)
        self.assertEqual(position["volume_long"], 4)

        api.close()

    @unittest.skip("无条件跳过")
    def test_get_trade(self):
        # 预设服务器端响应
        self.mock.run("test_td_basic_get_trade_simulate.script")
        # 测试: 模拟账户
        TqApi.RD = random.Random(4)
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        order1 = api.insert_order("DCE.jd2001", "BUY", "OPEN", 1)
        order2 = api.insert_order("SHFE.cu2001", "BUY", "OPEN", 2, limit_price=47550)
        while order1.status == "ALIVE" or order2.status == "ALIVE":
            api.wait_update()

        trade1 = api.get_trade("b8a1abcd1a6916c74da4f9fc3c6da5d7|1")
        trade2 = api.get_trade("1710cf5327ac435a7a97c643656412a9|2")

        self.assertEqual(str(trade1),
                         "{'order_id': 'b8a1abcd1a6916c74da4f9fc3c6da5d7', 'trade_id': 'b8a1abcd1a6916c74da4f9fc3c6da5d7|1', 'exchange_trade_id': 'b8a1abcd1a6916c74da4f9fc3c6da5d7|1', 'exchange_id': 'DCE', 'instrument_id': 'jd2001', 'direction': 'BUY', 'offset': 'OPEN', 'price': 4583.0, 'volume': 1, 'trade_date_time': 1568703599999500000, 'symbol': 'DCE.jd2001', 'user_id': 'TQSIM', 'commission': 6.122999999999999}")
        self.assertEqual(str(trade2),
                         "{'order_id': '1710cf5327ac435a7a97c643656412a9', 'trade_id': '1710cf5327ac435a7a97c643656412a9|2', 'exchange_trade_id': '1710cf5327ac435a7a97c643656412a9|2', 'exchange_id': 'SHFE', 'instrument_id': 'cu2001', 'direction': 'BUY', 'offset': 'OPEN', 'price': 47550.0, 'volume': 2, 'trade_date_time': 1568703599999500000, 'symbol': 'SHFE.cu2001', 'user_id': 'TQSIM', 'commission': 23.189999999999998}")
        self.assertEqual(trade1.direction, "BUY")
        self.assertEqual(trade1.offset, "OPEN")
        self.assertEqual(trade1.price, 4583.0)
        self.assertEqual(trade1.volume, 1)
        self.assertEqual(trade1.trade_date_time, 1568703599999500000)
        self.assertEqual(trade1.commission, 6.122999999999999)

        self.assertEqual(trade2.direction, "BUY")
        self.assertEqual(trade2.offset, "OPEN")
        self.assertEqual(trade2.price, 47550.0)
        self.assertEqual(trade2.volume, 2)
        self.assertEqual(trade2.trade_date_time, 1568703599999500000)
        self.assertEqual(trade2.commission, 23.189999999999998)

        api.close()

    # @unittest.skip("无条件跳过")
    def test_get_order(self):
        # 预设服务器端响应
        self.mock.run("test_td_basic_get_order_simulate.script")
        # 测试: 模拟账户下单
        TqApi.RD = random.Random(4)
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        order1 = api.insert_order("DCE.jd2001", "BUY", "OPEN", 1)
        order2 = api.insert_order("SHFE.cu2001", "SELL", "OPEN", 2, limit_price=47340)
        while order1.status == "ALIVE" or order2.status == "ALIVE":
            api.wait_update()

        orders = api.get_order()
        get_order1 = api.get_order(order1.order_id)
        get_order2 = api.get_order(order2.order_id)

        self.assertEqual(str(get_order1),
                         "{'order_id': 'b8a1abcd1a6916c74da4f9fc3c6da5d7', 'exchange_order_id': 'b8a1abcd1a6916c74da4f9fc3c6da5d7', 'exchange_id': 'DCE', 'instrument_id': 'jd2001', 'direction': 'BUY', 'offset': 'OPEN', 'volume_orign': 1, 'volume_left': 0, 'limit_price': nan, 'price_type': 'ANY', 'volume_condition': 'ANY', 'time_condition': 'IOC', 'insert_date_time': 631123200000000000, 'last_msg': '全部成交', 'status': 'FINISHED', 'user_id': 'TQSIM', 'symbol': 'DCE.jd2001', 'frozen_margin': 0.0}")
        self.assertEqual(str(get_order2),
                         "{'order_id': '1710cf5327ac435a7a97c643656412a9', 'exchange_order_id': '1710cf5327ac435a7a97c643656412a9', 'exchange_id': 'SHFE', 'instrument_id': 'cu2001', 'direction': 'SELL', 'offset': 'OPEN', 'volume_orign': 2, 'volume_left': 0, 'limit_price': 47340.0, 'price_type': 'LIMIT', 'volume_condition': 'ANY', 'time_condition': 'GFD', 'insert_date_time': 631123200000000000, 'last_msg': '全部成交', 'status': 'FINISHED', 'user_id': 'TQSIM', 'symbol': 'SHFE.cu2001', 'frozen_margin': 0.0}")

        self.assertEqual(get_order1.order_id, "b8a1abcd1a6916c74da4f9fc3c6da5d7")
        self.assertEqual(get_order1.direction, "BUY")
        self.assertEqual(get_order1.offset, "OPEN")
        self.assertEqual(get_order1.volume_orign, 1)
        self.assertEqual(get_order1.volume_left, 0)
        self.assertEqual(get_order1.limit_price != get_order1.limit_price, True)  # 判断nan
        self.assertEqual(get_order1.price_type, "ANY")
        self.assertEqual(get_order1.volume_condition, "ANY")
        self.assertEqual(get_order1.time_condition, "IOC")
        self.assertEqual(get_order1.insert_date_time, 631123200000000000)
        self.assertEqual(get_order1.last_msg, "全部成交")
        self.assertEqual(get_order1.status, "FINISHED")
        self.assertEqual(get_order1.symbol, "DCE.jd2001")
        self.assertEqual(get_order1.frozen_margin, 0)

        self.assertEqual(get_order2.order_id, "1710cf5327ac435a7a97c643656412a9")
        self.assertEqual(get_order2.direction, "SELL")
        self.assertEqual(get_order2.offset, "OPEN")
        self.assertEqual(get_order2.volume_orign, 2)
        self.assertEqual(get_order2.volume_left, 0)
        self.assertEqual(get_order2.limit_price, 47340)  # 判断nan
        self.assertEqual(get_order2.price_type, "LIMIT")
        self.assertEqual(get_order2.volume_condition, "ANY")
        self.assertEqual(get_order2.time_condition, "GFD")
        self.assertEqual(get_order2["insert_date_time"], 631123200000000000)
        self.assertEqual(get_order2["last_msg"], "全部成交")
        self.assertEqual(get_order2["status"], "FINISHED")
        self.assertEqual(get_order2.symbol, "SHFE.cu2001")
        self.assertEqual(get_order2.frozen_margin, 0)

        api.close()

    @unittest.skip("无条件跳过")
    def test_is_changing(self):
        # 预设服务器端响应
        self.mock.run("test_func_basic_is_changing.script")
        # 测试: 模拟账户下单
        TqApi.RD = random.Random(4)
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        quote = api.get_quote("SHFE.rb2001")
        position = api.get_position("SHFE.rb2001")
        order1 = api.insert_order("DCE.m2001", "BUY", "OPEN", 1)
        api.wait_update()
        order2 = api.insert_order("SHFE.rb2001", "SELL", "OPEN", 2)
        api.wait_update()
        self.assertEqual(api.is_changing(order2, "status"), True)
        self.assertEqual(api.is_changing(position, "volume_short"), True)
        self.assertEqual(api.is_changing(position, "volume_long"), False)
        order3 = api.insert_order("SHFE.rb2001", "BUY", "CLOSETODAY", 1)
        while order3.status == "ALIVE":
            api.wait_update()
        self.assertEqual(api.is_changing(order3, "status"), True)
        self.assertEqual(api.is_changing(position, "volume_short"), True)

        self.assertEqual(api.is_changing(quote, "last_price"), False)
        api.wait_update()
        self.assertEqual(api.is_changing(quote, "last_price"), True)
