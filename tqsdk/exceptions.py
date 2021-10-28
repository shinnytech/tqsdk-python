#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

import sys


class BacktestFinished(Exception):
    """
    回测结束会抛出此例外

    Example::

        from datetime import date
        from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished, TqSim

        sim = TqSim()
        api = TqApi(account=sim,
                    backtest=TqBacktest(start_dt=date(2018, 5, 1), end_dt=date(2018, 6, 1)),
                    auth=TqAuth("信易账户", "账户密码"))

        klines = api.get_kline_serial("DCE.m1901", 5 * 60, data_length=15)  # 获得 m1901 5分钟K线的引用
        target_pos = TargetPosTask(api, "DCE.m1901")

        try:
            while True:  # 策略代码
                api.wait_update()
                if api.is_changing(klines):
                    ma = sum(klines.close.iloc[-15:]) / 15
                    if klines.close.iloc[-1] > ma:
                        target_pos.set_target_volume(5)
                    elif klines.close.iloc[-1] < ma:
                        target_pos.set_target_volume(0)
        except BacktestFinished:
            api.close()
            print("回测结束")
            print(sim.tqsdk_stat)  # 回测时间内账户交易信息统计结果

    """

    _orig_excepthook = None

    def __init__(self, api):
        message = "回测结束"
        super().__init__(message)
        if BacktestFinished._orig_excepthook is None:
            BacktestFinished._orig_excepthook = sys.excepthook

            def _except_catcher(type, value, traceback):
                if type is BacktestFinished:
                    if api._web_gui:
                        try:
                            api._print("----------- Backtest finished, press [Ctrl + C] to exit. -----------")
                            while True:
                                api.wait_update()
                        except KeyboardInterrupt:
                            pass

                    if not api._loop.is_closed():
                        api.close()
                    sys.exit()
                BacktestFinished._orig_excepthook(type, value, traceback)

            sys.excepthook = _except_catcher


class TqTimeoutError(Exception):
    """
    获取数据超时会抛出此例外

    Example::

        from tqsdk import TqApi, TqAuth, TqTimeoutError

        api = TqApi(auth=TqAuth("信易账户", "账户密码"))

        symbols = ["CZCE.RS808", "CZCE.RS809", "CZCE.RS908", "CZCE.RS909"]  # CZCE.RS808 没有任何成交数据，无法取到 kline
        klines = {}

        for s in symbols:
            try:
                klines[s] = api.get_kline_serial(s, 5 * 60, data_length=15)
            except TqTimeoutError as e:
                print(f"获取 {s} 合约K线 超时！！！")

        for s in klines:  # 打印出成功取到的 kline
            print(s, klines[s].iloc[-1])

        while True:
            api.wait_update()
            # 策略代码 。。。。

    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class TqBacktestPermissionError(Exception):
    """
    没有回测权限报错
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class TqRiskRuleError(Exception):
    """
    风控触发的报错
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message
