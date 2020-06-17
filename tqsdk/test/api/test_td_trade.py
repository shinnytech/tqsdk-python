#!usr/bin/env python3
#-*- coding:utf-8 -*-
"""
@author: yanqiong
@file: test_td_trade.py
@create_on: 2020/6/12
@description: 
"""
import os
import random
import unittest

from tqsdk import TqApi, TqAccount, utils
from tqsdk.test.api.helper import MockInsServer, MockServer


class TestTdTrade(unittest.TestCase):
    """
    实盘账户下，insert_order 各种情况测试
    """

    def setUp(self):
        self.ins = MockInsServer(5000)
        self.mock = MockServer(td_url_character="q7.htfutures.com")
        self.ins_url_2020_06_16 = "http://127.0.0.1:5000/t/md/symbols/2020-06-16.json"
        self.md_url = "ws://127.0.0.1:5100/"
        self.td_url = "ws://127.0.0.1:5200/"

    def tearDown(self):
        self.ins.close()
        self.mock.close()

    def test_insert_order_shfe_anyprice(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_insert_order_shfe_anyprice.script"))
        # 测试
        account = TqAccount("H海通期货", "83011119", "********")
        utils.RD = random.Random(4)
        # 测试
        with self.assertRaises(Exception):
            with TqApi(account=account, _ins_url=self.ins_url_2020_06_16, _md_url=self.md_url, _td_url=self.td_url,
                       debug=False) as api:
                order1 = api.insert_order("SHFE.au2012", "BUY", "OPEN", 1)

    def test_insert_order_shfe_limit_fok(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_insert_order_shfe_limit_fok.script"))
        # 测试
        account = TqAccount("H海通期货", "83011119", "********")
        utils.RD = random.Random(4)
        with TqApi(account=account, _ins_url=self.ins_url_2020_06_16, _md_url=self.md_url, _td_url=self.td_url, debug=False) as api:
            order1 = api.insert_order("SHFE.rb2010", "BUY", "OPEN", 2, limit_price=3500, advanced="FOK", order_id="PYSDK_insert_SHFE_limit_FOK")
            while True:
                api.wait_update()
                if order1.status == "FINISHED":
                    break
            self.assertEqual("PYSDK_insert_SHFE_limit_FOK", order1.order_id)
            self.assertEqual("    25169789", order1.exchange_order_id)
            self.assertEqual("SHFE", order1.exchange_id)
            self.assertEqual("rb2010", order1.instrument_id)
            self.assertEqual("BUY", order1.direction)
            self.assertEqual("OPEN", order1.offset)
            self.assertEqual(2, order1.volume_orign)
            self.assertEqual(2, order1.volume_left)
            self.assertEqual(3500.0, order1.limit_price)
            self.assertEqual(1593585599000000000, order1.insert_date_time)
            self.assertEqual("FINISHED", order1.status)
            self.assertEqual("LIMIT", order1.price_type)
            self.assertEqual("ALL", order1.volume_condition)
            self.assertEqual("IOC", order1.time_condition)
            self.assertEqual("已撤单报单已提交", order1.last_msg)
            self.assertEqual("{'order_id': 'PYSDK_insert_SHFE_limit_FOK', 'exchange_order_id': '    25169789', 'exchange_id': 'SHFE', 'instrument_id': 'rb2010', 'direction': 'BUY', 'offset': 'OPEN', 'volume_orign': 2, 'volume_left': 2, 'limit_price': 3500.0, 'price_type': 'LIMIT', 'volume_condition': 'ALL', 'time_condition': 'IOC', 'insert_date_time': 1593585599000000000, 'last_msg': '已撤单报单已提交', 'status': 'FINISHED', 'seqno': 19, 'user_id': '83011119'}",
                             str(order1))

    def test_insert_order_shfe_limit_fak(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_insert_order_shfe_limit_fak.script"))
        # 测试
        account = TqAccount("H海通期货", "83011119", "********")
        utils.RD = random.Random(4)
        with TqApi(account=account, _ins_url=self.ins_url_2020_06_16, _md_url=self.md_url, _td_url=self.td_url, debug=False) as api:
            order1 = api.insert_order("SHFE.rb2010", "BUY", "OPEN", 2, limit_price=3500, advanced="FAK", order_id="PYSDK_insert_SHFE_limit_FAK")
            while True:
                api.wait_update()
                if order1.status == "FINISHED":
                    break
            self.assertEqual("PYSDK_insert_SHFE_limit_FAK", order1.order_id)
            self.assertEqual("    25308102", order1.exchange_order_id)
            self.assertEqual("SHFE", order1.exchange_id)
            self.assertEqual("rb2010", order1.instrument_id)
            self.assertEqual("BUY", order1.direction)
            self.assertEqual("OPEN", order1.offset)
            self.assertEqual(2, order1.volume_orign)
            self.assertEqual(2, order1.volume_left)
            self.assertEqual(3500.0, order1.limit_price)
            self.assertEqual(1593585743000000000, order1.insert_date_time)
            self.assertEqual("FINISHED", order1.status)
            self.assertEqual("LIMIT", order1.price_type)
            self.assertEqual("ANY", order1.volume_condition)
            self.assertEqual("IOC", order1.time_condition)
            self.assertEqual("已撤单报单已提交", order1.last_msg)
            self.assertEqual("{'order_id': 'PYSDK_insert_SHFE_limit_FAK', 'exchange_order_id': '    25308102', 'exchange_id': 'SHFE', 'instrument_id': 'rb2010', 'direction': 'BUY', 'offset': 'OPEN', 'volume_orign': 2, 'volume_left': 2, 'limit_price': 3500.0, 'price_type': 'LIMIT', 'volume_condition': 'ANY', 'time_condition': 'IOC', 'insert_date_time': 1593585743000000000, 'last_msg': '已撤单报单已提交', 'status': 'FINISHED', 'seqno': 21, 'user_id': '83011119'}",
                             str(order1))

    def test_insert_order_dec_best(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_insert_order_dec_best.script"))
        # 测试
        account = TqAccount("H海通期货", "83011119", "********")
        utils.RD = random.Random(4)
        # 测试
        with self.assertRaises(Exception):
            with TqApi(account=account, _ins_url=self.ins_url_2020_06_16, _md_url=self.md_url, _td_url=self.td_url,
                       debug=False) as api:
                order1 = api.insert_order("DCE.m2009", "BUY", "OPEN", 1, limit_price="BEST", order_id="PYSDK_insert_DCE_BEST")

    def test_insert_order_dec_fivelevel(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_insert_order_dec_fivelevel.script"))
        # 测试
        account = TqAccount("H海通期货", "83011119", "********")
        utils.RD = random.Random(4)
        # 测试
        with self.assertRaises(Exception):
            with TqApi(account=account, _ins_url=self.ins_url_2020_06_16, _md_url=self.md_url,
                       _td_url=self.td_url,
                       debug=False) as api:
                order1 = api.insert_order("DCE.m2009", "BUY", "OPEN", 1, limit_price="FIVELEVEL",
                                          order_id="PYSDK_insert_DCE_FIVELEVEL")

    def test_insert_order_dce_anyprice(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_insert_order_dce_anyprice.script"))
        # 测试
        account = TqAccount("H海通期货", "83011119", "********")
        utils.RD = random.Random(4)
        with TqApi(account=account, _ins_url=self.ins_url_2020_06_16, _md_url=self.md_url, _td_url=self.td_url,
                   debug=False) as api:
            order1 = api.insert_order("DCE.m2009", "BUY", "OPEN", 1, order_id="PYSDK_insert_DCE_any")
            while True:
                api.wait_update()
                if order1.status == "FINISHED":
                    break
            self.assertEqual("PYSDK_insert_DCE_any", order1.order_id)
            self.assertEqual("    15350014", order1.exchange_order_id)
            self.assertEqual("DCE", order1.exchange_id)
            self.assertEqual("m2009", order1.instrument_id)
            self.assertEqual("BUY", order1.direction)
            self.assertEqual("OPEN", order1.offset)
            self.assertEqual(1, order1.volume_orign)
            self.assertEqual(0, order1.volume_left)
            self.assertEqual(0.0, order1.limit_price)
            self.assertEqual(1593586583000000000, order1.insert_date_time)
            self.assertEqual("FINISHED", order1.status)
            self.assertEqual("ANY", order1.price_type)
            self.assertEqual("ANY", order1.volume_condition)
            self.assertEqual("IOC", order1.time_condition)
            self.assertEqual("全部成交", order1.last_msg)
            self.assertEqual(
                "{'order_id': 'PYSDK_insert_DCE_any', 'exchange_order_id': '    15350014', 'exchange_id': 'DCE', 'instrument_id': 'm2009', 'direction': 'BUY', 'offset': 'OPEN', 'volume_orign': 1, 'volume_left': 0, 'limit_price': 0.0, 'price_type': 'ANY', 'volume_condition': 'ANY', 'time_condition': 'IOC', 'insert_date_time': 1593586583000000000, 'last_msg': '全部成交', 'status': 'FINISHED', 'seqno': 38, 'user_id': '83011119'}",
                str(order1))

    def test_insert_order_dce_anyprice_fok(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_insert_order_dce_anyprice_fok.script"))
        # 测试
        account = TqAccount("H海通期货", "83011119", "********")
        utils.RD = random.Random(4)
        with TqApi(account=account, _ins_url=self.ins_url_2020_06_16, _md_url=self.md_url, _td_url=self.td_url,
                   debug=False) as api:
            order1 = api.insert_order("DCE.m2009", "BUY", "CLOSE", 2, advanced="FOK", order_id="PYSDK_insert_DCE_any_FOK")
            while True:
                api.wait_update()
                if order1.status == "FINISHED":
                    break
            self.assertEqual("PYSDK_insert_DCE_any_FOK", order1.order_id)
            self.assertEqual("    13681949", order1.exchange_order_id)
            self.assertEqual("DCE", order1.exchange_id)
            self.assertEqual("m2009", order1.instrument_id)
            self.assertEqual("BUY", order1.direction)
            self.assertEqual("CLOSE", order1.offset)
            self.assertEqual(2, order1.volume_orign)
            self.assertEqual(0, order1.volume_left)
            self.assertEqual(0.0, order1.limit_price)
            self.assertEqual(1593657995000000000, order1.insert_date_time)
            self.assertEqual("FINISHED", order1.status)
            self.assertEqual("ANY", order1.price_type)
            self.assertEqual("ALL", order1.volume_condition)
            self.assertEqual("IOC", order1.time_condition)
            self.assertEqual("全部成交", order1.last_msg)
            self.assertEqual(
                "{'order_id': 'PYSDK_insert_DCE_any_FOK', 'exchange_order_id': '    13681949', 'exchange_id': 'DCE', 'instrument_id': 'm2009', 'direction': 'BUY', 'offset': 'CLOSE', 'volume_orign': 2, 'volume_left': 0, 'limit_price': 0.0, 'price_type': 'ANY', 'volume_condition': 'ALL', 'time_condition': 'IOC', 'insert_date_time': 1593657995000000000, 'last_msg': '全部成交', 'status': 'FINISHED', 'seqno': 6, 'user_id': '83011119'}",
                str(order1))

    def test_insert_order_dce_limit_fak(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_insert_order_dce_limit_fak.script"))
        # 测试
        account = TqAccount("H海通期货", "83011119", "********")
        utils.RD = random.Random(4)
        with TqApi(account=account, _ins_url=self.ins_url_2020_06_16, _md_url=self.md_url, _td_url=self.td_url,
                   debug=False) as api:
            order1 = api.insert_order("DCE.m2009", "BUY", "OPEN", 2, limit_price=2800, advanced="FAK", order_id="PYSDK_insert_DCE_limit_FAK")
            while True:
                api.wait_update()
                if order1.status == "FINISHED":
                    break
            self.assertEqual("PYSDK_insert_DCE_limit_FAK", order1.order_id)
            self.assertEqual("    15189608", order1.exchange_order_id)
            self.assertEqual("DCE", order1.exchange_id)
            self.assertEqual("m2009", order1.instrument_id)
            self.assertEqual("BUY", order1.direction)
            self.assertEqual("OPEN", order1.offset)
            self.assertEqual(2, order1.volume_orign)
            self.assertEqual(2, order1.volume_left)
            self.assertEqual(2800.0, order1.limit_price)
            self.assertEqual(1593585989000000000, order1.insert_date_time)
            self.assertEqual("FINISHED", order1.status)
            self.assertEqual("LIMIT", order1.price_type)
            self.assertEqual("ANY", order1.volume_condition)
            self.assertEqual("IOC", order1.time_condition)
            self.assertEqual("已撤单", order1.last_msg)
            self.assertEqual(
                "{'order_id': 'PYSDK_insert_DCE_limit_FAK', 'exchange_order_id': '    15189608', 'exchange_id': 'DCE', 'instrument_id': 'm2009', 'direction': 'BUY', 'offset': 'OPEN', 'volume_orign': 2, 'volume_left': 2, 'limit_price': 2800.0, 'price_type': 'LIMIT', 'volume_condition': 'ANY', 'time_condition': 'IOC', 'insert_date_time': 1593585989000000000, 'last_msg': '已撤单', 'status': 'FINISHED', 'seqno': 24, 'user_id': '83011119'}",
                str(order1))

    def test_insert_order_dce_limit_fok(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_insert_order_dce_limit_fok.script"))
        # 测试
        account = TqAccount("H海通期货", "83011119", "********")
        utils.RD = random.Random(4)
        with TqApi(account=account, _ins_url=self.ins_url_2020_06_16, _md_url=self.md_url, _td_url=self.td_url,
                   debug=False) as api:
            order1 = api.insert_order("DCE.m2009", "BUY", "OPEN", 2, limit_price=2800, advanced="FOK", order_id="PYSDK_insert_DCE_limit_FOK")
            while True:
                api.wait_update()
                if order1.status == "FINISHED":
                    break
            self.assertEqual("PYSDK_insert_DCE_limit_FOK", order1.order_id)
            self.assertEqual("    15236982", order1.exchange_order_id)
            self.assertEqual("DCE", order1.exchange_id)
            self.assertEqual("m2009", order1.instrument_id)
            self.assertEqual("BUY", order1.direction)
            self.assertEqual("OPEN", order1.offset)
            self.assertEqual(2, order1.volume_orign)
            self.assertEqual(2, order1.volume_left)
            self.assertEqual(2800.0, order1.limit_price)
            self.assertEqual(1593586120000000000, order1.insert_date_time)
            self.assertEqual("FINISHED", order1.status)
            self.assertEqual("LIMIT", order1.price_type)
            self.assertEqual("ALL", order1.volume_condition)
            self.assertEqual("IOC", order1.time_condition)
            self.assertEqual("已撤单", order1.last_msg)
            self.assertEqual(
                "{'order_id': 'PYSDK_insert_DCE_limit_FOK', 'exchange_order_id': '    15236982', 'exchange_id': 'DCE', 'instrument_id': 'm2009', 'direction': 'BUY', 'offset': 'OPEN', 'volume_orign': 2, 'volume_left': 2, 'limit_price': 2800.0, 'price_type': 'LIMIT', 'volume_condition': 'ALL', 'time_condition': 'IOC', 'insert_date_time': 1593586120000000000, 'last_msg': '已撤单', 'status': 'FINISHED', 'seqno': 27, 'user_id': '83011119'}",
                str(order1))

    def test_insert_order_dce_limit_fak1(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_insert_order_dce_limit_fak1.script"))
        # 测试
        account = TqAccount("H海通期货", "83011119", "********")
        utils.RD = random.Random(4)
        with TqApi(account=account, _ins_url=self.ins_url_2020_06_16, _md_url=self.md_url, _td_url=self.td_url,
                   debug=False) as api:
            order1 = api.insert_order("DCE.m2009", "BUY", "OPEN", 1, limit_price=2890, advanced="FAK", order_id="PYSDK_insert_DCE_limit_FAK1")
            while True:
                api.wait_update()
                if order1.status == "FINISHED":
                    break
            self.assertEqual("PYSDK_insert_DCE_limit_FAK1", order1.order_id)
            self.assertEqual("    15266799", order1.exchange_order_id)
            self.assertEqual("DCE", order1.exchange_id)
            self.assertEqual("m2009", order1.instrument_id)
            self.assertEqual("BUY", order1.direction)
            self.assertEqual("OPEN", order1.offset)
            self.assertEqual(1, order1.volume_orign)
            self.assertEqual(0, order1.volume_left)
            self.assertEqual(2890.0, order1.limit_price)
            self.assertEqual(1593586261000000000, order1.insert_date_time)
            self.assertEqual("FINISHED", order1.status)
            self.assertEqual("LIMIT", order1.price_type)
            self.assertEqual("ANY", order1.volume_condition)
            self.assertEqual("IOC", order1.time_condition)
            self.assertEqual("全部成交", order1.last_msg)
            self.assertEqual(
                "{'order_id': 'PYSDK_insert_DCE_limit_FAK1', 'exchange_order_id': '    15266799', 'exchange_id': 'DCE', 'instrument_id': 'm2009', 'direction': 'BUY', 'offset': 'OPEN', 'volume_orign': 1, 'volume_left': 0, 'limit_price': 2890.0, 'price_type': 'LIMIT', 'volume_condition': 'ANY', 'time_condition': 'IOC', 'insert_date_time': 1593586261000000000, 'last_msg': '全部成交', 'status': 'FINISHED', 'seqno': 30, 'user_id': '83011119'}",
                str(order1))

    def test_insert_order_dce_limit_fok1(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_insert_order_dce_limit_fok1.script"))
        # 测试
        account = TqAccount("H海通期货", "83011119", "********")
        utils.RD = random.Random(4)
        with TqApi(account=account, _ins_url=self.ins_url_2020_06_16, _md_url=self.md_url, _td_url=self.td_url,
                   debug=False) as api:
            order1 =  api.insert_order("DCE.m2009", "SELL", "OPEN", 2, limit_price=2905, advanced="FOK", order_id="PYSDK_insert_DCE_limit_FOK1")
            while True:
                api.wait_update()
                if order1.status == "FINISHED":
                    break
            self.assertEqual("PYSDK_insert_DCE_limit_FOK1", order1.order_id)
            self.assertEqual("    13619123", order1.exchange_order_id)
            self.assertEqual("DCE", order1.exchange_id)
            self.assertEqual("m2009", order1.instrument_id)
            self.assertEqual("SELL", order1.direction)
            self.assertEqual("OPEN", order1.offset)
            self.assertEqual(2, order1.volume_orign)
            self.assertEqual(0, order1.volume_left)
            self.assertEqual(2905.0, order1.limit_price)
            self.assertEqual(1593657671000000000, order1.insert_date_time)
            self.assertEqual("FINISHED", order1.status)
            self.assertEqual("LIMIT", order1.price_type)
            self.assertEqual("ALL", order1.volume_condition)
            self.assertEqual("IOC", order1.time_condition)
            self.assertEqual("全部成交", order1.last_msg)
            self.assertEqual(
                "{'order_id': 'PYSDK_insert_DCE_limit_FOK1', 'exchange_order_id': '    13619123', 'exchange_id': 'DCE', 'instrument_id': 'm2009', 'direction': 'SELL', 'offset': 'OPEN', 'volume_orign': 2, 'volume_left': 0, 'limit_price': 2905.0, 'price_type': 'LIMIT', 'volume_condition': 'ALL', 'time_condition': 'IOC', 'insert_date_time': 1593657671000000000, 'last_msg': '全部成交', 'status': 'FINISHED', 'seqno': 2, 'user_id': '83011119'}",
                str(order1))
