#!/usr/bin/env python
#  -*- coding: utf-8 -*-
"""
天勤接口的PYTHON封装, 提供以下功能

* 连接行情和交易服务器或天勤终端的websocket扩展接口, 接收行情及交易推送数据
* 在内存中存储管理一份完整的业务数据(行情+交易), 并在接收到新数据包时更新内存数据
* 通过一批函数接口, 支持用户代码访问业务数据
* 发送交易指令


* PYTHON SDK使用文档: https://doc.shinnytech.com/pysdk/latest/
* 天勤行情终端下载: https://www.shinnytech.com/tianqin
* 天勤使用文档: https://doc.shinnytech.com/tq/latest/
"""
__author__ = 'chengzhi'

import json
import uuid
import sys
import time
import logging
import copy
import asyncio
import functools
import websockets
import requests
import weakref
import pandas as pd
import numpy as np
from .__version__ import __version__
from tqsdk.sim import TqSim
from tqsdk.subaccount import TqSubAccount


class TqApi(object):
    """
    天勤接口及数据管理类.

    通常情况下, 一个线程中应该只有一个TqApi的实例, 它负责维护网络连接, 接收行情及账户数据, 并在内存中维护业务数据截面
    """
    DEFAULT_MD_URL = "wss://openmd.shinnytech.com/t/md/front/mobile"
    DEFAULT_INS_URL = "https://openmd.shinnytech.com/t/md/symbols/latest.json"

    def __init__(self, account=None, url=None, backtest=None, debug=None, loop=None):
        """
        创建天勤接口实例

        Args:
            account (TqAccount/TqSim/str): 交易账号:
                * TqAccount: 使用实盘帐号, 直连行情和交易服务器(不通过天勤终端), 需提供期货公司/帐号/密码

                * TqSim: 使用 Api 自带的模拟功能, 直连行情服务器或连接天勤终端(例如使用历史复盘进行测试)接收行情数据

                * str: 连接天勤终端, 实盘交易填写期货公司提供的帐号, 使用天勤终端内置的模拟交易填写"SIM", 需先在天勤终端内登录交易

            url (str): [可选]指定服务器的地址
                * 当 account 为 TqAccount 类型时, 可以通过该参数指定交易服务器地址, 默认使用 opentd.shinnytech.com. 行情始终使用 openmd.shinnytech.com

                * 当 account 为 TqSim 类型时, 可以通过该参数指定行情服务器地址, 默认使用 openmd.shinnytech.com, 可以指定为天勤终端的地址

                * 当 account 为 str 类型时, 可以通过该参数指定天勤终端的地址, 默认本机

            backtest (TqBacktest): [可选]传入 TqBacktest 对象将进入回测模式, 回测模式下会将帐号转为 TqSim 并只连接 openmd.shinnytech.com 接收行情数据

            debug(str): [可选]将调试信息输出到指定文件, 默认不输出.

            loop(asyncio.AbstractEventLoop): [可选]使用指定的 IOLoop, 默认创建一个新的.

        Example::

            # 使用实盘帐号直连行情和交易服务器
            from tqsdk import TqApi, TqAccount
            api = TqApi(TqAccount("H海通期货", "022631", "123456"))

            # 使用实盘帐号连接天勤终端(需先在天勤终端内登录交易)
            from tqsdk import TqApi
            api = TqApi("022631")

            # 使用模拟帐号直连行情和交易服务器
            from tqsdk import TqApi, TqSim
            api = TqApi(TqSim())

            # 进行策略回测
            from datetime import date
            from tqsdk import TqApi, TqSim, TqBacktest
            api = TqApi(TqSim(), backtest=TqBacktest(start_dt=date(2018, 5, 1), end_dt=date(2018, 10, 1)))
        """
        if account is None:
            msg = """__init__() missing 1 required positional argument: 'account'  
            
只有在天勤中运行策略程序时, 才可以省略账户信息. 如果需要在天勤外运行策略程序, 您必须在创建TqApi时明确提供账号和策略ID, 像这样:

api = TqApi("7382621.abcd")  # 7382621 是期货账号, 必须与天勤当前登录的期货账号一致. abcd 是策略ID, 可以任意设定, 用于策略运行监控 

当天勤处于复盘模式时, 自动创建了一个名叫 "SIM" 的模拟账号, 此时TqApi也需要明确指定 "SIM" 作为期货账号: 
api = TqApi("SIM.abcd") 
"""
            raise TypeError(msg)
        self.loop = asyncio.new_event_loop() if loop is None else loop  # 创建一个新的 ioloop, 避免和其他框架/环境产生干扰
        # 回测需要行情和交易 lockstep, 而 asyncio 没有将内部的 _ready 队列暴露出来, 因此 monkey patch call_soon 函数用来判断是否有任务等待执行
        self.loop.call_soon = functools.partial(self._call_soon, self.loop.call_soon)
        self.event_rev, self.check_rev = 0, 0
        self.requests = {}  # 记录已发出的请求
        self.serials = {}  # 记录所有数据序列
        self.account_id = account if isinstance(account, str) else account.account_id
        self.logger = logging.getLogger("TqApi")  # 调试信息输出
        if debug and not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)
            sh = logging.StreamHandler()
            sh.setLevel(logging.INFO)
            sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(sh)
            fh = logging.FileHandler(filename=debug)
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(fh)
        self.send_chan, self.recv_chan = TqChan(self), TqChan(self)  # 消息收发队列
        self.data = {"_path": [], "_listener": weakref.WeakSet()}  # 数据存储
        self.diffs = []  # 自上次wait_update返回后收到更新数据的数组
        self.pending_diffs = []  # 从网络上收到的待处理的 diffs, 只在 wait_update 函数执行过程中才可能为非空
        self.prototype = self._gen_prototype()  # 各业务数据的原型, 用于决定默认值及将收到的数据转为特定的类型
        self.tasks = set()  # 由api维护的所有根task，不包含子task，子task由其父task维护
        self.exceptions = []  # 由api维护的所有task抛出的例外
        self.wait_timeout = False  # wait_update 是否触发超时
        if sys.platform.startswith("win"):
            self.create_task(self._windows_patch())  # Windows系统下asyncio不支持KeyboardInterrupt的临时补丁
        self.create_task(self._notify_watcher())  # 监控服务器发送的通知
        self._setup_connection(account, url, backtest)  # 初始化通讯连接
        deadline = time.time() + 60
        try:
            while self.data.get("mdhis_more_data", True) or self.data.get("trade", {}).get(self.account_id, {}).get("trade_more_data", True):
                if not self.wait_update(deadline=deadline):  # 等待连接成功并收取截面数据
                    raise Exception("接收数据超时，请检查客户端及网络是否正常")
        except:
            self.close()
            raise
        self.diffs = []  # 截面数据不算做更新数据

    # ----------------------------------------------------------------------
    def close(self):
        """
        关闭天勤接口实例并释放相应资源

        Example::

            # m1901开多3手
            from tqsdk import TqApi, TqSim
            from contextlib import closing

            with closing(TqApi(TqSim())) as api:
                api.insert_order(symbol="DCE.m1901", direction="BUY", offset="OPEN", volume=3)
        """
        # 检查是否需要发送多余的序列
        for _, serial in self.serials.items():
            self._process_serial_extra_array(serial)
        self._run_until_idle()  # 由于有的处于 ready 状态 task 可能需要报撤单, 因此一直运行到没有 ready 状态的 task
        for task in self.tasks:
            task.cancel()
        while self.tasks:  # 等待 task 执行完成
            self._run_once()
        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        self.loop.close()

    # ----------------------------------------------------------------------
    def get_quote(self, symbol):
        """
        获取指定合约的盘口行情.

        Args:
            symbol (str): 指定合约代码。注意：天勤接口从0.8版本开始，合约代码格式变更为 交易所代码.合约代码 的格式. 可用的交易所代码如下：
                         * CFFEX: 中金所
                         * SHFE: 上期所
                         * DCE: 大商所
                         * CZCE: 郑商所
                         * INE: 能源交易所(原油)

        Returns:
            dict: 返回一个如下结构所示的 dict 对象的引用, 当行情更新时, 此对象的内容会被自动更新

            .. literalinclude:: ../../tqsdk/api.py
                :pyobject: TqApi._gen_quote_prototype
                :dedent: 12
                :start-after: {
                :end-before: }

            注意: 在 tqsdk 还没有收到行情数据包时, 此对象中各项内容为 NaN 或 0

        Example::

            # 获取 SHFE.cu1812 合约的报价
            from tqsdk import TqApi, TqSim

            api = TqApi(TqSim())
            quote = api.get_quote("SHFE.cu1812")
            while True:
                api.wait_update()
                print(quote["last_price"])

            #以上代码将输出
            nan
            nan
            24575.0
            24575.0
            ...
        """
        quote = self._get_obj(self.data, ["quotes", symbol], self.prototype["quotes"]["#"])
        if symbol not in self.requests.setdefault("quotes", set()):
            self.requests["quotes"].add(symbol)
            self.send_chan.send_nowait({
                "aid": "subscribe_quote",
                "ins_list": ",".join(self.requests["quotes"]),
            })
        deadline = time.time() + 30
        while not self.loop.is_running() and quote["datetime"] == "":
            #@todo: merge diffs
            if not self.wait_update(deadline=deadline):
                raise Exception("获取行情超时，请检查客户端及网络是否正常，且合约代码填写正确")
        return quote

    # ----------------------------------------------------------------------
    def get_kline_serial(self, symbol, duration_seconds, data_length=200, chart_id=None):
        """
        获取k线序列数据

        请求指定合约及周期的K线数据. 序列数据会随着时间推进自动更新

        Args:
            symbol (str): 指定合约代码.

            duration_seconds (int): K线数据周期，以秒为单位。例如: 1分钟线为60,1小时线为3600,日线为86400

            data_length (int): 需要获取的序列长度。每个序列最大支持请求 8964 个数据

            chart_id (str): [可选]指定序列id, 默认由 api 自动生成

        Returns:
            pandas.DataFrame: 本函数总是返回一个 pandas.DataFrame 实例. 行数=data_length, 包含以下列:

            id: int, 1234 (k线序列号)
            datetime: int, 1501080715000000000 (K线起点时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
            open: float, 51450.0 (K线起始时刻的最新价)
            high: float, 51450.0 (K线时间范围内的最高价)
            low: float, 51450.0 (K线时间范围内的最低价)
            close: float, 51450.0 (K线结束时刻的最新价)
            volume: int, 11 (K线时间范围内的成交量)
            open_oi: int, 27354 (K线起始时刻的持仓量)
            close_oi: int, 27355 (K线结束时刻的持仓量)

        Example::

            # 获取 SHFE.cu1812 的1分钟线
            from tqsdk import TqApi, TqSim

            api = TqApi(TqSim())
            k_serial = api.get_kline_serial("SHFE.cu1812", 60)
            while True:
                api.wait_update()
                print(k_serial.iloc[-1]["close"])

            # 预计的输出是这样的:
            50970.0
            50970.0
            50960.0
            ...
        """
        if data_length > 8964:
            data_length = 8964
        duration_seconds = int(duration_seconds)  # 转成整数
        dur_id = duration_seconds * 1000000000
        request = (symbol, duration_seconds, data_length, chart_id)
        if request not in self.requests.setdefault("klines", {}):
            serial = self._init_serial(self._get_obj(self.data, ["klines", symbol, str(dur_id)]), data_length, self.prototype["klines"]["*"]["*"]["data"]["@"])
            self.requests["klines"][request] = serial
            self.serials[id(serial["df"])] = serial
            self.send_chan.send_nowait({
                "aid": "set_chart",
                "chart_id": chart_id if chart_id is not None else self._generate_chart_id("realtime", symbol, duration_seconds),
                "ins_list": symbol,
                "duration": dur_id,
                "view_width": data_length,
            })
        else:
            serial = self.requests["klines"][request]
        deadline = time.time() + 30
        while not self.loop.is_running() and not self._is_serial_ready(serial):
            #@todo: merge diffs
            if not self.wait_update(deadline=deadline):
                raise Exception("获取行情超时，请检查客户端及网络是否正常，且合约代码填写正确")
        return serial["df"]

    # ----------------------------------------------------------------------
    def get_tick_serial(self, symbol, data_length=200, chart_id=None):
        """
        获取tick序列数据

        请求指定合约的Tick序列数据. 序列数据会随着时间推进自动更新

        Args:
            symbol (str): 指定合约代码.

            data_length (int): 需要获取的序列长度。每个序列最大支持请求 8964 个数据

            chart_id (str): [可选]指定序列id, 默认由 api 自动生成

        Returns:
            pandas.DataFrame: 本函数总是返回一个 pandas.DataFrame 实例. 行数=data_length, 包含以下列:

            id: int, tick序列号
            datetime: int, 1501074872000000000 (tick从交易所发出的时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
            last_price: float, 3887.0 (最新价)
            average: float, 3820.0 (当日均价)
            highest: float, 3897.0 (当日最高价)
            lowest: float, 3806.0 (当日最低价)
            ask_price1: float, 3886.0 (卖一价)
            ask_volume1: int, 3 (卖一量)
            bid_price1: float, 3881.0 (买一价)
            bid_volume1: int, 18 (买一量)
            volume: int 7823 (当日成交量)
            amount: float, 19237841.0 (成交额)
            open_interest: int, 1941 (持仓量)

        Example::

            # 获取 SHFE.cu1812 的Tick序列
            from tqsdk import TqApi, TqSim

            api = TqApi(TqSim())
            serial = api.get_tick_serial("SHFE.cu1812")
            while True:
                api.wait_update()
                print(serial.iloc[-1]["bid_price1"], serial.iloc[-1]["ask_price1"])

            # 预计的输出是这样的:
            50860.0 51580.0
            50860.0 51580.0
            50820.0 51580.0
            ...
        """
        if data_length > 8964:
            data_length = 8964
        request = (symbol, data_length, chart_id)
        if request not in self.requests.setdefault("ticks", {}):
            serial = self._init_serial(self._get_obj(self.data, ["ticks", symbol]), data_length, self.prototype["ticks"]["*"]["data"]["@"])
            self.requests["ticks"][request] = serial
            self.serials[id(serial["df"])] = serial
            self.send_chan.send_nowait({
                "aid": "set_chart",
                "chart_id": chart_id if chart_id is not None else self._generate_chart_id("realtime", symbol, 0),
                "ins_list": symbol,
                "duration": 0,
                "view_width": data_length,
            })
        else:
            serial = self.requests["ticks"][request]
        deadline = time.time() + 30
        while not self.loop.is_running() and not self._is_serial_ready(serial):
            #@todo: merge diffs
            if not self.wait_update(deadline=deadline):
                raise Exception("获取行情超时，请检查客户端及网络是否正常，且合约代码填写正确")
        return serial["df"]

    # ----------------------------------------------------------------------
    def insert_order(self, symbol, direction, offset, volume, limit_price=None, order_id=None):
        """
        发送下单指令

        Args:
            symbol (str): 拟下单的合约symbol, 格式为 交易所代码.合约代码,  例如 "SHFE.cu1801"

            direction (str): "BUY" 或 "SELL"

            offset (str): "OPEN", "CLOSE" 或 "CLOSETODAY"

            volume (int): 需要下单的手数

            limit_price (float): [可选]下单价格, 默认市价单

            order_id (str): [可选]指定下单单号, 默认由 api 自动生成

        Returns:
            dict: 本函数总是返回一个如下结构所示的包含委托单信息的dict的引用. 每当order中信息改变时, 此dict会自动更新.

            .. literalinclude:: ../../tqsdk/api.py
                :pyobject: TqApi._gen_order_prototype
                :dedent: 12
                :start-after: {
                :end-before: }

        Example::

            # 市价开3手 DCE.m1809 多仓
            from tqsdk import TqApi, TqSim

            api = TqApi(TqSim())
            order = api.insert_order(symbol="DCE.m1809", direction="BUY", offset="OPEN", volume=3)
            while True:
                api.wait_update()
                print("单状态: %s, 已成交: %d 手" % (order["status"], order["volume_orign"] - order["volume_left"]))

            # 预计的输出是这样的:
            单状态: ALIVE, 已成交: 0 手
            单状态: ALIVE, 已成交: 0 手
            单状态: FINISHED, 已成交: 3 手
            ...
        """
        if not order_id:
            order_id = self._generate_order_id()
        (exchange_id, instrument_id) = symbol.split(".", 1)
        msg = {
            "aid": "insert_order",
            "user_id": self.account_id,
            "order_id": order_id,
            "exchange_id": exchange_id,
            "instrument_id": instrument_id,
            "direction": direction,
            "offset": offset,
            "volume": volume,
            "volume_condition": "ANY",
        }
        if limit_price is None:
            msg["price_type"] = "ANY"
            msg["time_condition"] = "IOC"
        else:
            msg["price_type"] = "LIMIT"
            msg["time_condition"] = "GFD"
            msg["limit_price"] = limit_price
        self.send_chan.send_nowait(msg)
        order = self.get_order(order_id)
        order.update({
            "order_id": order_id,
            "exchange_id": exchange_id,
            "instrument_id": instrument_id,
            "direction": direction,
            "offset": offset,
            "volume_orign": volume,
            "volume_left": volume,
            "status": "ALIVE",
        })
        return order

    # ----------------------------------------------------------------------
    def cancel_order(self, order_or_order_id):
        """
        发送撤单指令

        Args:
            order_or_order_id (str/dict): 拟撤委托单的 dict 或 单号

        Example::

            # 挂价开3手 DCE.m1809 多仓, 如果价格变化则撤单重下，直到全部成交
            from tqsdk import TqApi, TqSim

            api = TqApi(TqSim())
            quote = api.get_quote("DCE.m1809")
            order = {}

            while True:
                api.wait_update()
                # 当行情有变化且当前挂单价格不优时，则撤单
                if order and api.is_changing(quote) and order["status"] == "ALIVE" and quote["bid_price1"] > order["limit_price"]:
                    print("价格改变，撤单重下")
                    api.cancel_order(order)
                # 当委托单已撤或还没有下单时则下单
                if (not order and api.is_changing(quote)) or (api.is_changing(order) and order["volume_left"] != 0 and order["status"] == "FINISHED"):
                    print("下单: 价格 %f" % quote["bid_price1"])
                    order = api.insert_order(symbol="DCE.m1809", direction="BUY", offset="OPEN", volume=order.get("volume_left", 3), limit_price=quote["bid_price1"])
                if api.is_changing(order):
                    print("单状态: %s, 已成交: %d 手" % (order["status"], order["volume_orign"] - order["volume_left"]))


            # 预计的输出是这样的:
            下单: 价格 3117.000000
            单状态: ALIVE, 已成交: 0 手
            价格改变，撤单重下
            下单: 价格 3118.000000
            单状态: ALIVE, 已成交: 0 手
            单状态: FINISHED, 已成交: 3 手
            ...
        """
        if isinstance(order_or_order_id, dict):
            order_id = order_or_order_id.get("order_id", "")
        else:
            order_id = order_or_order_id
        msg = {
            "aid": "cancel_order",
            "user_id": self.account_id,
            "order_id": order_id,
        }
        self.send_chan.send_nowait(msg)

    # ----------------------------------------------------------------------
    def get_account(self):
        """
        获取用户账户资金信息

        Returns:
            dict: 本函数总是返回一个如下结构所示的包含用户账户资金信息的dict的引用. 每当其中信息改变时, 此dict会自动更新.

            .. literalinclude:: ../../tqsdk/api.py
                :pyobject: TqApi._gen_account_prototype
                :dedent: 12
                :start-after: {
                :end-before: }

            注意: 在 tqsdk 还没有收到账户数据包时, 此对象中各项内容为NaN

        Example::

            # 获取当前浮动盈亏
            from tqsdk import TqApi, TqSim

            api = TqApi(TqSim())
            account = api.get_account()
            while True:
                api.wait_update()
                print(account["float_profit"])

            # 预计的输出是这样的:
            2180.0
            2080.0
            2080.0
            ...
        """
        return self._get_obj(self.data, ["trade", self.account_id, "accounts", "CNY"], self.prototype["trade"]["*"]["accounts"]["@"])

    # ----------------------------------------------------------------------
    def get_position(self, symbol=None):
        """
        获取用户持仓信息

        Args:
            symbol (str): [可选]合约代码, 默认返回所有持仓

        Returns:
            dict: 当指定了symbol时, 返回一个如下结构所示的包含指定symbol持仓信息的引用. 每当其中信息改变时, 此dict会自动更新.

            .. literalinclude:: ../../tqsdk/api.py
                :pyobject: TqApi._gen_position_prototype
                :dedent: 12
                :start-after: {
                :end-before: }

            不带symbol参数调用 get_position 函数, 将返回包含用户所有持仓的一个嵌套dict, 其中每个元素的key为合约代码, value为上述格式的dict

            注意: 在 tqsdk 还没有收到持仓信息时, 此对象中各项内容为空或0

        Example::

            # 获取 DCE.m1809 当前浮动盈亏
            from tqsdk import TqApi, TqSim

            api = TqApi(TqSim())
            position = api.get_position("DCE.m1809")
            while True:
                api.wait_update()
                print(position["float_profit_long"] + position["float_profit_short"])

            # 预计的输出是这样的:
            300.0
            300.0
            330.0
            ...
        """
        if symbol:
            return self._get_obj(self.data, ["trade", self.account_id, "positions", symbol], self.prototype["trade"]["*"]["positions"]["@"])
        return self._get_obj(self.data, ["trade", self.account_id, "positions"])

    # ----------------------------------------------------------------------
    def get_order(self, order_id=None):
        """
        获取用户委托单信息

        Args:
            order_id (str): [可选]单号, 默认返回所有委托单

        Returns:
            dict: 当指定了order_id时, 返回一个如下结构所示的包含指定order_id委托单信息的引用. 每当其中信息改变时, 此dict会自动更新.

            .. literalinclude:: ../../tqsdk/api.py
                :pyobject: TqApi._gen_order_prototype
                :dedent: 12
                :start-after: {
                :end-before: }

            不带order_id参数调用get_order函数, 将返回包含用户所有委托单的一个嵌套dict, 其中每个元素的key为合约代码, value为上述格式的dict

            注意: 在 tqsdk 还没有收到委托单信息时, 此对象中各项内容为空

        Example::

            # 获取当前总挂单手数
            from tqsdk import TqApi, TqSim

            api = TqApi(TqSim())
            orders = api.get_order()
            while True:
                api.wait_update()
                print(sum(o["volume_left"] for oid, o in orders.items() if not oid.startswith("_") and o["status"] == "ALIVE"))

            # 预计的输出是这样的:
            3
            3
            0
            ...
        """
        if order_id:
            return self._get_obj(self.data, ["trade", self.account_id, "orders", order_id], self.prototype["trade"]["*"]["orders"]["@"])
        return self._get_obj(self.data, ["trade", self.account_id, "orders"])

    # ----------------------------------------------------------------------
    def wait_update(self, deadline=None):
        """
        等待业务数据更新

        调用此函数将阻塞当前线程, 等待天勤主进程发送业务数据更新并返回

        Args:
            deadline (float): [可选]指定截止时间，自unix epoch(1970-01-01 00:00:00 GMT)以来的秒数(time.time())。默认没有超时(无限等待)

        Returns:
            bool: 如果收到业务数据更新则返回 True, 如果到截止时间依然没有收到业务数据更新则返回 False

        注意: 由于存在网络延迟, 因此有数据更新不代表之前发出的所有请求都被处理了, 例如::

            from tqsdk import TqApi, TqSim

            api = TqApi(TqSim())
            quote = api.get_quote("SHFE.cu1812")
            api.wait_update()
            print(quote["datetime"])

            可能输出 ""(空字符串), 表示还没有收到该合约的行情
        """
        if self.loop.is_running():
            raise Exception("不能在协程中调用 wait_update, 如需在协程中等待业务数据更新请使用 register_update_notify")
        self.wait_timeout = False
        # 先尝试执行各个task,再请求下个业务数据
        self._run_until_idle()
        # 检查是否需要发送多余的序列
        for _, serial in self.serials.items():
            self._process_serial_extra_array(serial)
        self.send_chan.send_nowait({"aid": "peek_message"})
        # 先 _fetch_msg 再判断 deadline, 避免当 deadline 立即触发时无法接收数据
        update_task = self.create_task(self._fetch_msg())
        deadline_handle = None if deadline is None else self.loop.call_later(max(0, deadline - time.time()), self._set_wait_timeout)
        try:
            while not self.wait_timeout and not self.pending_diffs:
                self._run_once()
            return len(self.pending_diffs) != 0
        finally:
            self.diffs = self.pending_diffs
            self.pending_diffs = []
            for d in self.diffs:
                self._merge_diff(self.data, d, self.prototype, False)
            for _, serial in self.serials.items():
                if self.is_changing(serial["root"]):
                    self._update_serial(serial)
            if deadline_handle:
                deadline_handle.cancel()
            update_task.cancel()

    # ----------------------------------------------------------------------
    def is_changing(self, obj, key=None):
        """
        判定obj最近是否有更新

        当业务数据更新导致 wait_update 返回后可以使用该函数判断本次业务数据更新是否包含特定obj或其中某个字段

        Args:
            obj (any): 任意业务对象, 包括 get_quote 返回的 quote, get_kline_serial 返回的 k_serial, get_account 返回的 account 等

            key (str/list of str): [可选]需要判断的字段，默认不指定
                                  * 不指定: 当该obj下的任意字段有更新时返回True, 否则返回 False.
                                  * str: 当该obj下的指定字段有更新时返回True, 否则返回 False.
                                  * list of str: 当该obj下的指定字段中的任何一个字段有更新时返回True, 否则返回 False.

        Returns:
            bool: 如果本次业务数据更新包含了待判定的数据则返回 True, 否则返回 False.

        Example::

            # 追踪 SHFE.cu1812 的最新价更新
            from tqsdk import TqApi, TqSim

            api = TqApi(TqSim())
            quote = api.get_quote("SHFE.cu1812")
            while True:
                api.wait_update()
                if api.is_changing(quote, "last_price"):
                    print(quote["last_price"])

            # 以上代码运行后的输出是这样的:
            51800.0
            51810.0
            51800.0
            ...
        """
        if obj is None:
            return False
        if not isinstance(key, list):
            key = [key] if key else []
        try:
            if isinstance(obj, pd.DataFrame):
                if id(obj) in self.serials:
                    path = self.serials[id(obj)]["root"]["_path"]
                elif len(obj) == 0:
                    return False
                else:
                    duration = int(obj["duration"].iloc[0])*1000000000
                    path = ["klines", obj["symbol"].iloc[0], str(duration)] if duration != 0 else ["ticks", obj["symbol"].iloc[0]]
            elif isinstance(obj, pd.Series):
                duration = int(obj["duration"])*1000000000
                path = ["klines", obj["symbol"], str(duration), "data", str(int(obj["id"]))] if duration != 0 else ["ticks", obj["symbol"], "data", str(int(obj["id"]))]
            else:
                path = obj["_path"]
        except (KeyError, IndexError):
            return False
        for diff in self.diffs:
            if self._is_key_exist(diff, path, key):
                return True
        return False

    # ----------------------------------------------------------------------
    def is_serial_ready(self, obj):
        """
        判断是否已经从服务器收到了所有订阅的数据

        Returns:
            bool: 返回 True 表示已经从服务器收到了所有订阅的数据

        Example::

            # 判断是否已经从服务器收到了最后 3000 根 SHFE.cu1812 的分钟线数据
            from tqsdk import TqApi, TqSim

            api = TqApi(TqSim())
            k_serial = api.get_kline_serial("SHFE.cu1812", 60, data_length=3000)
            while True:
                api.wait_update()
                print(api.is_serial_ready(k_serial))

            # 预计的输出是这样的:
            False
            False
            True
            True
            ...
        """
        return self._is_serial_ready(self.serials[id(obj)])

    # ----------------------------------------------------------------------
    def create_task(self, coro):
        """
        创建一个task

        一个task就是一个协程，task的调度是在 wait_update 函数中完成的，如果代码从来没有调用 wait_update，则task也得不到执行

        Args:
            coro (coroutine):  需要创建的协程

        Example::

            # 一个简单的task
            import asyncio
            from tqsdk import TqApi, TqSim

            async def hello():
                await asyncio.sleep(3)
                print("hello world")

            api = TqApi(TqSim())
            api.create_task(hello())
            while True:
                api.wait_update()

            #以上代码将在3秒后输出
            hello world
        """
        task = self.loop.create_task(coro)
        if asyncio.Task.current_task(loop=self.loop) is None:
            self.tasks.add(task)
            task.add_done_callback(self._on_task_done)
        return task

    # ----------------------------------------------------------------------
    def register_update_notify(self, obj=None, chan=None):
        """
        注册一个channel以便接受业务数据更新通知

        调用此函数将返回一个channel, 当obj更新时会通知该channel

        推荐使用 async with api.register_update_notify() as update_chan 来注册更新通知

        如果直接调用 update_chan = api.register_update_notify() 则使用完成后需要调用 await update_chan.close() 避免资源泄漏

        Args:
            obj (any/list of any): [可选]任意业务对象, 包括 get_quote 返回的 quote, get_kline_serial 返回的 k_serial, get_account 返回的 account 等。默认不指定，监控所有业务对象

            chan (TqChan): [可选]指定需要注册的channel。默认不指定，由本函数创建

        Example::

            # 获取 SHFE.cu1812 合约的报价
            from tqsdk import TqApi, TqSim

            async def demo():
                quote = api.get_quote("SHFE.cu1812")
                async with api.register_update_notify(quote) as update_chan:
                    async for _ in update_chan:
                        print(quote["last_price"])

            api = TqApi(TqSim())
            api.create_task(demo())
            while True:
                api.wait_update()

            #以上代码将输出
            nan
            51850.0
            51850.0
            51690.0
            ...
        """
        if chan is None:
            chan = TqChan(self, last_only=True)
        if not isinstance(obj, list):
            obj = [obj] if obj else [self.data]
        for o in obj:
            listener = self.serials[id(o)]["root"]["_listener"] if isinstance(o, pd.DataFrame) else o["_listener"]
            listener.add(chan)
        return chan

    # ----------------------------------------------------------------------
    def _call_soon(self, org_call_soon, callback, *args, **kargs):
        """ioloop.call_soon的补丁, 用来追踪是否有任务完成并等待执行"""
        self.event_rev += 1
        return org_call_soon(callback, *args, **kargs)

    def _setup_connection(self, account, url, backtest):
        """初始化数据连接"""
        if backtest:  # 如果处于回测模式则将帐号转为模拟帐号，并直接连接 openmd
            if not isinstance(account, TqSim):
                account = TqSim(account_id=self.account_id)
            url = None
        if isinstance(account, str):  # 如果帐号类型是字符串，则连接天勤客户端
            self.send_chan.send_nowait({
                "aid": "req_login",
                "user_name": self.account_id,
            })
            self.recv_chan.send_nowait({
                "aid":"rtn_data",
                "data":[{
                    "quotes": self._fetch_symbol_info(TqApi.DEFAULT_INS_URL),  # 获取合约信息
                    "trade": {self.account_id:{"trade_more_data": False}},  # 天勤以 mdhis_more_data 来标记账户截面发送结束
                }],
            })
            self.create_task(self._connect((url if url else "ws://127.0.0.1:7777/"), self.send_chan, self.recv_chan))  # 启动到天勤客户端的连接
        else:
            # 默认连接 opemmd, 除非使用模拟帐号并指定了 url (例如: 使用模拟帐号连接天勤客户端使用历史复盘)
            ws_md_send_chan, ws_md_recv_chan = TqChan(self), TqChan(self)
            md_url = url if url and isinstance(account, TqSim) else TqApi.DEFAULT_MD_URL
            ws_md_recv_chan.send_nowait({
                "aid": "rtn_data",
                "data": [{"quotes": self._fetch_symbol_info(TqApi.DEFAULT_INS_URL)}]
            })  # 获取合约信息
            self.create_task(self._connect(md_url, ws_md_send_chan, ws_md_recv_chan))  # 启动行情websocket连接
            if backtest:  # 如果处于回测模式，则将行情连接对接到 backtest 上
                bt_send_chan, bt_recv_chan = TqChan(self), TqChan(self)
                self.create_task(backtest._run(self, bt_send_chan, bt_recv_chan, ws_md_send_chan, ws_md_recv_chan))
                ws_md_send_chan, ws_md_recv_chan = bt_send_chan, bt_recv_chan
            if isinstance(account, TqSim):
                self.create_task(account._run(self, self.send_chan, self.recv_chan, ws_md_send_chan, ws_md_recv_chan))
            else:
                ws_td_send_chan, ws_td_recv_chan = TqChan(self), TqChan(self)
                td_url = url if url else "wss://opentd.shinnytech.com/trade/user0"
                self.create_task(self._connect(td_url, ws_td_send_chan, ws_td_recv_chan))  # 启动交易websocket连接
                self.create_task(account._run(self, self.send_chan, self.recv_chan, ws_md_send_chan, ws_md_recv_chan, ws_td_send_chan, ws_td_recv_chan))
        if "." in self.account_id and (isinstance(account, str) or isinstance(account, TqAccount)):
            main_send_chan, main_recv_chan = self.send_chan, self.recv_chan
            self.send_chan, self.recv_chan = TqChan(self), TqChan(self)
            self.create_task(TqSubAccount(self.account_id)._run(self, self.send_chan, self.recv_chan, main_send_chan, main_recv_chan))

    def _fetch_symbol_info(self, url):
        """获取合约信息"""
        rsp = requests.get(url, headers={"Accept": "application/json"}, timeout=30)
        rsp.raise_for_status()
        return {
            k: {
                "margin": v.get("margin"),
                "commission": v.get("commission"),
                "price_tick": v["price_tick"],
                "price_decs": v["price_decs"],
                "volume_multiple": v["volume_multiple"],
                "max_limit_order_volume": v.get("max_limit_order_volume", 0),
                "max_market_order_volume": v.get("max_market_order_volume", 0),
                "min_limit_order_volume": v.get("min_limit_order_volume", 0),
                "min_market_order_volume": v.get("min_market_order_volume", 0),
                "underlying_symbol": v.get("underlying_symbol", ""),
                "strike_price": v.get("strike_price", float("nan")),
                "change": None,
                "change_percent": None,
                "expired": v["expired"],
            } for k, v in rsp.json().items()
        }

    def _init_serial(self, root, width, default):
        last_id = root.get("last_id", -1)
        serial = {
            "root": root,
            "width": width,
            "default": default,
            "array": np.array([[i] + [default[k] if i < 0 else TqApi._get_obj(root, ["data", str(i)], default)[k] for k in default] for i in range(last_id+1-width, last_id+1)], order="F"),
            "ready": False,
            "update_row": 0,
            "all_attr": set(default.keys()) | {"id", "symbol","duration"},
            "extra_array": {},
        }
        serial["df"] = pd.DataFrame(serial["array"], columns=["id"] + list(default.keys()))
        serial["df"]["symbol"] = root["_path"][1]
        serial["df"]["duration"] = 0 if root["_path"][0] == "ticks" else int(root["_path"][-1])//1000000000
        return serial

    def _is_serial_ready(self, serial):
        if not serial["ready"]:
            serial["ready"] = serial["array"][-1, 0] != -1 and np.count_nonzero(serial["array"][:,list(serial["default"].keys()).index("datetime")+1]) == min(serial["array"][-1, 0] + 1, serial["width"])
        return serial["ready"]

    def _update_serial(self, serial):
        last_id = serial["root"].get("last_id", -1)
        array = serial["array"]
        serial["update_row"] = 0
        if self._is_serial_ready(serial):
            shift = min(last_id - int(array[-1,0]), serial["width"])
            if shift != 0:
                array[0:serial["width"]-shift] = array[shift:serial["width"]]
                for ext in serial["extra_array"].values():
                    ext[0:serial["width"]-shift] = ext[shift:serial["width"]]
                    if ext.dtype == np.float:
                        ext[serial["width"]-shift:] = np.nan
                    elif ext.dtype == np.object:
                        ext[serial["width"]-shift:] = None
                    elif ext.dtype == np.int:
                        ext[serial["width"]-shift:] = 0
                    elif ext.dtype == np.bool:
                        ext[serial["width"]-shift:] = False
                    else:
                        ext[serial["width"]-shift:] = np.nan
            serial["update_row"] = max(serial["width"]-shift-1,0)
        for i in range(serial["update_row"], serial["width"]):
            index = last_id - serial["width"] + 1 + i
            item = serial["default"] if index < 0 else TqApi._get_obj(serial["root"], ["data", str(index)], serial["default"])
            array[i] = [index] + [item[k] for k in serial["default"]]

    def _process_serial_extra_array(self, serial):
        if len(serial["df"].columns) != len(serial["all_attr"]):
            for col in set(serial["df"].columns.values) - serial["all_attr"]:
                serial["update_row"] = 0
                serial["extra_array"][col] = serial["df"][col].to_numpy()
            for col in serial["all_attr"] - set(serial["df"].columns.values):
                del serial["extra_array"][col]
            serial["all_attr"] = set(serial["df"].columns.values)
        if serial["update_row"] == serial["width"]:
            return
        symbol = serial["root"]["_path"][1]
        duration = 0 if serial["root"]["_path"][0] == "ticks" else int(serial["root"]["_path"][-1])
        cols = list(serial["extra_array"].keys())
        # 归并数据序列
        while len(cols) != 0:
            col = cols[0].split(".")[0]
            # 找相关序列，首先查找以col开头的序列
            group = [c for c in cols if c.startswith(col+".") or c == col]
            cols = [c for c in cols if c not in group]
            data = {c[len(col):]:serial["extra_array"][c][serial["update_row"]:] for c in group}
            self._process_chart_data(serial, symbol, duration, col, serial["width"]- serial["update_row"], int(serial["array"][-1,0])+1,data)
        serial["update_row"] = serial["width"]

    def _process_chart_data(self,serial, symbol, duration, col, count, right, data):
        if not data:
            return
        if ".open" in data:
            data_type = "KSERIAL"
        elif ".type" in data:
            data_type = data[".type"]
            rows = np.where(np.not_equal(data_type, None))[0]
            if len(rows) == 0:
                return
            data_type = data_type[rows[0]]
        else:
            data_type = "LINE"
        if data_type in {"LINE", "DOT", "DASH", "BAR"}:
            self._send_series_data(symbol, duration, col, {
                "type": "SERIAL",
                "range_left": right-count,
                "range_right": right-1,
                "data": data[""].tolist(),
                "style": data_type,
                "color": int(data.get(".color", [0xFFFF0000])[-1]),
                "width": int(data.get(".width", [1])[-1]),
                "board": data.get(".board", ["MAIN"])[-1],
            })
        elif data_type == "KSERIAL":
            self._send_series_data(symbol, duration, col, {
                "type": "KSERIAL",
                "range_left": right-count,
                "range_right": right-1,
                "open": data[".open"].tolist(),
                "high": data[".high"].tolist(),
                "low": data[".low"].tolist(),
                "close": data[".close"].tolist(),
                "board": data.get(".board", ["MAIN"])[-1],
            })

    def _send_series_data(self, symbol, duration, serial_id, serial_data):
        chart_id = self.account_id.replace(".", "_")
        pack = {
            "aid": "set_chart_data",
            "chart_id": chart_id,
            "symbol": symbol,
            "dur_nano": duration,
            "datas": {
                serial_id: serial_data,
            }
        }
        self.send_chan.send_nowait(pack)

    def _run_once(self):
        """执行 ioloop 直到 ioloop.stop 被调用"""
        if not self.exceptions:
            self.loop.run_forever()
        if self.exceptions:
            raise self.exceptions.pop(0)

    def _run_until_idle(self):
        """执行 ioloop 直到没有待执行任务"""
        while self.check_rev != self.event_rev:
            check_handle = self.loop.call_soon(self._check_event, self.event_rev+1)
            try:
                self._run_once()
            finally:
                check_handle.cancel()

    def _check_event(self, rev):
        self.check_rev = rev
        self.loop.stop()

    def _set_wait_timeout(self):
        self.wait_timeout = True
        self.loop.stop()

    def _on_task_done(self, task):
        """当由 api 维护的 task 执行完成后取出运行中遇到的例外并停止 ioloop"""
        try:
            exception = task.exception()
            if exception:
                self.exceptions.append(exception)
        except asyncio.CancelledError:
            pass
        finally:
            self.tasks.remove(task)
            self.loop.stop()

    async def _windows_patch(self):
        """Windows系统下asyncio不支持KeyboardInterrupt的临时补丁, 详见 https://bugs.python.org/issue23057"""
        while True:
            await asyncio.sleep(1)

    async def _notify_watcher(self):
        """将从服务器收到的通知打印出来"""
        processed_notify = set()
        notify = self._get_obj(self.data, ["notify"])
        async with self.register_update_notify(notify) as update_chan:
            async for _ in update_chan:
                all_notifies = {k for k in notify if not k.startswith("_")}
                notifies = all_notifies - processed_notify
                processed_notify = all_notifies
                for n in notifies:
                    try:
                        level = getattr(logging, notify[n]["level"])
                    except (AttributeError, KeyError):
                        level = logging.INFO
                    self.logger.log(level, "通知: %s", notify[n]["content"])

    async def _connect(self, url, send_chan, recv_chan):
        """启动websocket客户端"""
        resend_request = {}  # 重连时需要重发的请求
        while True:
            try:
                async with websockets.connect(url, max_size=None, extra_headers={"User-Agent": "tqsdk-python %s" % __version__}) as client:
                    if resend_request:
                        self.logger.warning("与 %s 的网络连接已恢复", url)
                    send_task = self.create_task(self._send_handler(client, url, resend_request, send_chan))
                    try:
                        async for msg in client:
                            self.logger.debug("websocket message received from %s: %s", url, msg)
                            await recv_chan.send(json.loads(msg))
                    finally:
                        send_task.cancel()
                        await send_task
            # 希望做到的效果是遇到网络问题可以断线重连, 但是可能抛出的例外太多了(TimeoutError,socket.gaierror等), 又没有文档或工具可以理出 try 代码中所有可能遇到的例外
            # 而这里的 except 又需要处理所有子函数及子函数的子函数等等可能抛出的例外, 因此这里只能遇到问题之后再补, 并且无法避免 false positive 和 false negative
            except (websockets.exceptions.ConnectionClosed, OSError):
                self.logger.warning("与 %s 的网络连接断开，请检查客户端及网络是否正常", url)
            await asyncio.sleep(10)

    async def _send_handler(self, client, url, resend_request, send_chan):
        """websocket客户端数据发送协程"""
        try:
            for msg in resend_request.values():
                await client.send(msg)
                self.logger.debug("websocket init message sent to %s: %s", url, msg)
            async for pack in send_chan:
                msg = json.dumps(pack)
                aid = pack.get("aid")
                if aid == "subscribe_quote":
                    resend_request["subscribe_quote"] = msg
                elif aid == "set_chart":
                    if pack["ins_list"]:
                        resend_request[pack["chart_id"]] = msg
                    else:
                        resend_request.pop(pack["chart_id"], None)
                elif aid == "req_login":
                    resend_request["req_login"] = msg
                await client.send(msg)
                self.logger.debug("websocket message sent to %s: %s", url, msg)
        except asyncio.CancelledError:  # 取消任务不抛出异常，不然等待者无法区分是该任务抛出的取消异常还是有人直接取消等待者
            pass

    async def _fetch_msg(self):
        while not self.pending_diffs:
            pack = await self.recv_chan.recv()
            if pack is None:
                return
            self.pending_diffs.extend(pack.get("data", []))

    @staticmethod
    def _merge_diff(result, diff, prototype, persist):
        """更新业务数据,并同步发送更新通知，保证业务数据的更新和通知是原子操作"""
        for key in list(diff.keys()):
            value_type = type(diff[key])
            if value_type is str and key in prototype and not type(prototype[key]) is str:
                diff[key] = prototype[key]
            if diff[key] is None:
                if persist or "#" in prototype:
                    del diff[key]
                else:
                    dv = result.pop(key, None)
                    TqApi._notify_update(dv, True)
            elif value_type is dict:
                default = None
                tpersist = persist
                if key in prototype:
                    tpt = prototype[key]
                elif "*" in prototype:
                    tpt = prototype["*"]
                elif "@" in prototype:
                    tpt = prototype["@"]
                    default = tpt
                elif "#" in prototype:
                    tpt = prototype["#"]
                    default = tpt
                    tpersist = True
                else:
                    tpt = {}
                target = TqApi._get_obj(result, [key], default=default)
                TqApi._merge_diff(target, diff[key], tpt, tpersist)
                if len(diff[key]) == 0:
                    del diff[key]
            elif key in result and (result[key] == diff[key] or (diff[key] != diff[key] and result[key] != result[key])):
                # 判断 diff[key] != diff[key] and result[key] != result[key] 以处理 value 为 nan 的情况
                del diff[key]
            else:
                result[key] = diff[key]
        if len(diff) != 0:
            TqApi._notify_update(result, False)

    @staticmethod
    def _notify_update(target, recursive):
        """同步通知业务数据更新"""
        if isinstance(target, dict):
            for q in target["_listener"]:
                q.send_nowait(True)
            if recursive:
                for v in target.values():
                    TqApi._notify_update(v, recursive)

    @staticmethod
    def _get_obj(root, path, default=None):
        """获取业务数据"""
        # todo: support nested dict for default value
        d = root
        for i in range(len(path)):
            if path[i] not in d:
                dv = {} if i != len(path) - 1 or default is None else copy.copy(default)
                if isinstance(dv, dict):
                    dv["_path"] = d["_path"] + [path[i]]
                    dv["_listener"] = weakref.WeakSet()
                d[path[i]] = dv
            d = d[path[i]]
        return d

    @staticmethod
    def _is_key_exist(diff, path, key):
        """判断指定数据是否存在"""
        for p in path:
            if not isinstance(diff, dict) or p not in diff:
                return False
            diff = diff[p]
        if not isinstance(diff, dict):
            return False
        for k in key:
            if k in diff:
                return True
        return len(key) == 0

    @staticmethod
    def _gen_prototype():
        """所有业务数据的原型"""
        return {
            "quotes": {
                "#": TqApi._gen_quote_prototype(),  # 行情的数据原型
            },
            "klines": {
                "*": {
                    "*": {
                        "data": {
                            "@": TqApi._gen_kline_prototype(),  # K线的数据原型
                        }
                    }
                }
            },
            "ticks": {
                "*": {
                    "data": {
                        "@": TqApi._gen_tick_prototype(),  # Tick的数据原型
                    }
                }
            },
            "trade": {
                "*": {
                    "accounts": {
                        "@": TqApi._gen_account_prototype(),  # 账户的数据原型
                    },
                    "orders": {
                        "@": TqApi._gen_order_prototype(),  # 委托单的数据原型
                    },
                    "trades": {
                        "@": TqApi._gen_trade_prototype(),  # 成交的数据原型
                    },
                    "positions": {
                        "@": TqApi._gen_position_prototype(),  # 持仓的数据原型
                    }
                }
            },
        }

    @staticmethod
    def _gen_quote_prototype():
        """行情的数据原型"""
        return {
            "datetime": "",  # "2017-07-26 23:04:21.000001" (行情从交易所发出的时间(北京时间))
            "ask_price1": float("nan"),  # 6122.0 (卖一价)
            "ask_volume1": 0,  # 3 (卖一量)
            "bid_price1": float("nan"),  # 6121.0 (买一价)
            "bid_volume1": 0,  # 7 (买一量)
            "last_price": float("nan"),  # 6122.0 (最新价)
            "highest": float("nan"),  # 6129.0 (当日最高价)
            "lowest": float("nan"),  # 6101.0 (当日最低价)
            "open": float("nan"),  # 6102.0 (开盘价)
            "close": float("nan"),  # nan (收盘价)
            "average": float("nan"),  # 6119.0 (当日均价)
            "volume": 0,  # 89252 (成交量)
            "amount": float("nan"),  # 5461329880.0 (成交额)
            "open_interest": 0,  # 616424 (持仓量)
            "settlement": float("nan"),  # nan (结算价)
            "upper_limit": float("nan"),  # 6388.0 (涨停价)
            "lower_limit": float("nan"),  # 5896.0 (跌停价)
            "pre_open_interest": 0,  # 616620 (昨持仓量)
            "pre_settlement": float("nan"),  # 6142.0 (昨结算价)
            "pre_close": float("nan"),  # 6106.0 (昨收盘价)
            "price_tick": float("nan"),  # 10.0 (合约价格单位)
            "price_decs": 0,  # 0 (合约价格小数位数)
            "volume_multiple": 0,  # 10 (合约乘数)
            "max_limit_order_volume": 0,  # 500 (最大限价单手数)
            "max_market_order_volume": 0,  # 0 (最大市价单手数)
            "min_limit_order_volume": 0,  # 1 (最小限价单手数)
            "min_market_order_volume": 0,  # 0 (最小市价单手数)
            "underlying_symbol": "",  # SHFE.rb1901 (标的合约)
            "strike_price": float("nan"),  # nan (行权价)
            "change": float("nan"),  # −20.0 (涨跌)
            "change_percent": float("nan"),  # −0.00325 (涨跌幅)
            "expired": False,  # False (合约是否已下市)
        }

    @staticmethod
    def _gen_kline_prototype():
        """K线的数据原型"""
        return {
            "datetime": 0,  # 1501080715000000000 (K线起点时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
            "open": float("nan"),  # 51450.0 (K线起始时刻的最新价)
            "high": float("nan"),  # 51450.0 (K线时间范围内的最高价)
            "low": float("nan"),  # 51450.0 (K线时间范围内的最低价)
            "close": float("nan"),  # 51450.0 (K线结束时刻的最新价)
            "volume": 0,  # 11 (K线时间范围内的成交量)
            "open_oi": 0,  # 27354 (K线起始时刻的持仓量)
            "close_oi": 0,  # 27355 (K线结束时刻的持仓量)
        }

    @staticmethod
    def _gen_tick_prototype():
        """Tick的数据原型"""
        return {
            "datetime": 0,  # 1501074872000000000 (tick从交易所发出的时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
            "last_price": float("nan"),  # 3887.0 (最新价)
            "average": float("nan"),  # 3820.0 (当日均价)
            "highest": float("nan"),  # 3897.0 (当日最高价)
            "lowest": float("nan"),  # 3806.0 (当日最低价)
            "ask_price1": float("nan"),  # 3886.0 (卖一价)
            "ask_volume1": 0,  # 3 (卖一量)
            "bid_price1": float("nan"),  # 3881.0 (买一价)
            "bid_volume1": 0,  # 18 (买一量)
            "volume": 0,  # 7823 (当日成交量)
            "amount": float("nan"),  # 19237841.0 (成交额)
            "open_interest": 0,  # 1941 (持仓量)
        }

    @staticmethod
    def _gen_account_prototype():
        """账户的数据原型"""
        return {
            "currency": "",  # "CNY" (币种)
            "pre_balance": float("nan"),  # 9912934.78 (昨日账户权益)
            "static_balance": float("nan"),  # (静态权益)
            "balance": float("nan"),  # 9963216.55 (账户权益)
            "available": float("nan"),  # 9480176.15 (可用资金)
            "float_profit": float("nan"),  # 8910.0 (浮动盈亏)
            "position_profit": float("nan"),  # 1120.0(持仓盈亏)
            "close_profit": float("nan"),  # -11120.0 (本交易日内平仓盈亏)
            "frozen_margin": float("nan"),  # 0.0(冻结保证金)
            "margin": float("nan"),  # 11232.23 (保证金占用)
            "frozen_commission": float("nan"),  # 0.0 (冻结手续费)
            "commission": float("nan"),  # 123.0 (本交易日内交纳的手续费)
            "frozen_premium": float("nan"),  # 0.0 (冻结权利金)
            "premium": float("nan"),  # 0.0 (本交易日内交纳的权利金)
            "deposit": float("nan"),  # 1234.0 (本交易日内的入金金额)
            "withdraw": float("nan"),  # 890.0 (本交易日内的出金金额)
            "risk_ratio": float("nan"),  # 0.048482375 (风险度)
        }

    @staticmethod
    def _gen_order_prototype():
        """委托单的数据原型"""
        return {
            "order_id": "",  # "123" (委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的)
            "exchange_order_id": "",  # "1928341" (交易所单号)
            "exchange_id": "",  # "SHFE" (交易所)
            "instrument_id": "",  # "rb1901" (交易所内的合约代码)
            "direction": "",  # "BUY" (下单方向, BUY=买, SELL=卖)
            "offset": "",  # "OPEN" (开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今)
            "volume_orign": 0,  # 10 (总报单手数)
            "volume_left": 0,  # 5 (未成交手数)
            "limit_price": float("nan"),  # 4500.0 (委托价格, 仅当 price_type = LIMIT 时有效)
            "price_type": "",  # "LIMIT" (价格类型, ANY=市价, LIMIT=限价)
            "volume_condition": "",  # "ANY" (手数条件, ANY=任何数量, MIN=最小数量, ALL=全部数量)
            "time_condition": "",  # "GFD" (时间条件, IOC=立即完成，否则撤销, GFS=本节有效, GFD=当日有效, GTC=撤销前有效, GFA=集合竞价有效)
            "insert_date_time": 0,  # 1501074872000000000 (下单时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
            "last_msg": "",  # "报单成功" (委托单状态信息)
            "status": "",  # "ALIVE" (委托单状态, ALIVE=有效, FINISHED=已完)
        }

    @staticmethod
    def _gen_trade_prototype():
        """成交的数据原型"""
        return {
            "order_id": "",  # "123" (委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的)
            "trade_id": "",  # "123|19723" (成交ID, 对于一个用户的所有成交，这个ID都是不重复的)
            "exchange_trade_id": "",  # "829414" (交易所成交号)
            "exchange_id": "",  # "SHFE" (交易所)
            "instrument_id": "",  # "rb1901" (交易所内的合约代码)
            "direction": "",  # "BUY" (下单方向, BUY=买, SELL=卖)
            "offset": "",  # "OPEN" (开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今)
            "price": float("nan"),  # 4510.0 (成交价格)
            "volume": 0,  # 5 (成交手数)
            "trade_date_time": 0,  # 1501074872000000000 (成交时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
        }

    @staticmethod
    def _gen_position_prototype():
        """持仓的数据原型"""
        return {
            "exchange_id": "",  # "SHFE" (交易所)
            "instrument_id": "",  # "rb1901" (交易所内的合约代码)
            "volume_long_today": 0,  # 10 (多头今仓手数)
            "volume_long_his": 0,  # 5 (多头老仓手数)
            "volume_long": 0,  # 15 (多头手数)
            "volume_long_frozen_today": 0,  # 3 (多头今仓冻结)
            "volume_long_frozen_his": 0,  # 2 (多头老仓冻结)
            "volume_long_frozen": 0,  # 5 (多头持仓冻结)
            "volume_short_today": 0,  # 3 (空头今仓手数)
            "volume_short_his": 0,  # 0 (空头老仓手数)
            "volume_short": 0,  # 3 (空头手数)
            "volume_short_frozen_today": 0,  # 0 (空头今仓冻结)
            "volume_short_frozen_his": 0,  # 0 (空头老仓冻结)
            "volume_short_frozen": 0,  # 0 (空头持仓冻结)
            "open_price_long": float("nan"),  # 3120.0 (多头开仓均价)
            "open_price_short": float("nan"),  # 3310.0 (空头开仓均价)
            "open_cost_long": float("nan"),  # 468000.0 (多头开仓市值)
            "open_cost_short": float("nan"),  # 99300.0 (空头开仓市值)
            "position_price_long": float("nan"),  # 3200.0 (多头持仓均价)
            "position_price_short": float("nan"),  # 3330.0 (空头持仓均价)
            "position_cost_long": float("nan"),  # 480000.0 (多头持仓市值)
            "position_cost_short": float("nan"),  # 99900.0 (空头持仓市值)
            "float_profit_long": float("nan"),  # 12000.0 (多头浮动盈亏)
            "float_profit_short": float("nan"),  # 3300.0 (空头浮动盈亏)
            "float_profit": float("nan"),  # 15300.0 (浮动盈亏)
            "position_profit_long": float("nan"),  # 0.0 (多头持仓盈亏)
            "position_profit_short": float("nan"),  # 3900.0 (空头持仓盈亏)
            "position_profit": float("nan"),  # 3900.0 (持仓盈亏)
            "margin_long": float("nan"),  # 50000.0 (多头占用保证金)
            "margin_short": float("nan"),  # 10000.0 (空头占用保证金)
            "margin": float("nan"),  # 60000.0 (占用保证金)
        }

    @staticmethod
    def _generate_chart_id(module, symbol, duration_seconds):
        """生成chart id"""
        chart_id = "PYSDK_" + module + "_" + uuid.uuid4().hex
        return chart_id

    @staticmethod
    def _generate_order_id():
        """生成order id"""
        return uuid.uuid4().hex

    @staticmethod
    def _get_trading_day_start_time(trading_day):
        """给定交易日, 获得交易日起始时间"""
        begin_mark = 631123200000000000  # 1990-01-01
        start_time = trading_day - 21600000000000  # 6小时
        week_day = (start_time - begin_mark) // 86400000000000 % 7
        if week_day >= 5:
            start_time -= 86400000000000 * (week_day-4)
        return start_time

    @staticmethod
    def _get_trading_day_end_time(trading_day):
        """给定交易日, 获得交易日结束时间"""
        return trading_day + 64799999999999  # 18小时

    @staticmethod
    def _get_trading_day_from_timestamp(timestamp):
        """给定时间, 获得其所属的交易日"""
        begin_mark = 631123200000000000  # 1990-01-01
        days = (timestamp - begin_mark) // 86400000000000  # 自 1990-01-01 以来的天数
        if (timestamp - begin_mark) % 86400000000000 >= 64800000000000:  # 大于18点, 天数+1
            days += 1
        week_day = days % 7
        if week_day >= 5:  # 如果是周末则移到星期一
            days += 7 - week_day
        return begin_mark + days * 86400000000000

    def draw_text(self, base_k_dataframe, text, x=None, y=None, id=None, board="MAIN", color=0xFFFF0000):
        """
        配合天勤使用时, 在天勤的行情图上绘制一个字符串

        Args:
            base_k_dataframe (pandas.DataFrame): 基础K线数据序列, 要绘制的K线将出现在这个K线图上. 需要画图的数据以附加列的形式存在

            text (str): 要显示的字符串

            x (int): X 坐标, 以K线的序列号表示. 可选, 缺省为对齐最后一根K线,

            y (float): Y 坐标. 可选, 缺省为最后一根K线收盘价

            id (str): 字符串ID, 可选. 以相同ID多次调用本函数, 后一次调用将覆盖前一次调用的效果

            board (str): 选择图板, 可选, 缺省为 "MAIN" 表示绘制在主图

            color (ARGB): 文本颜色, 可选, 缺省为红色.

        Example::

            # 在主图最近K线的最低处标一个"最低"文字
            klines = api.get_kline_serial("SHFE.cu1905", 86400)
            indic = np.where(klines["low"] == klines["low"].min())[0]
            value = klines["low"].min()
            api.draw_text(klines, "测试413423", x=indic, y=value, color=0xFF00FF00)
        """
        if id is None:
            id = uuid.uuid4().hex
        if y is None:
            y = base_k_dataframe["close"].iloc[-1]
        serial = {
            "type": "TEXT",
            "x1": self._offset_to_x(base_k_dataframe, x),
            "y1": y,
            "text": text,
            "color": color,
            "board": board,
        }
        self._send_chart_data(id, serial)

    def draw_line(self, base_k_dataframe, x1, y1, x2, y2, id=None, board="MAIN", line_type="LINE", color=0xFFFF0000, width=1):
        """
        配合天勤使用时, 在天勤的行情图上绘制一个直线/线段/射线

        Args:
            base_k_dataframe (pandas.DataFrame): 基础K线数据序列, 要绘制的K线将出现在这个K线图上. 需要画图的数据以附加列的形式存在

            x1 (int): 第一个点的 X 坐标, 以K线的序列号表示

            y1 (float): 第一个点的 Y 坐标

            x2 (int): 第二个点的 X 坐标, 以K线的序列号表示

            y2 (float): 第二个点的 Y 坐标

            id (str): 字符串ID, 可选. 以相同ID多次调用本函数, 后一次调用将覆盖前一次调用的效果

            board (str): 选择图板, 可选, 缺省为 "MAIN" 表示绘制在主图

            line_type ("LINE" | "SEG" | "RAY"): 画线类型, 可选, 默认为 LINE. LINE=直线, SEG=线段, RAY=射线

            color (ARGB): 线颜色, 可选, 缺省为 红色

            width (int): 线宽度, 可选, 缺省为 1
        """
        if id is None:
            id = uuid.uuid4().hex
        serial = {
            "type": line_type,
            "x1": self._offset_to_x(base_k_dataframe, x1),
            "y1": y1,
            "x2": self._offset_to_x(base_k_dataframe, x2),
            "y2": y2,
            "color": color,
            "width": width,
            "board": board,
        }
        self._send_chart_data(id, serial)

    def draw_box(self, base_k_dataframe, x1, y1, x2, y2, id=None, board="MAIN", bg_color=0x00000000, color=0xFFFF0000, width=1):
        """
        配合天勤使用时, 在天勤的行情图上绘制一个矩形

        Args:
            base_k_dataframe (pandas.DataFrame): 基础K线数据序列, 要绘制的K线将出现在这个K线图上. 需要画图的数据以附加列的形式存在

            x1 (int): 矩形左上角的 X 坐标, 以K线的序列号表示

            y1 (float): 矩形左上角的 Y 坐标

            x2 (int): 矩形左上角的 X 坐标, 以K线的序列号表示

            y2 (float): 矩形左上角的 Y 坐标

            id (str): ID, 可选. 以相同ID多次调用本函数, 后一次调用将覆盖前一次调用的效果

            board (str): 选择图板, 可选, 缺省为 "MAIN" 表示绘制在主图

            bg_color (ARGB): 填充颜色, 可选, 缺省为 空

            color (ARGB): 边框颜色, 可选, 缺省为 红色

            width (int): 边框宽度, 可选, 缺省为 1

        Example::

            # 给主图最后5根K线加一个方框
            klines = api.get_kline_serial("SHFE.cu1905", 86400)
            api.draw_box(klines, x1=-5, y1=klines.iloc[-5]["close"], x2=-1, y2=klines.iloc[-1]["close"], width=1, color=0xFF0000FF, bg_color=0x8000FF00)
        """
        if id is None:
            id = uuid.uuid4().hex
        serial = {
            "type": "BOX",
            "x1": self._offset_to_x(base_k_dataframe, x1),
            "y1": y1,
            "x2": self._offset_to_x(base_k_dataframe, x2),
            "y2": y2,
            "bg_color": bg_color,
            "color": color,
            "width": width,
            "board": board,
        }
        self._send_chart_data(id, serial)

    def _send_chart_data(self, base_kserial_frame, serial_id, serial_data):
        chart_id = self.account_id.replace(".", "_")
        s = self.serials[id(base_kserial_frame)]
        p = s.serial_root["_path"]
        symbol = p[-2]
        dur_nano = int(p[-1])
        pack = {
            "aid": "set_chart_data",
            "chart_id": chart_id,
            "symbol": symbol,
            "dur_nano": dur_nano,
            "datas": {
                serial_id: serial_data,
            }
        }
        self.api.send_chan.send_nowait(pack)

    def _offset_to_x(self, base_k_dataframe, x):
        if x is None:
            return base_k_dataframe["id"].iloc[-1]
        elif x < 0:
            return base_k_dataframe["id"].iloc[-1] + 1 + x
        elif x >= 0:
            return base_k_dataframe["id"].iloc[0] + x


