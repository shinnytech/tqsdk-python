.. _mddatas:

合约, 行情和历史数据
====================================================

合约代码
----------------------------------------------------
TqSdk中的合约代码, 统一采用 交易所代码.交易所内品种代码 的格式. 交易所代码为全大写字母, 交易所内品种代码的大小写规范, 遵从交易所规定, 大小写敏感.

其中 TqSdk 免费版本提供全部的期货、商品/金融期权和上证50、沪深300、中证500和中证1000的实时行情

购买或申请 TqSdk 专业版试用后可提供A股股票的实时和历史行情，具体免费版和专业版的区别，请点击 `天勤量化专业版 <https://www.shinnytech.com/tqsdk-buy/>`_

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
KQD                快期外盘主连合约
SSWE               上期所仓单
SSE                上海证券交易所
SZSE               深圳证券交易所
GFEX               广州期货交易所
================== ====================================================================

一些合约代码示例::

	SHFE.cu1901  -  上期所 cu1901 期货合约
	DCE.m1901    -  大商所 m1901 期货合约
	CZCE.SR901   -  郑商所 SR901 期货合约
	CFFEX.IF1901 -  中金所 IF1901 期货合约
	INE.sc2109   -  上期能源 sc2109 期货合约
	GFEX.si2301  -  广期所 si2301 期货合约

	CZCE.SPD SR901&SR903  - 郑商所 SR901&SR903 跨期合约
	DCE.SP a1709&a1801    - 大商所 a1709&a1801 跨期合约
	GFEX.SP si2308&si2309 - 广期所 si2308&si2309 跨期组合

	DCE.m1807-C-2450    - 大商所豆粕期权
	CZCE.CF003C11000    - 郑商所棉花期权
	SHFE.au2004C308     - 上期所黄金期权
	CFFEX.IO2002-C-3550 - 中金所沪深300股指期权
	INE.sc2109C450      - 上期能源原油期权
	GFEX.si2308-C-5800  - 广期所硅期权


	KQ.m@CFFEX.IF - 中金所IF品种主连合约
	KQ.i@SHFE.bu - 上期所bu品种指数

	KQD.m@CBOT.ZS - 美黄豆主连

	SSWE.CUH - 上期所仓单铜现货数据

	SSE.600000 - 上交所浦发银行股票编码
	SZSE.000001 - 深交所平安银行股票编码
	SSE.000016 - 上证50指数
	SSE.000300 - 沪深300指数
	SSE.000905 - 中证500指数
	SSE.000852 - 中证1000指数
	SSE.510050 - 上交所上证50ETF
	SSE.510300 - 上交所沪深300ETF
	SZSE.159919 - 深交所沪深300ETF
	SSE.10002513 - 上交所上证50ETF期权
	SSE.10002504 - 上交所沪深300ETF期权
	SZSE.90000097 - 深交所沪深300ETF期权
	SZSE.159915 - 易方达创业板ETF
	SZSE.90001277 - 创业板ETF期权
	SZSE.159922 - 深交所中证500ETF
	SZSE.90001355 - 深交所中证500ETF期权
	SSE.510500 - 上交所中证500ETF
	SSE.10004497 - 上交所中证500ETF期权
	SZSE.159901 - 深交所100ETF



**注意：并非所有合约都是可交易合约.**

需要注意郑商所的期货合约格式为合约字母大写，并且只有三位数字位，同时不同家交易所的期权代码格式也各不相同

天勤指数的计算方式为根据在市期货合约的昨持仓量加权平均

天勤主力的选定标准为该合约持仓量和成交量均为最大后，在下一个交易日开盘后进行切换，且切换后不会再切换到之前的合约


.. image:
  ...


实时行情
----------------------------------------------------
:py:meth:`~tqsdk.TqApi.get_quote` 函数提供实时行情和合约信息::

    q = api.get_quote("SHFE.cu2201")

