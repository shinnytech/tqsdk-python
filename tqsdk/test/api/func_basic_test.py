#!/usr/bin/env python
#  -*- coding: utf-8 -*-
import os
import random
import unittest
from tqsdk.test.api.helper import MockInsServer, MockServer
from tqsdk import TqApi


class TestFuncBasic(unittest.TestCase):
    """
    功能函数部分基本功能测试.

    测试TqApi功能相关函数

    注: 在本地运行测试用例前需设置IDE中运行环境变量(Environment variables): PYTHONHASHSEED=32
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

    # @unittest.skip("无条件跳过")
    def test_is_changing(self):
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "test_func_basic_is_changing.script"))
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

        api.close()