class TqAccount(object):
    """天勤实盘类"""
    def __init__(self, broker_id, account_id, password):
        """
        创建天勤实盘实例

        Args:
            broker_id (str): 期货公司, 可以在天勤终端中查看期货公司名称

            account_id (str): 帐号

            password (str): 密码
        """
        self.broker_id = broker_id
        self.account_id = account_id
        self.password = password

    async def _run(self, api, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan, td_send_chan, td_recv_chan):
        await td_send_chan.send({
            "aid": "req_login",
            "bid": self.broker_id,
            "user_name": self.account_id.rsplit(".", 1)[0],
            "password": self.password,
        })
        md_task = api.create_task(self._md_handler(api_recv_chan, md_send_chan, md_recv_chan))
        td_task = api.create_task(self._td_handler(api_recv_chan, td_send_chan, td_recv_chan))
        try:
            async for pack in api_send_chan:
                if pack["aid"] == "subscribe_quote" or pack["aid"] == "set_chart":
                    await md_send_chan.send(pack)
                elif pack["aid"] != "peek_message":
                    await td_send_chan.send(pack)
        finally:
            md_task.cancel()
            td_task.cancel()

    async def _md_handler(self, api_recv_chan, md_send_chan, md_recv_chan):
        async for pack in md_recv_chan:
            await md_send_chan.send({"aid":"peek_message"})
            await api_recv_chan.send(pack)

    async def _td_handler(self, api_recv_chan, td_send_chan, td_recv_chan):
        async for pack in td_recv_chan:
            await td_send_chan.send({"aid":"peek_message"})
            await api_recv_chan.send(pack)


