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
        self.ins_url_2020_04_02 = "https://openmd.shinnytech.com/t/md/symbols/2020-04-02.json"
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
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_insert_order_simulate.script.lzma"))
        # 测试: 模拟账户下单
        # 非回测, 则需在盘中生成测试脚本: 测试脚本重新生成后，数据根据实际情况有变化,因此需要修改assert语句的内容
        TqApi.RD = random.Random(2)
        api = TqApi(_ins_url=self.ins_url_2019_07_03, _td_url=self.td_url, _md_url=self.md_url)
        order1 = api.insert_order("DCE.jd2005", "BUY", "OPEN", 1)
        order2 = api.insert_order("SHFE.cu2004", "BUY", "OPEN", 2, limit_price=49200)

        while order1.status == "ALIVE" or order2.status == "ALIVE":
            api.wait_update()

        self.assertEqual(order1.order_id, "5c6e433715ba2bdd177219d30e7a269f")
        self.assertEqual(order1.direction, "BUY")
        self.assertEqual(order1.offset, "OPEN")
        self.assertEqual(order1.volume_orign, 1)
        self.assertEqual(order1.volume_left, 0)
        self.assertNotEqual(order1.limit_price, order1.limit_price)  # 判断nan
        self.assertEqual(order1.price_type, "ANY")
        self.assertEqual(order1.volume_condition, "ANY")
        self.assertEqual(order1.time_condition, "IOC")
        self.assertAlmostEqual(1584423143664478000 / 1e9, order1.insert_date_time / 1e9, places=1)
        self.assertEqual(order1.status, "FINISHED")
        for k, v in order1.trade_records.items():  # 模拟交易为一次性全部成交，因此只有一条成交记录
            self.assertAlmostEqual(1584423143664478000 / 1e9, v.trade_date_time / 1e9, places=1)
            del v.trade_date_time
            self.assertEqual(str(v),
                             "{'order_id': '5c6e433715ba2bdd177219d30e7a269f', 'trade_id': '5c6e433715ba2bdd177219d30e7a269f|1', 'exchange_trade_id': '5c6e433715ba2bdd177219d30e7a269f|1', 'exchange_id': 'DCE', 'instrument_id': 'jd2005', 'direction': 'BUY', 'offset': 'OPEN', 'price': 3205.0, 'volume': 1, 'user_id': 'TQSIM', 'commission': 6.122999999999999}")

        self.assertEqual(order2.order_id, "cf1822ffbc6887782b491044d5e34124")
        self.assertEqual(order2.direction, "BUY")
        self.assertEqual(order2.offset, "OPEN")
        self.assertEqual(order2.volume_orign, 2)
        self.assertEqual(order2.volume_left, 0)
        self.assertEqual(order2.limit_price, 49200.0)
        self.assertEqual(order2.price_type, "LIMIT")
        self.assertEqual(order2.volume_condition, "ANY")
        self.assertEqual(order2.time_condition, "GFD")
        self.assertAlmostEqual(1584423143666130000 / 1e9, order2.insert_date_time / 1e9, places=1)
        self.assertEqual(order2.status, "FINISHED")
        for k, v in order2.trade_records.items():  # 模拟交易为一次性全部成交，因此只有一条成交记录
            self.assertAlmostEqual(1584423143666130000 / 1e9, v.trade_date_time / 1e9, places=1)
            del v.trade_date_time
            self.assertEqual(str(v),
                             "{'order_id': 'cf1822ffbc6887782b491044d5e34124', 'trade_id': 'cf1822ffbc6887782b491044d5e34124|2', 'exchange_trade_id': 'cf1822ffbc6887782b491044d5e34124|2', 'exchange_id': 'SHFE', 'instrument_id': 'cu2004', 'direction': 'BUY', 'offset': 'OPEN', 'price': 49200.0, 'volume': 2, 'user_id': 'TQSIM', 'commission': 23.189999999999998}")

        api.close()

    def test_cancel_order(self):
        """
        撤单

        注：本函数不是回测，重新在盘中生成测试用例script文件时更改为当前可交易的合约代码,且_ins_url可能需修改。
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_cancel_order_simulate.script.lzma"))
        # 测试: 模拟账户
        TqApi.RD = random.Random(2)
        api = TqApi(_ins_url=self.ins_url_2020_04_02, _td_url=self.td_url, _md_url=self.md_url)

        order1 = api.insert_order("DCE.jd2005", "BUY", "OPEN", 1, limit_price=3040)
        order2 = api.insert_order("SHFE.cu2005", "BUY", "OPEN", 2, limit_price=39600)
        api.wait_update()

        self.assertEqual("ALIVE", order1.status)
        self.assertEqual("ALIVE", order2.status)

        api.cancel_order(order1)
        api.cancel_order(order2.order_id)
        while order1.status != "FINISHED" or order2.status != "FINISHED":
            api.wait_update()

        self.assertEqual("FINISHED", order1.status)
        self.assertEqual("FINISHED", order2.status)
        self.assertNotEqual(order1.volume_left, 0)
        self.assertNotEqual(order2.volume_left, 0)

        api.close()

    def test_get_account(self):
        """
        获取账户资金信息
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_get_account_simulate.script.lzma"))
        # 测试: 获取数据
        api = TqApi(_ins_url=self.ins_url_2019_07_03, _td_url=self.td_url, _md_url=self.md_url)
        TqApi.RD = random.Random(4)
        order = api.insert_order("DCE.jd2005", "BUY", "OPEN", 1, limit_price=3340)
        while order.status == "ALIVE":
            api.wait_update()
        account = api.get_account()

        # 测试脚本重新生成后，数据根据实际情况有变化
        self.assertEqual(str(account),
                         "{'currency': 'CNY', 'pre_balance': 10000000.0, 'static_balance': 10000000.0, 'balance': 9999873.877, 'available': 9997016.477, 'ctp_balance': nan, 'ctp_available': nan, 'float_profit': -120.0, 'position_profit': -120.0, 'close_profit': 0.0, 'frozen_margin': 0.0, 'margin': 2857.4, 'frozen_commission': 0.0, 'commission': 6.122999999999999, 'frozen_premium': 0.0, 'premium': 0.0, 'deposit': 0.0, 'withdraw': 0.0, 'risk_ratio': 0.00028574360388405526, 'market_value': 0.0}")
        self.assertEqual(account.currency, "CNY")
        self.assertEqual(account.pre_balance, 10000000.0)
        self.assertEqual(9999873.877, account.balance)
        self.assertEqual(6.122999999999999, account["commission"])
        self.assertEqual(2857.4, account["margin"])
        self.assertEqual(-120.0, account.position_profit)
        api.close()

    def test_get_position(self):
        """
        获取持仓
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_get_position_simulate.script.lzma"))
        # 测试: 获取数据
        api = TqApi(_ins_url=self.ins_url_2019_07_03, _td_url=self.td_url, _md_url=self.md_url)
        order1 = api.insert_order("DCE.jd2005", "BUY", "OPEN", 1, limit_price=3345)
        order2 = api.insert_order("DCE.jd2005", "BUY", "OPEN", 3)
        order3 = api.insert_order("DCE.jd2005", "SELL", "OPEN", 3)

        while order1.status == "ALIVE" or order2.status == "ALIVE" or order3.status == "ALIVE":
            api.wait_update()

        position = api.get_position("DCE.jd2005")
        # 测试脚本重新生成后，数据根据实际情况有变化
        self.assertEqual(
            "{'exchange_id': 'DCE', 'instrument_id': 'jd2005', 'pos_long_his': 0, 'pos_long_today': 4, 'pos_short_his': 0, 'pos_short_today': 3, 'volume_long_today': 4, 'volume_long_his': 0, 'volume_long': 4, 'volume_long_frozen_today': 0, 'volume_long_frozen_his': 0, 'volume_long_frozen': 0, 'volume_short_today': 3, 'volume_short_his': 0, 'volume_short': 3, 'volume_short_frozen_today': 0, 'volume_short_frozen_his': 0, 'volume_short_frozen': 0, 'open_price_long': 3330.0, 'open_price_short': 3324.0, 'open_cost_long': 133200.0, 'open_cost_short': 99720.0, 'position_price_long': 3330.0, 'position_price_short': 3324.0, 'position_cost_long': 133200.0, 'position_cost_short': 99720.0, 'float_profit_long': -200.0, 'float_profit_short': -30.0, 'float_profit': -230.0, 'position_profit_long': -200.0, 'position_profit_short': -30.0, 'position_profit': -230.0, 'margin_long': 11429.6, 'margin_short': 8572.2, 'margin': 20001.800000000003, 'market_value_long': 0.0, 'market_value_short': 0.0, 'market_value': 0.0, 'last_price': 3325.0}",
            str(position))
        self.assertEqual(1, position.pos)
        self.assertEqual(4, position.pos_long)
        self.assertEqual(3, position.pos_short)
        self.assertEqual(position.exchange_id, "DCE")
        self.assertEqual(position.instrument_id, "jd2005")
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
        self.assertEqual(position.open_price_long, 3330.0)
        self.assertEqual(position.open_price_short, 3324.0)
        self.assertEqual(position.open_cost_long, 133200.0)
        self.assertEqual(position.open_cost_short, 99720.0)
        self.assertEqual(position.position_price_long, 3330.0)
        self.assertEqual(position.position_price_short, 3324.0)
        self.assertEqual(position.position_cost_long, 133200.0)
        self.assertEqual(position.position_cost_short, 99720.0)
        self.assertEqual(position.float_profit_long, -200.0)
        self.assertEqual(position.float_profit_short, -30.0)
        self.assertEqual(position.float_profit, -230.0)
        self.assertEqual(position.position_profit_long, -200.0)
        self.assertEqual(position.position_profit_short, -30.0)
        self.assertEqual(position.position_profit, -230.0)
        self.assertEqual(position.margin_long, 11429.6)
        self.assertEqual(position.margin_short, 8572.2)
        self.assertEqual(position.margin, 20001.800000000003)
        self.assertEqual(position.market_value_long, 0.0)
        self.assertEqual(position.market_value_short, 0.0)
        self.assertEqual(position.market_value, 0.0)
        self.assertEqual(position.last_price, 3325.0)

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
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_get_trade_simulate.script.lzma"))
        # 测试: 模拟账户
        TqApi.RD = random.Random(4)
        api = TqApi(_ins_url=self.ins_url_2019_07_03, _td_url=self.td_url, _md_url=self.md_url)
        order1 = api.insert_order("DCE.jd2005", "BUY", "OPEN", 1)
        order2 = api.insert_order("SHFE.cu2005", "BUY", "OPEN", 2, limit_price=40870)
        while order1.status == "ALIVE" or order2.status == "ALIVE":
            api.wait_update()

        trade1 = api.get_trade("1710cf5327ac435a7a97c643656412a9|1")
        trade2 = api.get_trade("8ca5996666ceab360512bd1311072231|2")
        self.assertAlmostEqual(1586414355666978000 / 1e9, trade1.trade_date_time / 1e9, places=1)
        self.assertAlmostEqual(1586414355667884000 / 1e9, trade2.trade_date_time / 1e9, places=1)
        del trade1["trade_date_time"]
        del trade2["trade_date_time"]
        self.assertEqual(str(trade1),
                         "{'order_id': '1710cf5327ac435a7a97c643656412a9', 'trade_id': '1710cf5327ac435a7a97c643656412a9|1', 'exchange_trade_id': '1710cf5327ac435a7a97c643656412a9|1', 'exchange_id': 'DCE', 'instrument_id': 'jd2005', 'direction': 'BUY', 'offset': 'OPEN', 'price': 3317.0, 'volume': 1, 'user_id': 'TQSIM', 'commission': 6.122999999999999}")
        self.assertEqual(str(trade2),
                         "{'order_id': '8ca5996666ceab360512bd1311072231', 'trade_id': '8ca5996666ceab360512bd1311072231|2', 'exchange_trade_id': '8ca5996666ceab360512bd1311072231|2', 'exchange_id': 'SHFE', 'instrument_id': 'cu2005', 'direction': 'BUY', 'offset': 'OPEN', 'price': 40870.0, 'volume': 2, 'user_id': 'TQSIM', 'commission': 23.189999999999998}")
        self.assertEqual(trade1.direction, "BUY")
        self.assertEqual(trade1.offset, "OPEN")
        self.assertEqual(trade1.price, 3317.0)
        self.assertEqual(trade1.volume, 1)
        self.assertEqual(trade1.commission, 6.122999999999999)

        self.assertEqual(trade2.direction, "BUY")
        self.assertEqual(trade2.offset, "OPEN")
        self.assertEqual(trade2.price, 40870.0)
        self.assertEqual(trade2.volume, 2)
        self.assertEqual(trade2.commission, 23.189999999999998)
        api.close()

    def test_get_order(self):
        """
        获取委托单信息
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_get_order_simulate.script.lzma"))
        # 测试: 模拟账户下单
        TqApi.RD = random.Random(4)
        api = TqApi(_ins_url=self.ins_url_2019_07_03, _td_url=self.td_url, _md_url=self.md_url)
        order1 = api.insert_order("DCE.jd2005", "BUY", "OPEN", 1)
        order2 = api.insert_order("SHFE.cu2005", "SELL", "OPEN", 2, limit_price=40750)
        while order1.status == "ALIVE" or order2.status == "ALIVE":
            api.wait_update()

        get_order1 = api.get_order(order1.order_id)
        get_order2 = api.get_order(order2.order_id)

        self.assertEqual(get_order1.order_id, "1710cf5327ac435a7a97c643656412a9")
        self.assertEqual(get_order1.direction, "BUY")
        self.assertEqual(get_order1.offset, "OPEN")
        self.assertEqual(get_order1.volume_orign, 1)
        self.assertEqual(get_order1.volume_left, 0)
        self.assertNotEqual(get_order1.limit_price, get_order1.limit_price)  # 判断nan
        self.assertEqual(get_order1.price_type, "ANY")
        self.assertEqual(get_order1.volume_condition, "ANY")
        self.assertEqual(get_order1.time_condition, "IOC")
        # 因为TqSim模拟交易的 insert_date_time 不是固定值，所以改为判断范围（前后100毫秒）
        self.assertAlmostEqual(1586415071223454000 / 1e9, get_order1.insert_date_time / 1e9, places=1)
        self.assertEqual(get_order1.last_msg, "全部成交")
        self.assertEqual(get_order1.status, "FINISHED")
        self.assertEqual(get_order1.frozen_margin, 0)

        self.assertEqual(get_order2.order_id, "8ca5996666ceab360512bd1311072231")
        self.assertEqual(get_order2.direction, "SELL")
        self.assertEqual(get_order2.offset, "OPEN")
        self.assertEqual(get_order2.volume_orign, 2)
        self.assertEqual(get_order2.volume_left, 0)
        self.assertEqual(get_order2.limit_price, 40750)
        self.assertEqual(get_order2.price_type, "LIMIT")
        self.assertEqual(get_order2.volume_condition, "ANY")
        self.assertEqual(get_order2.time_condition, "GFD")
        self.assertAlmostEqual(1586415071224110000 / 1e9, get_order2["insert_date_time"] / 1e9, places=1)
        self.assertEqual(get_order2["last_msg"], "全部成交")
        self.assertEqual(get_order2["status"], "FINISHED")
        self.assertEqual(get_order2.frozen_margin, 0)

        del get_order1["insert_date_time"]
        del get_order2["insert_date_time"]
        self.assertEqual(str(get_order1),
                         "{'order_id': '1710cf5327ac435a7a97c643656412a9', 'exchange_order_id': '1710cf5327ac435a7a97c643656412a9', 'exchange_id': 'DCE', 'instrument_id': 'jd2005', 'direction': 'BUY', 'offset': 'OPEN', 'volume_orign': 1, 'volume_left': 0, 'limit_price': nan, 'price_type': 'ANY', 'volume_condition': 'ANY', 'time_condition': 'IOC', 'last_msg': '全部成交', 'status': 'FINISHED', 'user_id': 'TQSIM', 'frozen_margin': 0.0, 'frozen_premium': 0.0}")
        self.assertEqual(str(get_order2),
                         "{'order_id': '8ca5996666ceab360512bd1311072231', 'exchange_order_id': '8ca5996666ceab360512bd1311072231', 'exchange_id': 'SHFE', 'instrument_id': 'cu2005', 'direction': 'SELL', 'offset': 'OPEN', 'volume_orign': 2, 'volume_left': 0, 'limit_price': 40750.0, 'price_type': 'LIMIT', 'volume_condition': 'ANY', 'time_condition': 'GFD', 'last_msg': '全部成交', 'status': 'FINISHED', 'user_id': 'TQSIM', 'frozen_margin': 0.0, 'frozen_premium': 0.0}")

        api.close()

    # 期权模拟交易盘中测试

    def test_insert_order_option(self):
        """
            期权下单
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file",
                                   "test_td_basic_insert_order_simulate_option.script.lzma"))
        # 测试: 模拟账户下单
        # 非回测, 则需在盘中生成测试脚本: 测试脚本重新生成后，数据根据实际情况有变化,因此需要修改assert语句的内容
        TqApi.RD = random.Random(2)
        api = TqApi(_ins_url=self.ins_url_2020_04_02, _td_url=self.td_url, _md_url=self.md_url)

        order1 = api.insert_order("SHFE.cu2006C47000", "BUY", "OPEN", 1, limit_price=135)
        order2 = api.insert_order("CZCE.SR007C5600", "SELL", "OPEN", 2, limit_price=30)
        order3 = api.insert_order("DCE.m2007-P-2900", "BUY", "OPEN", 3, limit_price=192)

        while order1.status == "ALIVE" or order2.status == "ALIVE" or order3.status == "ALIVE":
            api.wait_update()

        self.assertEqual(order1.order_id, "5c6e433715ba2bdd177219d30e7a269f")
        self.assertEqual(order1.direction, "BUY")
        self.assertEqual(order1.offset, "OPEN")
        self.assertEqual(order1.volume_orign, 1)
        self.assertEqual(order1.volume_left, 0)
        self.assertEqual(order1.limit_price, 135.0)
        self.assertEqual(order1.price_type, "LIMIT")
        self.assertEqual(order1.volume_condition, "ANY")
        self.assertEqual(order1.time_condition, "GFD")
        self.assertAlmostEqual(1586829882005334000 / 1e9, order1.insert_date_time / 1e9, places=1)
        self.assertEqual(order1.status, "FINISHED")
        for k, v in order1.trade_records.items():  # 模拟交易为一次性全部成交，因此只有一条成交记录
            self.assertAlmostEqual(1586829882005979000 / 1e9, v.trade_date_time / 1e9, places=1)
            del v.trade_date_time
            self.assertEqual(str(v),
                             "{'order_id': '5c6e433715ba2bdd177219d30e7a269f', 'trade_id': '5c6e433715ba2bdd177219d30e7a269f|1', 'exchange_trade_id': '5c6e433715ba2bdd177219d30e7a269f|1', 'exchange_id': 'SHFE', 'instrument_id': 'cu2006C47000', 'direction': 'BUY', 'offset': 'OPEN', 'price': 135.0, 'volume': 1, 'user_id': 'TQSIM', 'commission': 10}")

        self.assertEqual(order2.order_id, "cf1822ffbc6887782b491044d5e34124")
        self.assertEqual(order2.direction, "SELL")
        self.assertEqual(order2.offset, "OPEN")
        self.assertEqual(order2.volume_orign, 2)
        self.assertEqual(order2.volume_left, 0)
        self.assertEqual(order2.limit_price, 30.0)
        self.assertEqual(order2.price_type, "LIMIT")
        self.assertEqual(order2.volume_condition, "ANY")
        self.assertEqual(order2.time_condition, "GFD")
        self.assertAlmostEqual(1586829882236154000 / 1e9, order2.insert_date_time / 1e9, places=1)
        self.assertEqual(order2.status, "FINISHED")
        for k, v in order2.trade_records.items():  # 模拟交易为一次性全部成交，因此只有一条成交记录
            self.assertAlmostEqual(1586829882236518000 / 1e9, v.trade_date_time / 1e9, places=1)
            del v.trade_date_time
            self.assertEqual(str(v),
                             "{'order_id': 'cf1822ffbc6887782b491044d5e34124', 'trade_id': 'cf1822ffbc6887782b491044d5e34124|2', 'exchange_trade_id': 'cf1822ffbc6887782b491044d5e34124|2', 'exchange_id': 'CZCE', 'instrument_id': 'SR007C5600', 'direction': 'SELL', 'offset': 'OPEN', 'price': 30.0, 'volume': 2, 'user_id': 'TQSIM', 'commission': 20}")

        self.assertEqual(order3.order_id, "4067c3584ee207f8da94e3e8ab73738f")
        self.assertEqual(order3.direction, "BUY")
        self.assertEqual(order3.offset, "OPEN")
        self.assertEqual(order3.volume_orign, 3)
        self.assertEqual(order3.volume_left, 0)
        self.assertEqual(order3.limit_price, 192.0)
        self.assertEqual(order3.price_type, "LIMIT")
        self.assertEqual(order3.volume_condition, "ANY")
        self.assertEqual(order3.time_condition, "GFD")
        self.assertAlmostEqual(1586829882228039000 / 1e9, order3.insert_date_time / 1e9, places=1)
        self.assertEqual(order3.status, "FINISHED")
        for k, v in order3.trade_records.items():  # 模拟交易为一次性全部成交，因此只有一条成交记录
            self.assertAlmostEqual(1586829882228603000 / 1e9, v.trade_date_time / 1e9, places=1)
            del v.trade_date_time
            self.assertEqual(str(v),
                             "{'order_id': '4067c3584ee207f8da94e3e8ab73738f', 'trade_id': '4067c3584ee207f8da94e3e8ab73738f|3', 'exchange_trade_id': '4067c3584ee207f8da94e3e8ab73738f|3', 'exchange_id': 'DCE', 'instrument_id': 'm2007-P-2900', 'direction': 'BUY', 'offset': 'OPEN', 'price': 192.0, 'volume': 3, 'user_id': 'TQSIM', 'commission': 30}")

        api.close()

    def test_cancel_order_option(self):
        """
            撤单
            注：本函数不是回测，重新盘中生成测试用例script文件时更改为当前可交易的合约代码,且_ins_url可能需修改。
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_cancel_order_simulate_option.script.lzma"))
        # 测试: 模拟账户
        TqApi.RD = random.Random(2)
        api = TqApi(_ins_url=self.ins_url_2020_04_02, _td_url=self.td_url, _md_url=self.md_url)

        order1 = api.insert_order("DCE.m2007-P-2900", "BUY", "OPEN", 1, limit_price=150)
        order2 = api.insert_order("SHFE.cu2006C47000", "BUY", "OPEN", 2, limit_price=135)
        api.wait_update()

        self.assertEqual("ALIVE", order1.status)
        self.assertEqual("ALIVE", order2.status)

        api.cancel_order(order1)
        api.cancel_order(order2.order_id)
        while order1.status != "FINISHED" or order2.status != "FINISHED":
            api.wait_update()

        self.assertEqual("FINISHED", order1.status)
        self.assertEqual("FINISHED", order2.status)
        self.assertNotEqual(order1.volume_left, 0)
        self.assertNotEqual(order2.volume_left, 0)

        api.close()

    def test_get_account_option(self):
        """
            获取账户资金信息
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_get_account_simulate_option.script.lzma"))
        # 测试: 获取数据
        api = TqApi(_ins_url=self.ins_url_2020_04_02, _td_url=self.td_url, _md_url=self.md_url)
        TqApi.RD = random.Random(4)

        order1 = api.insert_order("CZCE.SR007C5600", "SELL", "OPEN", 2, limit_price=50)
        order2 = api.insert_order("DCE.m2007-P-2900", "BUY", "OPEN", 3, limit_price=180)

        while order1.status == "ALIVE" or order2.status == "ALIVE":
            api.wait_update()

        account = api.get_account()

        # 测试脚本重新生成后，数据根据实际情况有变化
        self.assertEqual(str(account),
                         "{'currency': 'CNY', 'pre_balance': 10000000.0, 'static_balance': 10000000.0, 'balance': 9998650.0, 'available': 9989752.8, 'ctp_balance': nan, 'ctp_available': nan, 'float_profit': -300.0, 'position_profit': 0.0, 'close_profit': 0.0, 'frozen_margin': 0.0, 'margin': 4797.200000000001, 'frozen_commission': 0.0, 'commission': 50.0, 'frozen_premium': 0.0, 'premium': -5400.0, 'deposit': 0.0, 'withdraw': 0.0, 'risk_ratio': 0.00047978477094407754, 'market_value': 4100.0}")
        self.assertEqual(account.currency, "CNY")
        self.assertEqual(account.pre_balance, 10000000.0)
        self.assertEqual(account.balance, 9998650.0)
        self.assertEqual(account["commission"], 50.0)
        self.assertEqual(account["margin"], 4797.200000000001)
        self.assertEqual(account.position_profit, 0.0)
        self.assertEqual(account.available, 9989752.8)
        self.assertNotEqual(account.ctp_balance, account.ctp_balance)  # nan
        self.assertEqual(account.float_profit, -300.0)
        self.assertEqual(account.position_profit, 0.0)
        self.assertEqual(account.margin, 4797.200000000001)
        self.assertEqual(account.commission, 50.0)
        self.assertEqual(account.premium, -5400.0)
        self.assertEqual(account.risk_ratio, 0.00047978477094407754)
        self.assertEqual(account.market_value, 4100.0)
        api.close()

    def test_get_position_option(self):
        """
            获取持仓
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_get_position_simulate_option.script.lzma"))
        # 测试: 获取数据
        api = TqApi(_ins_url=self.ins_url_2020_04_02, _td_url=self.td_url, _md_url=self.md_url)

        order1 = api.insert_order("CZCE.SR007C5600", "BUY", "OPEN", 2, limit_price=55)
        order2 = api.insert_order("CZCE.SR007C5600", "BUY", "OPEN", 3, limit_price=55)
        order3 = api.insert_order("CZCE.SR007C5600", "SELL", "OPEN", 3, limit_price=10)
        order4 = api.insert_order("CZCE.SR007C5600", "SELL", "OPEN", 3)  # 只有郑商所支持期权市价单
        order5 = api.insert_order("DCE.m2007-P-2900", "BUY", "OPEN", 1)  # 只有郑商所支持期权市价单

        while order1.status == "ALIVE" or order2.status == "ALIVE" or order3.status == "ALIVE" or order4.status == "ALIVE" or order5.status == "ALIVE":
            api.wait_update()
        self.assertEqual(order4.volume_left, 0)
        self.assertEqual(order5.volume_left, 1)

        position = api.get_position("CZCE.SR007C5600")
        position2 = api.get_position("DCE.m2007-P-2900")
        self.assertEqual(0, position2.pos_long)
        self.assertEqual(0, position2.pos_short)

        # 测试脚本重新生成后，数据根据实际情况有变化
        self.assertEqual(
            "{'exchange_id': 'CZCE', 'instrument_id': 'SR007C5600', 'pos_long_his': 0, 'pos_long_today': 5, 'pos_short_his': 0, 'pos_short_today': 6, 'volume_long_today': 5, 'volume_long_his': 0, 'volume_long': 5, 'volume_long_frozen_today': 0, 'volume_long_frozen_his': 0, 'volume_long_frozen': 0, 'volume_short_today': 6, 'volume_short_his': 0, 'volume_short': 6, 'volume_short_frozen_today': 0, 'volume_short_frozen_his': 0, 'volume_short_frozen': 0, 'open_price_long': 55.0, 'open_price_short': 22.5, 'open_cost_long': 2750.0, 'open_cost_short': 1350.0, 'position_price_long': 55.0, 'position_price_short': 22.5, 'position_cost_long': 2750.0, 'position_cost_short': 1350.0, 'float_profit_long': -1000.0, 'float_profit_short': -750.0, 'float_profit': -1750.0, 'position_profit_long': 0.0, 'position_profit_short': 0.0, 'position_profit': 0.0, 'margin_long': 0.0, 'margin_short': 8156.4000000000015, 'margin': 8156.4000000000015, 'market_value_long': 1750.0, 'market_value_short': -2100.0, 'market_value': -350.0, 'last_price': 35.0}",
            str(position))
        self.assertEqual(-1, position.pos)
        self.assertEqual(5, position.pos_long)
        self.assertEqual(6, position.pos_short)
        self.assertEqual(position.exchange_id, "CZCE")
        self.assertEqual(position.instrument_id, "SR007C5600")
        self.assertEqual(position.pos_long_his, 0)
        self.assertEqual(position.pos_long_today, 5)
        self.assertEqual(position.pos_short_his, 0)
        self.assertEqual(position.pos_short_today, 6)
        self.assertEqual(position.volume_long_today, 5)
        self.assertEqual(position.volume_long_his, 0)
        self.assertEqual(position.volume_long, 5)
        self.assertEqual(position.volume_long_frozen_today, 0)
        self.assertEqual(position.volume_long_frozen_his, 0)
        self.assertEqual(position.volume_long_frozen, 0)
        self.assertEqual(position.volume_short_today, 6)
        self.assertEqual(position.volume_short_his, 0)
        self.assertEqual(position.volume_short, 6)
        self.assertEqual(position.volume_short_frozen_today, 0)
        self.assertEqual(position.volume_short_frozen_his, 0)
        self.assertEqual(position.volume_short_frozen, 0)
        self.assertEqual(position.open_price_long, 55.0)
        self.assertEqual(position.open_price_short, 22.5)
        self.assertEqual(position.open_cost_long, 2750.0)
        self.assertEqual(position.open_cost_short, 1350.0)
        self.assertEqual(position.position_price_long, 55.0)
        self.assertEqual(position.position_price_short, 22.5)
        self.assertEqual(position.position_cost_long, 2750.0)
        self.assertEqual(position.position_cost_short, 1350.0)
        self.assertEqual(position.float_profit_long, -1000.0)
        self.assertEqual(position.float_profit_short, -750.0)
        self.assertEqual(position.float_profit, -1750.0)
        self.assertEqual(position.position_profit_long, 0.0)
        self.assertEqual(position.position_profit_short, 0.0)
        self.assertEqual(position.position_profit, 0.0)
        self.assertEqual(position.margin_long, 0.0)
        self.assertEqual(position.margin_short, 8156.4000000000015)
        self.assertEqual(position.margin, 8156.4000000000015)
        self.assertEqual(position.market_value_long, 1750.0)
        self.assertEqual(position.market_value_short, -2100.0)
        self.assertEqual(position.market_value, -350.0)
        self.assertEqual(position.last_price, 35.0)

        # 其他取值方式测试
        self.assertEqual(position["pos_long_today"], 5)
        self.assertEqual(position["pos_short_today"], 6)
        self.assertEqual(position["volume_long_his"], 0)
        self.assertEqual(position["volume_long"], 5)

        api.close()

    def test_get_trade_option(self):
        """
            获取成交记录
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_td_basic_get_trade_simulate_option.script.lzma"))
        # 测试: 模拟账户
        TqApi.RD = random.Random(4)
        api = TqApi(_ins_url=self.ins_url_2020_04_02, _td_url=self.td_url, _md_url=self.md_url)
        order1 = api.insert_order("CZCE.SR007C5600", "SELL", "OPEN", 1, limit_price=50)
        order2 = api.insert_order("DCE.m2007-P-2900", "BUY", "OPEN", 2, limit_price=180)

        while order1.status == "ALIVE" or order2.status == "ALIVE":
            api.wait_update()

        trade1 = api.get_trade("1710cf5327ac435a7a97c643656412a9|1")
        trade2 = api.get_trade("8ca5996666ceab360512bd1311072231|2")
        self.assertAlmostEqual(1586501231007428000 / 1e9, trade1.trade_date_time / 1e9, places=1)
        self.assertAlmostEqual(1586501233361505000 / 1e9, trade2.trade_date_time / 1e9, places=1)
        del trade1["trade_date_time"]
        del trade2["trade_date_time"]
        self.assertEqual(str(trade1),
                         "{'order_id': '1710cf5327ac435a7a97c643656412a9', 'trade_id': '1710cf5327ac435a7a97c643656412a9|1', 'exchange_trade_id': '1710cf5327ac435a7a97c643656412a9|1', 'exchange_id': 'CZCE', 'instrument_id': 'SR007C5600', 'direction': 'SELL', 'offset': 'OPEN', 'price': 50.0, 'volume': 1, 'user_id': 'TQSIM', 'commission': 10}")
        self.assertEqual(str(trade2),
                         "{'order_id': '8ca5996666ceab360512bd1311072231', 'trade_id': '8ca5996666ceab360512bd1311072231|2', 'exchange_trade_id': '8ca5996666ceab360512bd1311072231|2', 'exchange_id': 'DCE', 'instrument_id': 'm2007-P-2900', 'direction': 'BUY', 'offset': 'OPEN', 'price': 180.0, 'volume': 2, 'user_id': 'TQSIM', 'commission': 20}")
        self.assertEqual(trade1.direction, "SELL")
        self.assertEqual(trade1.offset, "OPEN")
        self.assertEqual(trade1.price, 50.0)
        self.assertEqual(trade1.volume, 1)
        self.assertEqual(trade1.commission, 10)

        self.assertEqual(trade2.direction, "BUY")
        self.assertEqual(trade2.offset, "OPEN")
        self.assertEqual(trade2.price, 180.0)
        self.assertEqual(trade2.volume, 2)
        self.assertEqual(trade2.commission, 20)
        api.close()
