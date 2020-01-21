.. _ta:

技术指标与序列计算函数
====================================================

技术指标
----------------------------------------------------
tqsdk.ta 模块中包含了大量技术指标. 每个技术指标是一个函数, 函数名为全大写, 第一参数总是K线序列, 以pandas.DataFrame格式返回计算结果. 以MACD为例::

    from tqsdk.ta import MACD

    klines = api.get_kline_serial("SHFE.cu1812", 60)   # 提取SHFE.cu1812的分钟线
    result = MACD(klines, 12, 26, 9)                        # 计算MACD指标
    print(result["diff"])                                   # MACD指标中的diff序列

tqsdk.ta 中目前提供的技术指标详表，请见 :ref:`tqsdk.ta`


序列计算函数
----------------------------------------------------
tqsdk.tafunc 模块中包含了一批序列计算函数. 它们是构成技术指标的基础. 在某些情况下, 您也可以直接使用这些序列计算函数以获取更大的灵活性.

例如, 技术指标MA(均线)总是按K线的收盘价来计算, 如果你需要计算最高价的均线, 可以使用ma函数::

    from tqsdk.tafunc import ma

    klines = api.get_kline_serial("SHFE.cu1812", 60)   # 提取SHFE.cu1812的分钟线
    result = ma(klines.high, 9)                        # 按K线的最高价序列做9分钟的移动平均
    print(result)                                      # 移动平均结果

tqsdk.tafunc 中目前提供的序列计算函数详表，请见 :ref:`tqsdk.tafunc`

