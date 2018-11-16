#!/usr/bin/env python
#  -*- coding: utf-8 -*-
"""
天勤接口的PYTHON封装, 提供以下功能

    * 连接天勤终端的websocket扩展接口, 从天勤终端接收行情及交易推送数据
    * 在内存中存储管理一份完整的业务数据(行情+交易), 并在接收到新数据包时更新内存数据
    * 通过一批函数接口, 支持用户代码访问业务数据
    * 发送交易指令


使用前, 需要在本机先启动一个天勤终端进程(版本 0.8 以上):

    * 天勤行情终端下载: http://www.shinnytech.com/tianqin
    * 天勤使用文档: http://doc.shinnytech.com/tq/latest/
    * PYTHON SDK使用文档: http://doc.shinnytech.com/pysdk/latest/
"""
__author__ = 'chengzhi'

import json
import uuid
import sys
import time
import logging
import copy
import asyncio
import websockets

class TqApi(object):
    """
    天勤接口及数据管理类.

    通常情况下, 一个进程中应该只有一个TqApi的实例, 它负责维护到天勤终端的网络连接, 从天勤终端接收行情及账户数据, 并在内存中维护数据存储池
    """
    def __init__(self, account_id, url=None, backtest=None, debug=None):
        """
        创建天勤接口实例

        Args:
            account_id (str): 指定交易账号, 实盘交易填写期货公司提供的帐号, 使用软件内置的模拟交易填写"SIM"
            
            url (str): [可选]指定天勤软件 websocket 地址, 默认为本机

            backtest (TqBacktest): [可选]传入 TqBacktest 对象将进入回测模式

            debug(str): [可选]将调试信息输出到指定文件, 默认不输出
        """
        self.loop = asyncio.new_event_loop()  # 创建一个新的ioloop, 避免和其他框架/环境产生干扰
        self.quote_symbols = set()  # 订阅的实时行情列表
        self.account_id = account_id  # 交易帐号id
        self.logger = logging.getLogger("TqApi")  # 调试信息输出
        if debug:
            self.logger.setLevel(logging.DEBUG)
            fh = logging.FileHandler(filename=debug)
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(fh)
        self.send_chan, self.recv_chan  = TqChan(self), TqChan(self)  # 消息收发队列
        self.event_rev, self.check_rev = 0, 0  # 回测需要行情和交易 lockstep, 而 asyncio 没有将内部的 _ready 队列暴露出来
        self.data = {"_path": [], "_listener": set()}  # 数据存储
        self.diffs = []  # 自上次wait_update返回后收到更新数据的数组
        self.prototype = {
            "quotes": {
                "*": self._gen_quote_prototype(),  # 行情的数据原型
            },
            "klines": {
                "*": {
                    "*": {
                        "data": {
                            "*": self._gen_kline_prototype(),  # K线的数据原型
                        }
                    }
                }
            },
            "ticks": {
                "*": {
                    "data": {
                        "*": self._gen_tick_prototype(),  # Tick的数据原型
                    }
                }
            },
            "trade": {
                "*": {
                    "accounts": {
                        "*": self._gen_account_prototype(),  # 账户的数据原型
                    },
                    "orders": {
                        "*": self._gen_order_prototype(),  # 委托单的数据原型
                    },
                    "trades": {
                        "*": self._gen_trade_prototype(),  # 成交的数据原型
                    },
                    "positions": {
                        "*": self._gen_position_prototype(),  # 持仓的数据原型
                    }
                }
            },
        }  # 各业务数据的原型, 用于决定默认值及将收到的数据转为特定的类型
        self.tasks = set()  # 由api维护的所有根task，不包含子task，子task由其父task维护
        self.exceptions = []  # 由api维护的所有task抛出的例外
        self.wait_timeout = False  # wait_update 是否触发超时
        if sys.platform.startswith("win"):
            self.create_task(self._windows_patch())  # Windows系统下asyncio不支持KeyboardInterrupt的临时补丁
        self.create_task(self._connect(url, self.send_chan, self.recv_chan))  # 启动websocket连接
        if backtest:  # 通常 api 是直接连接到 websocket 上, 如果启用了回测, 则在这中间插入 TqBacktest, api 将从 TqBacktest 收发数据
            ws_send_chan, ws_recv_chan = self.send_chan, self.recv_chan
            self.send_chan, self.recv_chan = TqChan(self), TqChan(self)
            self.create_task(backtest._run(self, self.send_chan, self.recv_chan, ws_send_chan, ws_recv_chan))
        deadline = time.time() + 60
        try:
            while self.data.get("mdhis_more_data", True):  # 等待连接成功并收取截面数据
                if not self.wait_update(deadline=deadline):
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
            from tqsdk.api import TqApi
            from contextlib import closing

            with closing(TqApi("SIM")) as api:
                api.insert_order(symbol="DCE.m1901", direction="BUY", offset="OPEN", volume=3)
        """
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

            .. literalinclude:: ../tqsdk/api.py
                :pyobject: TqApi._gen_quote_prototype
                :dedent: 12
                :start-after: {
                :end-before: }

            注意: 在 tqsdk 还没有收到行情数据包时, 此对象中各项内容为 NaN 或 0

        Example::

            # 获取 SHFE.cu1812 合约的报价
            from tqsdk.api import TqApi

            api = TqApi("SIM")
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
        if symbol not in self.quote_symbols:
            self.quote_symbols.add(symbol)
            s = ",".join(self.quote_symbols)
            self.send_chan.send_nowait({
                "aid": "subscribe_quote",
                "ins_list": s
            })
        return self._get_obj(self.data, ["quotes", symbol], self.prototype["quotes"]["*"])

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
            KlineSerialDataProxy: 本函数总是返回一个 KlineSerialDataProxy 的实例. 其中每个数据项的格式如下

            .. literalinclude:: ../tqsdk/api.py
                :pyobject: TqApi._gen_kline_prototype
                :dedent: 12
                :start-after: {
                :end-before: }

        Example::

            # 获取 SHFE.cu1812 的1分钟线
            from tqsdk.api import TqApi

            api = TqApi("SIM")
            k_serial = api.get_kline_serial("SHFE.cu1812", 60)
            while True:
                api.wait_update()
                print(k_serial[-1]["close"])

            # 预计的输出是这样的:
            50970.0
            50970.0
            50960.0
            ...
        """
        duration_seconds = int(duration_seconds) # 转成整数
        if not chart_id:
            chart_id = self._generate_chart_id("realtime", symbol, duration_seconds)
        if data_length > 8964:
            data_length = 8964
        dur_id = duration_seconds * 1000000000
        req = {
            "aid": "set_chart",
            "chart_id": chart_id,
            "ins_list": symbol,
            "duration": dur_id,
            "view_width": data_length,
        }
        self.send_chan.send_nowait(req)
        return SerialDataProxy(self._get_obj(self.data, ["klines", symbol, str(dur_id)]), data_length, self.prototype["klines"]["*"]["*"]["data"]["*"])

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
            TickSerialDataProxy: 本函数总是返回一个 TickSerialDataProxy 的实例. 其中每个数据项的格式如下

            .. literalinclude:: ../tqsdk/api.py
                :pyobject: TqApi._gen_tick_prototype
                :dedent: 12
                :start-after: {
                :end-before: }

        Example::

            # 获取 SHFE.cu1812 的Tick序列
            from tqsdk.api import TqApi

            api = TqApi("SIM")
            serial = api.get_tick_serial("SHFE.cu1812")
            while True:
                api.wait_update()
                print(serial[-1]["bid_price1"], serial[-1]["ask_price1"])

            # 预计的输出是这样的:
            50860.0 51580.0
            50860.0 51580.0
            50820.0 51580.0
            ...
        """
        if not chart_id:
            chart_id = self._generate_chart_id("realtime", symbol, 0)
        if data_length > 8964:
            data_length = 8964
        req = {
            "aid": "set_chart",
            "chart_id": chart_id,
            "ins_list": symbol,
            "duration": 0,
            "view_width": data_length,
        }
        self.send_chan.send_nowait(req)
        return SerialDataProxy(self._get_obj(self.data, ["ticks", symbol]), data_length, self.prototype["ticks"]["*"]["data"]["*"])

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

            .. literalinclude:: ../tqsdk/api.py
                :pyobject: TqApi._gen_order_prototype
                :dedent: 12
                :start-after: {
                :end-before: }

        Example::

            # 市价开3手 DCE.m1809 多仓
            from tqsdk.api import TqApi

            api = TqApi("SIM")
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
        order = self._get_obj(self.data, ["trade", self.account_id, "orders", order_id], self.prototype["trade"]["*"]["orders"]["*"])
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
            from tqsdk.api import TqApi

            api = TqApi("SIM")
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

            .. literalinclude:: ../tqsdk/api.py
                :pyobject: TqApi._gen_account_prototype
                :dedent: 12
                :start-after: {
                :end-before: }

            注意: 在 tqsdk 还没有收到账户数据包时, 此对象中各项内容为NaN

        Example::

            # 获取当前浮动盈亏
            from tqsdk.api import TqApi

            api = TqApi("SIM")
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
        return self._get_obj(self.data, ["trade", self.account_id, "accounts", "CNY"], self.prototype["trade"]["*"]["accounts"]["*"])

    # ----------------------------------------------------------------------
    def get_position(self, symbol=None):
        """
        获取用户持仓信息

        Args:
            symbol (str): [可选]合约代码, 默认返回所有持仓

        Returns:
            dict: 当指定了symbol时, 返回一个如下结构所示的包含指定symbol持仓信息的引用. 每当其中信息改变时, 此dict会自动更新.

            .. literalinclude:: ../tqsdk/api.py
                :pyobject: TqApi._gen_position_prototype
                :dedent: 12
                :start-after: {
                :end-before: }

            不带symbol参数调用 get_position 函数, 将返回包含用户所有持仓的一个嵌套dict, 其中每个元素的key为合约代码, value为上述格式的dict

            注意: 在 tqsdk 还没有收到持仓信息时, 此对象中各项内容为空或0

        Example::

            # 获取 DCE.m1809 当前浮动盈亏
            from tqsdk.api import TqApi

            api = TqApi("SIM")
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
            return self._get_obj(self.data, ["trade", self.account_id, "positions", symbol], self.prototype["trade"]["*"]["positions"]["*"])
        return self._get_obj(self.data, ["trade", self.account_id, "positions"])

    # ----------------------------------------------------------------------
    def get_order(self, order_id=None):
        """
        获取用户委托单信息

        Args:
            order_id (str): [可选]单号, 默认返回所有委托单

        Returns:
            dict: 当指定了order_id时, 返回一个如下结构所示的包含指定order_id委托单信息的引用. 每当其中信息改变时, 此dict会自动更新.

            .. literalinclude:: ../tqsdk/api.py
                :pyobject: TqApi._gen_order_prototype
                :dedent: 12
                :start-after: {
                :end-before: }

            不带order_id参数调用get_order函数, 将返回包含用户所有委托单的一个嵌套dict, 其中每个元素的key为合约代码, value为上述格式的dict

            注意: 在 tqsdk 还没有收到委托单信息时, 此对象中各项内容为空

        Example::

            # 获取当前总挂单手数
            from tqsdk.api import TqApi

            api = TqApi("SIM")
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
            return self._get_obj(self.data, ["trade", self.account_id, "orders", order_id], self.prototype["trade"]["*"]["orders"]["*"])
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

            from tqsdk.api import TqApi

            api = TqApi("SIM")
            quote = api.get_quote("SHFE.cu1812")
            api.wait_update()
            print(quote["datetime"])

            可能输出 ""(空字符串), 表示还没有收到该合约的行情
        """
        if self.loop.is_running():
            raise Exception("不能在协程中调用 wait_update, 如需在协程中等待业务数据更新请使用 register_update_notify")
        self.diffs = []
        self.wait_timeout = False
        # 先尝试执行各个task,再请求下个业务数据
        self._run_until_idle()
        self.send_chan.send_nowait({"aid":"peek_message"})
        deadline_handle = None if deadline is None else self.loop.call_later(deadline - time.time(), self._set_wait_timeout)
        update_task = self.create_task(self._fetch_msg())
        try:
            while not self.wait_timeout and not self.diffs:
                self._run_once()
            return len(self.diffs) != 0
        finally:
            for d in self.diffs:
                self._merge_diff(self.data, d, self.prototype)
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
            from tqsdk.api import TqApi

            api = TqApi("SIM")
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
        if self.loop.is_running():
            raise Exception("不能在协程中调用 is_changing, 如需在协程中判断业务数据更新请使用 register_update_notify")
        if obj is None:
            return False
        if not isinstance(key, list):
            key = [key] if key else []
        try:
            path = obj.serial_root["_path"] if isinstance(obj, SerialDataProxy) else obj["_path"]
        except KeyError:
            return False
        for diff in self.diffs:
            if self._is_key_exist(diff, path, key):
                return True
        return False

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
            from tqsdk.api import TqApi

            async def hello():
                await asyncio.sleep(3)
                print("hello world")

            api = TqApi("SIM")
            api.create_task(hello())
            while True:
                api.wait_update()

            #以上代码将在3秒后输出
            hello world
        """
        task = self.loop.create_task(coro)
        self.event_rev += 1
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
            from tqsdk.api import TqApi

            async def demo():
                quote = api.get_quote("SHFE.cu1812")
                async with api.register_update_notify(quote) as update_chan:
                    async for _ in update_chan:
                        print(quote["last_price"])

            api = TqApi("SIM")
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
            listener = o.serial_root["_listener"] if isinstance(o, SerialDataProxy) else o["_listener"]
            listener.add(chan)
        return chan

    # ----------------------------------------------------------------------
    def _run_once(self):
        if not self.exceptions:
            self.loop.run_forever()
        if self.exceptions:
            raise self.exceptions.pop(0)

    def _run_until_idle(self):
        while self.check_rev != self.event_rev:
            check_handle = self.loop.call_soon(self._check_event, self.event_rev)
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

    async def _connect(self, url, send_chan, recv_chan):
        """启动websocket客户端"""
        async with websockets.connect(url if url else "ws://127.0.0.1:7777", max_size=None) as client:
            send_task = self.create_task(self._send_handler(client, send_chan))
            try:
                async for msg in client:
                    self.logger.debug("websocket message received: %s", msg)
                    await recv_chan.put(json.loads(msg))
            except websockets.exceptions.ConnectionClosed:
                print("网络连接断开，请检查客户端及网络是否正常", file=sys.stderr)
                raise
            finally:
                await recv_chan.close()
                await send_chan.close()
                await send_task

    async def _send_handler(self, client, send_chan):
        """websocket客户端数据发送协程"""
        async for pack in send_chan:
            msg = json.dumps(pack)
            await client.send(msg)
            self.logger.debug("websocket message sent: %s", msg)

    async def _fetch_msg(self):
        while not self.diffs:
            pack = await self.recv_chan.recv()
            if pack is None:
                return
            self.diffs.extend(pack.get("data", []))

    @staticmethod
    def _merge_diff(result, diff, prototype):
        """更新业务数据,并同步发送更新通知，保证业务数据的更新和通知是原子操作"""
        for key in list(diff.keys()):
            if isinstance(diff[key], str) and key in prototype and not isinstance(prototype[key], str):
                diff[key] = prototype[key]
            if diff[key] is None:
                dv = result.pop(key, None)
                TqApi._notify_update(dv, True)
            elif isinstance(diff[key], dict):
                target = TqApi._get_obj(result, [key])
                tpt = prototype.get("*", {})
                if key in prototype:
                    tpt = prototype[key]
                TqApi._merge_diff(target, diff[key], tpt)
                if len(diff[key]) == 0:
                    del diff[key]
            elif key in result and result[key] == diff[key]:
                del diff[key]
            else:
                result[key] = diff[key]
        if len(diff) != 0:
            TqApi._notify_update(result, False)

    @staticmethod
    def _notify_update(target, recursive):
        """同步通知业务数据更新"""
        if isinstance(target, dict):
            target["_listener"] = {q for q in target["_listener"] if not q.closed}
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
                    dv["_listener"] = set()
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
            "static_balance":float("nan"),  # (静态权益)
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
            "exchange_order_id":"",  # "1928341" (交易所单号)
            "exchange_id": "",  # "SHFE" (交易所)
            "instrument_id": "",  # "rb1901" (交易所内的合约代码)
            "direction": "",  # "BUY" (下单方向, BUY=买, SELL=卖)
            "offset": "",  # "OPEN" (开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今)
            "volume_orign":0,  # 10 (总报单手数)
            "volume_left":0,  # 5 (未成交手数)
            "limit_price": float("nan"),  # 4500.0 (委托价格, 仅当 price_type = LIMIT 时有效)
            "price_type": "",  # "LIMIT" (价格类型, ANY=市价, LIMIT=限价)
            "volume_condition": "",  # "ANY" (手数条件, ANY=任何数量, MIN=最小数量, ALL=全部数量)
            "time_condition": "",  # "GFD" (时间条件, IOC=立即完成，否则撤销, GFS=本节有效, GFD=当日有效, GTC=撤销前有效, GFA=集合竞价有效)
            "insert_date_time": 0,  # 1501074872000000000 (下单时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
            "last_msg":"",  # "报单成功" (委托单状态信息)
            "status": "",  # "ALIVE" (委托单状态, ALIVE=有效, FINISHED=已完)
        }

    @staticmethod
    def _gen_trade_prototype():
        """成交的数据原型"""
        return {
            "order_id": "",  # "123" (委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的)
            "trade_id": "",  # "123|19723" (成交ID, 对于一个用户的所有成交，这个ID都是不重复的)
            "exchange_trade_id":"",  # "829414" (交易所成交号)
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


class SerialDataProxy(object):
    """
    K线及Tick序列数据包装器, 方便数据读取使用

    Examples::

        # 获取一个分钟线序列, ks 即是 SerialDataProxy 的实例
        ks = api.get_kline_serial("SHFE.cu1812", 60)

        # 获取最后一根K线
        a = ks[-1]
        # 获取倒数第5根K线
        a = ks[-5]
        # a == {
        #     "datetime": ...,
        #     "open": ...,
        #     "high": ...,
        #     "low": ...,
        #     ...
        # }

        # 获取特定字段的序列
        cs = ks.close
        # cs = [3245, 3421, 3345, ...]

        # 将序列转为 pandas.DataFrame
        ks.to_dataframe()
    """
    def __init__(self, serial_root, width, default):
        self.serial_root = serial_root
        self.width = width
        self.default = default
        self.attr = list(self.default.keys())

    def __getattr__(self, name):
        return [self[i][name] for i in range(0, self.width)]

    def __getitem__(self, key):
        last_id = self.serial_root.get("last_id", None)
        if not last_id:
            return self.default.copy()
        if key < 0:
            data_id = last_id + 1 + key
        else:
            data_id = last_id - self.width + 1 + key
        return TqApi._get_obj(self.serial_root, ["data", str(data_id)], self.default)

    def to_dataframe(self):
        """
        将当前该序列中的数据转换为 pandas.DataFrame

        Returns:
            pandas.DataFrame: 每行是一条行情数据

            注意: 返回的 DataFrame 反映的是当前的行情数据，不会自动更新，当行情数据有变化后需要重新调用 to_dataframe

        Example::

            # 判断K线是否为阳线
            from tqsdk.api import TqApi

            api = TqApi("SIM")
            k_serial = api.get_kline_serial("SHFE.cu1812", 60)
            while True:
                api.wait_update()
                df = k_serial.to_dataframe()
                print(df["close"] > df["open"])

            # 预计的输出是这样的:
            0       True
            1       True
            2      False
                   ...
            197    False
            198     True
            199    False
            Length: 200, dtype: bool
            ...
        """
        import pandas as pd
        rows = {}
        for i in range(0, self.width):
            rows[i] = {k: v for k, v in self[i].items() if not k.startswith("_")}
        return pd.DataFrame.from_dict(rows, orient="index")


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
            self.api.event_rev += 1
            self.closed = True
            await asyncio.Queue.put(self, None)

    async def send(self, item):
        """
        异步发送数据到channel中

        Args:
            item (any): 待发送的对象
        """
        if not self.closed:
            self.api.event_rev += 1
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
            self.api.event_rev += 1
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
