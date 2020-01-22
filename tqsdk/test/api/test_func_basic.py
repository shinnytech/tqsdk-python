#!/usr/bin/env python
#  -*- coding: utf-8 -*-
import os
import random
import unittest
from tqsdk.test.api.helper import MockInsServer, MockServer
from tqsdk import TqApi


class TestFuncBasic(unittest.TestCase):
    """
    TqApi中功能函数的基本功能测试.

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

    def test_is_changing(self):
        """is_changing() 测试"""

        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_func_basic_is_changing.script.lzma"))
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
