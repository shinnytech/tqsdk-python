#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'

from datetime import datetime, time, timedelta
from typing import Optional, Union

import numpy as np
from pandas import DataFrame

from tqsdk.api import TqApi
from tqsdk import utils
from tqsdk.datetime import _get_trading_timestamp, _get_trade_timestamp, _get_trading_day_from_timestamp
from tqsdk.rangeset import _rangeset_slice, _rangeset_head
from tqsdk.tradeable import TqAccount, TqKq, TqSim


def twap_table(api: TqApi, symbol: str, target_pos: int, duration: int, min_volume_each_step: int, max_volume_each_step: int,
         account: Optional[Union[TqAccount, TqKq, TqSim]] = None):
    """
    返回基于 twap 策略的计划任务时间表。下单需要配合 TargetPosScheduler 使用。

    Args:
        api (TqApi): TqApi实例，该task依托于指定api下单/撤单

        symbol (str): 拟下单的合约 symbol, 格式为 交易所代码.合约代码,  例如 "SHFE.cu1801"

        target_pos (int): 目标持仓手数

        duration (int): 算法执行的时长，以秒为单位，时长可以跨非交易时间段，但是不可以跨交易日
        * 设置为 60*10, 可以是 10:10～10:15 + 10:30~10:35

        min_volume_each_step (int): 调整持仓手数最小值，每步调整的持仓手数默认在最小和最大值中产生

        max_volume_each_step (int): 调整持仓手数最大值，每步调整的持仓手数默认在最小和最大值中产生

        account (TqAccount/TqKq/TqSim): [可选]指定发送下单指令的账户实例, 多账户模式下，该参数必须指定

    Returns:
        pandas.DataFrame: 本函数返回一个 pandas.DataFrame 实例. 表示一份计划任务时间表。每一行表示一项目标持仓任务，包含以下列:

            + interval: 当前这项任务的持续时间长度，单位为秒
            + target_pos: 当前这项任务的目标持仓
            + price: 当前这项任务的下单价格模式，支持 PASSIVE（排队价），ACTIVE（对价），None（不下单，表示暂停一段时间）

    Example1::

        from tqsdk import TqApi, TargetPosScheduler
        from tqsdk.algorithm import twap_table

        api = TqApi(auth="信易账户,用户密码")
        quote = api.get_quote("CZCE.MA109")

        # 设置twap任务参数
        time_table = twap_table(api, "CZCE.MA109", -100, 600, 1, 5)  # 目标持仓 -100 手，600s 内完成
        print(time_table.to_string())

        target_pos_sch = TargetPosScheduler(api, "CZCE.MA109", time_table)
        # 启动循环
        while not target_pos_sch.is_finished():
            api.wait_update()
        api.close()


    Example2::

        from tqsdk import TqApi, TargetPosScheduler
        from tqsdk.algorithm import twap_table

        api = TqApi(auth="信易账户,用户密码")
        quote = api.get_quote("CZCE.MA109")

        # 设置 twap 任务参数，
        time_table = twap_table(api, "CZCE.MA109", -100, 600, 1, 5)  # 目标持仓 -100 手，600s 内完成

        # 定制化调整 time_table，例如希望第一项任务延迟 10s 再开始下单
        # 可以在 time_table 的头部加一行
        time_table = pandas.concat([
            DataFrame([[10, 10, None]], columns=['interval', 'target_pos', 'price']),
            time_table
        ], ignore_index=True)

        target_pos_sch = TargetPosScheduler(api, "CZCE.MA109", time_table)
        while not target_pos_sch.is_finished():
            api.wait_update()

        # 获取 target_pos_sch 实例所有的成交列表
        print(target_pos_sch.trades_df)

        # 利用成交列表，您可以计算出策略的各种表现指标，例如：
        average_trade_price = sum(scheduler.trades_df['price'] * scheduler.trades_df['volume']) / sum(scheduler.trades_df['volume'])
        print("成交均价:", average_trade_price)
        api.close()

    """
    account = api._account._check_valid(account)
    if account is None:
        raise Exception(f"多账户模式下, 需要指定账户实例 account")
    min_volume_each_step = int(min_volume_each_step)
    max_volume_each_step = int(max_volume_each_step)
    if max_volume_each_step <= 0 or min_volume_each_step <= 0:
        raise Exception("请调整参数, min_volume_each_step、max_volume_each_step 必须是大于 0 的整数。")
    if min_volume_each_step > max_volume_each_step:
        raise Exception("请调整参数, min_volume_each_step 必须小于 max_volume_each_step。")

    pos = api.get_position(symbol, account)
    target_pos = int(target_pos)
    delta_pos = target_pos - pos.pos
    volume = abs(delta_pos)  # 总的下单手数

    # 得到有效的手数序列和时间间隔序列
    if volume < max_volume_each_step:
        interval_list, volume_list = [duration], [volume]
    else:
        volume_list = _gen_random_list(sum_val=volume, min_val=min_volume_each_step, max_val=max_volume_each_step)

        interval = int(duration / len(volume_list))
        if interval < 3:
            raise Exception("请调整参数, 每次下单时间间隔不能小于3s, 将单次下单手数阈值调大或者增长下单时间。")
        min_interval = int(max(3, interval - 2))
        max_interval = int(interval * 2 - max(3, interval - 2)) + 1
        interval_list = _gen_random_list(sum_val=duration, min_val=min_interval, max_val=max_interval,
                                         length=len(volume_list))

    time_table = DataFrame(columns=['interval', 'volume', 'price'])
    for index, volume in enumerate(volume_list):
        assert interval_list[index] >= 3
        active_interval = 2
        time_table = time_table.append([
            {"interval": interval_list[index] - active_interval, "volume": volume, "price": "PASSIVE"},
            {"interval": active_interval, "volume": 0, "price": "ACTIVE"}
        ], ignore_index=True)
    time_table['volume'] = time_table['volume'].mul(-1 if delta_pos < 0 else 1)
    time_table['target_pos'] = time_table['volume'].cumsum()
    time_table['target_pos'] = time_table['target_pos'].add(pos.pos)
    time_table.drop(columns=['volume'], inplace=True)
    time_table = time_table.astype({'target_pos': 'int64', 'interval': 'float64'})
    return time_table