class TqChan(asyncio.Queue):
    """用于协程间通讯的channel"""
    def __init__(self, api, last_only=False):
        """
        创建channel实例

        Args:
            last_only (bool): 为True时只存储最后一个发送到channel的对象
        """
        asyncio.Queue.__init__(self, loop=api.loop)
        self.api = api
        self.last_only = last_only
        self.closed = False

    async def close(self):
        """
        关闭channel

        关闭后send将不起作用,recv在收完剩余数据后会立即返回None
        """
        if not self.closed:
            self.closed = True
            await asyncio.Queue.put(self, None)

    async def send(self, item):
        """
        异步发送数据到channel中

        Args:
            item (any): 待发送的对象
        """
        if not self.closed:
            if self.last_only:
                while not self.empty():
                    asyncio.Queue.get_nowait(self)
            await asyncio.Queue.put(self, item)

    def send_nowait(self, item):
        """
        尝试立即发送数据到channel中

        Args:
            item (any): 待发送的对象

        Raises:
            asyncio.QueueFull: 如果channel已满则会抛出 asyncio.QueueFull
        """
        if not self.closed:
            if self.last_only:
                while not self.empty():
                    asyncio.Queue.get_nowait(self)
            asyncio.Queue.put_nowait(self, item)

    async def recv(self):
        """
        异步接收channel中的数据，如果channel中没有数据则一直等待

        Returns:
            any: 收到的数据，如果channel已被关闭则会立即收到None
        """
        if self.closed and self.empty():
            return None
        return await asyncio.Queue.get(self)

    def recv_nowait(self):
        """
        尝试立即接收channel中的数据

        Returns:
            any: 收到的数据，如果channel已被关闭则会立即收到None

        Raises:
            asyncio.QueueFull: 如果channel中没有数据则会抛出 asyncio.QueueEmpty
        """
        if self.closed and self.empty():
            return None
        return asyncio.Queue.get_nowait(self)

    def recv_latest(self, latest):
        """
        尝试立即接收channel中的最后一个数据

        Args:
            latest (any): 如果当前channel中没有数据或已关闭则返回该对象

        Returns:
            any: channel中的最后一个数据
        """
        while (self.closed and self.qsize() > 1) or (not self.closed and not self.empty()):
            latest = asyncio.Queue.get_nowait(self)
        return latest

    def __aiter__(self):
        return self

    async def __anext__(self):
        value = await asyncio.Queue.get(self)
        if self.closed and self.empty():
            raise StopAsyncIteration
        return value

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
