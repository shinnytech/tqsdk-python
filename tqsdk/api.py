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
    * 天勤使用文档: http://doc.tq18.cn/tq/latest/
"""
__author__ = 'chengzhi'

import json
import uuid
import sys
import time
import asyncio
import websockets


class TqApi(object):
    """
    天勤接口及数据管理类.

    通常情况下, 一个进程中应该有一个TqApi的实例, 它负责维护到天勤终端的网络连接, 从天勤终端接收行情及账户数据, 并在内存中维护数据存储池
    """
    def __init__(self, account_id):
        """
        创建天勤接口实例

        Args:
            account_id (str): 指定交易账号, 实盘交易填写期货公司提供的帐号, 使用软件内置的模拟交易填写"SIM"
        """
        self.data = {"_path": []}  # 数据存储
        self.diffs = []  # 每次收到更新数据的数组
        self.loop = asyncio.get_event_loop()
        self.quote_symbol_list = []  # 订阅的实时行情列表
        self.account_id = account_id  # 交易帐号id
        self.send_chan = TqChan()  # websocket发送队列
        self.update_chans = [TqChan(last_only=True)]  # 业务数据更新所需要通知的队列，第一个元素用于wait_update
        self.tasks = set()  # 由api维护的所有根task，不包含子task，子task由其父task维护
        if sys.platform.startswith('win'):
            self.create_task(self._windows_patch())  # Windows系统下asyncio不支持KeyboardInterrupt的临时补丁
        self.create_task(self._connect())  # 启动websocket连接
        self.wait_update(timeout=30)  # 等待连接成功并收取截面数据

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
            dict: 返回如下结构所示的一个 dict 对象的引用, 当行情更新时, 此对象的内容被自动更新::

                {
                    'datetime': '2017-07-26 23:04:21.000001', # tick从交易所发出的时间(北京时间)
                    'last_price': 6122.0, # 最新价
                    'bid_price1': 6121.0, # 买一价
                    'ask_price1': 6122.0, # 卖一价
                    'bid_volume1': 54, # 买一量
                    'ask_volume1': 66, # 卖一量
                    'upper_limit': 6388.0, # 涨停价
                    'lower_limit': 5896.0, # 跌停价
                    'volume': 89252, # 成交量
                    'amount': 5461329880.0, # 成交额
                    'open_interest': 616424, # 持仓量
                    'highest': 6129.0, # 当日最高价
                    'lowest': 6101.0, # 当日最低价
                    'average': 6119.0, # 当日均价
                    'open': 6102.0, # 开盘价
                    'close': '-', # 收盘价
                    'settlement': '-', # 结算价
                    'pre_close': 6106.0, # 昨收盘价
                    'pre_settlement': 6142.0 #  昨结算价
                    'pre_open_interest': 616620, # 昨持仓量
                }

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
        if symbol not in self.quote_symbol_list:
            self.quote_symbol_list.append(symbol)
            s = ",".join(self.quote_symbol_list)
            self._send_json({
                "aid": "subscribe_quote",
                "ins_list": s
            })
        return self._get_obj(self.data, ["quotes", symbol], {
            "datetime": "",
            "ask_price1": float("nan"),
            "ask_volume1": 0,
            "bid_price1": float("nan"),
            "bid_volume1": 0,
            "last_price": float("nan"),
            "highest": float("nan"),
            "lowest": float("nan"),
            "open": float("nan"),
            "close": float("nan"),
            "average": float("nan"),
            "volume": 0,
            "amount": float("nan"),
            "open_interest": 0,
            "settlement": float("nan"),
            "upper_limit": float("nan"),
            "lower_limit": float("nan"),
            "pre_open_interest": 0,
            "pre_settlement": float("nan"),
            "pre_close": float("nan"),
        })

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
            KlineSerialDataProxy: 本函数总是返回一个 KlineSerialDataProxy 的实例.

            其中每个数据项的格式如下::

                {
                    'datetime': 1501080715000000000L, # K线起点时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数
                    'open': 51450, # K线起始时刻的最新价
                    'high': 51450, # K线时间范围内的最高价
                    'low': 51450, # K线时间范围内的最低价
                    'close': 51450, # K线结束时刻的最新价
                    'volume': 0, # K线时间范围内的成交量
                    'open_oi': 27354, # K线起始时刻的持仓量
                    'close_oi': 27354 # K线结束时刻的持仓量
                }

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
        if not chart_id:
            chart_id = self._generate_chart_id(symbol, duration_seconds)
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
        self._send_json(req)
        return KlineSerialDataProxy(self._get_obj(self.data, ["klines", symbol, str(dur_id)]), data_length)

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
            TickSerialDataProxy: 本函数总是返回一个 TickSerialDataProxy 的实例.

            其中每个数据项的格式如下::

                {
                    'datetime': 1501074872000000000L, # tick从交易所发出的时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数
                    'trading_day': 1501084800000000000L, #交易日, 格式同上
                    'last_price': 3887, # 最新价
                    'bid_price1': 3881, # 买一价
                    'ask_price1': 3886, # 卖一价
                    'bid_volume1': 5, # 买一量
                    'ask_volume1': 1, #卖一量
                    'highest': 3887, # 当日最高价
                    'lowest': 3886,    # 当日最低价
                    'volume': 6, # 成交量
                    'amount': 19237841.0 # 成交额
                    'open_interest': 1796 # 持仓量
                },

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
            chart_id = self._generate_chart_id(symbol, 0)
        req = {
            "aid": "set_chart",
            "chart_id": chart_id,
            "ins_list": symbol,
            "duration": 0,
            "view_width": data_length,
        }
        self._send_json(req)
        return TickSerialDataProxy(self._get_obj(self.data, ["ticks", symbol]), data_length)

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
            dict: 本函数总是返回一个包含委托单信息的dict的引用. 每当order中信息改变时, 此dict会自动更新.

            其格式如下::

                {
                    "order_id": "123", # 委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
                    "exchange_id": "SHFE", # 交易所
                    "instrument_id": "cu1801", # 合约代码
                    "direction": "BUY", # 下单方向, BUY=买, SELL=卖
                    "offset": "OPEN", # 开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今
                    "volume_orign": 6, # 总报单手数
                    "volume_left": 3, # 未成交手数
                    "price_type": "LIMIT", # 价格类型, ANY=市价, LIMIT=限价
                    "limit_price": 45000, # 委托价格, 仅当 price_type = LIMIT 时有效
                    "status": "ALIVE", # 委托单状态, ALIVE=有效, FINISHED=已完
                    "insert_date_time": 1928374000000000, # 下单时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数
                    "exchange_order_id": "434214", # 交易所单号
                },

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
            "price_type": "ANY" if limit_price is None else "LIMIT",
            "volume_condition": "ANY" if limit_price is None else "ALL",
            "time_condition": "IOC" if limit_price is None else "GTC",
            "hedge_flag": "SPECULATION",
            "limit_price": limit_price,
        }
        self._send_json(msg)
        order = msg.copy()
        order.update({
            "status": "ALIVE",
            "volume_orign": volume,
            "volume_left": volume,
        })
        self._merge_diff(self.data, {
            "trade": {
                self.account_id: {
                    "orders": {
                        order_id: order,
                    }
                }
            }
        })
        order = self.get_order(order_id)
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
        self._send_json(msg)

    # ----------------------------------------------------------------------
    def get_account(self):
        """
        获取用户账户资金信息

        Returns:
            dict: 本函数总是返回一个包含用户账户资金信息的dict的引用. 每当其中信息改变时, 此dict会自动更新.

            其格式如下::

                {
                    "balance": 9963216.550000003, # 账户权益
                    "available": 9480176.150000002, # 可用资金
                    "deposit": 42344, # 本交易日内的入金金额
                    "withdraw": 42344, # 本交易日内的出金金额
                    "commission": 123, # 本交易日内交纳的手续费
                    "preminum": 123, # 本交易日内交纳的权利金
                    "float_profit": 8910.231, # 浮动盈亏
                    "risk_ratio": 0.048482375, # 风险度
                    "margin": 11232.23, # 占用资金
                    "frozen_margin": 12345, # 冻结保证金
                    "frozen_commission": 123, # 冻结手续费
                    "frozen_premium": 123, # 冻结权利金
                    "close_profit": 12345, # 本交易日内平仓盈亏
                }

            注意: 在 tqsdk 还没有收到账户数据包时, 此对象中各项内容为0

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
        return self._get_obj(self.data, ["trade", self.account_id, "accounts", "CNY"], {
            "balance": 0,
            "available": 0,
            "deposit": 0,
            "withdraw": 0,
            "commission": 0,
            "preminum": 0,
            "float_profit": 0,
            "risk_ratio": 0,
            "margin": 0,
            "frozen_margin": 0,
            "frozen_commission": 0,
            "frozen_premium": 0,
            "close_profit": 0,
        })

    # ----------------------------------------------------------------------
    def get_position(self, symbol=None):
        """
        获取用户持仓信息

        Args:
            symbol (str): [可选]合约代码, 默认返回所有持仓

        Returns:
            dict: 当指定了symbol时, 返回一个包含指定symbol持仓信息的引用. 每当其中信息改变时, 此dict会自动更新.

            其格式如下::

                {
                    "exchange_id": "SHFE", # 交易所
                    "instrument_id": "cu1801", # 交易所内的合约代码
                    "volume_long": 5, # 多头持仓手数
                    "volume_short": 5, # 空头持仓手数
                    "hedge_flag": "SPEC", # 套保标记
                    "open_price_long": 3203.5, # 多头开仓均价
                    "open_price_short": 3100.5, # 空头开仓均价
                    "open_cost_long": 3203.5, # 多头开仓市值
                    "open_cost_short": 3100.5, # 空头开仓市值
                    "margin": 32324.4, # 占用保证金
                    "float_profit_long": 32324.4, # 多头浮动盈亏
                    "float_profit_short": 32324.4, # 空头浮动盈亏
                    "volume_long_today": 5, # 多头今仓手数
                    "volume_long_his": 5, # 多头老仓手数
                    "volume_long_frozen": 5, # 多头持仓冻结
                    "volume_long_frozen_today": 5, # 多头今仓冻结
                    "volume_short_today": 5, # 空头今仓手数
                    "volume_short_his": 5, # 空头老仓手数
                    "volume_short_frozen": 5, # 空头持仓冻结
                    "volume_short_frozen_today": 5, # 空头今仓冻结
                },

            不带symbol参数调用 get_position 函数, 将返回包含用户所有持仓的一个嵌套dict, 格式如下::

                {
                    "SHFE.cu1801":{
                        "exchange_id": "SHFE", # 交易所
                        "instrument_id": "cu1801", # 交易所内的合约代码
                        "volume_long": 5, # 多头持仓手数
                        ...
                    },
                    "CFFEX.IF1801":{
                        "exchange_id": "CFFEX", # 交易所
                        "instrument_id": "IF1801", # 交易所内的合约代码
                        "volume_long": 3, # 多头持仓手数
                        ...
                    },
                    ...
                }

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
            return self._get_obj(self.data, ["trade", self.account_id, "positions", symbol], {
                "exchange_id": symbol.split(".", 1)[0],
                "instrument_id": symbol.split(".", 1)[1],
                "volume_long": 0,
                "volume_short": 0,
                "hedge_flag": "",
                "open_price_long": 0,
                "open_price_short": 0,
                "open_cost_long": 0,
                "open_cost_short": 0,
                "margin": 0,
                "float_profit_long": 0,
                "float_profit_short": 0,
                "volume_long_today": 0,
                "volume_long_his": 0,
                "volume_long_frozen": 0,
                "volume_long_frozen_today": 0,
                "volume_short_today": 0,
                "volume_short_his": 0,
                "volume_short_frozen": 0,
                "volume_short_frozen_today": 0,
            })
        return self._get_obj(self.data, ["trade", self.account_id, "positions"])

    # ----------------------------------------------------------------------
    def get_order(self, order_id=None):
        """
        获取用户委托单信息

        Args:
            order_id (str): [可选]单号, 默认返回所有委托单

        Returns:
            dict: 当指定了 order_id 时, 返回一个指定 order_id 委托单信息的引用. 每当其中信息改变时, 此dict会自动更新.

            其格式如下::

                {
                    "order_id": "123", # 委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
                    "exchange_id": "SHFE", # 交易所
                    "instrument_id": "cu1801", # 合约代码
                    "direction": "BUY", # 下单方向, BUY=买, SELL=卖
                    "offset": "OPEN", # 开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今
                    "volume_orign": 6, # 总报单手数
                    "volume_left": 3, # 未成交手数
                    "price_type": "LIMIT", # 价格类型, ANY=市价, LIMIT=限价
                    "limit_price": 45000, # 委托价格, 仅当 price_type = LIMIT 时有效
                    "status": "ALIVE", # 委托单状态, ALIVE=有效, FINISHED=已完
                    "insert_date_time": 1928374000000000, # 下单时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数
                    "exchange_order_id": "434214", # 交易所单号
                },

            不带 order_id 参数调用 get_order 函数, 将返回包含用户所有委托单的一个嵌套dict, 格式如下::

                {
                    "4123f73if3":{
                        "order_id": "4123f73if3", # 委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
                        "exchange_id": "SHFE", # 交易所
                        "instrument_id": "cu1801", # 合约代码
                        "direction": "BUY", # 下单方向
                        "offset": "OPEN", # 开平标志
                        ...
                    },
                    "34u3kf834jf":{
                        "order_id": "34u3kf834jf", # 委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
                        "exchange_id": "SHFE", # 交易所
                        "instrument_id": "cu1801", # 合约代码
                        "direction": "BUY", # 下单方向
                        "offset": "OPEN", # 开平标志
                        ...
                    },
                    ...
                }

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
            return self._get_obj(self.data, ["trade", self.account_id, "orders", order_id])
        return self._get_obj(self.data, ["trade", self.account_id, "orders"])

    # ----------------------------------------------------------------------
    def wait_update(self, timeout=None):
        """
        等待业务数据更新

        调用此函数将阻塞当前线程, 等待天勤主进程发送业务数据更新并返回, 如果触发超时则会抛出 TimeoutError

        Args:
            timeout (float):  [可选]指定超时时间，单位:秒。默认没有超时(无限等待)

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
        deadline = None if timeout is None else time.time() + timeout
        update_task = self.create_task(self.update_chans[0].recv())
        try:
            while not update_task.done():
                timeout = None if deadline is None else max(deadline - time.time(), 0)
                done, pending = self.loop.run_until_complete(asyncio.wait(self.tasks, timeout=timeout, return_when=asyncio.FIRST_COMPLETED))
                if len(done) == 0:
                    raise TimeoutError
                self.tasks.difference_update(done)
                # 取出已完成任务的结果，如果执行过程中遇到例外会在这里抛出
                for t in done:
                    t.result()
        finally:
            update_task.cancel()
            self.tasks.discard(update_task)

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
        if asyncio.Task.current_task() is None:
            self.tasks.add(task)
        return task

    # ----------------------------------------------------------------------
    def register_update_notify(self, chan=None):
        """
        注册一个channel以便接受业务数据更新通知

        调用此函数将返回一个channel, 当天勤主进程发送业务数据更新时会通知该channel

        推荐使用 async with api.register_update_notify() as update_chan 来注册更新通知

        如果直接调用 update_chan = api.register_update_notify() 则使用完成后需要调用 await update_chan.close() 避免资源泄漏

        Args:
            chan (TqChan): [可选]指定需要注册的channel。默认不指定，由本函数创建

        Example::

            # 获取 SHFE.cu1812 合约的报价
            import asyncio
            from tqsdk.api import TqApi

            async def demo():
                quote = api.get_quote("SHFE.cu1812")
                async with api.register_update_notify() as update_chan:
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
            chan = TqChan(last_only=True)
        self.update_chans.append(chan)
        return chan

    # ----------------------------------------------------------------------
    async def _windows_patch(self):
        """Windows系统下asyncio不支持KeyboardInterrupt的临时补丁, 详见 https://bugs.python.org/issue23057"""
        while True:
            await asyncio.sleep(1)

    async def _connect(self):
        """启动websocket客户端"""
        async with websockets.connect("ws://127.0.0.1:7777/", max_size=None) as client:
            send_task = self.create_task(self._send_handler(client))
            try:
                async for msg in client:
                    await self._on_receive_msg(msg)
            except websockets.exceptions.ConnectionClosed:
                print("网络连接断开，请检查客户端及网络是否正常", file=sys.stderr)
                raise
            send_task.cancel()

    async def _send_handler(self, client):
        """websocket客户端数据发送协程"""
        async for msg in self.send_chan:
            await client.send(msg)

    def _send_json(self, obj):
        """向天勤主进程发送JSON包"""
        self.send_chan.send_nowait(json.dumps(obj))
        if not self.loop.is_running():
            self.loop.call_soon(self.loop.stop)
            self.loop.run_forever()


    async def _on_receive_msg(self, msg):
        """收到数据推送"""
        pack = json.loads(msg)
        if not self.data.get("mdhis_more_data", True):
            self.diffs = []
        self.diffs.extend(pack.get("data", []))
        for data in self.diffs:
            self._merge_diff(self.data, data)
        if not self.data.get("mdhis_more_data", True):
            self.update_chans[:] = [q for q in self.update_chans if not q.closed]
            for q in self.update_chans:
                await q.send(True)

    @staticmethod
    def _merge_diff(result, diff):
        """更新业务数据"""
        for key in list(diff.keys()):
            if diff[key] is None:
                result.pop(key, None)
            elif isinstance(diff[key], dict):
                target = TqApi._get_obj(result, [key])
                TqApi._merge_diff(target, diff[key])
                if len(diff[key]) == 0:
                    del diff[key]
            elif key in result and result[key] == diff[key]:
                del diff[key]
            else:
                result[key] = diff[key]

    @staticmethod
    def _get_obj(root, path, default=None):
        """获取业务数据"""
        # todo: support nested dict for default value
        d = root
        for i in range(len(path)):
            if path[i] not in d:
                dv = {} if i != len(path) - 1 or default is None else default
                if isinstance(dv, dict):
                    dv["_path"] = d["_path"] + [path[i]]
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
    def _generate_chart_id(symbol, duration_seconds):
        """生成chart id"""
        chart_id = "PYSDK_" + uuid.uuid4().hex
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

    """
    def __init__(self, serial_root, width, default):
        self.serial_root = serial_root
        self.width = width
        self.default = default
        self.attr = list(self.default.keys())

    def __getattr__(self, name):
        if name not in self.attr:
            return []
        last_id = self.serial_root.get("last_id", None)
        if not last_id:
            return []
        return [self[i][name] for i in range(0, self.width)]

    def __getitem__(self, key):
        last_id = self.serial_root.get("last_id", None)
        if not last_id:
            return self.default.copy()
        if key < 0:
            data_id = last_id + 1 + key
        else:
            data_id = last_id - self.width + 1 + key
        return TqApi._get_obj(self.serial_root, ["data", str(data_id)], default=self.default.copy())


class KlineSerialDataProxy(SerialDataProxy):
    """K线序列数据包装器"""
    def __init__(self, serial_root, width):
        SerialDataProxy.__init__(self, serial_root, width, {
            "datetime": 0,
            "open": float("nan"),
            "high": float("nan"),
            "low": float("nan"),
            "close": float("nan"),
            "volume": 0,
            "open_oi": 0,
            "close_oi": 0,
        })


class TickSerialDataProxy(SerialDataProxy):
    """Tick序列数据包装器"""
    def __init__(self, serial_root, width):
        SerialDataProxy.__init__(self, serial_root, width, {
            "datetime": 0,
            "last_price": float("nan"),
            "average": float("nan"),
            "highest": float("nan"),
            "lowest": float("nan"),
            "ask_price1": float("nan"),
            "ask_volume1": 0,
            "bid_price1": float("nan"),
            "bid_volume1": 0,
            "volume": 0,
            "amount": float("nan"),
            "open_interest": 0,
        })


class TimeoutError(Exception):
    """操作超时"""
    pass


class TqChan(asyncio.Queue):
    """用于协程间通讯的channel"""
    def __init__(self, last_only=False):
        """
        创建channel实例

        Args:
            last_only (bool): 为True时只存储最后一个发送到channel的对象
        """
        asyncio.Queue.__init__(self)
        self.last_only = last_only
        self.closed = False

    async def close(self):
        """
        关闭channel

        关闭后send将不起作用,recv在收完剩余数据后会立即返回None
        """
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
