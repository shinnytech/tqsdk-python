#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

import os
import unittest
import random
import datetime
from tqsdk import TqApi, TqBacktest, BacktestFinished
from tqsdk.test.api.helper import MockServer


class TestTdBacktest(unittest.TestCase):
    """
    回测时的交易测试.

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
        self.ins_url_2019_12_04 = "https://openmd.shinnytech.com/t/md/symbols/2019-12-04.json"
        self.ins_url_2020_02_18 = "https://openmd.shinnytech.com/t/md/symbols/2020-02-18.json"
        self.md_url = "ws://127.0.0.1:5100/"
        self.td_url = "ws://127.0.0.1:5200/"

    def tearDown(self):
        # self.ins.close()
        self.mock.close()

    def test_various_combinations_of_order_1(self):
        """
            测试 能在回测时正常使用开、平顺序的多种组合方式下单
            1 单次开平 * n次 (本测试函数)
            2 多次开 一次全平完
            3 多次开 分多次平完
            4 单次开 分多次平完

            related commit: a2623aed0fd1d5e5e01c7d2452e7f7f7de999c6e
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_various_combinations_of_order_1.script.lzma"))
        # 测试1：单次开平 * n次
        TqApi.RD = random.Random(4)
        api = TqApi(
            backtest=TqBacktest(start_dt=datetime.datetime(2019, 12, 10, 9), end_dt=datetime.datetime(2019, 12, 11)),
            _ins_url=self.ins_url_2019_07_03, _td_url=self.td_url, _md_url=self.md_url)
        symbol = "DCE.m2005"
        position = api.get_position(symbol)

        for i in range(3):
            order_open = api.insert_order(symbol, "BUY", "OPEN", 1)
            while order_open.status != "FINISHED":
                api.wait_update()
            self.assertEqual(position.pos, 1)
            order_close = api.insert_order(symbol, "SELL", "CLOSE", 1)
            while order_close.status != "FINISHED":
                api.wait_update()
            self.assertEqual(position.pos, 0)

        api.close()

    def test_various_combinations_of_order_2(self):
        """
            测试 能在回测时正常使用开、平顺序的多种组合方式下单
            1 单次开平 * n次
            2 多次开 一次全平完 (本测试函数)
            3 多次开 分多次平完
            4 单次开 分多次平完

            related commit: a2623aed0fd1d5e5e01c7d2452e7f7f7de999c6e
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_various_combinations_of_order_2.script.lzma"))
        # 测试2：多次开,一次全平完
        TqApi.RD = random.Random(4)
        api = TqApi(
            backtest=TqBacktest(start_dt=datetime.datetime(2019, 12, 10, 9), end_dt=datetime.datetime(2019, 12, 11)),
            _ins_url=self.ins_url_2019_07_03, _td_url=self.td_url, _md_url=self.md_url)
        symbol = "DCE.m2005"
        position = api.get_position(symbol)

        order_open1 = api.insert_order(symbol, "BUY", "OPEN", 1)
        order_open2 = api.insert_order(symbol, "BUY", "OPEN", 1)
        order_open3 = api.insert_order(symbol, "BUY", "OPEN", 1)
        while order_open1.status != "FINISHED" or order_open2.status != "FINISHED" or order_open3.status != "FINISHED":
            api.wait_update()
        self.assertEqual(position.pos, 3)

        order_close1 = api.insert_order(symbol, "SELL", "CLOSE", 3)
        while order_close1.status != "FINISHED":
            api.wait_update()
        self.assertEqual(position.pos, 0)

        api.close()

    def test_various_combinations_of_order_3(self):
        """
            测试 能在回测时正常使用开、平顺序的多种组合方式下单
            1 单次开平 * n次
            2 多次开 一次全平完
            3 多次开 分多次平完 (本测试函数)
            4 单次开 分多次平完

            related commit: a2623aed0fd1d5e5e01c7d2452e7f7f7de999c6e
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_various_combinations_of_order_3.script.lzma"))
        # 测试3：多次开 分多次平完
        TqApi.RD = random.Random(4)
        api = TqApi(
            backtest=TqBacktest(start_dt=datetime.datetime(2019, 12, 10, 9), end_dt=datetime.datetime(2019, 12, 11)),
            _ins_url=self.ins_url_2019_07_03, _td_url=self.td_url, _md_url=self.md_url)
        symbol = "DCE.m2005"
        position = api.get_position(symbol)

        t = 3
        for i in range(t):
            order_open = api.insert_order(symbol, "BUY", "OPEN", 1)
            while order_open.status != "FINISHED":
                api.wait_update()
            self.assertEqual(position.pos, i + 1)

        for i in range(t):
            order_close = api.insert_order(symbol, "SELL", "CLOSE", 1)
            while order_close.status != "FINISHED":
                api.wait_update()
            self.assertEqual(position.pos, t - 1 - i)

        api.close()

    def test_various_combinations_of_order_4(self):
        """
            测试 能在回测时正常使用开、平顺序的多种组合方式下单
            1 单次开平 * n次
            2 多次开 一次全平完
            3 多次开 分多次平完
            4 单次开 分多次平完 (本测试函数)

            related commit: a2623aed0fd1d5e5e01c7d2452e7f7f7de999c6e
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_various_combinations_of_order_4.script.lzma"))
        # 测试4：单次开 分多次平完
        TqApi.RD = random.Random(4)
        api = TqApi(
            backtest=TqBacktest(start_dt=datetime.datetime(2019, 12, 10, 9), end_dt=datetime.datetime(2019, 12, 11)),
            _ins_url=self.ins_url_2019_07_03, _td_url=self.td_url, _md_url=self.md_url)
        symbol = "DCE.m2005"
        position = api.get_position(symbol)
        trades = api.get_trade()

        order_open = api.insert_order(symbol, "BUY", "OPEN", 3)
        while order_open.status != "FINISHED":
            api.wait_update()
        self.assertEqual(position.pos, 3)
        for i in range(3):
            order_close = api.insert_order(symbol, "SELL", "CLOSE", 1)
            while order_close.status != "FINISHED":
                api.wait_update()

        self.assertEqual(len(trades), 4)
        self.assertEqual(position.pos, 0)

        api.close()

    def test_sim_insert_order_time_check_1(self):
        """
        模拟交易下单时间判断测试1

        测试时间段：
            2019.12.2(周一) 21:00 - 25:00
        订阅合约的条件:
            1. 无夜盘
            2. 有夜盘, 在23：00结束
            3. 有夜盘, 在25：00结束
        测试：
            1. 21：00起始时刻两个有夜盘合约下单，无夜盘合约不能下单；
            2. 在正常夜盘可下单时段两个有夜盘合约能下单,无夜盘合约不能成；
            3. 23：00某一夜盘合约停止交易后不能下单，另一有夜盘合约能下单；
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_sim_insert_order_time_check_1.script.lzma"))

        # 测试
        TqApi.RD = random.Random(4)
        api = TqApi(
            backtest=TqBacktest(datetime.datetime(2019, 12, 2, 21, 0, 0), datetime.datetime(2019, 12, 3, 1, 0, 0)),
            _ins_url=self.ins_url_2019_12_04, _td_url=self.td_url, _md_url=self.md_url)  # 2019.12.2周一
        symbol1 = "DCE.jd2002"  # 无夜盘
        symbol2 = "SHFE.rb2002"  # 夜盘23点结束
        symbol3 = "SHFE.cu2002"  # 夜盘凌晨1点结束
        quote1 = api.get_quote(symbol1)
        quote2 = api.get_quote(symbol2)
        quote3 = api.get_quote(symbol3)
        position1 = api.get_position(symbol1)
        position2 = api.get_position(symbol2)
        position3 = api.get_position(symbol3)
        try:
            # 1 回测起始时间(21:00:00)下单
            order1 = api.insert_order(symbol=symbol1, direction="BUY", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.order_id, "8534f45738d048ec0f1099c6c3e1b258")
            self.assertEqual(order1.direction, 'BUY')
            self.assertEqual(order1.offset, 'OPEN')
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 1)
            self.assertEqual(order1.limit_price, 3963.0)
            self.assertEqual(order1.price_type, 'LIMIT')
            self.assertEqual(order1.volume_condition, 'ANY')
            self.assertEqual(order1.time_condition, 'GFD')
            self.assertEqual(1575291600000000000, order1.insert_date_time)

            self.assertEqual(order2.order_id, "c79d679346d4ac7a5c3902b38963dc6e")
            self.assertEqual(order2.direction, 'BUY')
            self.assertEqual(order2.offset, 'OPEN')
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order2.limit_price, 3522.0)
            self.assertEqual(order2.price_type, 'LIMIT')
            self.assertEqual(order2.volume_condition, 'ANY')
            self.assertEqual(order2.time_condition, 'GFD')
            self.assertEqual(1575291600000000000, order2.insert_date_time)
            self.assertEqual(order3.order_id, "43000de01b2ed40ed3addccb2c33be0a")
            self.assertEqual(order3.direction, 'BUY')
            self.assertEqual(order3.offset, 'OPEN')
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(order3.limit_price, 47390.0)
            self.assertEqual(order3.price_type, 'LIMIT')
            self.assertEqual(order3.volume_condition, 'ANY')
            self.assertEqual(order3.time_condition, 'GFD')
            self.assertEqual(1575291600000000000, order3.insert_date_time)

            # 2 正常夜盘时间下单
            while datetime.datetime.strptime(quote3.datetime, "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime(2019, 12, 2,
                                                                                                          21, 15):
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="BUY", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 1)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(1575292559999999000, order1.insert_date_time)
            self.assertEqual(1575292559999999000, order2.insert_date_time)
            self.assertEqual(1575292559999999000, order3.insert_date_time)

            # 3 23：00rb2002停止交易后不能下单，cu2002能下单；
            while datetime.datetime.strptime(quote3.datetime, "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime(2019, 12, 2,
                                                                                                          23, 0, 0):
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="BUY", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 1)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 2)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(1575298859999999000, order1.insert_date_time)
            self.assertEqual(1575298859999999000, order2.insert_date_time)
            self.assertEqual(1575298859999999000, order3.insert_date_time)

            while True:
                api.wait_update()
        except BacktestFinished:
            self.assertEqual(position1.pos, 0)
            self.assertEqual(position2.pos, 4)
            self.assertEqual(position3.pos, 9)
            api.close()

    def test_sim_insert_order_time_check_2(self):
        """
        模拟交易下单时间判断测试2

        测试时间段：
            2020.2.17(周一) 10:15 - 10:45
        订阅合约的条件:
            IF、T（无盘中休息时间）,cu（有盘中休息时间）
        测试：
            1. 10:15 - 10:30期间 IF和T能下单，cu不能下单
            2. 10:15 - 10:30之间 IF、T能下单
            3. 10:30 - 10:45之间 IF、T、cu都能下单
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_sim_insert_order_time_check_2.script.lzma"))
        # 测试
        TqApi.RD = random.Random(4)
        api = TqApi(
            backtest=TqBacktest(datetime.datetime(2020, 2, 17, 10, 15, 0), datetime.datetime(2020, 2, 17, 10, 45, 0)),
            _ins_url=self.ins_url_2020_02_18, _td_url=self.td_url, _md_url=self.md_url)
        symbol1 = "SHFE.cu2003"
        symbol2 = "CFFEX.T2003"
        symbol3 = "CFFEX.IF2003"
        quote1 = api.get_quote(symbol1)
        quote2 = api.get_quote(symbol2)
        quote3 = api.get_quote(symbol3)
        position1 = api.get_position(symbol1)
        position2 = api.get_position(symbol2)
        position3 = api.get_position(symbol3)
        try:
            # 1 10:15 - 10:30期间IF和T能下单，cu不能下单
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 1)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(1581905700000000000, order1.insert_date_time)
            self.assertEqual(1581905700000000000, order2.insert_date_time)
            self.assertEqual(1581905700000000000, order3.insert_date_time)

            # 2 10:15 - 10:30之间 IF、T能下单；
            while datetime.datetime.strptime(quote3.datetime, "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime(2020, 2, 17,
                                                                                                          10, 20):
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="BUY", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 1)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(1581906059999999000, order1.insert_date_time)
            self.assertEqual(1581906059999999000, order2.insert_date_time)
            self.assertEqual(1581906059999999000, order3.insert_date_time)

            # 3 10:30 - 10:45之间 IF、T、cu都能下单；
            while datetime.datetime.strptime(quote3.datetime, "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime(2020, 2, 17,
                                                                                                          10, 30):
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="BUY", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 0)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(1581906659999999000, order1.insert_date_time)
            self.assertEqual(1581906659999999000, order2.insert_date_time)
            self.assertEqual(1581906659999999000, order3.insert_date_time)

            while True:
                api.wait_update()
        except BacktestFinished:
            self.assertEqual(position1.pos, 1)
            self.assertEqual(position2.pos, 6)
            self.assertEqual(position3.pos, 9)
            api.close()

    def test_sim_insert_order_time_check_3(self):
        """
        模拟交易下单时间判断测试3

        测试时间段：
            2020.2.17(周一) 10:29:29 - 15:18
        订阅合约条件：
            IF、T（无盘中休息时间）,cu（有盘中休息时间）
        测试：
            1. 10：29：29 IF、T能下单, cu不能下单
            2. 10:30 之后都能下单
            3. 11：29：29.999999 能下单
            4. 13:00 之后T、IF能下单，cu不能下单
            5. 13:30 之后都能下单
            6. 15:00 - 15:15 : T能下单，IF、cu不能下单;
            7. 15:14:59 只有T2003能下单

        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_sim_insert_order_time_check_3.script.lzma"))
        # 测试
        TqApi.RD = random.Random(4)
        api = TqApi(
            backtest=TqBacktest(datetime.datetime(2020, 2, 17, 10, 29, 29), datetime.datetime(2020, 2, 17, 15, 18, 0)),
            _ins_url=self.ins_url_2020_02_18)  # 2019.12.2周一
        symbol1 = "SHFE.cu2003"
        symbol2 = "CFFEX.T2003"
        symbol3 = "CFFEX.IF2003"
        quote1 = api.get_quote(symbol1)
        quote2 = api.get_quote(symbol2)
        quote3 = api.get_quote(symbol3)
        position1 = api.get_position(symbol1)
        position2 = api.get_position(symbol2)
        position3 = api.get_position(symbol3)
        try:
            # 1 10：29：29 IF、T能下单, cu不能下单
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 1)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(1581906569000000000, order1.insert_date_time)
            self.assertEqual(1581906569000000000, order2.insert_date_time)
            self.assertEqual(1581906569000000000, order3.insert_date_time)

            # 2 10:30 之后都能下单；
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2020-02-17 10:30:00.000000":
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 0)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(1581906659999999000, order1.insert_date_time)
            self.assertEqual(1581906659999999000, order2.insert_date_time)
            self.assertEqual(1581906659999999000, order3.insert_date_time)

            # 3 11：29：29.999999 能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) != "2020-02-17 11:29:59.999999":
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.bid_price1)  # 使用quote1.bid_price1使其立即成交
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 0)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(1581910199999999000, order1.insert_date_time)
            self.assertEqual(1581910199999999000, order2.insert_date_time)
            self.assertEqual(1581910199999999000, order3.insert_date_time)

            # 4 13:00 之后T、IF能下单，cu不能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2020-02-17 13:00:00.000000":
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 1)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(1581915839999999000, order1.insert_date_time)
            self.assertEqual(1581915839999999000, order2.insert_date_time)
            self.assertEqual(1581915839999999000, order3.insert_date_time)

            # 5 13:30 之后都能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2020-02-17 13:30:00.000000":
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 0)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(1581917459999999000, order1.insert_date_time)
            self.assertEqual(1581917459999999000, order2.insert_date_time)
            self.assertEqual(1581917459999999000, order3.insert_date_time)

            # 6 15:00 - 15:15 : T能下单，IF、cu不能下单;
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2020-02-17 15:00:00.000000":
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 1)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 3)
            self.assertEqual(1581922859999999000, order1.insert_date_time)
            self.assertEqual(1581922859999999000, order2.insert_date_time)
            self.assertEqual(1581922859999999000, order3.insert_date_time)

            # 7 15:14:59 只有T2003能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) != "2020-02-17 15:14:59.999999":
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 1)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 3)
            self.assertEqual(1581923699999999000, order1.insert_date_time)
            self.assertEqual(1581923699999999000, order2.insert_date_time)
            self.assertEqual(1581923699999999000, order3.insert_date_time)

            while True:
                api.wait_update()
        except BacktestFinished:
            self.assertEqual(position1.pos, -3)
            self.assertEqual(position2.pos, 14)
            self.assertEqual(position3.pos, 15)
            api.close()

    def test_sim_insert_order_time_check_4(self):
        """
        模拟交易下单时间判断测试4

        测试时间段：
            交易日(datetime.date)为周一, 夜盘从周五21点到周六凌晨1点
        订阅合约：
            cu(有夜盘,凌晨1点结束夜盘), rb(夜盘23点结束), jd(无夜盘)
        测试：
            1. 回测刚开始:current_datetime 为 18:00 , 都无法下单
            2. 周五晚21：00之后: cu和rb能下单
            3. 周五23点到周六凌晨1点前：cu能下单
            4. 周一早9点后都能下单
            5. 周一晚21点后cu和rb能下单
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_sim_insert_order_time_check_4.script.lzma"))

        TqApi.RD = random.Random(4)
        api = TqApi(backtest=TqBacktest(datetime.date(2019, 12, 2), datetime.date(2019, 12, 3)),
                    _ins_url=self.ins_url_2019_12_04)
        symbol1 = "SHFE.cu2002"  # 有夜盘,凌晨1点结束夜盘
        symbol2 = "SHFE.rb2002"  # 夜盘23点结束
        symbol3 = "DCE.jd2002"  # 无夜盘
        quote1 = api.get_quote(symbol1)
        quote2 = api.get_quote(symbol2)
        quote3 = api.get_quote(symbol3)
        position1 = api.get_position(symbol1)
        position2 = api.get_position(symbol2)
        position3 = api.get_position(symbol3)
        try:
            # 1 回测刚开始:current_datetime 为 18:00 , 都无法下单
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 1)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 2)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 3)
            self.assertEqual(1575021600000000000, order1.insert_date_time)
            self.assertEqual(1575021600000000000, order2.insert_date_time)
            self.assertEqual(1575021600000000000, order3.insert_date_time)

            # 2 周五晚21：00之后: cu和rb能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-11-29 21:00:00.000000":
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 0)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 3)
            self.assertEqual(1575032459999999000, order1.insert_date_time)
            self.assertEqual(1575032459999999000, order2.insert_date_time)
            self.assertEqual(1575032459999999000, order3.insert_date_time)

            # 3 周六凌晨1点前：cu能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-11-30 00:01:00.000000":
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 0)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 2)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 3)
            self.assertEqual(1575043319999999000, order1.insert_date_time)
            self.assertEqual(1575043319999999000, order2.insert_date_time)
            self.assertEqual(1575043319999999000, order3.insert_date_time)

            # 4 周一早9点后都能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-12-02 09:00:00.000000":
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 0)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(1575248459999999000, order1.insert_date_time)
            self.assertEqual(1575248459999999000, order2.insert_date_time)
            self.assertEqual(1575248459999999000, order3.insert_date_time)

            # 5 周一晚21点后cu和rb能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-12-02 21:00:00.000000":
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="BUY", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 0)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 3)
            self.assertEqual(1575291659999999000, order1.insert_date_time)
            self.assertEqual(1575291659999999000, order2.insert_date_time)
            self.assertEqual(1575291659999999000, order3.insert_date_time)

            while True:
                api.wait_update()
        except BacktestFinished:
            self.assertEqual(position1.pos, -2)
            self.assertEqual(position2.pos, 6)
            self.assertEqual(position3.pos, 3)
            api.close()

    def test_sim_insert_order_time_check_5(self):
        """
        模拟交易下单时间判断测试5

        测试时间段：
            交易日(datetime.date)在非周一，订阅有夜盘合约，判断其可交易时间段
        合约：
            cu(有夜盘,凌晨1点结束夜盘), rb(夜盘23点结束), jd(无夜盘)
        测试：
            1 回测刚开始:current_datetime 为 18:00 , 都无法下单
            2 前一日21点以后rb、cu能下单
            3 本交易日9：00后都能下单
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_sim_insert_order_time_check_5.script.lzma"))

        TqApi.RD = random.Random(4)
        api = TqApi(backtest=TqBacktest(datetime.date(2019, 12, 3), datetime.date(2019, 12, 4)),
                    _ins_url=self.ins_url_2019_12_04)
        symbol1 = "SHFE.cu2002"  # 有夜盘,凌晨1点结束夜盘
        symbol2 = "SHFE.rb2002"  # 夜盘23点结束
        symbol3 = "DCE.jd2002"  # 无夜盘
        quote1 = api.get_quote(symbol1)
        quote2 = api.get_quote(symbol2)
        quote3 = api.get_quote(symbol3)
        position1 = api.get_position(symbol1)
        position2 = api.get_position(symbol2)
        position3 = api.get_position(symbol3)
        try:
            # 1 回测刚开始:current_datetime 为 18:00 , 都无法下单
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 1)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 2)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 3)
            self.assertEqual(1575280800000000000, order1.insert_date_time)
            self.assertEqual(1575280800000000000, order2.insert_date_time)
            self.assertEqual(1575280800000000000, order3.insert_date_time)

            # 2 前一日21点以后rb、cu能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-12-02 21:00:00.000000":
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="BUY", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 0)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 3)
            self.assertEqual(1575291659999999000, order1.insert_date_time)
            self.assertEqual(1575291659999999000, order2.insert_date_time)
            self.assertEqual(1575291659999999000, order3.insert_date_time)

            # 3 本交易日9：00后都能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-12-03 09:00:00.000000":
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="BUY", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 0)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(1575334859999999000, order1.insert_date_time)
            self.assertEqual(1575334859999999000, order2.insert_date_time)
            self.assertEqual(1575334859999999000, order3.insert_date_time)

            while True:
                api.wait_update()
        except BacktestFinished:
            self.assertEqual(position1.pos, 2)
            self.assertEqual(position2.pos, 4)
            self.assertEqual(position3.pos, 3)
            api.close()

    def test_sim_insert_order_time_check_6(self):
        """
        模拟交易下单时间判断测试6

        测试：
            限价单，直到交易日结束都不能成交: 预期交易日结束撤单
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_sim_insert_order_time_check_6.script.lzma"))
        # 测试：
        TqApi.RD = random.Random(4)
        api = TqApi(backtest=TqBacktest(datetime.datetime(2019, 12, 2, 10, 31, 00), datetime.datetime(2019, 12, 3)),
                    _ins_url=self.ins_url_2019_12_04)
        symbol = "DCE.m2009"
        order1 = api.insert_order(symbol=symbol, direction="BUY", offset="OPEN", volume=5,
                                  limit_price=2750)  # 到交易日结束都无法成交
        order2 = api.insert_order(symbol=symbol, direction="BUY", offset="OPEN", volume=3)
        try:
            while True:
                api.wait_update()
        except BacktestFinished:
            self.assertEqual(order1.status, "FINISHED")
            self.assertEqual(order1.volume_orign, 5)
            self.assertEqual(order1.volume_left, 5)
            self.assertEqual(order2.status, "FINISHED")
            self.assertEqual(order2.volume_orign, 3)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order1.last_msg, "交易日结束，自动撤销当日有效的委托单（GFD）")
            api.close()

    def test_sim_insert_order_time_check_7(self):
        """
        模拟交易下单时间判断测试7

        订阅合约：
            订阅周六有行情的和周六无行情的
        测试：
            （回测从周六开始）
            1 回测刚开始:current_datetime 为 0:00 , 只有cu能下单
            2 白盘开始后,都能下单
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_sim_insert_order_time_check_7.script.lzma"))

        TqApi.RD = random.Random(4)
        api = TqApi(
            backtest=TqBacktest(datetime.datetime(2019, 11, 30, 0, 0, 0), datetime.datetime(2019, 12, 2, 9, 30)),
            _ins_url=self.ins_url_2019_12_04)
        symbol1 = "SHFE.cu2002"  # 有夜盘,凌晨1点结束夜盘
        symbol2 = "SHFE.rb2002"  # 夜盘23点结束
        symbol3 = "DCE.jd2002"  # 无夜盘
        quote1 = api.get_quote(symbol1)
        quote2 = api.get_quote(symbol2)
        quote3 = api.get_quote(symbol3)
        position1 = api.get_position(symbol1)
        position2 = api.get_position(symbol2)
        position3 = api.get_position(symbol3)
        try:
            # 1 回测刚开始:current_datetime 为 0:00 , 只有cu能下单
            order1 = api.insert_order(symbol=symbol1, direction="SELL", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 0)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 2)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 3)
            self.assertEqual(1575043200000000000, order1.insert_date_time)
            self.assertEqual(1575043200000000000, order2.insert_date_time)
            self.assertEqual(1575043200000000000, order3.insert_date_time)

            # 2 白盘开始后,都能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-12-02 09:00:00.000000":
                api.wait_update()
            order1 = api.insert_order(symbol=symbol1, direction="BUY", offset="OPEN", volume=1,
                                      limit_price=quote1.last_price)
            order2 = api.insert_order(symbol=symbol2, direction="BUY", offset="OPEN", volume=2,
                                      limit_price=quote2.last_price)
            order3 = api.insert_order(symbol=symbol3, direction="BUY", offset="OPEN", volume=3,
                                      limit_price=quote3.last_price)
            while order1.status != "FINISHED" or order2.status != "FINISHED" or order3.status != "FINISHED":
                api.wait_update()
            self.assertEqual(order1.volume_orign, 1)
            self.assertEqual(order1.volume_left, 0)
            self.assertEqual(order2.volume_orign, 2)
            self.assertEqual(order2.volume_left, 0)
            self.assertEqual(order3.volume_orign, 3)
            self.assertEqual(order3.volume_left, 0)
            self.assertEqual(1575248459999999000, order1.insert_date_time)
            self.assertEqual(1575248459999999000, order2.insert_date_time)
            self.assertEqual(1575248459999999000, order3.insert_date_time)

            while True:
                api.wait_update()
        except BacktestFinished:
            self.assertEqual(position1.pos, 0)
            self.assertEqual(position2.pos, 2)
            self.assertEqual(position3.pos, 3)
            api.close()
