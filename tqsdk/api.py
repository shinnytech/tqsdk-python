# encoding: UTF-8

"""
天勤接口的PYTHON封装, 提供以下功能

    * 连接天勤终端的websocket扩展接口, 从天勤终端接收行情及交易推送数据
    * 在内存中存储管理一份完整的业务数据(行情+交易), 并在接收到新数据包时更新内存数据
    * 通过一批函数接口, 支持用户代码访问业务数据
    * 发送交易指令


使用前, 需要在本机先启动一个天勤终端进程(版本 0.8 以上):

    * 天勤行情终端下载: http://www.tq18.cn
    * 天勤使用文档: http://doc.tq18.cn/tq/latest/
    * 天勤 websocket 扩展接口文档: http://doc.tq18.cn/tq/latest/extension/wsapi/index.html
"""

import json
import uuid
import tornado
from tornado import websocket


class TqApi(object):
    """
    天勤接口及数据管理类.

    通常情况下, 一个进程中应该有一个TqApi的实例, 它负责维护到天勤终端的网络连接, 从天勤终端接收行情及账户数据, 并在内存中维护数据存储池
    """
    def __init__(self, account_id):
        """
        创建天勤接口实例

        Args:
           account_id (str):  指定交易账号, 若不指定, 则默认为已登录的第一个交易账号
        """
        self.data = {"_path": []}  # 数据存储
        self.diffs = [] # 每次收到更新数据的数组
        self.loop = tornado.ioloop.IOLoop.current()
        self.client = None  # websocket客户端
        self.quote_symbol_list = []
        self.account_id = account_id
        self.loop.run_sync(self._connect, timeout=30)

    # ----------------------------------------------------------------------
    def peek_message(self):
        """
        启动主消息循环

        调用此函数将在当前线程阻塞式地运行一个消息循环, 用来处理与天勤主进程间的数据收发任务.

        Args:
           data_update_hook (function/list of function): 一个回调函数, 每当从天勤主进程接收到数据包后, 都会触发此回调函数, 用于运行用户业务代码

        注意: 此函数一旦运行, 将不会结束返回. 用户应当在提供的回调函数 data_update_hook 中处理业务, 而不能将代码写在 run() 之后
        """
        return self.loop.run_sync(self._peek_message)

    # ----------------------------------------------------------------------
    def get_quote(self, symbol):
        """
        获取指定合约的盘口行情.

        Args:
           symbol (str):  指定合约代码。注意：天勤接口从0.8版本开始，合约代码格式变更为 交易所代码.合约代码 的格式. 可用的交易所代码如下：
                         * CFFEX: 中金所
                         * SHFE: 上期所
                         * DCE: 大商所
                         * CZCE: 郑商所
                         * INE: 能源交易所(原油)

        Returns:
            dict: 返回如下结构所示的一个 dict 对象的引用, 当行情更新时, 此对象的内容被自动更新::

                {
                    u'datetime': u'2017-07-26 23:04:21.000001',# tick从交易所发出的时间(按北京时区)
                    u'last_price': 6122.0, # 最新价
                    u'bid_price1': 6121.0, # 买一价
                    u'ask_price1': 6122.0, # 卖一价
                    u'bid_volume1': 54, # 买一量
                    u'ask_volume1': 66, # 卖一量
                    u'upper_limit': 6388.0, # 涨停价
                    u'lower_limit': 5896.0, # 跌停价
                    u'volume': 89252, # 成交量
                    u'amount': 5461329880.0, # 成交额
                    u'open_interest': 616424, # 持仓量
                    u'highest': 6129.0, # 当日最高价
                    u'lowest': 6101.0, # 当日最低价
                    u'average': 6119.0, # 当日均价
                    u'open': 6102.0, # 开盘价
                    u'close': u'-', # 收盘价
                    u'settlement': u'-', # 结算价
                    u'pre_close': 6106.0, # 昨收盘价
                    u'pre_settlement': 6142.0 #  昨结算价
                    u'pre_open_interest': 616620, # 昨持仓量
                }

            注意: 在 tqsdk 还没有收到行情数据包时, 此对象中各项内容为 NaN 或 0

        Example::

            # 获取 SHFE.cu1803 合约的报价
            from tqsdk.api import TqApi

            api = TqApi()
            q = api.get_quote("SHFE.cu1803")
            def on_update():
                print (q["last_price"])
            api.run(on_update)

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
        return _get_obj(self.data, ["quotes", symbol], {
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

            duration_seconds (int): K线数据周期，以秒为单位。目前支持的周期包括：

                3秒，5秒，10秒，15秒，20秒，30秒，1分钟，2分钟，3分钟，5分钟，10分钟，15分钟，20分钟，30分钟，1小时，2小时，4小时，1日

            data_length (int): 需要获取的序列长度。每个序列最大支持请求 8964 个数据

        Returns:
            SerialDataProxy: 本函数总是返回一个 SerialDataProxy 的实例.
            其中每个数据项的格式如下::

                {
                    u'datetime': 1501080715000000000L, # K线起点时间(按北京时区)，以nano epoch 方式表示(等于从1970-01-01时刻开始的纳秒数)
                    u'open': 51450, # K线起始时刻的最新价
                    u'high': 51450, # K线时间范围内的最高价
                    u'low': 51450, # K线时间范围内的最低价
                    u'close': 51450, # K线结束时刻的最新价
                    u'volume': 0, # K线时间范围内的成交量
                    u'open_oi': 27354, # K线起始时刻的持仓量
                    u'close_oi': 27354 # K线结束时刻的持仓量
                }

        Example::

            # 获取 SHFE.cu1805 的1分钟线
            from tqsdk.api import TqApi

            api = TqApi()
            k_serial = api.get_kline_serial("SHFE.cu1805", 60)
            def on_update():
                print ("SHFE.cu1805 last_kline:", k_serial[-1]["close"])
            api.run(on_update)

            # 预计的输出是这样的:
            ('SHFE.cu1805 last_kline:', 50970.0)
            ('SHFE.cu1805 last_kline:', 50970.0)
            ('SHFE.cu1805 last_kline:', 50960.0)
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
        return KlineSerialDataProxy(_get_obj(self.data, ["klines", symbol, str(dur_id)]), data_length)

    # ----------------------------------------------------------------------
    def get_tick_serial(self, symbol, data_length=200, chart_id=None):
        """
        获取tick序列数据

        请求指定合约的Tick序列数据. 序列数据会随着时间推进自动更新

        Args:

            symbol (str): 指定合约代码.
            data_length (int): 需要获取的序列长度。每个序列最大支持请求 8964 个数据

        Returns:
            SerialDataProxy: 本函数总是返回一个 SerialDataProxy 的实例.
            其中每个数据项的格式如下::

                {
                    u'datetime': 1501074872000000000L, # tick从交易所发出的时间(按北京时区)，以nano epoch 方式表示(等于从1970-01-01时刻开始的纳秒数)
                    u'trading_day': 1501084800000000000L, #交易日, 格式同上
                    u'last_price': 3887, # 最新价
                    u'bid_price1': 3881, # 买一价
                    u'ask_price1': 3886, # 卖一价
                    u'bid_volume1': 5, # 买一量
                    u'ask_volume1': 1, #卖一量
                    u'highest': 3887, # 当日最高价
                    u'lowest': 3886,    # 当日最低价
                    u'volume': 6, # 成交量
                    u'open_interest': 1796 # 持仓量
                },

        Example::

            # 获取 SHFE.cu1803 的Tick序列
            from tqsdk.api import TqApi

            api = TqApi()
            serial = api.get_tick_serial("SHFE.cu1803")
            def on_update():
                print ("SHFE.cu1803 last_tick:", serial[-1]["bid_price1"], serial[-1]["ask_price1"])
            api.run(on_update)

            # 预计的输出是这样的:
            ('SHFE.cu1803 last_tick:', 50860.0, 51580.0)
            ('SHFE.cu1803 last_tick:', 50820.0, 51580.0)
            ('SHFE.cu1803 last_tick:', 50860.0, 51590.0)
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
        return TickSerialDataProxy(_get_obj(self.data, ["ticks", symbol]), data_length)

    # ----------------------------------------------------------------------
    def insert_order(self, symbol, direction, offset, volume, limit_price=None, order_id=None):
        """
        发送下单指令

        Args:
            symbol (str): 拟下单的合约symbol, 格式为 交易所代码.合约代码,  例如 "SHFE.cu1801"
            direction (str): "BUY" 或 "SELL"
            offset (str): "OPEN", "CLOSE" 或 "CLOSETODAY"
            volume (int): 需要下单的手数
            limit_price (float): 下单价格
            order_id (str): [可选]指定下单单号

        Returns:
            dict: 本函数总是返回一个包含委托单信息的dict的引用. 每当order中信息改变时, 此dict会自动更新.
            其格式如下::

                {
                    "order_id": "123",                            //委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
                    "exchange_id": "SHFE",                        //交易所
                    "instrument_id": "cu1801",                    //合约代码
                    "direction": "BUY",                           //下单方向
                    "offset": "OPEN",                             //开平标志
                    "volume_orign": 6,                            //总报单手数
                    "volume_left": 3,                             //未成交手数
                    "price_type": "LIMIT",                        //价格类型
                    "limit_price": 45000,                         //委托价格, 仅当 price_type = LIMIT 时有效
                    "status": "ALIVE",                            //委托单状态, ALIVE=有效, FINISHED=已完
                    "insert_date_time": 1928374000000000,         //下单时间
                    "exchange_order_id": "434214",                //交易所单号
                },

        Raises:
            ValueError: 如果api中未指定交易账号, 则抛出ValueError.

        """
        if not self.account_id:
            raise ValueError("account_id is invalid")
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
            "price_type": "MARKET" if limit_price is None else "LIMIT",
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
        self._merge_obj(self.data, {
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
            order_or_order_id (str / dict): 拟撤委托单的 dict 或 单号

        Raises:
            ValueError: 如果api中未指定交易账号, 则抛出ValueError.
        """
        if not self.account_id:
            raise ValueError("account_id is invalid")
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
                    "balance": 9963216.550000003,                 //账户权益
                    "available": 9480176.150000002,               //可用资金
                    "deposit": 42344,                             //本交易日内的入金金额
                    "withdraw": 42344,                            //本交易日内的出金金额
                    "commission": 123,                            //本交易日内交纳的手续费
                    "preminum": 123,                              //本交易日内交纳的权利金
                    "position_profit": 12345,                     //持仓盈亏
                    "float_profit": 8910.231,                     //浮动盈亏
                    "risk_ratio": 0.048482375,                    //风险度
                    "margin": 11232.23,                           //占用资金
                    "frozen_margin": 12345,                       //冻结保证金
                    "frozen_commission": 123,                     //冻结手续费
                    "frozen_premium": 123,                        //冻结权利金
                    "close_profit": 12345,                        //本交易日内平仓盈亏
                    "position_profit": 12345,                     //当前持仓盈亏
                }

            注意: 在 tqsdk 还没有收到行情数据包时, 此对象为空 {}

        Raises:
            ValueError: 如果api中未指定交易账号, 则抛出ValueError.
        """
        if not self.account_id:
            raise ValueError("account_id is invalid")
        return _get_obj(self.data, ["trade", self.account_id, "accounts", "CNY"])

    # ----------------------------------------------------------------------
    def get_position(self, symbol=None):
        """
        获取用户持仓信息

        Args:
            symbol (str): [可选]合约代码

        Returns:
            dict: 当指定了symbol时, 返回一个包含指定symbol持仓信息的引用. 每当其中信息改变时, 此dict会自动更新.
            其格式如下::

                {
                    "exchange_id": "SHFE",                        //交易所
                    "instrument_id": "cu1801",                    //交易所内的合约代码
                    "volume_long": 5,                             //多头持仓手数
                    "volume_short": 5,                            //空头持仓手数
                    "hedge_flag": "SPEC",                         //套保标记
                    "open_price_long": 3203.5,                    //多头开仓均价
                    "open_price_short": 3100.5,                   //空头开仓均价
                    "open_cost_long": 3203.5,                     //多头开仓市值
                    "open_cost_short": 3100.5,                    //空头开仓市值
                    "margin": 32324.4,                            //占用保证金
                    "float_profit_long": 32324.4,                 //多头浮动盈亏
                    "float_profit_short": 32324.4,                //空头浮动盈亏
                    "volume_long_today": 5,                       //多头今仓手数
                    "volume_long_his": 5,                         //多头老仓手数
                    "volume_long_frozen": 5,                      //多头持仓冻结
                    "volume_long_frozen_today": 5,                //多头今仓冻结
                    "volume_short_today": 5,                      //空头今仓手数
                    "volume_short_his": 5,                        //空头老仓手数
                    "volume_short_frozen": 5,                     //空头持仓冻结
                    "volume_short_frozen_today": 5,               //空头今仓冻结
                },

            不带symbol参数调用 get_position 函数, 将返回包含用户所有持仓的一个双层dict, 格式如下::

                {
                    "SHFE.cu1801":{
                        "exchange_id": "SHFE",                        //交易所
                        "instrument_id": "cu1801",                    //交易所内的合约代码
                        "volume_long": 5,                             //多头持仓手数
                        ...
                    },
                    "CFFEX.IF1801":{
                        "exchange_id": "CFFEX",                        //交易所
                        "instrument_id": "IF1801",                    //交易所内的合约代码
                        "volume_long": 5,                             //多头持仓手数
                        ...
                    },
                    ...
                }

            注意: 在 tqsdk 还没有收到持仓信息时, 此对象为空 {}

        Raises:
            ValueError: 如果api中未指定交易账号, 则抛出ValueError.
        """
        if not self.account_id:
            raise ValueError("account_id is invalid")
        if symbol:
            return _get_obj(self.data, ["trade", self.account_id, "positions", symbol])
        return _get_obj(self.data, ["trade", self.account_id, "positions"])

    # ----------------------------------------------------------------------
    def get_order(self, order_id=None):
        """
        获取用户委托单信息

        Args:
            order_id (str): [可选]单号

        Returns:
            dict: 当指定了 order_id 时, 返回一个指定 order_id 委托单信息的引用. 每当其中信息改变时, 此dict会自动更新.
            其格式如下::

                {
                    "order_id": "123",                            //委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
                    "exchange_id": "SHFE",                        //交易所
                    "instrument_id": "cu1801",                    //合约代码
                    "direction": "BUY",                           //下单方向
                    "offset": "OPEN",                             //开平标志
                    "volume_orign": 6,                            //总报单手数
                    "volume_left": 3,                             //未成交手数
                    "price_type": "LIMIT",                        //价格类型
                    "limit_price": 45000,                         //委托价格, 仅当 price_type = LIMIT 时有效
                    "status": "ALIVE",                            //委托单状态, ALIVE=有效, FINISHED=已完
                    "insert_date_time": 1928374000000000,         //下单时间
                    "exchange_order_id": "434214",                //交易所单号
                },

            不带 order_id 参数调用 get_order 函数, 将返回包含用户所有委托单的一个双层dict, 格式如下::

                {
                    "4123f73if3":{
                        "order_id": "4123f73if3",                     //委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
                        "exchange_id": "SHFE",                        //交易所
                        "instrument_id": "cu1801",                    //合约代码
                        "direction": "BUY",                           //下单方向
                        "offset": "OPEN",                             //开平标志
                        ...
                    },
                    "34u3kf834jf":{
                        "order_id": "34u3kf834jf",                    //委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
                        "exchange_id": "SHFE",                        //交易所
                        "instrument_id": "cu1801",                    //合约代码
                        "direction": "BUY",                           //下单方向
                        "offset": "OPEN",                             //开平标志
                        ...
                    },
                    ...
                }

            注意: 在 tqsdk 还没有收到委托单信息时, 此对象为空 {}

        Raises:
            ValueError: 如果api中未指定交易账号, 则抛出ValueError.
        """
        if not self.account_id:
            raise ValueError("account_id is invalid")
        if order_id:
            return _get_obj(self.data, ["trade", self.account_id, "orders", order_id])
        return _get_obj(self.data, ["trade", self.account_id, "orders"])

    # ----------------------------------------------------------------------
    def is_changing(self, obj, key=None):
        """
        判定obj最近是否有更新

        每当TqApi从天勤主进程接收到数据包后, 都会通过 data_update_hook 回调函数调用用户业务代码. 用户代码中如果需要判断特定obj或其中某个字段是否被本次数据包更新, 可以使用 is_changing 函数判定

        Args:
            obj (any): 任意业务对象, 包括 get_quote 返回的 quote, get_kline_serial 返回的 k_serial, get_account 返回的 account 等
            key (str/list of str): 需要判断的字段

        Returns:
            bool: 如果指定的obj被本次数据包修改了, 返回 True, 否则返回 False.

        Example::

            from tqsdk.api import TqApi

            api = TqApi()
            serial = api.get_tick_serial("SHFE.cu1803")
            def on_update():
                print ("SHFE.cu1803 serial change? ", api.is_changing(serial))
            api.run(on_update)

            # 以上代码运行后的输出是这样的:
            ('SHFE.cu1805 tick serial changed? ', False)
            ('SHFE.cu1805 tick serial changed? ', True)
            ('SHFE.cu1805 tick serial changed? ', False)
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

    def _is_key_exist(self, diff, path, key):
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

    # ----------------------------------------------------------------------
    async def _connect(self):
        """启动websocket客户端"""
        self.client = await tornado.websocket.websocket_connect(url="ws://192.168.1.241:7777/")

        # 收取截面数据后返回
        while self.data.get("mdhis_more_data", True):
            await self._peek_message()

    async def _peek_message(self):
        # 协程式读取数据
        msg = await self.client.read_message()
        return self._on_receive_msg(msg)

    def _send_json(self, obj):
        """向天勤主进程发送JSON包"""
        s = json.dumps(obj)

        self.client.write_message(s)

    def _on_receive_msg(self, msg):
        """收到数据推送"""
        if msg is None:
            raise Exception("接收数据失败，请检查客户端及网络是否正常")
        pack = json.loads(msg)
        if "data" in pack:
            self.diffs = pack["data"]
            for data in self.diffs:
                self._merge_obj(self.data, data)
        return True

    def _merge_obj(self, result, obj):
        for key in list(obj.keys()):
            if obj[key] is None:
                result.pop(key, None)
            elif isinstance(obj[key], dict):
                target = _get_obj(result, [key])
                self._merge_obj(target, obj[key])
            elif key in result and result[key] == obj[key]:
                obj.pop(key)
            else:
                result[key] = obj[key]

    def _generate_chart_id(self, symbol, duration_seconds):
        chart_id = "PYSDK_" + uuid.uuid4().hex
        return chart_id

    def _generate_order_id(self):
        return uuid.uuid4().hex


class SerialDataProxy(object):
    """
    K线及Tick序列数据包装器, 方便数据读取使用

    Examples::

        # 获取一个分钟线序列, ks 即是 SerialDataProxy 的实例
        ks = api.get_kline_serial("SHFE.cu1801", 60)

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
        # cs = [3245, 3421, 4345, ...]

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
        return [self[i][name] for i in range(last_id - self.width + 1, last_id + 1)]

    def __getitem__(self, key):
        last_id = self.serial_root.get("last_id", None)
        if not last_id:
            return self.default.copy()
        if key < 0:
            id = last_id + 1 + key
        else:
            id = last_id - self.width + 1 + key
        return _get_obj(self.serial_root, ["data", str(id)], default=self.default.copy())

class KlineSerialDataProxy(SerialDataProxy):
    def __init__(self, serial_root, width):
        SerialDataProxy.__init__(self, serial_root, width, {
            "datetime":0,
            "open": float("nan"),
            "high": float("nan"),
            "low": float("nan"),
            "close": float("nan"),
            "volume":0,
            "open_oi":0,
            "close_oi":0,
        })

class TickSerialDataProxy(SerialDataProxy):
    def __init__(self, serial_root, width):
        SerialDataProxy.__init__(self, serial_root, width, {
            "datetime":0,
            "last_price": float("nan"),
            "average": float("nan"),
            "highest": float("nan"),
            "lowest": float("nan"),
            "ask_price1": float("nan"),
            "ask_volume1":0,
            "bid_price1": float("nan"),
            "bid_volume1":0,
            "volume":0,
            "amount": float("nan"),
            "open_interest":0,
        })

def _get_obj(root, path, default=None):
    #todo: support nested dict for default value
    d = root
    for i in range(len(path)):
        if path[i] not in d:
            dv = {} if i != len(path) - 1 or default is None else default
            if isinstance(dv, dict):
                dv["_path"] = d["_path"] + [path[i]]
            d[path[i]] = dv
        d = d[path[i]]
    return d