返回值为一个dict, 结构如下::

    {
        "datetime": "2021-08-17 14:59:59.000001",  # 行情从交易所发出的时间(北京时间)
        "ask_price1": 69750.0,  # 卖一价
        "ask_volume1": 1,  # 卖一量
        "bid_price1": 69600.0,  # 买一价
        "bid_volume1": 2,  # 买一量
        "ask_price2": 69920.0,  # 卖二价
        "ask_volume2": 3,  # 卖二量
        "bid_price2": 69500.0,  # 买二价
        "bid_volume2": 3,  # 买二量
        "ask_price3": 69940.0,  # 卖三价
        "ask_volume3": 1,  # 卖三量
        "bid_price3": 69450.0,  # 买三价
        "bid_volume3": 1,  # 买三量
        "ask_price4": 70010.0,  # 卖四价
        "ask_volume4": 1,  # 卖四量
        "bid_price4": 69400.0,  # 买四价
        "bid_volume4": 1,  # 买四量
        "ask_price5": 70050.0,  # 卖五价
        "ask_volume5": 1,  # 卖五量
        "bid_price5": 69380.0,  # 买五价
        "bid_volume5": 1,  # 买五量
        "last_price": 69710.0,  # 最新价
        "highest": 70050.0,  # 当日最高价
        "lowest": 69520.0,  # 当日最低价
        "open": 69770.0,  # 开盘价
        "close": 69710.0,  # 收盘价
        "average": 69785.019711,  # 当日均价
        "volume": 761,  # 成交量
        "amount": 265532000.0,  # 成交额
        "open_interest": 8850,  # 持仓量
        "settlement": 69780.0,  # 结算价
        "upper_limit": 75880.0,  # 涨停价
        "lower_limit": 64630.0,  # 跌停价
        "pre_open_interest": 8791,  # 昨持仓量
        "pre_settlement": 70260.0,  # 昨结算价
        "pre_close": 69680.0,  # 昨收盘价
        "price_tick": 10.0,  # 合约价格变动单位
        "price_decs": 0,  # 合约价格小数位数
        "volume_multiple": 5.0,  # 合约乘数
        "max_limit_order_volume": 500,  # 最大限价单手数
        "max_market_order_volume": 0,  # 最大市价单手数
        "min_limit_order_volume": 0,  # 最小限价单手数
        "min_market_order_volume": 0,  # 最小市价单手数
        "underlying_symbol": "",  # 标的合约
        "strike_price": NaN,  # 行权价
        "ins_class": "FUTURE",  # 合约类型
        "instrument_id": "SHFE.cu2201",  # 合约代码
        "instrument_name": "沪铜2201",  # 合约中文名
        "exchange_id": "SHFE",  # 交易所代码
        "expired": false,  # 合约是否已下市
        "trading_time": "{'day': [['09:00:00', '10:15:00'], ['10:30:00', '11:30:00'], ['13:30:00', '15:00:00']], 'night': [['21:00:00', '25:00:00']]}",  # 交易时间段
        "expire_datetime": 1642402800.0,  # 到期具体日，以秒为单位的 timestamp 值
        "delivery_year": 2022,  # 期货交割日年份，只对期货品种有效。期权推荐使用最后行权日年份
        "delivery_month": 1,  # 期货交割日月份，只对期货品种有效。期权推荐使用最后行权日月份
        "last_exercise_datetime": NaN,  # 期权最后行权日，以秒为单位的 timestamp 值
        "exercise_year": 0,  # 期权最后行权日年份，只对期权品种有效。
        "exercise_month": 0,  # 期权最后行权日月份，只对期权品种有效。
        "option_class": "",  # 期权行权方式，看涨:'CALL'，看跌:'PUT'
        "exercise_type": "",  # 期权行权方式，美式:'A'，欧式:'E'
        "product_id": "cu",  # 品种代码
        "iopv": NaN,  # ETF实时单位基金净值
        "public_float_share_quantity": 0,  # 日流通股数，只对证券产品有效。
        "stock_dividend_ratio": [],  # 除权表 ["20190601,0.15","20200107,0.2"…]
        "cash_dividend_ratio": [],  # 除息表 ["20190601,0.15","20200107,0.2"…]
        "expire_rest_days": 153,   # 距离到期日的剩余天数（自然日天数），正数表示距离到期日的剩余天数，0表示到期日当天，负数表示距离到期日已经过去的天数
        "commission": 17.565,
        "margin": 31617.0
    }

对于每个合约, 只需要调用一次 get_quote 函数. 如果需要监控数据更新, 可以使用 :py:meth:`~tqsdk.TqApi.wait_update`::

    q = api.get_quote("SHFE.cu1812")  # 获取SHFE.cu1812合约的行情

    while api.wait_update():
      print(q.last_price)    # 收到新行情时都会执行这行


K线数据
----------------------------------------------------
:py:meth:`~tqsdk.TqApi.get_kline_serial` 函数获取指定合约和周期的K线序列数据::

    klines = api.get_kline_serial("SHFE.cu1812", 10)  # 获取SHFE.cu1812合约的10秒K线

获取按照时间对齐的多合约K线::

    klines = api.get_kline_serial(["SHFE.au1912", "SHFE.au2006"], 5)  # 获取SHFE.au2006向SHFE.au1912对齐的K线

详细使用方法及说明请见 :py:meth:`~tqsdk.TqApi.get_kline_serial` 函数使用说明。

:py:meth:`~tqsdk.TqApi.get_kline_serial` 的返回值是一个 pandas.DataFrame, 包含以下列::

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

对于每个K线序列, 只需要调用一次 :py:meth:`~tqsdk.TqApi.get_kline_serial` . 如果需要监控数据更新, 可以使用 :py:meth:`~tqsdk.TqApi.wait_update` ::

    klines = api.get_kline_serial("SHFE.cu1812", 10)  # 获取SHFE.cu1812合约的10秒K线

    while api.wait_update():
        print(klines.iloc[-1])    # K线数据有任何变动时都会执行这行


如果只想在新K线出现时收到信号, 可以配合使用 :py:meth:`~tqsdk.TqApi.is_changing`::

    klines = api.get_kline_serial("SHFE.cu1812", 10)        # 获取SHFE.cu1812合约的10秒K线

    while api.wait_update():
        if api.is_changing(klines.iloc[-1], "datetime"):    # 判定最后一根K线的时间是否有变化
            print(klines.iloc[-1])                          # 当最后一根K线的时间有变(新K线生成)时才会执行到这里


Tick序列
----------------------------------------------------
:py:meth:`~tqsdk.TqApi.get_tick_serial` 函数获取指定合约的Tick序列数据::

    ticks = api.get_tick_serial("SHFE.cu1812")  # 获取SHFE.cu1812合约的Tick序列

:py:meth:`~tqsdk.TqApi.get_tick_serial` 的返回值是一个 pandas.DataFrame, 常见用法示例如下::

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

  关于 :py:meth:`~tqsdk.TqApi.wait_update` 和 :py:meth:`~tqsdk.TqApi.is_changing` 的详细说明, 请见 :ref:`framework`
