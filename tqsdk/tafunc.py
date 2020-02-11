#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

"""
tqsdk.tafunc 模块包含了一批用于技术指标计算的函数
(函数基本保持 参数为pandas.Series类型则返回值为pandas.Series类型)
"""

import datetime
import pandas as pd
import numpy as np


def ref(series, n):
    """
    简单移动: 求series序列位移n个周期的结果

        注意: 当n为0, 函数返回原序列; 当n为有效值但当前的series序列元素个数不足 n + 1 个, 函数返回 NaN 序列

    Args:
        series (pandas.Series): 数据序列

        n (int): 位移周期

    Returns:
        pandas.Series: 位移后的序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        pre_close = tafunc.ref(klines.close, 1)  # 将收盘价序列右移一位, 得到昨收盘序列
        change = klines.close - pre_close        # 收盘价序列 - 昨收盘序列, 得到涨跌序列
        print(list(change))
    """
    m = series.shift(n)
    return m


def std(series, n):
    """
    标准差: 求series序列每n个周期的标准差

        注意: n为0的情况下, 或当n为有效值但当前的series序列元素个数不足n个, 函数返回 NaN 序列

    Args:
        series (pandas.Series): 数据序列

        n (int): 标准差的周期

    Returns:
        pandas.Series: 标准差序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        std = tafunc.std(klines.close, 5)  # 收盘价序列每5项计算一个标准差
        print(list(std))
    """
    m = series.rolling(n).std()
    return m


def ma(series, n):
    """
    简单移动平均线: 求series序列n周期的简单移动平均

        计算公式:
        ma(x, 5) = (x(1) + x(2) + x(3) + x(4) + x(5)) / 5

        注意:
        1. 简单移动平均线将设定周期内的值取平均值, 其中各元素的权重都相等
        2. n为0的情况下, 或当n为有效值但当前的series序列元素个数不足n个, 函数返回 NaN 序列

    Args:
        series (pandas.Series): 数据序列

        n (int): 周期

    Returns:
        pandas.Series: 简单移动平均值序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        ma = tafunc.ma(klines.close, 5)
        print(list(ma))
    """
    ma_data = series.rolling(n).mean()
    return ma_data


def sma(series, n, m):
    """
    扩展指数加权移动平均: 求series序列n周期的扩展指数加权移动平均
    
        计算公式:
        sma(x, n, m) = sma(x, n, m).shift(1) * (n - m) / n + x(n) * m / n
        
        注意: n必须大于m

    Args:
        series (pandas.Series): 数据序列
        
        n (int): 周期
        
        m (int): 权重

    Returns:
        pandas.Series: 扩展指数加权移动平均序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        sma = tafunc.sma(klines.close, 5, 2)  # 收盘价序列每5项计算一个扩展指数加权移动平均值
        print(list(sma))
    """
    sma_data = series.ewm(alpha=m / n, adjust=False).mean()
    return sma_data


def ema(series, n):
    """
    指数加权移动平均线: 求series序列n周期的指数加权移动平均

        计算公式:
            ema(x, n) = 2 * x / (n + 1) + (n - 1) * ema(x, n).shift(1) / (n + 1)

        注意:
            1. n 需大于等于1
            2. 对距离当前较近的k线赋予了较大的权重

    Args:
        series (pandas.Series): 数据序列

        n (int): 周期

    Returns:
        pandas.Series: 指数加权移动平均线序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        ema = tafunc.ema(klines.close, 5)
        print(list(ema))
    """
    ema_data = series.ewm(span=n, adjust=False).mean()
    return ema_data


def ema2(series, n):
    """
    线性加权移动平均: 求series值的n周期线性加权移动平均 (也称WMA)

        计算公式:
            ema2(x, n) = [n * x(0) + (n - 1) * x(1) + (x - 2) * x(2) + ... + 1 * x(n - 1)] / [n + (n - 1) + (n - 2) + ... + 1]

        注意: 当n为有效值但当前的series序列元素个数不足n个, 函数返回 NaN 序列

    Args:
        series (pandas.Series): 数据序列

        n (int): 周期

    Returns:
        pandas.Series: 线性加权移动平均线序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        ema2 = tafunc.ema2(klines.close, 5)  # 求收盘价在5个周期的线性加权移动平均值
        print(list(ema2))
    """
    weights = list(i for i in range(1, n + 1))  # 对应的权值列表

    def average(elements):
        return np.average(elements, weights=weights)

    ema2 = series.rolling(window=n).apply(average, raw=True)
    return ema2


