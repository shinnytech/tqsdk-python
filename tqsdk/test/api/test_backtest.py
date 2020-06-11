#!usr/bin/env python3
#-*- coding:utf-8 -*-
__author__ = 'yanqiong'

import os
import unittest
import random
import datetime
from tqsdk import TqApi, TqBacktest, BacktestFinished, utils
from tqsdk.test.api.helper import MockServer, MockInsServer


class TestTdBacktest(unittest.TestCase):
    """
    回测时的交易测试.

    注：
    1. 在本地运行测试用例前需设置运行环境变量(Environment variables), 保证api中dict及set等类型的数据序列在每次运行时元素顺序一致: PYTHONHASHSEED=32
    2. 若测试用例中调用了会使用uuid的功能函数时（如insert_order()会使用uuid生成order_id）,
        则：在生成script文件时及测试用例中都需设置 utils.RD = random.Random(x), 以保证两次生成的uuid一致, x取值范围为0-2^32
    3. 对盘中的测试用例（即非回测）：因为TqSim模拟交易 Order 的 insert_date_time 和 Trade 的 trade_date_time 不是固定值，所以改为判断范围。
        盘中时：self.assertAlmostEqual(1575292560005832000 / 1e9, order1.insert_date_time / 1e9, places=1)
        回测时：self.assertEqual(1575291600000000000, order1.insert_date_time)
    """

    def setUp(self):
        self.ins = MockInsServer(5000)
        self.ins_url_2019_07_03 = "http://127.0.0.1:5000/t/md/symbols/2019-07-03.json"

    def tearDown(self):
        self.ins.close()

    def test_backtest(self):
        """
        回测耗时测试
        """
        # 预设服务器端响应
        dir_path = os.path.dirname(os.path.realpath(__file__))
        log_path = os.path.join(dir_path, "log_file", "test_backtest.script.lzma")
        times = []
        for i in range(10):
            mock = MockServer()
            md_url = "ws://127.0.0.1:5100/"
            td_url = "ws://127.0.0.1:5200/"
            mock.run(log_path)
            utils.RD = random.Random(4)
            try:
                start = datetime.datetime.now()
                backtest = TqBacktest(start_dt=datetime.datetime(2019, 8, 10), end_dt=datetime.datetime(2019, 9, 11))
                api = TqApi(backtest=backtest, _ins_url=self.ins_url_2019_07_03, _md_url=md_url, _td_url=td_url)
                symbol = "DCE.m2005"
                klines = api.get_kline_serial(symbol, duration_seconds=60)
                while True:
                    api.wait_update()
            except BacktestFinished:
                delta = datetime.datetime.now() - start
                self.assertLess(delta.seconds, 40)
                times.append(delta.seconds + delta.microseconds * 1e-6)
                # print(delta.seconds + delta.microseconds * 1e-6)
                api.close()
                mock.close()
        print(times)
        print(sum(times))
        # ========== 修改前 ============
        # [20.058858, 18.350247, 19.814365, 19.169111, 18.58476, 18.734992, 18.637698, 18.527309, 18.654314, 18.652076]
        # 189.18373
        # [19.259541, 18.033101, 19.00233, 18.137294, 17.934805, 17.953442, 18.236877, 18.747868, 18.131909, 18.198524]
        # 183.635691
        # [17.987942, 17.700216, 21.198522, 18.957277, 18.745181, 18.159449, 16.900526, 18.356927, 18.58457, 20.561317]
        # 187.15192699999997
        # [16.854246, 16.377385, 16.75057, 17.49881, 18.408146, 20.370532, 23.466372, 20.019639, 16.666278, 16.749415]
        # 183.161393
        # ========== 修改后 ============
        # [19.544926, 19.034779, 21.507498, 21.350583, 25.793425, 20.315148, 19.989836, 20.932867, 20.023674, 20.198707]
        # 208.691443
        # [17.251422, 18.158654, 26.825384, 24.231112, 20.700655, 19.715653, 19.95414, 20.494304, 20.119251, 20.927037]
        # 208.377612
        # [21.386568, 21.046802, 22.369997, 21.05664, 21.414775, 24.902344, 19.702351, 19.393192, 19.351624, 19.559272]
        # 210.18356499999996
        # [21.918383, 19.350111, 23.959561, 22.413958, 17.849031, 18.16576, 19.929737, 22.728424, 20.465735, 20.808115]
        # 207.58881499999995
