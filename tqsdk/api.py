#!/usr/bin/env python
#  -*- coding: utf-8 -*-
"""
天勤接口的PYTHON封装, 提供以下功能

* 连接行情和交易服务器或天勤终端的websocket扩展接口, 接收行情及交易推送数据
* 在内存中存储管理一份完整的业务数据(行情+交易), 并在接收到新数据包时更新内存数据
* 通过一批函数接口, 支持用户代码访问业务数据
* 发送交易指令


* PYTHON SDK使用文档: https://doc.shinnytech.com/pysdk/latest/
* 天勤vscode插件使用文档: https://doc.shinnytech.com/pysdk/latest/devtools/vscode.html
* 天勤用户论坛: https://www.shinnytech.com/qa/
"""
__author__ = 'chengzhi'

import re
import json
import ssl
import uuid
import sys
import time
import logging
import copy
import ctypes
import asyncio
import functools
import certifi
import websockets
import requests
import random
import base64
import os
from datetime import datetime
from typing import Union, List, Any, Optional
import pandas as pd
import numpy as np
from .__version__ import __version__
from tqsdk.sim import TqSim
from tqsdk.objs import Entity, Quote, Kline, Tick, Account, Position, Order, Trade
from tqsdk.backtest import TqBacktest, TqReplay
from tqsdk.tqwebhelper import TqWebHelper