def crossup(a, b):
    """
    向上穿越: 表当a从下方向上穿过b, 成立返回1, 否则返回0

    Args:
        a (pandas.Series): 数据序列1

        b (pandas.Series): 数据序列2

    Returns:
        pandas.Series: 上穿标志序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        crossup = tafunc.crossup(tafunc.ma(klines.close, 5), tafunc.ma(klines.close, 10))
        print(list(crossup))
    """
    crossup_data = pd.Series(np.where((a > b) & (a.shift(1) <= b.shift(1)), 1, 0))
    return crossup_data


def crossdown(a, b):
    """
    向下穿越: 表示当a从上方向下穿b，成立返回1, 否则返回0

    Args:
        a (pandas.Series): 数据序列1

        b (pandas.Series): 数据序列2

    Returns:
        pandas.Series: 下穿标志序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc
        
        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        crossdown = tafunc.crossdown(tafunc.ma(klines.close, 5), tafunc.ma(klines.close, 10))
        print(list(crossdown))
    """
    crossdown_data = pd.Series(np.where((a < b) & (a.shift(1) >= b.shift(1)), 1, 0))
    return crossdown_data


def count(cond, n):
    """
    统计n周期中满足cond条件的个数

        注意: 如果n为0, 则从第一个有效值开始统计

    Args:
        cond (array_like): 条件

        n (int): 周期

    Returns:
        pandas.Series: 统计值序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        # 统计从申请到的行情数据以来到当前这段时间内, 5周期均线上穿10周期均线的次数:
        count = tafunc.count(tafunc.crossup(tafunc.ma(klines.close, 5), tafunc.ma(klines.close, 10)), 0)
        print(list(count))
    """
    if n == 0:  # 从第一个有效值开始统计
        count_data = pd.Series(np.where(cond, 1, 0).cumsum())
    else:  # 统计每个n周期
        count_data = pd.Series(pd.Series(np.where(cond, 1, 0)).rolling(n).sum())
    return count_data


def trma(series, n):
    """
    三角移动平均: 求series的n周期三角移动平均值

        计算方法:
            三角移动平均线公式, 是采用算数移动平均, 并且对第一个移动平均线再一次应用算数移动平均

        注意: n为0的情况下, 或当n为有效值但当前的series序列元素个数不足n个, 函数返回 NaN 序列

    Args:
        series (pandas.Series): 数据序列

        n (int): 周期

    Returns:
        pandas.Series: 三角移动平均值序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        trma = tafunc.trma(klines.close, 10)
        print(list(trma))
    """
    if n % 2 == 0:
        n1 = int(n / 2)
        n2 = int(n / 2 + 1)
    else:
        n1 = n2 = int((n + 1) / 2)
    ma_half = ma(series, n1)
    trma_data = ma(ma_half, n2)
    return trma_data


def harmean(series, n):
    """
    调和平均值: 求series在n个周期内的调和平均值

        计算方法:
            harmean(x, 5) = 1 / [(1 / x(1) + 1 / x(2) + 1 / x(3) + 1 / x(4) + 1 / x(5)) / 5]

        注意:
        1. 调和平均值与倒数的简单平均值互为倒数
        2. 当n为0, 或当n为有效值但当前的series序列元素个数不足n个, 函数返回 NaN 序列

    Args:
        series (pandas.Series): 数据序列

        n (int): 周期

    Returns:
        pandas.Series: 调和平均值序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        harmean = tafunc.harmean(klines.close, 5)  # 求5周期收盘价的调和平均值
        print(list(harmean))
    """
    harmean_data = n / ((1 / series).rolling(n).sum())
    return harmean_data


def numpow(series, n, m):
    """
    自然数幂方和

        计算方法:
            numpow(x, n, m) = n ^ m * x + (n - 1) ^ m * x.shift(1) + (n - 2) ^ m * x.shift(2) + ... + 2 ^ m * x.shift(n - 2) + 1 ^ m * x.shift(n - 1)

        注意: 当n为有效值但当前的series序列元素个数不足n个, 函数返回 NaN 序列

    Args:
        series (pandas.Series): 数据序列

        n (int): 自然数

        m (int): 实数

    Returns:
        pandas.Series: 幂方和序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        numpow = tafunc.numpow(klines.close, 5, 2)
        print(list(numpow))
    """
    numpow_data = sum((n - i) ** m * series.shift(i) for i in range(n))
    return numpow_data


def abs(series):
    """
    获取series的绝对值

        注意: 正数的绝对值是它本身, 负数的绝对值是它的相反数, 0的绝对值还是0

    Args:
        series (pandas.Series): 数据序列

    Returns:
        pandas.Series: 绝对值序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        abs = tafunc.abs(klines.close)
        print(list(abs))
    """
    abs_data = pd.Series(np.absolute(series))
    return abs_data


