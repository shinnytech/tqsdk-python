.. _mddatas:

合约, 行情和历史数据
====================================================

合约代码
----------------------------------------------------
TqSdk中的合约代码, 统一采用 交易所代码.交易所内品种代码 的格式. 交易所代码为全大写字母, 交易所内品种代码的大小写规范, 遵从交易所规定, 大小写敏感.

目前 TqSdk 支持的交易所包括:

================== ====================================================================
CODE               NAME
================== ====================================================================
SHFE               上海期货交易所
DCE                大连商品交易所
CZCE               郑州商品交易所
CFFEX              中国金融交易所
INE                上海能源中心(原油在这里)
KQ                 快期 (所有主连合约, 指数都归属在这里)
SSWE               上期所仓单
SSE                上海证券交易所(尚未上线)
SZSE               深圳证券交易所(尚未上线)
================== ====================================================================

一些合约代码示例::

	SHFE.cu1901 - 上期所 cu1901 期货合约
	DCE.m1901 - 大商所 m1901 期货合约
	CZCE.SR901 - 郑商所 SR901 期货合约
	CFFEX.IF1901 - 中金所 IF1901 期货合约

	CZCE.SPD SR901&SR903 - 郑商所 SR901&SR903 跨期合约
	DCE.SP a1709&a1801 - 大商所 a1709&a1801 跨期合约

	DCE.m1807-C-2450 - 大商所豆粕期权

	KQ.m@CFFEX.IF - 中金所IF品种主连合约
	KQ.i@SHFE.bu - 上期所bu品种指数

**注意：并非所有合约都是可交易合约.**

如您需要获得某个特定合约的代码，可以在天勤终端中察看

.. image:
  ...


实时行情
----------------------------------------------------
:py:meth:`~tqsdk.api.TqApi.get_quote` 函数提供实时行情和合约信息::

    q = api.get_quote("SHFE.cu1901")