class TqApi(object):
    """
    天勤接口及数据管理类

    该类中所有参数只针对天勤外部IDE编写使用, 在天勤内使用 api = TqApi() 即可指定为当前天勤终端登录用户

    通常情况下, 一个线程中 **应该只有一个** TqApi的实例, 它负责维护网络连接, 接收行情及账户数据, 并在内存中维护业务数据截面
    """

    RD = random.Random()  # 初始化随机数引擎
    DEFAULT_INS_URL = "https://openmd.shinnytech.com/t/md/symbols/latest.json"
    DEFAULT_MD_URL = "wss://openmd.shinnytech.com/t/md/front/mobile"
    DEFAULT_TD_URL = "wss://opentd.shinnytech.com/trade/user0"

    def __init__(self, account: Union['TqAccount', TqSim, None] = None, auth: Optional[str] = None, url: Optional[str] = None,
                 backtest: Union[TqBacktest, TqReplay, None] = None, web_gui: [bool, str] = False, debug: Optional[str] = None,
                 loop: Optional[asyncio.AbstractEventLoop] = None, _ins_url=None, _md_url=None, _td_url=None) -> None:
        """
        创建天勤接口实例

        Args:
            account (None/TqAccount/TqSim): [可选]交易账号:
                * None: 账号将根据命令行参数决定, 默认为 :py:class:`~tqsdk.sim.TqSim`

                * :py:class:`~tqsdk.api.TqAccount` : 使用实盘账号, 直连行情和交易服务器(不通过天勤终端), 需提供期货公司/帐号/密码

                * :py:class:`~tqsdk.sim.TqSim` : 使用 TqApi 自带的内部模拟账号

            auth (str): [可选]用户权限认证对象
                * 用户权限认证对象为天勤用户论坛的邮箱和密码，中间以英文逗号分隔，例如： "tianqin@qq.com,123456"
                天勤论坛注册链接 https://www.shinnytech.com/register-intro/

            url (str): [可选]指定服务器的地址
                * 当 account 为 :py:class:`~tqsdk.api.TqAccount` 类型时, 可以通过该参数指定交易服务器地址, \
                默认使用 wss://opentd.shinnytech.com/trade/user0, 行情始终使用 wss://openmd.shinnytech.com/t/md/front/mobile

                * 当 account 为 :py:class:`~tqsdk.sim.TqSim` 类型时, 可以通过该参数指定行情服务器地址,\
                默认使用 wss://openmd.shinnytech.com/t/md/front/mobile

            backtest (TqBacktest/TqReplay): [可选] 进入时光机，此时强制要求 account 类型为 :py:class:`~tqsdk.sim.TqSim`

                * :py:class:`~tqsdk.backtest.TqBacktest` : 传入 TqBacktest 对象，进入回测模式 \
                在回测模式下, TqBacktest 连接 wss://openmd.shinnytech.com/t/md/front/mobile 接收行情数据, \
                由 TqBacktest 内部完成回测时间段内的行情推进和 K 线、Tick 更新.

                * :py:class:`~tqsdk.backtest.TqReplay` : 传入 TqReplay 对象, 进入复盘模式 \
                在复盘模式下, TqReplay 会在服务器申请复盘日期的行情资源, 由服务器推送复盘日期的行情.

            debug(str): [可选] 指定一个日志文件名, 将调试信息输出到指定文件. 默认不输出.

            loop(asyncio.AbstractEventLoop): [可选]使用指定的 IOLoop, 默认创建一个新的.

            web_gui(bool/str): [可选]是否启用图形化界面功能, 默认不启用.
                * 启用图形化界面传入参数 web_gui=True 会每次以随机端口生成网页，也可以直接设置本机IP和端口 web_gui=[ip]:port 为网页地址，
                ip 可选，默认为 0.0.0.0，参考example 6
                * 为了图形化界面能够接收到程序传输的数据并且刷新，在程序中，需要循环调用 api.wait_update的形式去更新和获取数据
                * 推荐打开图形化界面的浏览器为Google Chrome 或 Firefox

        Example1::

            # 使用实盘帐号直连行情和交易服务器
            from tqsdk import TqApi, TqAccount
            api = TqApi(TqAccount("H海通期货", "022631", "123456"))

        Example2::

            # 使用模拟帐号直连行情服务器
            from tqsdk import TqApi, TqSim
            api = TqApi(TqSim())  # 不填写参数则默认为 TqSim() 模拟账号

        Example3::

            # 进行策略回测
            from datetime import date
            from tqsdk import TqApi, TqBacktest
            api = TqApi(backtest=TqBacktest(start_dt=date(2018, 5, 1), end_dt=date(2018, 10, 1)))

        Example4::

            # 进行策略复盘
            from datetime import date
            from tqsdk import TqApi, TqReplay
            api = TqApi(backtest=TqReplay(replay_dt=date(2019, 12, 16)))

        Example5::

            # 开启 web_gui 功能，使用默认参数True
            from tqsdk import TqApi
            api = TqApi(web_gui=True)

        Example6::

            # 开启 web_gui 功能，使用本机IP端口固定网址生成
            from tqsdk import TqApi
            api = TqApi(web_gui=":9876")  # 等价于 api = TqApi(web_gui="0.0.0.0:9876")

        """

        # 初始化 logger
        self._logger = logging.getLogger("TqApi")
        self._logger.setLevel(logging.DEBUG)
        if not self._logger.handlers:
            sh = logging.StreamHandler()
            sh.setLevel(logging.INFO)
            if backtest:  # 如果回测, 则去除第一个本地时间
                log_format = logging.Formatter('%(levelname)s - %(message)s')
            else:
                log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            sh.setFormatter(log_format)
            self._logger.addHandler(sh)
            if debug:
                fh = logging.FileHandler(filename=debug)
                fh.setFormatter(log_format)
                self._logger.addHandler(fh)

        # 记录参数
        self._account = TqSim() if account is None else account
        self._backtest = backtest
        self._ins_url = TqApi.DEFAULT_INS_URL
        self._md_url = TqApi.DEFAULT_MD_URL
        self._td_url = TqApi.DEFAULT_TD_URL

        # 支持用户授权
        self._access_token = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJobi1MZ3ZwbWlFTTJHZHAtRmlScjV5MUF5MnZrQmpLSFFyQVlnQ0UwR1JjIn0.eyJqdGkiOiJjZDAzM2JhNC1lZTJkLTRhNjUtYmVjNi04NTAyZmQyMjk4NmUiLCJleHAiOjE2MTI0MDQwMTEsIm5iZiI6MCwiaWF0IjoxNTgwODY4MDExLCJpc3MiOiJodHRwczovL2F1dGguc2hpbm55dGVjaC5jb20vYXV0aC9yZWFsbXMvc2hpbm55dGVjaCIsInN1YiI6IjYzMzJhZmUwLWU5OWQtNDc1OC04MjIzLWY5OTBiN2RmOGY4NSIsInR5cCI6IkJlYXJlciIsImF6cCI6InNoaW5ueV90cSIsImF1dGhfdGltZSI6MCwic2Vzc2lvbl9zdGF0ZSI6IjliNTY1MzYzLTRkNmEtNDc0ZS1hYmMzLTQ0YzU0N2ZhMDZjYiIsImFjciI6IjEiLCJzY29wZSI6ImF0dHJpYnV0ZXMiLCJncmFudHMiOnsiZmVhdHVyZXMiOlsiYWR2Il0sImFjY291bnRzIjpbIioiXX19.OtSweF6mXilJNkQwJQR38BTdYWfShxJrlUIxvHRoZ6AZMtJ9pRMx1SS9mmO9SmA_OPBouLybDmPFbcAMK6_Z4hXNYzd1TyXbPMNIPaMg7E12IEe6RxmsP15j-txfB3lC8LJlc9ey9Y-Hbg2goxS9RCj5m5PR8MuHYwx_E1PwEkOkoBw0eJG5jT0gVh8nHN_p7zsbXOo0PVVNxK1ZBuU-t5NeHy3E33LAOxG1VjqAeOrE4YZrprKcHu6ekd4WPy77cllSRMX6Ob2i9uIFmErbtFK76eYJoPmetSEljAcXwjg3_vWcYOj-xzCeFZoaV9ysNvbANzCS0nAelMvWlBHrkA'
        if auth:
            comma_index = auth.find(',')
            email, pwd = auth[:comma_index], auth[comma_index + 1:]
            headers = {
                "User-Agent": "tqsdk-python %s" % __version__,
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            response = requests.post("https://auth.shinnytech.com/auth/realms/shinnytech/protocol/openid-connect/token",
                                     headers=headers,
                                     data="grant_type=password&username=%s&password=%s&client_id=shinny_tq&client_secret=be30b9f4-6862-488a-99ad-21bde0400081" % (email, pwd),
                                     timeout=30)
            if response.status_code == 200:
                self._access_token = json.loads(response.content)["access_token"]
                self._logger.info("用户权限认证成功")
            else:
                self._logger.warning("用户权限认证失败 (%d,%s)" % (response.status_code, response.content))

        if url and isinstance(self._account, TqSim):
            self._md_url = url
        if isinstance(self._account, TqAccount):
            if url:
                self._td_url = url
            else:
                # 支持分散部署的交易中继网关
                response = requests.get("https://files.shinnytech.com/broker-list.json", headers=self._base_headers,
                                        timeout=30)
                broker_list = json.loads(response.content)
                if self._account._broker_id not in broker_list:
                    raise Exception("不支持该期货公司-%s，请联系期货公司。" % (self._account._broker_id))
                if "TQ" not in broker_list[self._account._broker_id]["category"]:
                    raise Exception("不支持该期货公司-%s，请联系期货公司。" % (self._account._broker_id))
                self._td_url = broker_list[self._account._broker_id]["url"]
        if _ins_url:
            self._ins_url = _ins_url
        if _md_url:
            self._md_url = _md_url
        if _td_url:
            self._td_url = _td_url
        self._loop = asyncio.SelectorEventLoop() if loop is None else loop  # 创建一个新的 ioloop, 避免和其他框架/环境产生干扰

        # 初始化loop
        self._send_chan, self._recv_chan = TqChan(self), TqChan(self)  # 消息收发队列
        self._tasks = set()  # 由api维护的所有根task，不包含子task，子task由其父task维护
        self._exceptions = []  # 由api维护的所有task抛出的例外
        # 回测需要行情和交易 lockstep, 而 asyncio 没有将内部的 _ready 队列暴露出来,
        # 因此 monkey patch call_soon 函数用来判断是否有任务等待执行
        self._loop.call_soon = functools.partial(self._call_soon, self._loop.call_soon)
        self._event_rev, self._check_rev = 0, 0

        # 内部关键数据
        self._requests = {
            "quotes": set(),
            "klines": {},
            "ticks": {},
        }  # 记录已发出的请求
        self._serials = {}  # 记录所有数据序列
        # 记录所有(若有多个serial 则仅data_length不同, right_id相同)合约、周期相同的多合约K线中最大的更新数据范围
        # key:(主合约,(所有副合约),duration), value:(K线的新数据中主合约最小的id, 主合约的right_id)。用于is_changing()中新K线生成的判定
        self._klines_update_range = {}
        self._data = Entity()  # 数据存储
        self._data._instance_entity([])
        self._diffs = []  # 自上次wait_update返回后收到更新数据的数组
        self._pending_diffs = []  # 从网络上收到的待处理的 diffs, 只在 wait_update 函数执行过程中才可能为非空
        self._prototype = self._gen_prototype()  # 各业务数据的原型, 用于决定默认值及将收到的数据转为特定的类型
        self._wait_timeout = False  # wait_update 是否触发超时

        # slave模式的api不需要完整初始化流程
        self._is_slave = isinstance(account, TqApi)
        self._slaves = []
        if self._is_slave:
            self._master = account
            if self._master._is_slave:
                raise Exception("不可以为slave再创建slave")
            self._master._slaves.append(self)
            self._account = self._master._account
            self._web_gui = False # 如果是slave, _web_gui 一定是 False
            return  # 注: 如果是slave,则初始化到这里结束并返回,以下代码不执行

        self._web_gui = web_gui
        # 初始化
        if sys.platform.startswith("win"):
            self.create_task(self._windows_patch())  # Windows系统下asyncio不支持KeyboardInterrupt的临时补丁
        self.create_task(self._notify_watcher())  # 监控服务器发送的通知
        self._setup_connection()  # 初始化通讯连接

        # 等待初始化完成
        deadline = time.time() + 60
        try:
            while self._data.get("mdhis_more_data", True) \
                    or self._data.get("trade", {}).get(self._account._account_id, {}).get("trade_more_data", True):
                if not self.wait_update(deadline=deadline):  # 等待连接成功并收取截面数据
                    raise Exception("接收数据超时，请检查客户端及网络是否正常")
        except:
            self.close()
            raise
        # 使用非空list,使得wait_update()能正确发送peek_message; 使用空dict, 使得is_changing()返回false, 因为截面数据不算做更新数据.
        self._diffs = [{}]

    # ----------------------------------------------------------------------
    def copy(self) -> 'TqApi':
        """
        创建当前TqApi的一个副本. 这个副本可以在另一个线程中使用

        Returns:
            :py:class:`~tqsdk.api.TqApi`: 返回当前TqApi的一个副本. 这个副本可以在另一个线程中使用
        """
        slave_api = TqApi(self)
        # 将当前api的_data值复制到_copy_diff中, 然后merge到副本api的_data里
        _copy_diff = {}
        TqApi._deep_copy_dict(self._data, _copy_diff)
        slave_api._merge_diff(slave_api._data, _copy_diff, slave_api._prototype, False)
        return slave_api

    def close(self) -> None:
        """
        关闭天勤接口实例并释放相应资源

        Example::

            # m1901开多3手
            from tqsdk import TqApi
            from contextlib import closing

            with closing(TqApi()) as api:
                api.insert_order(symbol="DCE.m1901", direction="BUY", offset="OPEN", volume=3)
        """
        if self._loop.is_running():
            raise Exception("不能在协程中调用 close, 如需关闭 api 实例需在 wait_update 返回后再关闭")
        elif asyncio._get_running_loop():
            raise Exception(
                "TqSdk 使用了 python3 的原生协程和异步通讯库 asyncio，您所使用的 IDE 不支持 asyncio, 请使用 pycharm 或其它支持 asyncio 的 IDE")

        # 总会发送 serial_extra_array 数据，由 TqWebHelper 处理
        for _, serial in self._serials.items():
            self._process_serial_extra_array(serial)
        self._run_until_idle()  # 由于有的处于 ready 状态 task 可能需要报撤单, 因此一直运行到没有 ready 状态的 task
        for task in self._tasks:
            task.cancel()
        while self._tasks:  # 等待 task 执行完成
            self._run_once()
        self._loop.run_until_complete(self._loop.shutdown_asyncgens())
        self._loop.close()

    # ----------------------------------------------------------------------
    def get_quote(self, symbol: str) -> Quote:
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
            :py:class:`~tqsdk.objs.Quote`: 返回一个盘口行情引用. 其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新.

            注意: 在 tqsdk 还没有收到行情数据包时, 此对象中各项内容为 NaN 或 0

        Example::

            # 获取 SHFE.cu1812 合约的报价
            from tqsdk import TqApi

            api = TqApi()
            quote = api.get_quote("SHFE.cu1812")
            print(quote.last_price)
            while api.wait_update():
                print(quote.last_price)

            # 预计的输出是这样的:
            nan
            24575.0
            24575.0
            ...
        """
        if symbol not in self._data.get("quotes", {}):
            raise Exception("代码 %s 不存在, 请检查合约代码是否填写正确" % (symbol))
        quote = self._get_obj(self._data, ["quotes", symbol], self._prototype["quotes"]["#"])
        if symbol not in self._requests["quotes"]:
            self._requests["quotes"].add(symbol)
            self._send_pack({
                "aid": "subscribe_quote",
                "ins_list": ",".join(self._requests["quotes"]),
            })
        deadline = time.time() + 30
        while not self._loop.is_running() and quote["datetime"] == "":
            # @todo: merge diffs
            if not self.wait_update(deadline=deadline):
                raise Exception("获取 %s 的行情超时，请检查客户端及网络是否正常，且合约代码填写正确" % (symbol))
        return quote

    # ----------------------------------------------------------------------
    def get_kline_serial(self, symbol: Union[str, List[str]], duration_seconds: int, data_length: int = 200,
                         chart_id: Optional[str] = None) -> pd.DataFrame:
        """
        获取k线序列数据

        请求指定合约及周期的K线数据. 序列数据会随着时间推进自动更新

        Args:
            symbol (str/list of str): 指定合约代码或合约代码列表.
                * str: 一个合约代码
                * list of str: 合约代码列表 （一次提取多个合约的K线并根据相同的时间向第一个合约（主合约）对齐)

            duration_seconds (int): K线数据周期, 以秒为单位。例如: 1分钟线为60,1小时线为3600,日线为86400。\
            注意: 周期在日线以内时此参数可以任意填写, 在日线以上时只能是日线(86400)的整数倍

            data_length (int): 需要获取的序列长度。默认200根, 返回的K线序列数据是从当前最新一根K线开始往回取data_length根。\
            每个序列最大支持请求 8964 个数据

            chart_id (str): [可选]指定序列id, 默认由 api 自动生成

            **注：关于传入合约代码列表 获取多合约K线的说明：**

                1 主合约的字段名为原始K线数据字段，从第一个副合约开始，字段名在原始字段后加数字，如第一个副合约的开盘价为 "open1" , 第二个副合约的收盘价为 "close2"。

                2 每条K线都包含了订阅的所有合约数据，即：如果任意一个合约（无论主、副）在某个时刻没有数据（即使其他合约在此时有数据）,\
                    则不能对齐，此多合约K线在该时刻那条数据被跳过，现象表现为K线不连续（如主合约有夜盘，而副合约无夜盘，则生成的多合约K线无夜盘时间的数据）。

                3 若设置了较大的序列长度参数，而所有可对齐的数据并没有这么多，则序列前面部分数据为NaN（这与获取单合约K线且数据不足序列长度时情况相似）。

                4 若主合约与副合约的交易时间在所有合约数据中最晚一根K线时间开始往回的 8964*周期 时间段内完全不重合，则无法生成多合约K线，程序会报出获取数据超时异常。

                5 **回测暂不支持** 获取多合约K线, 若在回测时获取多合约K线，程序会报出获取数据超时异常。

                6 datetime、duration是所有合约公用的字段，则未单独为每个副合约增加一份副本，这两个字段使用原始字段名（即没有数字后缀）。

        Returns:
            pandas.DataFrame: 本函数总是返回一个 pandas.DataFrame 实例. 行数=data_length, 包含以下列:

            * id: 1234 (k线序列号)
            * datetime: 1501080715000000000 (K线起点时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
            * open: 51450.0 (K线起始时刻的最新价)
            * high: 51450.0 (K线时间范围内的最高价)
            * low: 51450.0 (K线时间范围内的最低价)
            * close: 51450.0 (K线结束时刻的最新价)
            * volume: 11 (K线时间范围内的成交量)
            * open_oi: 27354 (K线起始时刻的持仓量)
            * close_oi: 27355 (K线结束时刻的持仓量)

        Example1::

            # 获取 SHFE.cu1812 的1分钟线
            from tqsdk import TqApi

            api = TqApi()
            klines = api.get_kline_serial("SHFE.cu1812", 60)
            print(klines.iloc[-1].close)
            while True:
                api.wait_update()
                print(klines.iloc[-1].close)

            # 预计的输出是这样的:
            50970.0
            50970.0
            50960.0
            ...

        Example2::

            # 获取按时间对齐的多合约K线
            from tqsdk import TqApi

            api = TqApi()
            # 获取 CFFEX.IF1912 按照K线时间向 SHFE.au2006 对齐的K线
            klines = api.get_kline_serial(["SHFE.au2006", "CFFEX.IF2006"], 5, data_length=10)
            print("多合约K线：", klines.iloc[-1])
            while True:
                api.wait_update()
                if api.is_changing(klines.iloc[-1], ["close1", "close"]):  # 判断任何一个收盘价是否有更新
                    dif = klines.close1 - klines.close  # 使用对齐的K线直接计算价差等数据
                    print("价差序列：", dif)

        Example3::

            # 使用tqsdk自带的时间转换函数, 将最后一根K线的纳秒时间转换为 datetime.datetime 类型
            from tqsdk import tafunc
            ...

            klines = api.get_kline_serial("DCE.jd2001", 10)
            kline_time = tafunc.time_to_datetime(klines.iloc[-1]["datetime"])  # datetime.datetime 类型值
            print(type(kline_time), kline_time)
            print(kline_time.year, kline_time.month, kline_time.day, kline_time.hour, kline_time.minute, kline_time.second)
            ...
        """
        if not isinstance(symbol, list):
            symbol = [symbol]
        for s in symbol:
            if s not in self._data.get("quotes", {}):
                raise Exception("代码 %s 不存在, 请检查合约代码是否填写正确" % (s))
        duration_seconds = int(duration_seconds)  # 转成整数
        if duration_seconds <= 0 or duration_seconds > 86400 and duration_seconds % 86400 != 0:
            raise Exception("K线数据周期 %d 错误, 请检查K线数据周期值是否填写正确" % (duration_seconds))
        data_length = int(data_length)
        if data_length <= 0:
            raise Exception("K线数据序列长度 %d 错误, 请检查序列长度是否填写正确" % (data_length))
        if data_length > 8964:
            data_length = 8964
        dur_id = duration_seconds * 1000000000
        request = (tuple(symbol), duration_seconds, data_length, chart_id)  # request 中 symbols 为 tuple 序列
        serial = self._requests["klines"].get(request, None)
        pack = {
            "aid": "set_chart",
            "chart_id": chart_id if chart_id is not None else self._generate_chart_id("realtime"),
            "ins_list": ",".join(symbol),
            "duration": dur_id,
            "view_width": data_length if len(symbol) == 1 else 8964,
            # 如果同时订阅了两个以上合约K线，初始化数据时默认获取 1w 根K线(初始化完成后修改指令为设定长度)
        }
        if serial is None or chart_id is not None:  # 判断用户是否指定了 chart_id（参数）, 如果指定了，则一定会发送新的请求。
            self._send_pack(pack.copy())  # 注意：将数据权转移给TqChan时其所有权也随之转移，因pack还需要被用到，所以传入副本
        if serial is None:
            serial = self._init_serial([self._get_obj(self._data, ["klines", s, str(dur_id)]) for s in symbol],
                                       data_length, self._prototype["klines"]["*"]["*"]["data"]["@"])
            serial["chart"] = self._get_obj(self._data, ["charts", pack["chart_id"]])  # 保存chart信息
            serial["chart"].update(pack)
            self._requests["klines"][request] = serial
            self._serials[id(serial["df"])] = serial
        deadline = time.time() + 30
        while not self._loop.is_running() and not serial["init"]:
            # @todo: merge diffs
            if not self.wait_update(deadline=deadline):
                if len(symbol) > 1:
                    raise Exception("获取 %s (%d) 的K线超时，请检查客户端及网络是否正常，或任一副合约在主合约行情的最后 %d 秒内无可对齐的K线" % (
                    symbol, duration_seconds, 8964 * duration_seconds))
                else:
                    raise Exception("获取 %s (%d) 的K线超时，请检查客户端及网络是否正常" % (symbol, duration_seconds))
        return serial["df"]

    # ----------------------------------------------------------------------
    def get_tick_serial(self, symbol: str, data_length: int = 200, chart_id: Optional[str] = None) -> pd.DataFrame:
        """
        获取tick序列数据

        请求指定合约的Tick序列数据. 序列数据会随着时间推进自动更新

        Args:
            symbol (str): 指定合约代码.

            data_length (int): 需要获取的序列长度。每个序列最大支持请求 8964 个数据

            chart_id (str): [可选]指定序列id, 默认由 api 自动生成

        Returns:
            pandas.DataFrame: 本函数总是返回一个 pandas.DataFrame 实例. 行数=data_length, 包含以下列:

            * id: 12345 tick序列号
            * datetime: 1501074872000000000 (tick从交易所发出的时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
            * last_price: 3887.0 (最新价)
            * average: 3820.0 (当日均价)
            * highest: 3897.0 (当日最高价)
            * lowest: 3806.0 (当日最低价)
            * ask_price1: 3886.0 (卖一价)
            * ask_volume1: 3 (卖一量)
            * bid_price1: 3881.0 (买一价)
            * bid_volume1: 18 (买一量)
            * volume: 7823 (当日成交量)
            * amount: 19237841.0 (成交额)
            * open_interest: 1941 (持仓量)

        Example::

            # 获取 SHFE.cu1812 的Tick序列
            from tqsdk import TqApi

            api = TqApi()
            serial = api.get_tick_serial("SHFE.cu1812")
            while True:
                api.wait_update()
                print(serial.iloc[-1].bid_price1, serial.iloc[-1].ask_price1)

            # 预计的输出是这样的:
            50860.0 51580.0
            50860.0 51580.0
            50820.0 51580.0
            ...
        """
        if symbol not in self._data.get("quotes", {}):
            raise Exception("代码 %s 不存在, 请检查合约代码是否填写正确" % (symbol))
        data_length = int(data_length)
        if data_length <= 0:
            raise Exception("K线数据序列长度 %d 错误, 请检查序列长度是否填写正确" % (data_length))
        if data_length > 8964:
            data_length = 8964
        request = (symbol, data_length, chart_id)
        serial = self._requests["ticks"].get(request, None)
        pack = {
            "aid": "set_chart",
            "chart_id": chart_id if chart_id is not None else self._generate_chart_id("realtime"),
            "ins_list": symbol,
            "duration": 0,
            "view_width": data_length,
        }
        if serial is None or chart_id is not None:  # 判断用户是否指定了 chart_id（参数）, 如果指定了，则一定会发送新的请求。
            self._send_pack(pack.copy())  # pack 的副本数据和所有权转移给TqChan
        if serial is None:
            serial = self._init_serial([self._get_obj(self._data, ["ticks", symbol])], data_length,
                                       self._prototype["ticks"]["*"]["data"]["@"])
            serial["chart"] = self._get_obj(self._data, ["charts", pack["chart_id"]])
            serial["chart"].update(pack)
            self._requests["ticks"][request] = serial
            self._serials[id(serial["df"])] = serial
        deadline = time.time() + 30
        while not self._loop.is_running() and not serial["init"]:
            # @todo: merge diffs
            if not self.wait_update(deadline=deadline):
                raise Exception("获取 %s 的Tick超时，请检查客户端及网络是否正常，且合约代码填写正确" % (symbol))
        return serial["df"]

    # ----------------------------------------------------------------------
    def insert_order(self, symbol: str, direction: str, offset: str, volume: int, limit_price: Optional[float] = None,
                     order_id: Optional[str] = None) -> Order:
        """
        发送下单指令. **注意: 指令将在下次调用** :py:meth:`~tqsdk.api.TqApi.wait_update` **时发出**

        Args:
            symbol (str): 拟下单的合约symbol, 格式为 交易所代码.合约代码,  例如 "SHFE.cu1801"

            direction (str): "BUY" 或 "SELL"

            offset (str): "OPEN", "CLOSE" 或 "CLOSETODAY"  \
            (上期所和原油分平今/平昨, 平今用"CLOSETODAY", 平昨用"CLOSE"; 其他交易所直接用"CLOSE" 按照交易所的规则平仓)

            volume (int): 需要下单的手数

            limit_price (float): [可选]下单价格, 默认市价单 (上期所、原油和中金所不支持市价单, 需填写此参数值)

            order_id (str): [可选]指定下单单号, 默认由 api 自动生成

        Returns:
            :py:class:`~tqsdk.objs.Order`: 返回一个委托单对象引用. 其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新.

        Example::

            # 市价开3手 DCE.m1809 多仓
            from tqsdk import TqApi

            api = TqApi()
            order = api.insert_order(symbol="DCE.m1809", direction="BUY", offset="OPEN", volume=3)
            while True:
                api.wait_update()
                print("单状态: %s, 已成交: %d 手" % (order.status, order.volume_orign - order.volume_left))

            # 预计的输出是这样的:
            单状态: ALIVE, 已成交: 0 手
            单状态: ALIVE, 已成交: 0 手
            单状态: FINISHED, 已成交: 3 手
            ...
        """
        if symbol not in self._data.get("quotes", {}):
            raise Exception("合约代码 %s 不存在, 请检查合约代码是否填写正确" % (symbol))
        if direction not in ("BUY", "SELL"):
            raise Exception("下单方向(direction) %s 错误, 请检查 direction 参数是否填写正确" % (direction))
        if offset not in ("OPEN", "CLOSE", "CLOSETODAY"):
            raise Exception("开平标志(offset) %s 错误, 请检查 offset 是否填写正确" % (offset))
        volume = int(volume)
        if volume <= 0:
            raise Exception("下单手数(volume) %s 错误, 请检查 volume 是否填写正确" % (volume))
        limit_price = float(limit_price) if limit_price is not None else None
        if not order_id:
            order_id = self._generate_order_id()
        (exchange_id, instrument_id) = symbol.split(".", 1)
        msg = {
            "aid": "insert_order",
            "user_id": self._account._account_id,
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
        self._send_pack(msg)
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
            "_this_session": True,
            "limit_price": limit_price if limit_price is not None else float("nan"),
            "price_type": "ANY" if limit_price is None else "LIMIT",
            "volume_condition": "ANY",
            "time_condition": "IOC" if limit_price is None else "GFD",
        })
        return order

    # ----------------------------------------------------------------------
    def cancel_order(self, order_or_order_id: Union[str, Order]) -> None:
        """
        发送撤单指令. **注意: 指令将在下次调用** :py:meth:`~tqsdk.api.TqApi.wait_update` **时发出**

        Args:
            order_or_order_id (str/ :py:class:`~tqsdk.objs.Order` ): 拟撤委托单或单号

        Example::

            # 挂价开3手 DCE.m1809 多仓, 如果价格变化则撤单重下，直到全部成交
            from tqsdk import TqApi

            api = TqApi()
            quote = api.get_quote("DCE.m1809")
            order = {}

            while True:
                api.wait_update()
                # 当行情有变化且当前挂单价格不优时，则撤单
                if order and api.is_changing(quote) and order.status == "ALIVE" and quote.bid_price1 > order.limit_price:
                    print("价格改变，撤单重下")
                    api.cancel_order(order)
                # 当委托单已撤或还没有下单时则下单
                if (not order and api.is_changing(quote)) or (api.is_changing(order) and order.volume_left != 0 and order.status == "FINISHED"):
                    print("下单: 价格 %f" % quote.bid_price1)
                    order = api.insert_order(symbol="DCE.m1809", direction="BUY", offset="OPEN", volume=order.get("volume_left", 3), limit_price=quote.bid_price1)
                if api.is_changing(order):
                    print("单状态: %s, 已成交: %d 手" % (order.status, order.volume_orign - order.volume_left))


            # 预计的输出是这样的:
            下单: 价格 3117.000000
            单状态: ALIVE, 已成交: 0 手
            价格改变，撤单重下
            下单: 价格 3118.000000
            单状态: ALIVE, 已成交: 0 手
            单状态: FINISHED, 已成交: 3 手
            ...
        """
        if isinstance(order_or_order_id, Order):
            order_id = order_or_order_id.order_id
        else:
            order_id = order_or_order_id
        msg = {
            "aid": "cancel_order",
            "user_id": self._account._account_id,
            "order_id": order_id,
        }
        self._send_pack(msg)

    # ----------------------------------------------------------------------
    def get_account(self) -> Account:
        """
        获取用户账户资金信息

        Returns:
            :py:class:`~tqsdk.objs.Account`: 返回一个账户对象引用. 其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新.

        Example::

            # 获取当前浮动盈亏
            from tqsdk import TqApi

            api = TqApi()
            account = api.get_account()
            print(account.float_profit)

            # 预计的输出是这样的:
            2180.0
            2080.0
            2080.0
            ...
        """
        return self._get_obj(self._data, ["trade", self._account._account_id, "accounts", "CNY"],
                             self._prototype["trade"]["*"]["accounts"]["@"])

    # ----------------------------------------------------------------------
    def get_position(self, symbol: Optional[str] = None) -> Union[Position, Entity]:
        """
        获取用户持仓信息

        Args:
            symbol (str): [可选]合约代码, 不填则返回所有持仓

        Returns:
            :py:class:`~tqsdk.objs.Position`: 当指定了 symbol 时, 返回一个持仓对象引用.
            其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新.

            不填 symbol 参数调用本函数, 将返回包含用户所有持仓的一个tqsdk.objs.Entity对象引用, 使用方法与dict一致, \
            其中每个元素的key为合约代码, value为 :py:class:`~tqsdk.objs.Position`。

            注意: 为保留一些可供用户查询的历史信息, 如 volume_long_yd(本交易日开盘前的多头持仓手数) 等字段, 因此服务器会返回当天已平仓合约( pos_long 和 pos_short 等字段为0)的持仓信息

        Example::

            # 获取 DCE.m1809 当前浮动盈亏
            from tqsdk import TqApi

            api = TqApi()
            position = api.get_position("DCE.m1809")
            print(position.float_profit_long + position.float_profit_short)
            while api.wait_update():
                print(position.float_profit_long + position.float_profit_short)

            # 预计的输出是这样的:
            300.0
            330.0
            ...
        """
        if symbol:
            if symbol not in self._data.get("quotes", {}):
                raise Exception("代码 %s 不存在, 请检查合约代码是否填写正确" % (symbol))
            return self._get_obj(self._data, ["trade", self._account._account_id, "positions", symbol],
                                 self._prototype["trade"]["*"]["positions"]["@"])
        return self._get_obj(self._data, ["trade", self._account._account_id, "positions"])

    # ----------------------------------------------------------------------
    def get_order(self, order_id: Optional[str] = None) -> Union[Order, Entity]:
        """
        获取用户委托单信息

        Args:
            order_id (str): [可选]单号, 不填单号则返回所有委托单

        Returns:
            :py:class:`~tqsdk.objs.Order`: 当指定了order_id时, 返回一个委托单对象引用. \
            其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新.

            不填order_id参数调用本函数, 将返回包含用户所有委托单的一个tqsdk.objs.Entity对象引用, \
            使用方法与dict一致, 其中每个元素的key为委托单号, value为 :py:class:`~tqsdk.objs.Order`

            注意: 在刚下单后, tqsdk 还没有收到回单信息时, 此对象中各项内容为空

        Example::

            # 获取当前总挂单手数
            from tqsdk import TqApi

            api = TqApi()
            orders = api.get_order()
            while True:
                api.wait_update()
                print(sum(order.volume_left for oid, order in orders.items() if order.status == "ALIVE"))

            # 预计的输出是这样的:
            3
            3
            0
            ...
        """
        if order_id:
            return self._get_obj(self._data, ["trade", self._account._account_id, "orders", order_id],
                                 self._prototype["trade"]["*"]["orders"]["@"])
        return self._get_obj(self._data, ["trade", self._account._account_id, "orders"])

    # ----------------------------------------------------------------------
    def get_trade(self, trade_id: Optional[str] = None) -> Union[Trade, Entity]:
        """
        获取用户成交信息

        Args:
            trade_id (str): [可选]成交号, 不填成交号则返回所有委托单

        Returns:
            :py:class:`~tqsdk.objs.Trade`: 当指定了trade_id时, 返回一个成交对象引用. \
            其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新.

            不填trade_id参数调用本函数, 将返回包含用户当前交易日所有成交记录的一个tqsdk.objs.Entity对象引用, 使用方法与dict一致, \
            其中每个元素的key为成交号, value为 :py:class:`~tqsdk.objs.Trade`

            推荐优先使用 :py:meth:`~tqsdk.objs.Order.trade_records` 获取某个委托单的相应成交记录, 仅当确有需要时才使用本函数.

        """
        if trade_id:
            return self._get_obj(self._data, ["trade", self._account._account_id, "trades", trade_id],
                                 self._prototype["trade"]["*"]["trades"]["@"])
        return self._get_obj(self._data, ["trade", self._account._account_id, "trades"])

    # ----------------------------------------------------------------------
    def wait_update(self, deadline: Optional[float] = None) -> None:
        """
        等待业务数据更新

        调用此函数将阻塞当前线程, 等待天勤主进程发送业务数据更新并返回

        注: 它是TqApi中最重要的一个函数, 每次调用它时都会发生这些事:
            * 实际发出网络数据包(如行情订阅指令或交易指令等).
            * 尝试从服务器接收一个数据包, 并用收到的数据包更新内存中的业务数据截面.
            * 让正在运行中的后台任务获得动作机会(如策略程序创建的后台调仓任务只会在wait_update()时发出交易指令).
            * 如果没有收到数据包，则挂起等待.

        Args:
            deadline (float): [可选]指定截止时间，自unix epoch(1970-01-01 00:00:00 GMT)以来的秒数(time.time())。默认没有超时(无限等待)

        Returns:
            bool: 如果收到业务数据更新则返回 True, 如果到截止时间依然没有收到业务数据更新则返回 False

        注意:
            * 天勤终端里策略日志窗口输出的内容由每次调用wait_update()时发出.
            * 由于存在网络延迟, 因此有数据更新不代表之前发出的所有请求都被处理了, 例如::

                from tqsdk import TqApi

                api = TqApi()
                quote = api.get_quote("SHFE.cu1812")
                api.wait_update()
                print(quote.datetime)

            可能输出 ""(空字符串), 表示还没有收到该合约的行情
        """
        if self._loop.is_running():
            raise Exception("不能在协程中调用 wait_update, 如需在协程中等待业务数据更新请使用 register_update_notify")
        elif asyncio._get_running_loop():
            raise Exception(
                "TqSdk 使用了 python3 的原生协程和异步通讯库 asyncio，您所使用的 IDE 不支持 asyncio, 请使用 pycharm 或其它支持 asyncio 的 IDE")
        self._wait_timeout = False
        # 先尝试执行各个task,再请求下个业务数据
        self._run_until_idle()

        # 总会发送 serial_extra_array 数据，由 TqWebHelper 处理
        for _, serial in self._serials.items():
            self._process_serial_extra_array(serial)
        # 先尝试执行各个task,再请求下个业务数据
        self._run_until_idle()
        if not self._is_slave and self._diffs:
            self._send_chan.send_nowait({
                "aid": "peek_message"
            })
        # 先 _fetch_msg 再判断 deadline, 避免当 deadline 立即触发时无法接收数据
        update_task = self.create_task(self._fetch_msg())
        deadline_handle = None if deadline is None else self._loop.call_later(max(0, deadline - time.time()),
                                                                              self._set_wait_timeout)
        try:
            while not self._wait_timeout and not self._pending_diffs:
                self._run_once()
            return len(self._pending_diffs) != 0
        finally:
            self._diffs = self._pending_diffs
            self._pending_diffs = []
            # 清空K线更新范围，避免在 wait_update 未更新K线时仍通过 is_changing 的判断
            self._klines_update_range = {}
            for d in self._diffs:
                self._merge_diff(self._data, d, self._prototype, False)
            for _, serial in self._serials.items():
                # K线df的更新与原始数据、left_id、right_id、more_data、last_id相关，其中任何一个发生改变都应重新计算df
                # 注：订阅某K线后再订阅合约代码、周期相同但长度更短的K线时, 服务器不会再发送已有数据到客户端，即chart发生改变但内存中原始数据未改变。
                # 检测到K线数据或chart的任何字段发生改变则更新serial的数据
                if self.is_changing(serial["df"]) or self.is_changing(serial["chart"]):
                    if len(serial["root"]) == 1:  # 订阅单个合约
                        self._update_serial_single(serial)
                    else:  # 订阅多个合约
                        self._update_serial_multi(serial)
            if deadline_handle:
                deadline_handle.cancel()
            update_task.cancel()

    # ----------------------------------------------------------------------
    def is_changing(self, obj: Any, key: Union[str, List[str], None] = None) -> bool:
        """
        判定obj最近是否有更新

        当业务数据更新导致 wait_update 返回后可以使用该函数判断 **本次业务数据更新是否包含特定obj或其中某个字段** 。

        关于判断K线更新的说明：
        当生成新K线时，其所有字段都算作有更新，若此时执行 api.is_changing(klines.iloc[-1]) 则一定返回True。

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
            from tqsdk import TqApi

            api = TqApi()
            quote = api.get_quote("SHFE.cu1812")
            print(quote.last_price)
            while True:
                api.wait_update()
                if api.is_changing(quote, "last_price"):
                    print(quote.last_price)

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
                if id(obj) in self._serials:
                    paths = []
                    for root in self._serials[id(obj)]["root"]:
                        paths.append(root["_path"])
                elif len(obj) == 0:
                    return False
                else:  # 处理传入的为一个 copy 出的 DataFrame (与原 DataFrame 数据相同的另一个object)
                    duration = int(obj["duration"].iloc[0]) * 1000000000
                    paths = [
                        ["klines", obj[k].iloc[0], str(duration)] if duration != 0 else ["ticks", obj["symbol"].iloc[0]]
                        for k in obj.keys() if k.startswith("symbol")]
            elif isinstance(obj, pd.Series):
                ins_list = [v for k, v in obj.items() if k.startswith("symbol")]
                if len(ins_list) > 1:  # 如果是K线的Series
                    # 处理：一根新K线的数据被拆分到多个数据包中时 diff 中只有最后一个包的数据，
                    # 则 is_changing 无法根据前面数据包中的字段来判断K线有更新(仅在生成多合约新K线时产生此问题),因此：用_klines_update_range记录/判定更新
                    new_kline_range = self._klines_update_range.get(
                        (ins_list[0], tuple(ins_list[1:]), obj["duration"] * 1000000000), (0, 0))
                    if obj["id"] >= new_kline_range[0] and obj["id"] < new_kline_range[1]:  # 保持左闭右开规范
                        return True
                duration = int(obj["duration"]) * 1000000000
                paths = []
                if duration != 0:
                    for i in range(0, len(ins_list)):
                        # pandas的key值序列会保持固定顺序, 则ins_list[i]对应的是"id"+str(i)，否则不成立。 todo:增加测试用例以保证其顺序一致，若不再顺序一致则修改此处用法
                        key_id = "id" + str(i) if i != 0 else "id"
                        if key_id in obj.keys():
                            paths.append(["klines", ins_list[i], str(duration), "data", str(int(obj[key_id]))])
                        else:
                            paths.append(["klines", ins_list[i], str(duration), "data", str(-1)])
                else:
                    paths.append(["ticks", obj["symbol"], "data", str(int(obj["id"]))])

            else:
                paths = [obj["_path"]]
        except (KeyError, IndexError):
            return False
        for diff in self._diffs:
            # 如果传入key：生成一个dict（key:序号，value: 字段）, 遍历这个dict并在_is_key_exist()判断key是否存在
            if (isinstance(obj, pd.DataFrame) or isinstance(obj, pd.Series)) and len(key) != 0:
                k_dict = {}
                for k in key:
                    if k not in obj.index:
                        continue
                    m = re.match(r'(.*?)(\d+)$', k)  # 匹配key中的数字
                    if m is None:  # 无数字
                        k_dict.setdefault(0, []).append(k)
                    elif int(m.group(2)) < len(paths):
                        m_k = int(m.group(2))
                        k_dict.setdefault(m_k, []).append(m.group(1))
                for k_id, v in k_dict.items():
                    if self._is_key_exist(diff, paths[k_id], v):
                        return True
            else:  # 如果没有传入key：遍历所有path
                for path in paths:
                    if self._is_key_exist(diff, path, key):
                        return True
        return False

    # ----------------------------------------------------------------------
    def is_serial_ready(self, obj: pd.DataFrame) -> bool:
        """
        判断是否已经从服务器收到了所有订阅的数据

        Args:
            obj (pandas.Dataframe): K线数据

        Returns:
            bool: 返回 True 表示已经从服务器收到了所有订阅的数据

        Example::

            # 判断是否已经从服务器收到了最后 3000 根 SHFE.cu1812 的分钟线数据
            from tqsdk import TqApi

            api = TqApi()
            klines = api.get_kline_serial("SHFE.cu1812", 60, data_length=3000)
            while True:
                api.wait_update()
                print(api.is_serial_ready(klines))

            # 预计的输出是这样的:
            False
            False
            True
            True
            ...
        """
        return self._serials[id(obj)]["init"]

    # ----------------------------------------------------------------------
    def create_task(self, coro: asyncio.coroutine) -> asyncio.Task:
        """
        创建一个task

        一个task就是一个协程，task的调度是在 wait_update 函数中完成的，如果代码从来没有调用 wait_update，则task也得不到执行

        Args:
            coro (coroutine):  需要创建的协程

        Example::

            # 一个简单的task
            import asyncio
            from tqsdk import TqApi

            async def hello():
                await asyncio.sleep(3)
                print("hello world")

            api = TqApi()
            api.create_task(hello())
            while True:
                api.wait_update()

            #以上代码将在3秒后输出
            hello world
        """
        task = self._loop.create_task(coro)
        if asyncio.Task.current_task(loop=self._loop) is None:
            self._tasks.add(task)
            task.add_done_callback(self._on_task_done)
        return task

    # ----------------------------------------------------------------------
    def register_update_notify(self, obj: Optional[Any] = None, chan: Optional['TqChan'] = None) -> 'TqChan':
        """
        注册一个channel以便接受业务数据更新通知

        调用此函数将返回一个channel, 当obj更新时会通知该channel

        推荐使用 async with api.register_update_notify() as update_chan 来注册更新通知

        如果直接调用 update_chan = api.register_update_notify() 则使用完成后需要调用 await update_chan.close() 避免资源泄漏

        Args:
            obj (any/list of any): [可选]任意业务对象, 包括 get_quote 返回的 quote, get_kline_serial 返回的 k_serial, \
            get_account 返回的 account 等。默认不指定，监控所有业务对象

            chan (TqChan): [可选]指定需要注册的channel。默认不指定，由本函数创建

        Example::

            # 获取 SHFE.cu1812 合约的报价
            from tqsdk import TqApi

            async def demo():
                quote = api.get_quote("SHFE.cu1812")
                async with api.register_update_notify(quote) as update_chan:
                    async for _ in update_chan:
                        print(quote.last_price)

            api = TqApi()
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
            obj = [obj] if obj is not None else [self._data]
        for o in obj:
            if isinstance(o, pd.DataFrame):
                for root in self._serials[id(o)]["root"]:
                    listener = root["_listener"]
                    listener.add(chan)
            else:
                listener = o["_listener"]
                listener.add(chan)
        return chan

    # ----------------------------------------------------------------------
    def set_replay_speed(self, speed: float = 10.0) -> None:
        """
        调整复盘服务器行情推进速度

        Args:
            speed (float): 复盘服务器行情推进速度, 默认为 10.0

        """
        if isinstance(self._backtest, TqReplay):
            self._backtest._set_server_session({"aid": "ratio", "speed": speed})

    # ----------------------------------------------------------------------
    def _call_soon(self, org_call_soon, callback, *args, **kargs):
        """ioloop.call_soon的补丁, 用来追踪是否有任务完成并等待执行"""
        self._event_rev += 1
        return org_call_soon(callback, *args, **kargs)

    def _setup_connection(self):
        """初始化"""
        tq_web_helper = TqWebHelper(self)

        # 等待复盘服务器启动
        if isinstance(self._backtest, TqReplay):
            self._account = self._account if isinstance(self._account, TqSim) else TqSim()
            self._ins_url, self._md_url = self._backtest._create_server(self)

        # 连接合约和行情服务器
        ws_md_send_chan, ws_md_recv_chan = TqChan(self), TqChan(self)
        ws_md_recv_chan.send_nowait({
            "aid": "rtn_data",
            "data": [{
                "quotes": self._fetch_symbol_info(self._ins_url)
            }]
        })  # 获取合约信息
        self.create_task(self._connect(self._md_url, ws_md_send_chan, ws_md_recv_chan))  # 启动行情websocket连接

        # 复盘模式，定时发送心跳包, 并将复盘日期发在行情的 recv_chan
        if isinstance(self._backtest, TqReplay):
            ws_md_recv_chan.send_nowait({
                "aid": "rtn_data",
                "data": [{
                    "_tqsdk_replay": {
                        "replay_dt": int(datetime.combine(self._backtest._replay_dt, datetime.min.time()).timestamp() * 1e9)}
                }]
            })
            self.create_task(self._backtest._run())

        # 如果处于回测模式，则将行情连接对接到 backtest 上
        if isinstance(self._backtest, TqBacktest):
            self._account = self._account if isinstance(self._account, TqSim) else TqSim()
            bt_send_chan, bt_recv_chan = TqChan(self), TqChan(self)
            self.create_task(self._backtest._run(self, bt_send_chan, bt_recv_chan, ws_md_send_chan, ws_md_recv_chan))
            ws_md_send_chan, ws_md_recv_chan = bt_send_chan, bt_recv_chan

        # 启动TqSim或连接交易服务器
        if isinstance(self._account, TqSim):
            self.create_task(
                self._account._run(self, self._send_chan, self._recv_chan, ws_md_send_chan, ws_md_recv_chan))
        else:
            ws_td_send_chan, ws_td_recv_chan = TqChan(self), TqChan(self)
            self.create_task(self._connect(self._td_url, ws_td_send_chan, ws_td_recv_chan))
            self.create_task(
                self._account._run(self, self._send_chan, self._recv_chan, ws_md_send_chan, ws_md_recv_chan,
                                   ws_td_send_chan, ws_td_recv_chan))

        # 与 web 配合, 在 tq_web_helper 内部中处理 web_gui 选项
        web_send_chan, web_recv_chan = TqChan(self), TqChan(self)
        self.create_task(tq_web_helper._run(web_send_chan, web_recv_chan, self._send_chan, self._recv_chan))
        self._send_chan, self._recv_chan = web_send_chan, web_recv_chan

        # 发送第一个peek_message,因为只有当收到上游数据包时wait_update()才会发送peek_message
        self._send_chan.send_nowait({
            "aid": "peek_message"
        })

    def _fetch_symbol_info(self, url):
        """获取合约信息"""
        rsp = requests.get(url, headers=self._base_headers, timeout=30)
        rsp.raise_for_status()
        return {
            k: {
                "ins_class": v.get("class", ""),
                'instrument_id': v.get("instrument_id", ""),
                "margin": v.get("margin"),  # 用于内部实现模拟交易, 不作为 api 对外可用数据（即 Quote 类中无此字段）
                "commission": v.get("commission"),  # 用于内部实现模拟交易, 不作为 api 对外可用数据（即 Quote 类中无此字段）
                "price_tick": v["price_tick"],
                "price_decs": v["price_decs"],
                "volume_multiple": v["volume_multiple"],
                "max_limit_order_volume": v.get("max_limit_order_volume", 0),
                "max_market_order_volume": v.get("max_market_order_volume", 0),
                "min_limit_order_volume": v.get("min_limit_order_volume", 0),
                "min_market_order_volume": v.get("min_market_order_volume", 0),
                "underlying_symbol": v.get("underlying_symbol", ""),
                "strike_price": v.get("strike_price", float("nan")),
                "expired": v["expired"],
                "trading_time": v.get("trading_time"),
                "expire_datetime": v.get("expire_datetime"),
                "delivery_month": v.get("delivery_month"),
                "delivery_year": v.get("delivery_year"),
            } for k, v in rsp.json().items()
        }

    def _init_serial(self, root_list, width, default):
        last_id_list = [root.get("last_id", -1) for root in root_list]
        # 主合约的array字段
        array = [[default["datetime"]] + [i] + [default[k] for k in default if k != "datetime"] for i in
                 range(last_id_list[0] + 1 - width, last_id_list[0] + 1)]
        for last_id in last_id_list[1:]:
            # 将多个列横向合并
            array = np.hstack((array, [[i] + [default[k] for k in default if k != "datetime"] for i in
                                       range(last_id + 1 - width, last_id + 1)]))

        default_keys = ["id"] + [k for k in default.keys() if k != "datetime"]
        columns = ["datetime"] + default_keys
        for i in range(1, len(root_list)):
            columns += [k + str(i) for k in default_keys]
        serial = {
            "root": root_list,
            "width": width,
            "default": default,
            "array": np.array(array, order="F"),
            "init": False,  # 是否初始化完成. 完成状态: 订阅K线后已获取所有主、副合约的数据并填满df序列.
            "update_row": 0,  # 起始更新数据行
            "all_attr": set(columns) | {"symbol" + str(i) for i in range(1, len(root_list))} | {"symbol", "duration"},
            "extra_array": {},
        }
        serial["df"] = pd.DataFrame(serial["array"], columns=columns)
        serial["df"]["symbol"] = root_list[0]["_path"][1]
        for i in range(1, len(root_list)):
            serial["df"]["symbol" + str(i)] = root_list[i]["_path"][1]

        serial["df"]["duration"] = 0 if root_list[0]["_path"][0] == "ticks" else int(
            root_list[0]["_path"][-1]) // 1000000000
        return serial

    def _update_serial_single(self, serial):
        """处理订阅单个合约时K线的数据更新"""
        last_id = serial["root"][0].get("last_id", -1)
        array = serial["array"]
        serial["update_row"] = 0
        if serial["init"]:  # 已经初始化完成
            shift = min(last_id - int(array[-1, 1]), serial["width"])  # array[-1, 1]: 已有数据的last_id
            if shift != 0:
                array[0:serial["width"] - shift] = array[shift:serial["width"]]
                for ext in serial["extra_array"].values():
                    ext[0:serial["width"] - shift] = ext[shift:serial["width"]]
                    if np.issubdtype(ext.dtype, np.floating):
                        ext[serial["width"] - shift:] = np.nan
                    elif np.issubdtype(ext.dtype, np.object_):
                        ext[serial["width"] - shift:] = None
                    elif np.issubdtype(ext.dtype, np.integer):
                        ext[serial["width"] - shift:] = 0
                    elif np.issubdtype(ext.dtype, np.bool_):
                        ext[serial["width"] - shift:] = False
                    else:
                        ext[serial["width"] - shift:] = np.nan
            serial["update_row"] = max(serial["width"] - shift - 1, 0)
        else:
            left_id = serial["chart"].get("left_id", -1)
            right_id = serial["chart"].get("right_id", -1)
            if (left_id != -1 or right_id != -1) and not serial["chart"].get("more_data", True) and serial["root"][
                0].get("last_id", -1) != -1:
                serial["init"] = True

        for i in range(serial["update_row"], serial["width"]):
            index = last_id - serial["width"] + 1 + i
            item = serial["default"] if index < 0 else TqApi._get_obj(serial["root"][0], ["data", str(index)],
                                                                      serial["default"])
            array[i] = [item["datetime"]] + [index] + [item[k] for k in serial["default"].keys() if k != "datetime"]

    def _update_serial_multi(self, serial):
        """处理订阅多个合约时K线的数据更新"""
        # 判断初始化数据是否接收完全, 否: 则返回
        left_id = serial["chart"].get("left_id", -1)  # 主合约的left_id
        right_id = serial["chart"].get("right_id", -1)  # 主合约的right_id
        if (left_id == -1 and right_id == -1) or serial["chart"].get("more_data", True):
            return
        for root in serial["root"]:
            if root.get("last_id", -1) == -1:
                return

        array = serial["array"]
        ins_list = serial["chart"]["ins_list"].split(",")  # 合约列表

        if not serial["init"]:  # 未初始化完成则进行初始化处理. init完成状态: 订阅K线后获取所有数据并填满df序列.
            update_row = serial["width"] - 1  # 起始更新数据行,局部变量
            current_id = right_id  # 当前数据指针
            while current_id >= left_id and current_id >= 0 and update_row >= 0:  # 如果当前id >= left_id 且 数据尚未填满width长度
                master_item = serial["root"][0]["data"][str(current_id)]  # 主合约中 current_id 对应的数据
                # 此次更新的一行array初始化填入主合约数据
                row_data = [master_item["datetime"]] + [current_id] + [master_item[col] for col in
                                                                       serial["default"].keys() if col != "datetime"]
                tid = -1
                for symbol in ins_list[1:]:  # 遍历副合约
                    # 从binding中取出与symbol对应的last_id
                    tid = serial["root"][0].get("binding", {}).get(symbol, {}).get(str(current_id), -1)
                    if tid == -1:
                        break
                    other_item = serial["root"][ins_list.index(symbol)]["data"].get(str(tid))  # 取出tid对应的副合约数据
                    if other_item is None:
                        # 1 避免初始化时主合约和binding都收到但副合约数据尚未收到报错
                        # 2 使用break而非return: 避免夜盘时有binding数据但其对应的副合约需到白盘才有数据（即等待时间过长导致报超时错误）
                        tid = -1
                        break
                    row_data += [tid] + [other_item[col] for col in serial["default"].keys() if col != "datetime"]
                if tid != -1:
                    # 数据更新
                    array[update_row] = row_data
                    update_row -= 1
                current_id -= 1
            # 当主合约与某副合约的交易时间完全无重合时不会更新数据。当 update_row 发生了改变，表示数据有更新，则将序列就绪标志转为 True
            if update_row != serial["width"] - 1:
                serial["init"] = True
                serial["update_row"] = 0  # 若需发送数据给天勤，则发送所有数据

            # 修改行情订阅指令的 view_width
            self._send_pack({
                "aid": "set_chart",
                "chart_id": serial["chart"]["chart_id"],
                "ins_list": serial["chart"]["ins_list"],
                "duration": serial["chart"]["duration"],
                # 如果长度小于30,则默认请求30,以保证能包含到所有在向上处理数据时收到的新数据,30:get_klines_serial()中等待超时的秒数,最小K线序列为1s线
                "view_width": len(array) if len(array) >= 30 else 30,
            })
        else:  # 正常行情更新处理
            serial["update_row"] = serial["width"] - 1
            new_kline_range = None
            new_data_index = serial["width"] - 1  # 记录更新数据位置
            # 从 left_id 或 已有数据的最后一个 last_id 到服务器发回的最新数据的 last_id: 每次循环更新一行。max: 避免数据更新过多时产生大量多余循环判断
            for i in range(max(serial["chart"].get("left_id", -1), int(array[-1, 1])),
                           serial["root"][0].get("last_id", -1) + 1):
                # 如果某条主K线和某条副K线之间的 binding 映射数据存在: 则对应副合约数据也存在; 遍历主合约与所有副合约的binding信息, 如果都存在, 则将此K线填入array保存.
                master_item = serial["root"][0]["data"][str(i)]  # 主合约数据
                # array更新的一行数据: 初始化填入主合约数据
                row_data = [master_item["datetime"]] + [i] + [master_item[col] for col in serial["default"].keys() if
                                                              col != "datetime"]
                tid = -1
                for symbol in ins_list[1:]:  # 遍历副合约
                    # 从binding中取出与symbol对应的last_id
                    tid = (serial["root"][0].get("binding", {}).get(symbol, {}).get(str(i), -1))
                    if tid == -1:
                        break
                    # 取出tid对应的副合约数据
                    other_item = serial["root"][ins_list.index(symbol)]["data"].get(str(tid))
                    if other_item is None:
                        return
                    row_data += [tid] + [other_item[col] for col in serial["default"].keys() if col != "datetime"]
                # 如果有新增K线, 则向上移动一行；循环的第一条数据为原序列最后一条数据, 只更新不shift
                if tid != -1:
                    if i != array[-1, 1]:  # 如果不是已有数据的最后一行，表示生成新K线，则向上移动一行
                        new_data_index = new_data_index + 1
                        # 修改 serial["update_row"] 以保证发送正确数序列给天勤
                        serial["update_row"] = serial["update_row"] - 1 if serial["update_row"] > 0 else 0
                        if new_kline_range is None:  # 记录第一条新K线的id
                            new_kline_range = i
                    # 数据更新
                    array[new_data_index % serial["width"]] = row_data
            if new_kline_range is not None:  # 有新K线生成
                array[:] = np.roll(array, serial["width"] - (new_data_index % serial["width"]) - 1, axis=0)[:]

                remain = max(2 * serial["width"] - 1 - new_data_index, 0)
                for ext in serial["extra_array"].values():
                    ext[:remain] = ext[serial["width"] - remain:]
                    if ext.dtype == np.float:
                        ext[remain:] = np.nan
                    elif ext.dtype == np.object:
                        ext[remain:] = None
                    elif ext.dtype == np.int:
                        ext[remain:] = 0
                    elif ext.dtype == np.bool:
                        ext[remain:] = False
                    else:
                        ext[remain:] = np.nan

                k = (ins_list[0], tuple(ins_list[1:]), serial["df"]["duration"][0] * 1000000000)
                # 注: i 从 left_id 开始，shift最大长度为width，则必有：new_kline_range >= array[0,1]
                self._klines_update_range[k] = (
                    new_kline_range if not self._klines_update_range.get(k) else min(self._klines_update_range[k][0],
                                                                                     new_kline_range),
                    array[-1, 1] + 1)  # array[-1, 1] + 1： 保持左闭右开规范

    def _process_serial_extra_array(self, serial):
        for col in set(serial["df"].columns.values) - serial["all_attr"]:
            serial["update_row"] = 0
            serial["extra_array"][col] = serial["df"][col].to_numpy()
        # 如果策略中删除了之前添加到 df 中的序列，则 extra_array 中也将其删除
        for col in serial["all_attr"] - set(serial["df"].columns.values):
            del serial["extra_array"][col]
        serial["all_attr"] = set(serial["df"].columns.values)
        if serial["update_row"] == serial["width"]:
            return
        symbol = serial["root"][0]["_path"][1]  # 主合约的symbol，标志绘图的主合约
        duration = 0 if serial["root"][0]["_path"][0] == "ticks" else int(serial["root"][0]["_path"][-1])
        cols = list(serial["extra_array"].keys())
        # 归并数据序列
        while len(cols) != 0:
            col = cols[0].split(".")[0]
            # 找相关序列，首先查找以col开头的序列
            group = [c for c in cols if c.startswith(col + ".") or c == col]
            cols = [c for c in cols if c not in group]
            data = {c[len(col):]: serial["extra_array"][c][serial["update_row"]:] for c in group}
            self._process_chart_data_for_web(serial, symbol, duration, col, serial["width"] - serial["update_row"],
                                             int(serial["array"][-1, 1]) + 1, data)
        serial["update_row"] = serial["width"]

    def _process_chart_data_for_web(self, serial, symbol, duration, col, count, right, data):
        # 与 _process_chart_data 函数功能类似，但是处理成符合 diff 协议的序列，在 js 端就不需要特殊处理了
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
        send_data = {
            "type": "KSERIAL" if data_type == "KSERIAL" else "SERIAL",
            "range_left": right - count,
            "range_right": right - 1,
            "data": {}
        }
        # 在执行 _update_serial_single 时，有可能将未赋值的字段设置为 None, 这里如果为 None 则不发送这个 board 字段，
        # 因为 None 在 diff 协议中的含义是删除这个字段，这里仅仅表示不赋新值，下面的 color, width 同理
        board = data.get(".board", ["MAIN"])[-1]
        if board:
            send_data["board"] = data.get(".board", ["MAIN"])[-1]
        if data_type in {"LINE", "DOT", "DASH", "BAR"}:
            send_data["style"] = data_type
            color = data.get(".color", ["#FF0000"])[-1]
            if color:
                send_data["color"] = color if isinstance(color, str) else int(color)
            width = int(data.get(".width", [1])[-1])
            if width:
                send_data["width"] = int(data.get(".width", [1])[-1])
            for i in range(count):
                send_data["data"][i + right - count] = {
                    # 数据结构与 KSERIAL 保持一致，只有一列的时候，默认 key 值取 "value"
                    "value": data[""][i]
                }
            self._send_series_data(symbol, duration, col, send_data, aid="set_chart_data")
        elif data_type == "KSERIAL":
            for i in range(count):
                send_data["data"][i + right - count] = {
                    "open": data[".open"][i],
                    "high": data[".high"][i],
                    "low": data[".low"][i],
                    "close": data[".close"][i]
                }
            self._send_series_data(symbol, duration, col, send_data, aid="set_chart_data")

    def _send_series_data(self, symbol, duration, serial_id, serial_data, aid="set_chart_data"):
        pack = {
            "aid": aid,
            "symbol": symbol,
            "dur_nano": duration,
            "datas": {
                serial_id: serial_data,
            }
        }
        self._send_pack(pack)

    def _run_once(self):
        """执行 ioloop 直到 ioloop.stop 被调用"""
        if not self._exceptions:
            self._loop.run_forever()
        if self._exceptions:
            raise self._exceptions.pop(0)

    def _run_until_idle(self):
        """执行 ioloop 直到没有待执行任务"""
        while self._check_rev != self._event_rev:
            check_handle = self._loop.call_soon(self._check_event, self._event_rev + 1)
            try:
                self._run_once()
            finally:
                check_handle.cancel()

    def _check_event(self, rev):
        self._check_rev = rev
        self._loop.stop()

    def _set_wait_timeout(self):
        self._wait_timeout = True
        self._loop.stop()

    def _on_task_done(self, task):
        """当由 api 维护的 task 执行完成后取出运行中遇到的例外并停止 ioloop"""
        try:
            exception = task.exception()
            if exception:
                self._exceptions.append(exception)
        except asyncio.CancelledError:
            pass
        finally:
            self._tasks.remove(task)
            self._loop.stop()

    async def _windows_patch(self):
        """Windows系统下asyncio不支持KeyboardInterrupt的临时补丁, 详见 https://bugs.python.org/issue23057"""
        while True:
            await asyncio.sleep(1)

    async def _notify_watcher(self):
        """将从服务器收到的通知打印出来"""
        notify_logger = self._logger.getChild("Notify")
        processed_notify = set()
        notify = self._get_obj(self._data, ["notify"])
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
                    notify_logger.log(level, "通知: %s", notify[n]["content"])

    async def _connect(self, url, send_chan, recv_chan):
        """启动websocket客户端"""
        resend_request = {}  # 重连时需要重发的请求
        pos_symbols = {}  # 断线前持有的所有合约代码
        first_connect = True  # 首次连接标志
        un_processed = False  # 重连后尚未处理完标志
        keywords = {
            "max_size": None,
            "extra_headers": self._base_headers
        }
        if url.startswith("wss://"):
            ssl_context = ssl.create_default_context()
            ssl_context.load_verify_locations(certifi.where())
            keywords["ssl"] = ssl_context
        while True:
            try:
                async with websockets.connect(url, **keywords) as client:
                    # 发送网络连接建立的通知，code = 2019112901
                    notify_id = uuid.UUID(int=TqApi.RD.getrandbits(128)).hex
                    notify = {
                        "type": "MESSAGE",
                        "level": "INFO",
                        "code": 2019112901,
                        "content": "与 %s 的网络连接已建立" % url,
                        "url": url
                    }

                    if not first_connect:  # 如果不是第一次连接, 即为重连
                        # 发送网络连接重新建立的通知，code = 2019112902
                        notify["code"] = 2019112902
                        notify["level"] = "WARNING"
                        notify["content"] = "与 %s 的网络连接已恢复" % url
                        un_processed = True  # 重连后数据未处理完
                        t_pending_diffs = []
                        t_data = Entity()
                        t_data._instance_entity([])
                        if url == self._md_url:  # 获取重连时需发送的所有 set_chart 指令包
                            set_chart_packs = {k: v for k, v in resend_request.items() if v.get("aid") == "set_chart"}

                    # 发送网络连接建立的通知，code = 2019112901 or 2019112902，这里区分了第一次连接和重连
                    await recv_chan.send({
                        "aid": "rtn_data",
                        "data": [{
                            "notify": {
                                notify_id: notify
                            }
                        }]
                    })
                    send_task = self.create_task(
                        self._send_handler(client, url, resend_request, send_chan, first_connect))
                    try:
                        async for msg in client:
                            self._logger.debug("websocket message received from %s: %s", url, msg)
                            # 处理在重连后K线等行情没有一次性发送完全而导致部分数据为nan或-1等无用数据; 处理初重连前的持仓信息中多余的合约信息
                            pack = json.loads(msg)
                            if url == self._td_url:  # 如果是交易连接, 则保存所有的持仓合约
                                for d in pack.get("data", []):
                                    for user, trade_data in d.get("trade", {}).items():
                                        if user not in pos_symbols:
                                            pos_symbols[user] = set()
                                        pos_symbols[user].update(trade_data.get("positions", {}).keys())
                            if not first_connect and un_processed:  # 如果重连连接刚建立
                                pack_data = pack.get("data", [])
                                t_pending_diffs.extend(pack_data)
                                for d in pack_data:
                                    self._merge_diff(t_data, d, self._prototype, False)
                                if url == self._md_url:  # 如果连接行情系统: 将断线前订阅的所有行情数据收集到一起后才同时发送给下游, 以保证数据完整
                                    # 处理seriesl(k线/tick)
                                    if not all(
                                            [v.items() <= self._get_obj(t_data, ["charts", k, "state"]).items() for k, v
                                             in set_chart_packs.items()]):
                                        await client.send(json.dumps({
                                            "aid": "peek_message"
                                        }))
                                        self._logger.debug("websocket message sent to %s: %s, due to charts state", url,
                                                           '{"aid": "peek_message"}')
                                        continue  # 如果当前请求还没收齐回应, 不应继续处理
                                    # 在接收并处理完成指令后, 此时发送给客户端的数据包中的 left_id或right_id 至少有一个不是-1 , 并且 mdhis_more_data是False；否则客户端需要继续等待数据完全发送
                                    if not all([(self._get_obj(t_data, ["charts", k]).get("left_id",
                                                                                          -1) != -1 or self._get_obj(
                                        t_data, ["charts", k]).get("right_id", -1) != -1) and not t_data.get(
                                        "mdhis_more_data", True) for k in set_chart_packs.keys()]):
                                        await client.send(json.dumps({
                                            "aid": "peek_message"
                                        }))
                                        self._logger.debug(
                                            "websocket message sent to %s: %s, due to left_id or last_id", url,
                                            '{"aid": "peek_message"}')
                                        continue  # 如果当前所有数据未接收完全(定位信息还没收到, 或数据序列还没收到), 不应继续处理
                                    all_received = True  # 订阅K线数据完全接收标志
                                    for k, v in set_chart_packs.items():  # 判断已订阅的数据是否接收完全
                                        for symbol in v["ins_list"].split(","):
                                            if symbol:
                                                path = ["klines", symbol, str(v["duration"])] if v[
                                                                                                     "duration"] != 0 else [
                                                    "ticks", symbol]
                                                serial = self._get_obj(t_data, path)
                                                if serial.get("last_id", -1) == -1:
                                                    all_received = False
                                                    break
                                        if not all_received:
                                            break
                                    if not all_received:
                                        await client.send(json.dumps({
                                            "aid": "peek_message"
                                        }))
                                        self._logger.debug("websocket message sent to %s: %s, due to last_id", url,
                                                           '{"aid": "peek_message"}')
                                        continue
                                    # 处理实时行情quote
                                    if t_data.get("ins_list", "") != resend_request.get("subscribe_quote", {}).get(
                                            "ins_list", ""):
                                        await client.send(json.dumps({
                                            "aid": "peek_message"
                                        }))
                                        self._logger.debug("websocket message sent to %s: %s, due to subscribe_quote",
                                                           url, '{"aid": "peek_message"}')
                                        continue  # 如果实时行情quote未接收完全, 不应继续处理

                                elif url == self._td_url:  # 如果连接交易系统: 判断断线前的持仓合约比重连后真实持仓更多, 若是则发送删除指令将其删除
                                    if not all([(not t_data.get("trade", {}).get(user, {}).get("trade_more_data", True))
                                                for user in pos_symbols.keys()]):
                                        await client.send(json.dumps({
                                            "aid": "peek_message"
                                        }))
                                        self._logger.debug("websocket message sent to %s: %s, due to 'trade_more_data'",
                                                           url, '{"aid": "peek_message"}')
                                        continue  # 如果交易数据未接收完全, 不应继续处理
                                    for user, trade_data in t_data.get("trade", {}).items():
                                        symbols = set(trade_data.get("positions", {}).keys())  # 当前真实持仓中的合约
                                        if pos_symbols.get(user, set()) > symbols:  # 如果此用户历史持仓中的合约比当前真实持仓中更多: 删除多余合约信息
                                            t_pending_diffs.append({
                                                "trade": {
                                                    user: {
                                                        "positions": {symbol: None for symbol in
                                                                      (pos_symbols[
                                                                           user] - symbols)}
                                                    }
                                                }
                                            })

                                await recv_chan.send({
                                    "aid": "rtn_data",
                                    "data": t_pending_diffs
                                })
                                un_processed = False
                                continue

                            await recv_chan.send(pack)
                    finally:
                        send_task.cancel()
                        await send_task
            # 希望做到的效果是遇到网络问题可以断线重连, 但是可能抛出的例外太多了(TimeoutError,socket.gaierror等), 又没有文档或工具可以理出 try 代码中所有可能遇到的例外
            # 而这里的 except 又需要处理所有子函数及子函数的子函数等等可能抛出的例外, 因此这里只能遇到问题之后再补, 并且无法避免 false positive 和 false negative
            except (websockets.exceptions.ConnectionClosed, OSError):
                # 发送网络连接断开的通知，code = 2019112911
                notify_id = uuid.UUID(int=TqApi.RD.getrandbits(128)).hex
                notify = {
                    "type": "MESSAGE",
                    "level": "WARNING",
                    "code": 2019112911,
                    "content": "与 %s 的网络连接断开，请检查客户端及网络是否正常" % url,
                    "url": url
                }
                await recv_chan.send({
                    "aid": "rtn_data",
                    "data": [{
                        "notify": {
                            notify_id: notify
                        }
                    }]
                })
            finally:
                if first_connect:
                    first_connect = False
            await asyncio.sleep(10)

    async def _send_handler(self, client, url, resend_request, send_chan, first_connect):
        """websocket客户端数据发送协程"""
        try:
            for msg in resend_request.values():
                await send_chan.send(msg)
                self._logger.debug("websocket init message sent to %s: %s", url, msg)
            if not first_connect:  # 如果是重连
                await send_chan.send({
                    "aid": "peek_message"
                })
                self._logger.debug("websocket init message sent to %s: %s", url, '{"aid": "peek_message"}')
            async for pack in send_chan:
                aid = pack.get("aid")
                if aid == "subscribe_quote":
                    resend_request["subscribe_quote"] = pack
                elif aid == "set_chart":
                    if pack["ins_list"]:
                        resend_request[pack["chart_id"]] = pack
                    else:
                        resend_request.pop(pack["chart_id"], None)
                elif aid == "req_login":
                    resend_request["req_login"] = pack
                elif aid == "confirm_settlement":
                    resend_request["confirm_settlement"] = pack
                msg = json.dumps(pack)
                await client.send(msg)
                self._logger.debug("websocket message sent to %s: %s", url, msg)
        except asyncio.CancelledError:  # 取消任务不抛出异常，不然等待者无法区分是该任务抛出的取消异常还是有人直接取消等待者
            pass

    async def _fetch_msg(self):
        while not self._pending_diffs:
            pack = await self._recv_chan.recv()
            if pack is None:
                return
            if not self._is_slave:
                for slave in self._slaves:
                    slave._slave_recv_pack(copy.deepcopy(pack))
            self._pending_diffs.extend(pack.get("data", []))

    @property
    def _base_headers(self):
        headers = {
            "User-Agent": "tqsdk-python %s" % __version__,
            "Accept": "application/json",
            "Authorization": "Bearer %s" % self._access_token
        }
        return headers

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
            elif value_type is dict or value_type is Entity:
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
            elif key in result and (
                    result[key] == diff[key] or (diff[key] != diff[key] and result[key] != result[key])):
                # 判断 diff[key] != diff[key] and result[key] != result[key] 以处理 value 为 nan 的情况
                del diff[key]
            else:
                result[key] = diff[key]
        if len(diff) != 0:
            TqApi._notify_update(result, False)

    @staticmethod
    def _notify_update(target, recursive):
        """同步通知业务数据更新"""
        if isinstance(target, dict) or isinstance(target, Entity):
            for q in target["_listener"]:
                q.send_nowait(True)
            if recursive:
                for v in target.values():
                    TqApi._notify_update(v, recursive)

    @staticmethod
    def _get_obj(root, path, default=None):
        """获取业务数据"""
        d = root
        for i in range(len(path)):
            if path[i] not in d:
                if i != len(path) - 1 or default is None:
                    dv = Entity()
                else:
                    dv = copy.copy(default)
                dv._instance_entity(d["_path"] + [path[i]])

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

    def _gen_prototype(self):
        """所有业务数据的原型"""
        return {
            "quotes": {
                "#": Quote(self),  # 行情的数据原型
            },
            "klines": {
                "*": {
                    "*": {
                        "data": {
                            "@": Kline(self),  # K线的数据原型
                        }
                    }
                }
            },
            "ticks": {
                "*": {
                    "data": {
                        "@": Tick(self),  # Tick的数据原型
                    }
                }
            },
            "trade": {
                "*": {
                    "accounts": {
                        "@": Account(self),  # 账户的数据原型
                    },
                    "orders": {
                        "@": Order(self),  # 委托单的数据原型
                    },
                    "trades": {
                        "@": Trade(self),  # 成交的数据原型
                    },
                    "positions": {
                        "@": Position(self),  # 持仓的数据原型
                    }
                }
            },
        }

    @staticmethod
    def _generate_chart_id(module):
        """生成chart id"""
        chart_id = "PYSDK_" + module + "_" + uuid.UUID(int=TqApi.RD.getrandbits(128)).hex
        return chart_id

    @staticmethod
    def _generate_order_id():
        """生成order id"""
        return uuid.UUID(int=TqApi.RD.getrandbits(128)).hex

    @staticmethod
    def _get_trading_day_start_time(trading_day):
        """给定交易日, 获得交易日起始时间"""
        begin_mark = 631123200000000000  # 1990-01-01
        start_time = trading_day - 21600000000000  # 6小时
        week_day = (start_time - begin_mark) // 86400000000000 % 7
        if week_day >= 5:
            start_time -= 86400000000000 * (week_day - 4)
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

    @staticmethod
    def _deep_copy_dict(source, dest):
        for key, value in source.items():
            if isinstance(value, Entity):
                dest[key] = {}
                TqApi._deep_copy_dict(value, dest[key])
            else:
                dest[key] = value

    def _slave_send_pack(self, pack):
        if pack.get("aid", None) == "subscribe_quote":
            self._loop.call_soon_threadsafe(lambda: self._send_subscribe_quote(pack))
            return
        self._loop.call_soon_threadsafe(lambda: self._send_pack(pack))

    def _slave_recv_pack(self, pack):
        self._loop.call_soon_threadsafe(lambda: self._recv_chan.send_nowait(pack))

    def _send_subscribe_quote(self, pack):
        new_subscribe_set = self._requests["quotes"] | set(pack["ins_list"].split(","))
        if new_subscribe_set != self._requests["quotes"]:
            self._requests["quotes"] = new_subscribe_set
            self._send_pack({
                "aid": "subscribe_quote",
                "ins_list": ",".join(self._requests["quotes"])
            })

    def _send_pack(self, pack):
        if not self._is_slave:
            self._send_chan.send_nowait(pack)
        else:
            self._master._slave_send_pack(pack)

    def draw_text(self, base_k_dataframe: pd.DataFrame, text: str, x: Optional[int] = None, y: Optional[float] = None,
                  id: Optional[str] = None, board: str = "MAIN", color: Union[str, int] = "red") -> None:
        """
        配合天勤使用时, 在天勤的行情图上绘制一个字符串

        Args:
            base_k_dataframe (pandas.DataFrame): 基础K线数据序列, 要绘制的K线将出现在这个K线图上. 需要画图的数据以附加列的形式存在

            text (str): 要显示的字符串

            x (int): X 坐标, 以K线的序列号表示. 可选, 缺省为对齐最后一根K线,

            y (float): Y 坐标. 可选, 缺省为最后一根K线收盘价

            id (str): 字符串ID, 可选. 以相同ID多次调用本函数, 后一次调用将覆盖前一次调用的效果

            board (str): 选择图板, 可选, 缺省为 "MAIN" 表示绘制在主图

            color (str/int): 文本颜色, 可选, 缺省为 "red"
                * str : 符合 CSS Color 命名规则的字符串, 例如: "red", "#FF0000", "#FF0000FF", "rgb(255, 0, 0)", "rgba(255, 0, 0, .5)"
                * int : 十六进制整数表示颜色, ARGB, 例如: 0xffff0000

        Example::

            # 在主图最近K线的最低处标一个"最低"文字
            klines = api.get_kline_serial("SHFE.cu1905", 86400)
            indic = np.where(klines.low == klines.low.min())[0]
            value = klines.low.min()
            api.draw_text(klines, "测试413423", x=indic, y=value, color=0xFF00FF00)
        """
        if id is None:
            id = uuid.UUID(int=TqApi.RD.getrandbits(128)).hex
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
        self._send_chart_data(base_k_dataframe, id, serial)

    def draw_line(self, base_k_dataframe: pd.DataFrame, x1: int, y1: float, x2: int, y2: float,
                  id: Optional[str] = None, board: str = "MAIN", line_type: str = "LINE", color: Union[str, int] = "red",
                  width: int = 1) -> None:
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

            color (str/int): 线颜色, 可选, 缺省为 "red"
                * str : 符合 CSS Color 命名规则的字符串, 例如: "red", "#FF0000", "#FF0000FF", "rgb(255, 0, 0)", "rgba(255, 0, 0, .5)"
                * int : 十六进制整数表示颜色, ARGB, 例如: 0xffff0000

            width (int): 线宽度, 可选, 缺省为 1
        """
        if id is None:
            id = uuid.UUID(int=TqApi.RD.getrandbits(128)).hex
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
        self._send_chart_data(base_k_dataframe, id, serial)

    def draw_box(self, base_k_dataframe: pd.DataFrame, x1: int, y1: float, x2: int, y2: float, id: Optional[str] = None,
                 board: str = "MAIN", bg_color: Union[str, int] = "black", color: Union[str, int] = "red", width: int = 1) -> None:
        """
        配合天勤使用时, 在天勤的行情图上绘制一个矩形

        Args:
            base_k_dataframe (pandas.DataFrame): 基础K线数据序列, 要绘制的K线将出现在这个K线图上. 需要画图的数据以附加列的形式存在

            x1 (int): 矩形左上角的 X 坐标, 以K线的序列号表示

            y1 (float): 矩形左上角的 Y 坐标

            x2 (int): 矩形右下角的 X 坐标, 以K线的序列号表示

            y2 (float): 矩形右下角的 Y 坐标

            id (str): ID, 可选. 以相同ID多次调用本函数, 后一次调用将覆盖前一次调用的效果

            board (str): 选择图板, 可选, 缺省为 "MAIN" 表示绘制在主图

            bg_color (str/int): 填充颜色, 可选, 缺省为 "black"
                * str : 符合 CSS Color 命名规则的字符串, 例如: "red", "#FF0000", "#FF0000FF", "rgb(255, 0, 0)", "rgba(255, 0, 0, .5)"
                * int : 十六进制整数表示颜色, ARGB, 例如: 0xffff0000

            color (str/int): 边框颜色, 可选, 缺省为 "red"
                * str : 符合 CSS Color 命名规则的字符串, 例如: "red", "#FF0000", "#FF0000FF", "rgb(255, 0, 0)", "rgba(255, 0, 0, .5)"
                * int : 十六进制整数表示颜色, ARGB, 例如: 0xffff0000

            width (int): 边框宽度, 可选, 缺省为 1

        Example::

            # 给主图最后5根K线加一个方框
            klines = api.get_kline_serial("SHFE.cu1905", 86400)
            api.draw_box(klines, x1=-5, y1=klines.iloc[-5].close, x2=-1, \
            y2=klines.iloc[-1].close, width=1, color=0xFF0000FF, bg_color=0x8000FF00)
        """
        if id is None:
            id = uuid.UUID(int=TqApi.RD.getrandbits(128)).hex
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
        self._send_chart_data(base_k_dataframe, id, serial)

    def _send_chart_data(self, base_kserial_frame, serial_id, serial_data):
        s = self._serials[id(base_kserial_frame)]
        p = s["root"][0]["_path"]
        symbol = p[-2]
        dur_nano = int(p[-1])
        pack = {
            "aid": "set_chart_data",
            "symbol": symbol,
            "dur_nano": dur_nano,
            "datas": {
                serial_id: serial_data,
            }
        }
        self._send_pack(pack)

    def _offset_to_x(self, base_k_dataframe, x):
        if x is None:
            return int(base_k_dataframe["id"].iloc[-1])
        elif x < 0:
            return int(base_k_dataframe["id"].iloc[-1]) + 1 + x
        elif x >= 0:
            return int(base_k_dataframe["id"].iloc[0]) + x


class TqAccount(object):
    """天勤实盘类"""

    def __init__(self, broker_id: str, account_id: str, password: str, front_broker: Optional[str] = None,
                 front_url: Optional[str] = None) -> None:
        """
        创建天勤实盘实例

        Args:
            broker_id (str): 期货公司, 可以在天勤终端中查看期货公司名称

            account_id (str): 帐号

            password (str): 密码

            front_broker(str): [可选]CTP交易前置的Broker ID, 用于连接次席服务器, eg: "2020"

            front_url(str): [可选]CTP交易前置地址, 用于连接次席服务器, eg: "tcp://1.2.3.4:1234/"
        """
        if bool(front_broker) != bool(front_url):
            raise Exception("front_broker 和 front_url 参数需同时填写")

        self._broker_id = broker_id
        self._account_id = account_id
        self._password = password
        self._front_broker = front_broker
        self._front_url = front_url
        self._app_id = "SHINNY_TQ_1.0"
        self._system_info = ""
        try:
            l = ctypes.c_int(344)
            buf = ctypes.create_string_buffer(l.value)
            lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ctpse")
            if sys.platform.startswith("win"):
                if ctypes.sizeof(ctypes.c_voidp) == 4:
                    selib = ctypes.cdll.LoadLibrary(os.path.join(lib_path, "WinDataCollect32.dll"))
                    ret = getattr(selib, "?CTP_GetSystemInfo@@YAHPADAAH@Z")(buf, ctypes.byref(l))
                else:
                    selib = ctypes.cdll.LoadLibrary(os.path.join(lib_path, "WinDataCollect64.dll"))
                    ret = getattr(selib, "?CTP_GetSystemInfo@@YAHPEADAEAH@Z")(buf, ctypes.byref(l))
            elif sys.platform.startswith("linux"):
                selib = ctypes.cdll.LoadLibrary(os.path.join(lib_path, "LinuxDataCollect64.so"))
                ret = selib._Z17CTP_GetSystemInfoPcRi(buf, ctypes.byref(l))
            else:
                raise Exception("不支持该平台")
            if ret == 0:
                self._system_info = base64.b64encode(buf.raw[:l.value]).decode("utf-8")
            else:
                raise Exception("错误码: %d" % ret)
        except Exception as e:
            logging.getLogger("TqApi.TqAccount").debug("采集穿透式监管客户端信息失败: %s" % e)

    async def _run(self, api, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan, td_send_chan, td_recv_chan):
        req = {
            "aid": "req_login",
            "bid": self._broker_id,
            "user_name": self._account_id,
            "password": self._password,
        }
        if self._system_info:
            req["client_app_id"] = self._app_id
            req["client_system_info"] = self._system_info
        if self._front_broker:
            req["broker_id"] = self._front_broker
            req["front"] = self._front_url
        await td_send_chan.send(req)
        await td_send_chan.send({
            "aid": "confirm_settlement"
        })  # 自动发送确认结算单
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
            await md_send_chan.send({
                "aid": "peek_message"
            })
            await api_recv_chan.send(pack)

    async def _td_handler(self, api_recv_chan, td_send_chan, td_recv_chan):
        async for pack in td_recv_chan:
            await td_send_chan.send({
                "aid": "peek_message"
            })
            await api_recv_chan.send(pack)


class TqChan(asyncio.Queue):
    """用于协程间通讯的channel"""

    def __init__(self, api: 'TqApi', last_only: bool = False) -> None:
        """
        创建channel实例

        Args:
            last_only (bool): 为True时只存储最后一个发送到channel的对象
        """
        asyncio.Queue.__init__(self, loop=api._loop)
        self._api = api
        self._last_only = last_only
        self._closed = False

    async def close(self) -> None:
        """
        关闭channel

        关闭后send将不起作用,recv在收完剩余数据后会立即返回None
        """
        if not self._closed:
            self._closed = True
            await asyncio.Queue.put(self, None)

    async def send(self, item: Any) -> None:
        """
        异步发送数据到channel中

        Args:
            item (any): 待发送的对象
        """
        if not self._closed:
            if self._last_only:
                while not self.empty():
                    asyncio.Queue.get_nowait(self)
            await asyncio.Queue.put(self, item)

    def send_nowait(self, item: Any) -> None:
        """
        尝试立即发送数据到channel中

        Args:
            item (any): 待发送的对象

        Raises:
            asyncio.QueueFull: 如果channel已满则会抛出 asyncio.QueueFull
        """
        if not self._closed:
            if self._last_only:
                while not self.empty():
                    asyncio.Queue.get_nowait(self)
            asyncio.Queue.put_nowait(self, item)

    async def recv(self) -> Any:
        """
        异步接收channel中的数据，如果channel中没有数据则一直等待

        Returns:
            any: 收到的数据，如果channel已被关闭则会立即收到None
        """
        if self._closed and self.empty():
            return None
        return await asyncio.Queue.get(self)

    def recv_nowait(self) -> Any:
        """
        尝试立即接收channel中的数据

        Returns:
            any: 收到的数据，如果channel已被关闭则会立即收到None

        Raises:
            asyncio.QueueFull: 如果channel中没有数据则会抛出 asyncio.QueueEmpty
        """
        if self._closed and self.empty():
            return None
        return asyncio.Queue.get_nowait(self)

    def recv_latest(self, latest: Any) -> Any:
        """
        尝试立即接收channel中的最后一个数据

        Args:
            latest (any): 如果当前channel中没有数据或已关闭则返回该对象

        Returns:
            any: channel中的最后一个数据
        """
        while (self._closed and self.qsize() > 1) or (not self._closed and not self.empty()):
            latest = asyncio.Queue.get_nowait(self)
        return latest

    def __aiter__(self):
        return self

    async def __anext__(self):
        value = await asyncio.Queue.get(self)
        if self._closed and self.empty():
            raise StopAsyncIteration
        return value

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