def min(series1, series2):
    """
    获取series1和series2中的最小值

    Args:
        series1 (pandas.Series): 数据序列1

        series2 (pandas.Series): 数据序列2

    Returns:
        pandas.Series: 最小值序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        min = tafunc.min(klines.close, klines.open)
        print(list(min))
    """
    min_data = np.minimum(series1, series2)
    return min_data


def max(series1, series2):
    """
    获取series1和series2中的最大值

    Args:
        series1 (pandas.Series): 数据序列1

        series2 (pandas.Series): 数据序列2

    Returns:
        pandas.Series: 最大值序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        max = tafunc.max(klines.close, klines.open)
        print(list(max))
    """
    max_data = np.maximum(series1, series2)
    return max_data


def median(series, n):
    """
    中位数: 求series在n个周期内居于中间的数值
    
        注意:
            1. 当n为有效值但当前的series序列元素个数不足n个, 函数返回 NaN 序列
            2. 对n个周期内所有series排序后, 若n为奇数, 则选择第(n + 1) / 2个为中位数, 若n为偶数, 则中位数是(n / 2)以及(n / 2 + 1)的平均数

    Args:
        series (pandas.Series): 数据序列

        n (int): 周期

    Returns:
        pandas.Series: 中位数序列

    Example::

        例1:
            # 假设最近3日的收盘价为2727, 2754, 2748, 那么当前 median(df["close"], 3) 的返回值是2748
            median3 = tafunc.median(df["close"], 3)

        例2:
            # 假设最近4日的开盘价为2752, 2743, 2730, 2728, 那么当前 median(df["open"], 4) 的返回值是2736.5
            median4 = tafunc.median(df["open"], 4)
    """
    median_data = series.rolling(n).median()
    return median_data


def exist(cond, n):
    """
    判断n个周期内, 是否有满足cond的条件, 若满足则值为1, 不满足为0

    Args:
        cond (array_like): 条件

        n (int): 周期

    Returns:
        pandas.Series: 判断结果序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        # 判断4个周期中是否存在收盘价大于前一个周期的最高价, 存在返回1, 不存在则返回0
        exist = tafunc.exist(klines.close > klines.high.shift(1), 4)
        print(list(exist))
    """
    exist_data = pd.Series(np.where(pd.Series(np.where(cond, 1, 0)).rolling(n).sum() > 0, 1, 0))
    return exist_data


def every(cond, n):
    """
    判断n个周期内, 是否一直满足cond条件, 若满足则值为1, 不满足为0

    Args:
        cond (array_like): 条件

        n (int): 周期

    Returns:
        pandas.Series: 判断结果序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        # 判断在4周期内, 3周期的简单移动平均是否一直大于5周期的简单移动平均
        every = tafunc.every(tafunc.ma(klines.close, 3) > tafunc.ma(klines.close, 5), 4)
        print(list(every))
    """
    every_data = pd.Series(np.where(pd.Series(np.where(cond, 1, 0)).rolling(n).sum() == n, 1, 0))
    return every_data


def hhv(series, n):
    """
    求series在n个周期内的最高值

        注意: n为0的情况下, 或当n为有效值但当前的series序列元素个数不足n个, 函数返回 NaN 序列

    Args:
        series (pandas.Series): 数据序列

        n (int): 周期

    Returns:
        pandas.Series: 最高值序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        hhv = tafunc.hhv(klines.high, 4)  # 求4个周期最高价的最大值, 即4周期高点(包含当前k线)
        print(list(hhv))
    """
    hhv_data = series.rolling(n).max()
    return hhv_data


def llv(series, n):
    """
    求在n个周期内的最小值

        注意: n为0的情况下, 或当n为有效值但当前的series序列元素个数不足n个, 函数返回 NaN 序列

    Args:
        series (pandas.Series): 数据序列

        n (int): 周期

    Returns:
        pandas.Series: 最小值序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        llv = tafunc.llv(klines.low, 5)  # 求5根k线最低点(包含当前k线)
        print(list(llv))
    """
    llv_data = series.rolling(n).min()
    return llv_data