返回值为一个dict, 结构如下::

    {
        "datetime": "",  # "2017-07-26 23:04:21.000001" (行情从交易所发出的时间(北京时间))
        "ask_price5": float("nan"),  # 6122.0 (卖五价)
        "ask_volume5": 0,  # 3 (卖五量)
        "ask_price4": float("nan"),  # 6122.0 (卖四价)
        "ask_volume4": 0,  # 3 (卖四量)
        "ask_price3": float("nan"),  # 6122.0 (卖三价)
        "ask_volume3": 0,  # 3 (卖三量)
        "ask_price2": float("nan"),  # 6122.0 (卖二价)
        "ask_volume2": 0,  # 3 (卖二量)
        "ask_price1": float("nan"),  # 6122.0 (卖一价)
        "ask_volume1": 0,  # 3 (卖一量)
        "bid_price1": float("nan"),  # 6121.0 (买一价)
        "bid_volume1": 0,  # 7 (买一量)
        "bid_price2": float("nan"),  # 6121.0 (买二价)
        "bid_volume2": 0,  # 7 (买二量)
        "bid_price3": float("nan"),  # 6121.0 (买三价)
        "bid_volume3": 0,  # 7 (买三量)
        "bid_price4": float("nan"),  # 6121.0 (买四价)
        "bid_volume4": 0,  # 7 (买四量)
        "bid_price5": float("nan"),  # 6121.0 (买五价)
        "bid_volume5": 0,  # 7 (买五量)
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

对于每个合约, 只需要调用一次 get_quote 函数. 如果需要监控数据更新, 可以使用 :py:meth:`~tqsdk.api.TqApi.wait_update`::

    q = api.get_quote("SHFE.cu1812")  # 获取SHFE.cu1812合约的行情

    while api.wait_update():
      print(q.last_price)    # 收到新行情时都会执行这行


K线数据
----------------------------------------------------
:py:meth:`~tqsdk.api.TqApi.get_kline_serial` 函数获取指定合约和周期的K线序列数据::

    klines = api.get_kline_serial("SHFE.cu1812", 10)  # 获取SHFE.cu1812合约的10秒K线

获取按照时间对齐的多合约K线::

    klines = api.get_kline_serial(["SHFE.au1912", "SHFE.au2006"], 5)  # 获取SHFE.au2006向SHFE.au1912对齐的K线

详细使用方法及说明请见 :py:meth:`~tqsdk.api.TqApi.get_kline_serial` 函数使用说明。

:py:meth:`~tqsdk.api.TqApi.get_kline_serial` 的返回值是一个 pandas.DataFrame, 包含以下列::

    id: 1234 (k线序列号)
    datetime: 1501080715000000000 (K线起点时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
    open: 51450.0 (K线起始时刻的最新价)
    high: 51450.0 (K线时间范围内的最高价)
    low: 51450.0 (K线时间范围内的最低价)
    close: 51450.0 (K线结束时刻的最新价)
    volume: 11 (K线时间范围内的成交量)
    open_oi: 27354 (K线起始时刻的持仓量)
    close_oi: 27355 (K线结束时刻的持仓量)

要使用K线数据, 请使用 pandas.DataFrame 的相关函数. 常见用法示例如下::

    klines.iloc[-1].close  # 最后一根K线的收盘价
    klines.close          # 收盘价序列, 一个 pandas.Serial

TqSdk中, K线周期以秒数表示，支持不超过1日的任意周期K线，例如::

    api.get_kline_serial("SHFE.cu1901", 70) # 70秒线
    api.get_kline_serial("SHFE.cu1901", 86400) # 86400秒线, 即日线
    api.get_kline_serial("SHFE.cu1901", 86500) # 86500秒线, 超过1日，无效

TqSdk中最多可以获取每个K线序列的最后8000根K线，无论哪个周期。也就是说，你如果提取小时线，最多可以提取最后8000根小时线，如果提取分钟线，最多也是可以提取最后8000根分钟线。

对于每个K线序列, 只需要调用一次 :py:meth:`~tqsdk.api.TqApi.get_kline_serial` . 如果需要监控数据更新, 可以使用 :py:meth:`~tqsdk.api.TqApi.wait_update` ::

    klines = api.get_kline_serial("SHFE.cu1812", 10)  # 获取SHFE.cu1812合约的10秒K线

    while api.wait_update():
        print(klines.iloc[-1])    # K线数据有任何变动时都会执行这行


如果只想在新K线出现时收到信号, 可以配合使用 :py:meth:`~tqsdk.api.TqApi.is_changing`::

    klines = api.get_kline_serial("SHFE.cu1812", 10)        # 获取SHFE.cu1812合约的10秒K线

    while api.wait_update():
        if api.is_changing(klines.iloc[-1], "datetime"):    # 判定最后一根K线的时间是否有变化
            print(klines.iloc[-1])                          # 当最后一根K线的时间有变(新K线生成)时才会执行到这里


Tick序列
----------------------------------------------------
:py:meth:`~tqsdk.api.TqApi.get_tick_serial` 函数获取指定合约的Tick序列数据::

    ticks = api.get_tick_serial("SHFE.cu1812")  # 获取SHFE.cu1812合约的Tick序列

:py:meth:`~tqsdk.api.TqApi.get_tick_serial` 的返回值是一个 pandas.DataFrame, 常见用法示例如下::

    ticks.iloc[-1].bid_price1       # 最后一个Tick的买一价
    ticks.volume                    # 成交量序列, 一个 pandas.Serial

tick序列的更新监控, 与K线序列采用同样的方式.


关于合约及行情的一些常见问题
----------------------------------------------------
**怎样同时监控多个合约的行情变化**

  TqSdk可以订阅任意多个行情和K线, 并在一个wait_update中等待更新. 像这样::

    q1 = api.get_quote("SHFE.cu1901")
    q2 = api.get_quote("SHFE.cu1902")
    k1 = api.get_kline_serial("SHFE.cu1901", 60)
    k2 = api.get_kline_serial("SHFE.cu1902", 60)

    while api.wait_update():
      print("收到数据了")        # 上面4项中的任意一项有变化, 都会到这一句. 具体是哪个或哪几个变了, 用 is_changing 判断
      if api.is_changing(q1):
        print(q1)               # 如果q1变了, 就会执行这句
      if api.is_changing(q2):
        print(q2)
      if api.is_changing(k1):
        print(k1)
      if api.is_changing(k2):
        print(k2)

  关于 :py:meth:`~tqsdk.api.TqApi.wait_update` 和 :py:meth:`~tqsdk.api.TqApi.is_changing` 的详细说明, 请见 :ref:`framework`
