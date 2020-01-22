#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

import os
import unittest
import random
from datetime import datetime
from tqsdk import TqApi, TqBacktest
from tqsdk.test.api.helper import MockServer


class TestTdBacktest(unittest.TestCase):
    """
    回测时的交易测试.

    注：
    1: 在本地运行测试用例前需设置运行环境变量(Environment variables), 保证api中dict及set等类型的数据序列在每次运行时元素顺序一致: PYTHONHASHSEED=32
    2：若测试用例中调用了会使用uuid的功能函数时（如insert_order()会使用uuid生成order_id）,
        则：在生成script文件时及测试用例中都需设置 TqApi.RD = random.Random(x), 以保证两次生成的uuid一致, x取值范围为0-2^32
    """

    def setUp(self):
        # self.ins = MockInsServer(5000)
        self.mock = MockServer()
        # self.tq = WebsocketServer(5300)
        self.ins_url = "https://openmd.shinnytech.com/t/md/symbols/2019-07-03.json"
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
        api = TqApi(backtest=TqBacktest(start_dt=datetime(2019, 12, 10, 9), end_dt=datetime(2019, 12, 11)),
                    _ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
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
        api = TqApi(backtest=TqBacktest(start_dt=datetime(2019, 12, 10, 9), end_dt=datetime(2019, 12, 11)),
                    _ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
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
        api = TqApi(backtest=TqBacktest(start_dt=datetime(2019, 12, 10, 9), end_dt=datetime(2019, 12, 11)),
                    _ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
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
        api = TqApi(backtest=TqBacktest(start_dt=datetime(2019, 12, 10, 9), end_dt=datetime(2019, 12, 11)),
                    _ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
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