def avedev(series, n):
    """
    平均绝对偏差: 求series在n周期内的平均绝对偏差

        算法:
            计算avedev(df["close"],3)在最近一根K线上的值:
            (abs(df["close"] - (df["close"] + df["close"].shift(1) + df["close"].shift(2)) / 3) + abs(
            df["close"].shift(1) - (df["close"] + df["close"].shift(1) + df["close"].shift(2)) / 3) + abs(
            df["close"].shift(2) - (df["close"] + df["close"].shift(1) + df["close"].shift(2)) / 3)) / 3

        注意: n为0的情况下, 或当n为有效值但当前的series序列元素个数不足n个, 函数返回 NaN 序列

    Args:
        series (pandas.Series): 数据序列

        n (int): 周期

    Returns:
        pandas.Series: 平均绝对偏差序列

    Example::

        from tqsdk import TqApi, TqSim, tafunc

        api = TqApi(TqSim())
        klines = api.get_kline_serial("CFFEX.IF1908", 24 * 60 * 60)
        # 计算收盘价在5周期内的平均绝对偏差, 表示5个周期内每个周期的收盘价与5周期收盘价的平均值的差的绝对值的平均值, 判断收盘价与其均值的偏离程度:
        avedev = tafunc.avedev(klines.close, 5)
        print(list(avedev))
    """

    def mad(x):
        return np.fabs(x - x.mean()).mean()

    avedev_data = series.rolling(window=n).apply(mad, raw=True)
    return avedev_data


def _to_ns_timestamp(input_time):
    """
    辅助函数: 将传入的时间转换为int类型的纳秒级时间戳

    Args:
    input_time (str/ int/ float/ datetime.datetime): 需要转换的时间:
        * str: str 类型的时间，如Quote行情时间的datetime字段 (eg. 2019-10-14 14:26:01.000000)

        * int: int 类型纳秒级或秒级时间戳

        * float: float 类型纳秒级或秒级时间戳，如K线或tick的datetime字段 (eg. 1.57103449e+18)

        * datetime.datetime: datetime 模块中 datetime 类型

    Returns:
        int : int 类型纳秒级时间戳
    """

    if type(input_time) in {int, float, np.float64, np.float32, np.int64, np.int32}:  # 时间戳
        if input_time > 2 ** 32:  # 纳秒( 将 > 2*32数值归为纳秒级)
            return int(input_time)
        else:  # 秒
            return int(input_time * 1e9)

    elif isinstance(input_time, str):  # str 类型时间
        d = datetime.datetime.strptime(input_time, "%Y-%m-%d %H:%M:%S.%f")
        d = int(d.timestamp() * 1e9)
        return d
    elif isinstance(input_time, datetime.datetime):  # datetime 类型时间
        d = int(input_time.timestamp() * 1e9)
        return d
    else:
        raise TypeError("暂不支持此类型的转换")


def time_to_ns_timestamp(input_time):
    """
    将传入的时间转换为int类型的纳秒级时间戳

    Args:
        input_time (str/ int/ float/ datetime.datetime): 需要转换的时间:
            * str: str 类型的时间，如Quote行情时间的datetime字段 (eg. 2019-10-14 14:26:01.000000)

            * int: int 类型的纳秒级或秒级时间戳

            * float: float 类型的纳秒级或秒级时间戳，如K线或tick的datetime字段 (eg. 1.57103449e+18)

            * datetime.datetime: datetime 模块中的 datetime 类型时间

    Returns:
        int : int 类型的纳秒级时间戳

    Example::

        from tqsdk.tafunc import time_to_ns_timestamp
        print(time_to_ns_timestamp("2019-10-14 14:26:01.000000"))  # 将%Y-%m-%d %H:%M:%S.%f 格式的str类型转为纳秒时间戳
        print(time_to_ns_timestamp(1571103122))  # 将秒级转为纳秒时间戳
        print(time_to_ns_timestamp(datetime.datetime(2019, 10, 14, 14, 26, 1)))  # 将datetime.datetime时间转为纳秒时间戳
    """
    return _to_ns_timestamp(input_time)


def time_to_s_timestamp(input_time):
    """
    将传入的时间转换为int类型的秒级时间戳

    Args:
        input_time (str/ int/ float/ datetime.datetime): 需要转换的时间:
            * str: str 类型的时间，如Quote行情时间的datetime字段 (eg. 2019-10-14 14:26:01.000000)

            * int: int 类型的纳秒级或秒级时间戳

            * float: float 类型的纳秒级或秒级时间戳，如K线或tick的datetime字段 (eg. 1.57103449e+18)

            * datetime.datetime: datetime 模块中的 datetime 类型时间

    Returns:
        int : int类型的秒级时间戳

    Example::

        from tqsdk.tafunc import time_to_s_timestamp
        print(time_to_s_timestamp(1.57103449e+18))  # 将纳秒级时间戳转为秒级时间戳
        print(time_to_s_timestamp("2019-10-14 14:26:01.000000"))  # 将%Y-%m-%d %H:%M:%S.%f 格式的str类型时间转为秒级时间戳
        print(time_to_s_timestamp(datetime.datetime(2019, 10, 14, 14, 26, 1)))  # 将datetime.datetime时间转为秒时间戳
    """
    return int(_to_ns_timestamp(input_time) / 1e9)


