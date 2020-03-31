#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

import os
import unittest
import random
import datetime
from tqsdk import TqApi, TqBacktest, BacktestFinished, TargetPosTask
from tqsdk.test.api.helper import MockServer


class TestLib(unittest.TestCase):
    """
    对lib.py的测试

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
        self.ins_url = "https://openmd.shinnytech.com/t/md/symbols/2019-07-03.json"
        self.ins_url_2019_12_04 = "https://openmd.shinnytech.com/t/md/symbols/2019-12-04.json"
        self.ins_url_2020_02_18 = "https://openmd.shinnytech.com/t/md/symbols/2020-02-18.json"
        self.md_url = "ws://127.0.0.1:5100/"
        self.td_url = "ws://127.0.0.1:5200/"

    def tearDown(self):
        # self.ins.close()
        self.mock.close()

    def test_lib_insert_order_time_check_1(self):
        """
        lib下单时间判断测试1

        回测时间:
            周一21:00 - 周二10:00
        合约订阅：
            无夜盘; 有夜盘24：00结束; 有夜盘25：00结束
        测试：
            21：00起始时刻两个有夜盘合约立即下單，无夜盘合约第二日白盘下单；
            23：00某一夜盘合约停止交易后不能下單，另一合约能下單；
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_lib_insert_order_time_check_1.script.lzma"))

        TqApi.RD = random.Random(4)
        api = TqApi(
            backtest=TqBacktest(datetime.datetime(2019, 12, 2, 21, 0, 0), datetime.datetime(2019, 12, 3, 10, 0, 0)),
            _ins_url=self.ins_url_2019_12_04)  # 2019.12.2周一
        symbol1 = "DCE.jd2002"  # 无夜盘
        symbol2 = "SHFE.rb2002"  # 夜盘23点结束
        symbol3 = "SHFE.cu2002"  # 夜盘凌晨1点结束
        quote3 = api.get_quote(symbol3)
        target_pos1 = TargetPosTask(api, symbol1)
        target_pos2 = TargetPosTask(api, symbol2)
        target_pos3 = TargetPosTask(api, symbol3)
        position1 = api.get_position(symbol1)
        position2 = api.get_position(symbol2)
        position3 = api.get_position(symbol3)
        orders = api.get_order()
        try:
            # 1 21：00起始时刻有夜盘合约立即下單，无夜盘合约第二日白盘下单；
            target_pos1.set_target_volume(1)
            target_pos2.set_target_volume(2)
            target_pos3.set_target_volume(3)
            while datetime.datetime.strptime(quote3.datetime, "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime(2019, 12, 2,
                                                                                                          21, 2):
                api.wait_update()
            self.assertEqual(len(orders), 2)
            self.assertEqual(position1.pos, 0)
            self.assertEqual(position2.pos, 2)
            self.assertEqual(position3.pos, 3)

            # 2 23：00某一夜盘合约停止交易后不能下單，另一合约能下單；
            while datetime.datetime.strptime(quote3.datetime, "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime(2019, 12, 3,
                                                                                                          0, 0):
                api.wait_update()
            target_pos1.set_target_volume(4)
            target_pos2.set_target_volume(5)
            target_pos3.set_target_volume(6)
            while datetime.datetime.strptime(quote3.datetime, "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime(2019, 12, 3,
                                                                                                          0, 30):
                api.wait_update()
            self.assertEqual(len(orders), 3)
            self.assertEqual(position1.pos, 0)
            self.assertEqual(position2.pos, 2)
            self.assertEqual(position3.pos, 6)

            while True:
                api.wait_update()
        except BacktestFinished:
            # 验证下單情況
            # 第二个交易日白盘，将所有合约调整到目标手数
            self.assertEqual(len(orders), 5)
            self.assertEqual(position1.pos, 4)
            self.assertEqual(position2.pos, 5)
            self.assertEqual(position3.pos, 6)
            print("回测结束")
            api.close()

    def test_lib_insert_order_time_check_2(self):
        """
        lib下单时间判断测试2

        回测时间：
            10：15 - 10：45
        订阅合约：
            IF、T（无盘中休息时间）,cu（有盘中休息时间）
        测试：
          10:15 - 10:30期间IF和T能立即下单，cu等到10：30以后下单；
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_lib_insert_order_time_check_2.script.lzma"))

        TqApi.RD = random.Random(4)
        api = TqApi(
            backtest=TqBacktest(datetime.datetime(2020, 2, 17, 10, 15, 0), datetime.datetime(2020, 2, 17, 10, 45, 0)),
            _ins_url=self.ins_url_2020_02_18)
        symbol1 = "SHFE.cu2003"
        symbol2 = "CFFEX.T2003"
        symbol3 = "CFFEX.IF2003"
        quote3 = api.get_quote(symbol3)
        position1 = api.get_position(symbol1)
        position2 = api.get_position(symbol2)
        position3 = api.get_position(symbol3)
        target_pos1 = TargetPosTask(api, symbol1)
        target_pos2 = TargetPosTask(api, symbol2)
        target_pos3 = TargetPosTask(api, symbol3)
        orders = api.get_order()
        try:
            # 1  10:15 - 10:30期间IF和T能立即下单，cu等到10：30以后下单；
            target_pos1.set_target_volume(1)
            target_pos2.set_target_volume(2)
            target_pos3.set_target_volume(3)
            while datetime.datetime.strptime(quote3.datetime, "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime(2020, 2, 17,
                                                                                                          10,
                                                                                                          25):
                api.wait_update()
            self.assertEqual(len(orders), 2)
            self.assertEqual(position1.pos, 0)
            self.assertEqual(position2.pos, 2)
            self.assertEqual(position3.pos, 3)
            while True:
                api.wait_update()
        except BacktestFinished:
            # 验证下單情況
            self.assertEqual(len(orders), 3)
            self.assertEqual(position1.pos, 1)
            self.assertEqual(position2.pos, 2)
            self.assertEqual(position3.pos, 3)
            print("回测结束")
            api.close()

    def test_lib_insert_order_time_check_3(self):
        '''
        lib下单时间判断测试3

        回测时间：
            第一日白盘11:30 - 第二日白盘9：40
        订阅合约：
            IF、T（无盘中休息时间）,cu（有盘中休息时间）
        测试：
            1 T、IF在13：00后下单，cu到13：30后下单
            2 15:00 - 15:15 : T能下单，IF、cu不能下单
            3 2020.2.18 交易所通知cu这段时间没有夜盘，因此之前set的手数到第二个交易日开盘后下单
            4 cu在9点开盘下单，IF在9:30开盘下单
        '''
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_lib_insert_order_time_check_3.script.lzma"))

        TqApi.RD = random.Random(4)
        api = TqApi(backtest=TqBacktest(datetime.datetime(2020, 2, 17, 11, 30), datetime.datetime(2020, 2, 18, 9, 40)),
                    _ins_url=self.ins_url_2020_02_18)
        symbol1 = "SHFE.cu2003"
        symbol2 = "CFFEX.T2003"
        symbol3 = "CFFEX.IF2003"
        quote1 = api.get_quote(symbol1)
        quote2 = api.get_quote(symbol2)
        quote3 = api.get_quote(symbol3)
        position1 = api.get_position(symbol1)
        position2 = api.get_position(symbol2)
        position3 = api.get_position(symbol3)
        target_pos1 = TargetPosTask(api, symbol1)
        target_pos2 = TargetPosTask(api, symbol2)
        target_pos3 = TargetPosTask(api, symbol3)
        orders = api.get_order()
        try:
            # 1 T、IF在13：00后下单，cu到13：30后下单
            target_pos1.set_target_volume(1)
            target_pos2.set_target_volume(2)
            target_pos3.set_target_volume(3)

            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2020-02-17 13:15:00.000000":
                api.wait_update()
            self.assertEqual(len(orders), 2)
            self.assertEqual(position1.pos, 0)
            self.assertEqual(position2.pos, 2)
            self.assertEqual(position3.pos, 3)

            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2020-02-17 13:31:00.000000":
                api.wait_update()
            self.assertEqual(len(orders), 3)
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2020-02-17 13:40:00.000000":
                api.wait_update()
            self.assertEqual(position1.pos, 1)
            self.assertEqual(position2.pos, 2)
            self.assertEqual(position3.pos, 3)

            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2020-02-17 15:00:00.000000":
                api.wait_update()
            # 2 15:00 - 15:15 : T能下单，IF、cu不能下单
            target_pos1.set_target_volume(4)
            target_pos2.set_target_volume(5)
            target_pos3.set_target_volume(6)

            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2020-02-17 15:13:59.000000":
                api.wait_update()
            self.assertEqual(len(orders), 4)
            self.assertEqual(position1.pos, 1)
            self.assertEqual(position2.pos, 5)
            self.assertEqual(position3.pos, 3)

            # 3 2020.2.18 交易所通知cu这段时间没有夜盘，因此之前set的手数到第二个交易日开盘后下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2020-02-18 09:00:00.0000":
                api.wait_update()
            self.assertEqual(len(orders), 4)
            self.assertEqual(position1.pos, 1)
            self.assertEqual(position2.pos, 5)
            self.assertEqual(position3.pos, 3)
            # 4 cu在9点开盘下单，IF在9:30开盘下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2020-02-18 09:20:00.0000":
                api.wait_update()
            self.assertEqual(len(orders), 5)
            self.assertEqual(position1.pos, 4)
            self.assertEqual(position2.pos, 5)
            self.assertEqual(position3.pos, 3)
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2020-02-18 09:35:00.0000":
                api.wait_update()
            self.assertEqual(len(orders), 6)
            self.assertEqual(position1.pos, 4)
            self.assertEqual(position2.pos, 5)
            self.assertEqual(position3.pos, 6)

            while True:
                api.wait_update()
        except BacktestFinished:
            self.assertEqual(len(orders), 6)
            self.assertEqual(position1.pos, 4)
            self.assertEqual(position2.pos, 5)
            self.assertEqual(position3.pos, 6)
            api.close()

    def test_lib_insert_order_time_check_4(self):
        '''
        lib下单时间判断测试4

        回测时间：
            起始交易日（datetime.date）为周一
        订阅合约：
            cu（有夜盘,凌晨1点结束夜盘）,rb（夜盘23点结束）,jd（无夜盘）
        测试：
            (测试周五夜盘21点到周六凌晨1点及周一夜盘、周二白盘)
            1 周五晚21：00之后: cu、rb能下单, jd到周一的9点后下单
            2 周六凌晨1点前：cu能下单
            3 周一早9点后都能下单
            4 周一晚21点后cu、rb能下单
            5 周二白盘开始后，jd能下单
            '''
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_lib_insert_order_time_check_4.script.lzma"))

        TqApi.RD = random.Random(4)
        api = TqApi(backtest=TqBacktest(datetime.date(2019, 12, 2), datetime.date(2019, 12, 3)),
                    _ins_url=self.ins_url_2019_12_04)  # 2019.12.2:周一
        symbol1 = "SHFE.cu2002"  # 有夜盘,凌晨1点结束夜盘
        symbol2 = "SHFE.rb2002"  # 夜盘23点结束
        symbol3 = "DCE.jd2002"  # 无夜盘
        quote1 = api.get_quote(symbol1)
        quote2 = api.get_quote(symbol2)
        quote3 = api.get_quote(symbol3)
        position1 = api.get_position(symbol1)
        position2 = api.get_position(symbol2)
        position3 = api.get_position(symbol3)
        target_pos1 = TargetPosTask(api, symbol1)
        target_pos2 = TargetPosTask(api, symbol2)
        target_pos3 = TargetPosTask(api, symbol3)
        orders = api.get_order()
        try:
            # 1 周五晚21：00之后: cu、rb能下单, jd到周一的9点后下单
            target_pos1.set_target_volume(1)
            target_pos2.set_target_volume(2)
            target_pos3.set_target_volume(3)
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-11-29 21:05:00.000000":
                api.wait_update()
            self.assertEqual(len(orders), 2)
            self.assertEqual(position1.pos, 1)
            self.assertEqual(position2.pos, 2)
            self.assertEqual(position3.pos, 0)

            # 2 周五23点后到周六凌晨1点前：cu能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-11-29 23:00:00.000000":
                api.wait_update()
            target_pos1.set_target_volume(4)
            target_pos2.set_target_volume(5)
            target_pos3.set_target_volume(6)
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-11-29 23:05:00.000000":
                api.wait_update()
            self.assertEqual(len(orders), 3)
            self.assertEqual(position1.pos, 4)
            self.assertEqual(position2.pos, 2)
            self.assertEqual(position3.pos, 0)

            # 3 周一早9点后都能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-12-02 09:05:00.000000":
                api.wait_update()
            self.assertEqual(len(orders), 5)
            self.assertEqual(position1.pos, 4)
            self.assertEqual(position2.pos, 5)
            self.assertEqual(position3.pos, 6)

            # 4 周一晚21点后cu、rb能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-12-02 21:00:00.000000":
                api.wait_update()
            target_pos1.set_target_volume(0)
            target_pos2.set_target_volume(0)
            target_pos3.set_target_volume(0)
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-12-02 21:15:00.000000":
                api.wait_update()
            self.assertEqual(len(orders), 7)
            self.assertEqual(position1.pos, 0)
            self.assertEqual(position2.pos, 0)
            self.assertEqual(position3.pos, 6)

            # 5 周二白盘开始后，jd能下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-12-03 09:02:00.000000":
                api.wait_update()
            self.assertEqual(len(orders), 8)

            while True:
                api.wait_update()
        except BacktestFinished:
            self.assertEqual(len(orders), 8)
            self.assertEqual(position1.pos, 0)
            self.assertEqual(position2.pos, 0)
            self.assertEqual(position3.pos, 0)
            api.close()

    def test_lib_insert_order_time_check_5(self):
        '''
        lib下单时间判断测试5

        回测时间：
            起始交易日（datetime.date）在非周一
        订阅:
            cu（有夜盘,凌晨1点结束夜盘）,rb（夜盘23点结束）,jd（无夜盘）
        测试：
            1 起始回测在21点后rb、cu下单，到第二日9点后jd下单
            2 本交易日白盘9：00后jd下单
        '''
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_lib_insert_order_time_check_5.script.lzma"))

        TqApi.RD = random.Random(4)
        api = TqApi(backtest=TqBacktest(datetime.date(2019, 12, 3), datetime.date(2019, 12, 4)),
                    _ins_url=self.ins_url_2019_12_04)  # 2019, 12, 3:周二
        symbol1 = "SHFE.cu2002"  # 有夜盘,凌晨1点结束夜盘
        symbol2 = "SHFE.rb2002"  # 夜盘23点结束
        symbol3 = "DCE.jd2002"  # 无夜盘
        quote1 = api.get_quote(symbol1)
        quote2 = api.get_quote(symbol2)
        quote3 = api.get_quote(symbol3)
        position1 = api.get_position(symbol1)
        position2 = api.get_position(symbol2)
        position3 = api.get_position(symbol3)
        target_pos1 = TargetPosTask(api, symbol1)
        target_pos2 = TargetPosTask(api, symbol2)
        target_pos3 = TargetPosTask(api, symbol3)
        orders = api.get_order()
        try:
            # 1 起始回测在21点后rb、cu下单，到第二日9点后jd下单
            target_pos1.set_target_volume(1)
            target_pos2.set_target_volume(2)
            target_pos3.set_target_volume(3)
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-12-02 21:05:00.000000":
                api.wait_update()
            self.assertEqual(len(orders), 2)
            self.assertEqual(position1.pos, 1)
            self.assertEqual(position2.pos, 2)
            self.assertEqual(position3.pos, 0)
            # 2 本交易日白盘9：00后jd下单
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-12-03 09:02:00.000000":
                api.wait_update()
            self.assertEqual(len(orders), 3)
            while True:
                api.wait_update()
        except BacktestFinished:
            self.assertEqual(len(orders), 3)
            self.assertEqual(position1.pos, 1)
            self.assertEqual(position2.pos, 2)
            self.assertEqual(position3.pos, 3)
            api.close()

    def test_lib_insert_order_time_check_6(self):
        '''
        lib下单时间判断测试6

        测试：
            设置目标持仓后在TargetPosTask未下单前调整目标持仓， lib等到10：30有行情之后调整到的是最新目标持仓
        '''
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_lib_insert_order_time_check_6.script.lzma"))

        TqApi.RD = random.Random(4)
        api = TqApi(
            backtest=TqBacktest(start_dt=datetime.datetime(2019, 7, 11, 10, 15), end_dt=datetime.date(2019, 7, 12)),
            _ins_url=self.ins_url_2019_12_04)
        symbol1 = "SHFE.cu1908"
        symbol2 = "CFFEX.IF1908"  # 用于行情推进，到10：20
        quote2 = api.get_quote(symbol2)
        target_pos = TargetPosTask(api, symbol1)
        orders = api.get_order()
        position = api.get_position(symbol1)
        try:
            target_pos.set_target_volume(5)
            while quote2.datetime < "2019-07-11 10:20:00.000000":
                api.wait_update()
            self.assertEqual(len(api.get_order()), 0)
            target_pos.set_target_volume(2)
            while quote2.datetime < "2019-07-11 10:25:00.000000":
                api.wait_update()
            self.assertEqual(len(api.get_order()), 0)
            while True:
                api.wait_update()
        except BacktestFinished:
            self.assertEqual(len(orders), 1)
            self.assertEqual(position.pos, 2)
            api.close()

    def test_lib_insert_order_time_check_7(self):
        """
        lib下单时间判断测试7

        订阅合约：
            订阅周六有行情的和周六无行情的
        测试：
            (测试:回测从周六开始时 可交易时间段的计算、判断)
            1 回测刚开始:current_datetime 为 0:00 , 只有cu能下单，另外两个合约直到白盘9点下单
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.mock.run(os.path.join(dir_path, "log_file", "test_lib_insert_order_time_check_7.script.lzma"))

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
        target_pos1 = TargetPosTask(api, symbol1)
        target_pos2 = TargetPosTask(api, symbol2)
        target_pos3 = TargetPosTask(api, symbol3)
        orders = api.get_order()
        try:
            # 1 回测刚开始:current_datetime 为 0:00 , 只有cu能下单，另外两个合约直到白盘9点下单
            target_pos1.set_target_volume(1)
            target_pos2.set_target_volume(2)
            target_pos3.set_target_volume(3)
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-11-30 00:02:00.000000":
                api.wait_update()
            self.assertEqual(len(orders), 1)
            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-11-30 00:15:00.000000":
                api.wait_update()
            self.assertEqual(len(orders), 1)
            self.assertEqual(position1.pos, 1)
            self.assertEqual(position2.pos, 0)
            self.assertEqual(position3.pos, 0)

            while max(quote1.datetime, quote2.datetime, quote3.datetime) < "2019-12-02 09:05:00.000000":
                api.wait_update()
            self.assertEqual(len(orders), 3)
            self.assertEqual(position1.pos, 1)
            self.assertEqual(position2.pos, 2)
            self.assertEqual(position3.pos, 3)

            while True:
                api.wait_update()
        except BacktestFinished:
            self.assertEqual(position1.pos, 1)
            self.assertEqual(position2.pos, 2)
            self.assertEqual(position3.pos, 3)
            api.close()
