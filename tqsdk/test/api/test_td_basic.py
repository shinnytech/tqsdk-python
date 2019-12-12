#!/usr/bin/env python
#  -*- coding: utf-8 -*-
import os
import random
import unittest
from tqsdk.test.api.helper import MockInsServer, MockServer
from tqsdk import TqApi


class TestTdBasic(unittest.TestCase):
    """
    测试TqApi交易相关函数基本功能, 以及TqApi与交易服务器交互是否符合设计预期

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

    # 模拟交易测试

    # @unittest.skip("无条件跳过")
    def test_insert_order(self):
        """
        下单
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_insert_order_simulate.script"))
        # 测试: 模拟账户下单
        # 测试脚本重新生成后，数据根据实际情况有变化
        TqApi.RD = random.Random(2)
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        order1 = api.insert_order("DCE.jd2001", "BUY", "OPEN", 1)
        order2 = api.insert_order("SHFE.cu2001", "BUY", "OPEN", 2, limit_price=49200)

        while order1.status == "ALIVE" or order2.status == "ALIVE":
            api.wait_update()

        self.assertEqual(order1.order_id, "5c6e433715ba2bdd177219d30e7a269f")
        self.assertEqual(order1.direction, "BUY")
        self.assertEqual(order1.offset, "OPEN")
        self.assertEqual(order1.volume_orign, 1)
        self.assertEqual(order1.volume_left, 0)
        self.assertEqual(order1.limit_price != order1.limit_price, True)  # 判断nan
        self.assertEqual(order1.price_type, "ANY")
        self.assertEqual(order1.volume_condition, "ANY")
        self.assertEqual(order1.time_condition, "IOC")
        self.assertEqual(order1.insert_date_time, 631123200000000000)
        self.assertEqual(order1.status, "FINISHED")
        for k, v in order1.trade_records.items():  # 模拟交易为一次性全部成交
            self.assertEqual(str(v),
                             "{'order_id': '5c6e433715ba2bdd177219d30e7a269f', 'trade_id': '5c6e433715ba2bdd177219d30e7a269f|1', 'exchange_trade_id': '5c6e433715ba2bdd177219d30e7a269f|1', 'exchange_id': 'DCE', 'instrument_id': 'jd2001', 'direction': 'BUY', 'offset': 'OPEN', 'price': 4087.0, 'volume': 1, 'trade_date_time': 1576121399900001000, 'symbol': 'DCE.jd2001', 'user_id': 'TQSIM', 'commission': 6.122999999999999}")

        self.assertEqual(order2.order_id, "cf1822ffbc6887782b491044d5e34124")
        self.assertEqual(order2.direction, "BUY")
        self.assertEqual(order2.offset, "OPEN")
        self.assertEqual(order2.volume_orign, 2)
        self.assertEqual(order2.volume_left, 0)
        self.assertEqual(order2.limit_price, 49200.0)
        self.assertEqual(order2.price_type, "LIMIT")
        self.assertEqual(order2.volume_condition, "ANY")
        self.assertEqual(order2.time_condition, "GFD")
        self.assertEqual(order2.insert_date_time, 631123200000000000)
        self.assertEqual(order2.status, "FINISHED")
        for k, v in order2.trade_records.items():  # 模拟交易为一次性全部成交
            self.assertEqual(str(v),
                             "{'order_id': 'cf1822ffbc6887782b491044d5e34124', 'trade_id': 'cf1822ffbc6887782b491044d5e34124|2', 'exchange_trade_id': 'cf1822ffbc6887782b491044d5e34124|2', 'exchange_id': 'SHFE', 'instrument_id': 'cu2001', 'direction': 'BUY', 'offset': 'OPEN', 'price': 49200.0, 'volume': 2, 'trade_date_time': 1576121399900001000, 'symbol': 'SHFE.cu2001', 'user_id': 'TQSIM', 'commission': 23.189999999999998}")

        api.close()

    def test_cancel_order(self):
        """
        撤单
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_cancel_order_simulate.script"))
        # 测试: 模拟账户
        TqApi.RD = random.Random(2)
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)

        order1 = api.insert_order("DCE.jd2001", "BUY", "OPEN", 1, limit_price=4570)
        order2 = api.insert_order("SHFE.cu2001", "BUY", "OPEN", 2, limit_price=47070)
        api.wait_update()

        self.assertEqual("ALIVE", order1.status)
        self.assertEqual("ALIVE", order2.status)

        api.cancel_order(order1)
        api.cancel_order(order2.order_id)
        api.wait_update()

        self.assertEqual("FINISHED", order1.status)
        self.assertEqual("FINISHED", order2.status)

        api.close()

    def test_get_account(self):
        """
        获取账户资金信息
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_get_account_simulate.script"))
        # 测试: 获取数据
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        TqApi.RD = random.Random(4)
        order = api.insert_order("DCE.jd2001", "BUY", "OPEN", 1, limit_price=4570)
        while order.status == "ALIVE":
            api.wait_update()
        account = api.get_account()

        # 测试脚本重新生成后，数据根据实际情况有变化
        self.assertEqual(str(account),
                         "{'currency': 'CNY', 'pre_balance': 10000000.0, 'static_balance': 10000000.0, 'balance': 9994873.877, 'available': 9992016.477, 'float_profit': -5120.0, 'position_profit': -5120.0, 'close_profit': 0.0, 'frozen_margin': 0.0, 'margin': 2857.4, 'frozen_commission': 0.0, 'commission': 6.122999999999999, 'frozen_premium': 0.0, 'premium': 0.0, 'deposit': 0.0, 'withdraw': 0.0, 'risk_ratio': 0.00028588654896140217}")
        self.assertEqual(account.currency, "CNY")
        self.assertEqual(account.pre_balance, 10000000.0)
        self.assertEqual(9994873.877, account.balance)
        self.assertEqual(6.122999999999999, account["commission"])
        self.assertEqual(2857.4, account["margin"])
        self.assertEqual(-5120.0, account.position_profit)
        api.close()

    def test_get_position(self):
        """
        获取持仓
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_get_position_simulate.script"))
        # 测试: 获取数据
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        order1 = api.insert_order("DCE.jd2001", "BUY", "OPEN", 1, limit_price=4592)
        order2 = api.insert_order("DCE.jd2001", "BUY", "OPEN", 3)
        order3 = api.insert_order("DCE.jd2001", "SELL", "OPEN", 3)

        while order1.status == "ALIVE" or order2.status == "ALIVE" or order3.status == "ALIVE":
            api.wait_update()

        position = api.get_position("DCE.jd2001")
        # 测试脚本重新生成后，数据根据实际情况有变化
        self.assertEqual(
            "{'exchange_id': 'DCE', 'instrument_id': 'jd2001', 'pos_long_his': 0, 'pos_long_today': 4, 'pos_short_his': 0, 'pos_short_today': 3, 'volume_long_today': 4, 'volume_long_his': 0, 'volume_long': 4, 'volume_long_frozen_today': 0, 'volume_long_frozen_his': 0, 'volume_long_frozen': 0, 'volume_short_today': 3, 'volume_short_his': 0, 'volume_short': 3, 'volume_short_frozen_today': 0, 'volume_short_frozen_his': 0, 'volume_short_frozen': 0, 'open_price_long': 4193.0, 'open_price_short': 4059.0, 'open_cost_long': 167720.0, 'open_cost_short': 121770.0, 'position_price_long': 4193.0, 'position_price_short': 4059.0, 'position_cost_long': 167720.0, 'position_cost_short': 121770.0, 'float_profit_long': -5320.0, 'float_profit_short': -30.0, 'float_profit': -5350.0, 'position_profit_long': -5320.0, 'position_profit_short': -30.0, 'position_profit': -5350.0, 'margin_long': 11429.6, 'margin_short': 8572.2, 'margin': 20001.800000000003, 'symbol': 'DCE.jd2001', 'last_price': 4060.0}",
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
        self.assertEqual(position.open_price_long, 4193.0)
        self.assertEqual(position.open_price_short, 4059.0)
        self.assertEqual(position.open_cost_long, 167720.0)
        self.assertEqual(position.open_cost_short, 121770.0)
        self.assertEqual(position.position_price_long, 4193.0)
        self.assertEqual(position.position_price_short, 4059.0)
        self.assertEqual(position.position_cost_long, 167720.0)
        self.assertEqual(position.position_cost_short, 121770.0)
        self.assertEqual(position.float_profit_long, -5320.0)
        self.assertEqual(position.float_profit_short, -30.0)
        self.assertEqual(position.float_profit, -5350.0)
        self.assertEqual(position.position_profit_long, -5320.0)
        self.assertEqual(position.position_profit_short, -30.0)
        self.assertEqual(position.position_profit, -5350.0)
        self.assertEqual(position.margin_long, 11429.6)
        self.assertEqual(position.margin_short, 8572.2)
        self.assertEqual(position.margin, 20001.800000000003)
        self.assertEqual(position.symbol, "DCE.jd2001")
        self.assertEqual(position.last_price, 4060.0)

        # 其他取值方式测试
        self.assertEqual(position["pos_long_today"], 4)
        self.assertEqual(position["pos_short_today"], 3)
        self.assertEqual(position["volume_long_his"], 0)
        self.assertEqual(position["volume_long"], 4)

        api.close()

    def test_get_trade(self):
        """
        获取成交记录
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_get_trade_simulate.script"))
        # 测试: 模拟账户
        TqApi.RD = random.Random(4)
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        order1 = api.insert_order("DCE.jd2001", "BUY", "OPEN", 1)
        order2 = api.insert_order("SHFE.cu2001", "BUY", "OPEN", 2, limit_price=49200)
        while order1.status == "ALIVE" or order2.status == "ALIVE":
            api.wait_update()

        trade1 = api.get_trade("1710cf5327ac435a7a97c643656412a9|1")
        trade2 = api.get_trade("8ca5996666ceab360512bd1311072231|2")

        self.assertEqual(str(trade1),
                         "{'order_id': '1710cf5327ac435a7a97c643656412a9', 'trade_id': '1710cf5327ac435a7a97c643656412a9|1', 'exchange_trade_id': '1710cf5327ac435a7a97c643656412a9|1', 'exchange_id': 'DCE', 'instrument_id': 'jd2001', 'direction': 'BUY', 'offset': 'OPEN', 'price': 4058.0, 'volume': 1, 'trade_date_time': 1576114914812000000, 'symbol': 'DCE.jd2001', 'user_id': 'TQSIM', 'commission': 6.122999999999999}")
        self.assertEqual(str(trade2),
                         "{'order_id': '8ca5996666ceab360512bd1311072231', 'trade_id': '8ca5996666ceab360512bd1311072231|2', 'exchange_trade_id': '8ca5996666ceab360512bd1311072231|2', 'exchange_id': 'SHFE', 'instrument_id': 'cu2001', 'direction': 'BUY', 'offset': 'OPEN', 'price': 49200.0, 'volume': 2, 'trade_date_time': 1576114916000000000, 'symbol': 'SHFE.cu2001', 'user_id': 'TQSIM', 'commission': 23.189999999999998}")
        self.assertEqual(trade1.direction, "BUY")
        self.assertEqual(trade1.offset, "OPEN")
        self.assertEqual(trade1.price, 4058.0)
        self.assertEqual(trade1.volume, 1)
        self.assertEqual(trade1.trade_date_time, 1576114914812000000)
        self.assertEqual(trade1.commission, 6.122999999999999)

        self.assertEqual(trade2.direction, "BUY")
        self.assertEqual(trade2.offset, "OPEN")
        self.assertEqual(trade2.price, 49200.0)
        self.assertEqual(trade2.volume, 2)
        self.assertEqual(trade2.trade_date_time, 1576114916000000000)
        self.assertEqual(trade2.commission, 23.189999999999998)
        api.close()

    def test_get_order(self):
        """
        获取委托单信息
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_get_order_simulate.script"))
        # 测试: 模拟账户下单
        TqApi.RD = random.Random(4)
        api = TqApi(_ins_url=self.ins_url, _td_url=self.td_url, _md_url=self.md_url)
        order1 = api.insert_order("DCE.jd2001", "BUY", "OPEN", 1)
        order2 = api.insert_order("SHFE.cu2001", "SELL", "OPEN", 2, limit_price=47040)
        while order1.status == "ALIVE" or order2.status == "ALIVE":
            api.wait_update()

        get_order1 = api.get_order(order1.order_id)
        get_order2 = api.get_order(order2.order_id)

        self.assertEqual(str(get_order1),
                         "{'order_id': '1710cf5327ac435a7a97c643656412a9', 'exchange_order_id': '1710cf5327ac435a7a97c643656412a9', 'exchange_id': 'DCE', 'instrument_id': 'jd2001', 'direction': 'BUY', 'offset': 'OPEN', 'volume_orign': 1, 'volume_left': 0, 'limit_price': nan, 'price_type': 'ANY', 'volume_condition': 'ANY', 'time_condition': 'IOC', 'insert_date_time': 631123200000000000, 'last_msg': '全部成交', 'status': 'FINISHED', 'user_id': 'TQSIM', 'symbol': 'DCE.jd2001', 'frozen_margin': 0.0}")
        self.assertEqual(str(get_order2),
                         "{'order_id': '8ca5996666ceab360512bd1311072231', 'exchange_order_id': '8ca5996666ceab360512bd1311072231', 'exchange_id': 'SHFE', 'instrument_id': 'cu2001', 'direction': 'SELL', 'offset': 'OPEN', 'volume_orign': 2, 'volume_left': 0, 'limit_price': 47040.0, 'price_type': 'LIMIT', 'volume_condition': 'ANY', 'time_condition': 'GFD', 'insert_date_time': 631123200000000000, 'last_msg': '全部成交', 'status': 'FINISHED', 'user_id': 'TQSIM', 'symbol': 'SHFE.cu2001', 'frozen_margin': 0.0}")

        self.assertEqual(get_order1.order_id, "1710cf5327ac435a7a97c643656412a9")
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

        self.assertEqual(get_order2.order_id, "8ca5996666ceab360512bd1311072231")
        self.assertEqual(get_order2.direction, "SELL")
        self.assertEqual(get_order2.offset, "OPEN")
        self.assertEqual(get_order2.volume_orign, 2)
        self.assertEqual(get_order2.volume_left, 0)
        self.assertEqual(get_order2.limit_price, 47040)
        self.assertEqual(get_order2.price_type, "LIMIT")
        self.assertEqual(get_order2.volume_condition, "ANY")
        self.assertEqual(get_order2.time_condition, "GFD")
        self.assertEqual(get_order2["insert_date_time"], 631123200000000000)
        self.assertEqual(get_order2["last_msg"], "全部成交")
        self.assertEqual(get_order2["status"], "FINISHED")
        self.assertEqual(get_order2.symbol, "SHFE.cu2001")
        self.assertEqual(get_order2.frozen_margin, 0)

        api.close()
