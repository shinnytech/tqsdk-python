#!/usr/bin/env python
#  -*- coding: utf-8 -*-

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
        self.ins_url = "http://127.0.0.1:5000/"
        self.md_url = "ws://127.0.0.1:5100/"
        self.td_url = "ws://127.0.0.1:5200/"

    def tearDown(self):
        self.mock.close()
        self.ins.close()

    def test_get_quote_normal(self):
        """
        获取行情报价
        """
        # 预设服务器端响应
        self.mock.run("test_md_basic_get_quote_normal.script")
        # 获取行情
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        q = api.get_quote("SHFE.cu1901")
        self.assertEqual(46940.0, q.last_price)
        api.close()