def time_to_str(input_time):
    """
    将传入的时间转换为 %Y-%m-%d %H:%M:%S.%f 格式的 str 类型

    Args:
        input_time (int/ float/ datetime.datetime): 需要转换的时间:

            * int: int 类型的纳秒级或秒级时间戳

            * float: float 类型的纳秒级或秒级时间戳，如K线或tick的datetime字段 (eg. 1.57103449e+18)

            * datetime.datetime: datetime 模块中的 datetime 类型时间

    Returns:
        str : %Y-%m-%d %H:%M:%S.%f 格式的 str 类型时间

    Example::

        from tqsdk.tafunc import time_to_str
        print(time_to_str(1.57103449e+18))  # 将纳秒级时间戳转为%Y-%m-%d %H:%M:%S.%f 格式的str类型时间
        print(time_to_str(1571103122))  # 将秒级时间戳转为%Y-%m-%d %H:%M:%S.%f 格式的str类型时间
        print(time_to_str(datetime.datetime(2019, 10, 14, 14, 26, 1)))  # 将datetime.datetime时间转为%Y-%m-%d %H:%M:%S.%f 格式的str类型时间
    """
    # 转为秒级时间戳
    ts = _to_ns_timestamp(input_time) / 1e9
    # 转为 %Y-%m-%d %H:%M:%S.%f 格式的 str 类型时间
    dt = datetime.datetime.fromtimestamp(ts)
    dt = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    return dt


def time_to_datetime(input_time):
    """
    将传入的时间转换为 datetime.datetime 类型

    Args:
        input_time (int/ float/ str): 需要转换的时间:

            * int: int 类型的纳秒级或秒级时间戳

            * float: float 类型的纳秒级或秒级时间戳，如K线或tick的datetime字段 (eg. 1.57103449e+18)

            * str: str 类型的时间，如Quote行情时间的 datetime 字段 (eg. 2019-10-14 14:26:01.000000)

    Returns:
        datetime.datetime : datetime 模块中的 datetime 类型时间

    Example::

        from tqsdk.tafunc import time_to_datetime
        print(time_to_datetime(1.57103449e+18))  # 将纳秒级时间戳转为datetime.datetime时间
        print(time_to_datetime(1571103122))  # 将秒级时间戳转为datetime.datetime时间
        print(time_to_datetime("2019-10-14 14:26:01.000000"))  # 将%Y-%m-%d %H:%M:%S.%f 格式的str类型时间转为datetime.datetime时间
    """
    # 转为秒级时间戳
    ts = _to_ns_timestamp(input_time) / 1e9
    # 转为datetime.datetime类型
    dt = datetime.datetime.fromtimestamp(ts)
    return dt


def barlast(cond):
    """
    返回一个序列，其中每个值表示从上一次条件成立到当前的周期数
    注：
        如果从cond序列第一个值到某个位置之间没有True，则此位置的返回值为 -1；
        条件成立的位置上的返回值为0。


    Args:
        cond (pandas.Series): 条件序列(序列中的值需为 True 或 False)

    Returns:
        pandas.Series : 周期数序列（其长度和 cond 相同；最后一个值即为最后一次条件成立到最新一个数据的周期数）

    Example::

        from tqsdk import TqApi
        from tqsdk.tafunc import barlast

        api = TqApi()
        klines = api.get_kline_serial("SHFE.cu1912", 60)
        # print(list(klines.close))
        # print(list(klines.open))
        # print(list(klines.close > klines.open))
        n = barlast(klines.close > klines.open)  # 获取周期数序列
        print(list(n))
        print(n.iloc[-1])  # 获取最后一根k线到上一次满足 "收盘价大于开盘价" 条件的k线的周期数
        api.close()

    """
    cond = cond.to_numpy()
    v = np.array(~cond, dtype=np.int)
    c = np.cumsum(v)
    x = c[cond]
    d = np.diff(np.concatenate(([0], x)))
    if len(d) == 0:  # 如果cond长度为0或无True
        return pd.Series([-1] * len(cond))
    v[cond] = -d
    r = np.cumsum(v)
    r[:x[0]] = -1
    return pd.Series(r)