def vwap_table(api: TqApi, symbol: str, target_pos: int, duration: float,
               account: Optional[Union[TqAccount, TqKq, TqSim]] = None):
    """
    返回基于 vwap 策略的计划任务时间表。下单需要配合 TargetPosScheduler 使用。

    调用 vwap_table 函数，根据以下逻辑生成 time_table：

    1. 根据 target_pos - 当前合约的净持仓，得到总的需要调整手数
    2. 请求 symbol 合约的 ``1min`` K 线
    3. 采样取用最近 10 日内，以合约当前行情时间的下一分钟为起点，每日 duration / 60 根 K 线, \
    例如当前合约时间为 14:35:35，那么采样是会使用 14:36:00 开始的分钟线 K 线
    4. 按日期分组，分别计算交易日内，每根 K 线成交量占总成交量的比例
    5. 计算最近 10 日内相同分钟内的成交量占比的算术平均数，将第 1 步得到的总调整手数按照得到的比例分配
    6. 每一分钟，前 58s 以追加价格下单，后 2s 以对价价格下单

    Args:
        api (TqApi): TqApi实例，该task依托于指定api下单/撤单

        symbol (str): 拟下单的合约 symbol, 格式为 交易所代码.合约代码,  例如 "SHFE.cu2201"

        target_pos (int): 目标持仓手数

        duration (int): 算法执行的时长，以秒为单位，必须是 60 的整数倍，时长可以跨非交易时间段，但是不可以跨交易日
        * 设置为 60*10, 可以是 10:10～10:15 + 10:30~10:35

        account (TqAccount/TqKq/TqSim): [可选]指定发送下单指令的账户实例, 多账户模式下，该参数必须指定

    Returns:
        pandas.DataFrame: 本函数返回一个 pandas.DataFrame 实例. 表示一份计划任务时间表。每一行表示一项目标持仓任务，包含以下列:

            + interval: 当前这项任务的持续时间长度，单位为秒
            + target_pos: 当前这项任务的目标持仓
            + price: 当前这项任务的下单价格模式，支持 PASSIVE（排队价），ACTIVE（对价），None（不下单，表示暂停一段时间）

    Example1::

        from tqsdk import TqApi, TargetPosScheduler
        from tqsdk.algorithm import vwap_table

        api = TqApi(auth="信易账户,用户密码")
        quote = api.get_quote("CZCE.MA109")

        # 设置 vwap 任务参数
        time_table = vwap_table(api, "CZCE.MA109", -100, 600)  # 目标持仓 -100 手，600s 内完成
        print(time_table.to_string())

        target_pos_sch = TargetPosScheduler(api, "CZCE.MA109", time_table)
        # 启动循环
        while not target_pos_sch.is_finished():
            api.wait_update()
        api.close()


    """
    account = api._account._check_valid(account)
    if account is None:
        raise Exception(f"多账户模式下, 需要指定账户实例 account")

    TIME_CELL = 60  # 等时长下单的时间单元, 单位: 秒
    HISTORY_DAY_LENGTH = 10  # 使用多少天的历史数据用来计算每个时间单元的下单手数

    if duration % TIME_CELL or duration < 60:
        raise Exception(f"duration {duration} 参数应该为 {TIME_CELL} 的整数倍")

    pos = api.get_position(symbol, account)
    target_pos = int(target_pos)
    delta_pos = target_pos - pos.pos
    target_volume = abs(delta_pos)  # 总的下单手数
    if target_volume == 0:
        return DataFrame(columns=['interval', 'target_pos', 'price'])

    # 获取 Kline
    klines = api.get_kline_serial(symbol, TIME_CELL, data_length=int(10 * 60 * 60 / TIME_CELL * HISTORY_DAY_LENGTH))
    klines["time"] = klines.datetime.apply(lambda x: datetime.fromtimestamp(x // 1000000000).time())  # k线时间
    klines["date"] = klines.datetime.apply(lambda x: datetime.fromtimestamp(_get_trading_day_from_timestamp(x) // 1000000000).date())  # k线交易日

    quote = api.get_quote(symbol)
    # 当前交易日完整的交易时间段
    trading_timestamp = _get_trading_timestamp(quote, quote.datetime)
    trading_timestamp_nano_range = trading_timestamp['night'] + trading_timestamp['day']  # 当前交易日完整的交易时间段
    # 当前时间 行情时间
    current_timestamp_nano = _get_trade_timestamp(quote.datetime, float('nan'))
    if not trading_timestamp_nano_range[0][0] <= current_timestamp_nano < trading_timestamp_nano_range[-1][1]:
        raise Exception("当前时间不在指定的交易时间段内")

    current_datetime = datetime.fromtimestamp(current_timestamp_nano//1000000000)
    # 下一分钟的开始时间
    next_datetime = current_datetime.replace(second=0) + timedelta(minutes=1)
    start_datetime_nano = int(next_datetime.timestamp()) * 1000000000
    r = _rangeset_head(_rangeset_slice(trading_timestamp_nano_range, start_datetime_nano), int(duration * 1e9))
    if not (r and trading_timestamp_nano_range[0][0] <= r[-1][-1] < trading_timestamp_nano_range[-1][1]):
        raise Exception("指定时间段超出当前交易日")

    start_datetime = datetime.fromtimestamp(start_datetime_nano // 1000000000)
    end_datetime = datetime.fromtimestamp((r[-1][-1] - 1) // 1000000000)
    time_slot_start = time(start_datetime.hour, start_datetime.minute)  # 计划交易时段起始时间点
    time_slot_end = time(end_datetime.hour, end_datetime.minute)  # 计划交易时段终点时间点
    if time_slot_end > time_slot_start:  # 判断是否类似 23:00:00 开始， 01:00:00 结束这样跨天的情况
        klines = klines[(klines["time"] >= time_slot_start) & (klines["time"] <= time_slot_end)]
    else:
        klines = klines[(klines["time"] >= time_slot_start) | (klines["time"] <= time_slot_end)]

    # 获取在预设交易时间段内的所有K线, 即时间位于 time_slot_start 到 time_slot_end 之间的数据
    need_date = klines['date'].drop_duplicates()[-HISTORY_DAY_LENGTH:]
    klines = klines[klines['date'].isin(need_date)]

    grouped_datetime = klines.groupby(['date', 'time'])['volume'].sum()
    # 计算每个交易日内的预设交易时间段内的成交量总和(level=0: 表示按第一级索引"data"来分组)后,将每根k线的成交量除以所在交易日内的总成交量,计算其所占比例
    volume_percent = grouped_datetime / grouped_datetime.groupby(level=0).sum()
    predicted_percent = volume_percent.groupby(level=1).mean()  # 将历史上相同时间单元的成交量占比使用算数平均计算出预测值

    # 计算每个时间单元的成交量预测值
    time_table = DataFrame(columns=['interval', 'volume', 'price'])
    volume_left = target_volume  # 剩余手数
    percent_left = 1  # 剩余百分比
    for index, value in predicted_percent.items():
        volume = round(target_volume * (value / percent_left))
        volume_left -= volume
        percent_left -= value
        time_table = time_table.append([
            {"interval": TIME_CELL - 2, "volume": volume, "price": "PASSIVE"},
            {"interval": 2, "volume": 0, "price": "ACTIVE"}
        ], ignore_index=True)

    time_table['volume'] = time_table['volume'].mul(np.sign(delta_pos))
    time_table['target_pos'] = time_table['volume'].cumsum()
    time_table['target_pos'] = time_table['target_pos'].add(pos.pos)
    time_table.drop(columns=['volume'], inplace=True)
    time_table = time_table.astype({'target_pos': 'int64', 'interval': 'float64'})
    return time_table


def _gen_random_list(sum_val: int, min_val: int, max_val: int, length: int = None):
    """
    生成随机列表，参数应该满足：min_val * length <= sum_val <= max_val * length
    :param int sum_val: 列表元素之和
    :param int min_val: 列表元素最小值
    :param int max_val: 列表元素最大值
    :param int length: 列表长度，如果没有指定，则返回的列表长度没有指定
    :return: 整型列表，满足 sum(list) = sum_val, len(list) == length, min_val < any_item(list) < max_val
    """
    if length is None:
        length = sum_val * 2 // (min_val + max_val)  # 先确定 ist 长度，interval 大小，再生成 volume_list 随机列表
        # 例如：sum = 16 min_val = 11 max_val = 15，不满足 min_val * length <= sum_val <= max_val * length
        assert min_val * length <= sum_val <= max_val * length + min_val
    else:
        assert min_val * length <= sum_val <= max_val * length

    result_list = [min_val for _ in range(length)]
    if sum(result_list) == sum_val:
        return result_list  # 全部最小值刚好满足，可以提前退出
    result_rest_value = sum_val - min_val * length  # 剩余可以填充的个数
    result_rest_position = (max_val - min_val) * length  # 剩余需要填充的位置个数
    if sum_val > max_val * length:
        result_list.append(0)
        result_rest_position += min_val
    result_rest_list = _gen_shuffle_list(result_rest_value, result_rest_position)
    for i in range(len(result_list)):
        start = (max_val - min_val) * i
        end = (max_val - min_val) * (i + 1) if start < (max_val - min_val) * length else result_rest_position
        result_list[i] += sum(result_rest_list[start:end])
    assert len(result_list) == length or len(result_list) == length + 1
    assert sum(result_list) == sum_val
    return result_list


def _gen_shuffle_list(x: int, n: int):
    """从 n 个位置中随机选中 x 个"""
    assert x <= n
    result_list = [1 for _ in range(x)] + [0 for _ in range(n - x)]
    utils.RD.shuffle(result_list)
    return result_list
