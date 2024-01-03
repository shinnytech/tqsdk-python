#!/usr/bin/env python
#  -*- coding: utf-8 -*-
"""
包含有关时间处理的功能函数
"""

__author__ = 'limin'

import datetime
import time
from typing import Union

# 北京时间时区 CST (China Standard Time)
_cst_tz = datetime.timezone(datetime.timedelta(hours=8))


def _cst_now():
    """返回当前北京时间 datetime.datetime 类型"""
    return datetime.datetime.now(tz=_cst_tz)


def _convert_to_cst_datetime(user_dt: Union[datetime.date, datetime.datetime]):
    # 将用户输入的时间转换为东八区时间
    if isinstance(user_dt, datetime.datetime):
        if user_dt.tzinfo == _cst_tz:
            return user_dt
        return user_dt.replace(tzinfo=_cst_tz) if user_dt.tzinfo is None else user_dt.astimezone(tz=_cst_tz)
    else:
        return datetime.datetime(user_dt.year, user_dt.month, user_dt.day, tzinfo=_cst_tz)


def _convert_user_input_to_nano(start_dt: Union[datetime.date, datetime.datetime],
                                end_dt: Union[datetime.date, datetime.datetime]) -> (int, int):
    # 将用户输入的时间转换为对应交易时间段的纳秒时间戳
    if isinstance(start_dt, datetime.datetime):
        start_nano = _datetime_to_timestamp_nano(_convert_to_cst_datetime(start_dt))
    elif isinstance(start_dt, datetime.date):
        start_nano = _get_trading_day_start_time(_datetime_to_timestamp_nano(_convert_to_cst_datetime(start_dt)))
    else:
        raise Exception(f"start_dt 参数类型 {type(start_dt)} 错误, 只支持 datetime / date 类型，请检查是否正确")
    if isinstance(end_dt, datetime.datetime):
        end_nano = _datetime_to_timestamp_nano(_convert_to_cst_datetime(end_dt))
    elif isinstance(end_dt, datetime.date):
        end_nano = _get_trading_day_end_time(_datetime_to_timestamp_nano(_convert_to_cst_datetime(end_dt)))
    else:
        raise Exception(f"end_dt 参数类型 {type(end_dt)} 错误, 只支持 datetime / date 类型，请检查是否正确")
    return start_nano, end_nano


def _datetime_to_timestamp_nano(dt: datetime.datetime) -> int:
    # tqsdk 内部时间必须为东八区时间
    if dt.tzinfo != _cst_tz:
        dt = dt.replace(tzinfo=_cst_tz) if dt.tzinfo is None else dt.astimezone(tz=_cst_tz)
    # timestamp() 返回值精度为 microsecond，直接乘以 1e9 可能有精度问题
    return int(dt.timestamp() * 1000000) * 1000


def _timestamp_nano_to_datetime(nano: int) -> datetime.datetime:
    return datetime.datetime.fromtimestamp((nano // 1000) / 1000000, tz=_cst_tz)


def _timestamp_nano_to_str(nano: int, fmt="%Y-%m-%d %H:%M:%S.%f") -> str:
    return datetime.datetime.fromtimestamp((nano // 1000) / 1000000, tz=_cst_tz).strftime(fmt)


def _str_to_timestamp_nano(current_datetime: str, fmt="%Y-%m-%d %H:%M:%S.%f") -> int:
    return _datetime_to_timestamp_nano(datetime.datetime.strptime(current_datetime, fmt))


def _get_trading_day_start_time(trading_day):
    """给定交易日, 获得交易日起始时间"""
    begin_mark = 631123200000000000  # 1990-01-01
    start_time = trading_day - 21600000000000  # 6小时
    week_day = (start_time - begin_mark) // 86400000000000 % 7
    if week_day >= 5:
        start_time -= 86400000000000 * (week_day - 4)
    return start_time


def _get_trading_day_end_time(trading_day):
    """给定交易日, 获得交易日结束时间"""
    return trading_day + 64799999999999  # 18小时


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


def _get_trading_timestamp(quote, current_datetime: str):
    """ 将 quote 在 current_datetime 所在交易日的所有可交易时间段转换为纳秒时间戳(tqsdk内部使用的时间戳统一为纳秒)并返回 """
    # 获取当前交易日时间戳
    current_trading_day_timestamp = _get_trading_day_from_timestamp(_str_to_timestamp_nano(current_datetime))
    # 获取上一交易日时间戳
    last_trading_day_timestamp = _get_trading_day_from_timestamp(
        _get_trading_day_start_time(current_trading_day_timestamp) - 1)
    trading_timestamp = {
        "day": _get_period_timestamp(current_trading_day_timestamp, quote["trading_time"].get("day", [])),
        "night": _get_period_timestamp(last_trading_day_timestamp, quote["trading_time"].get("night", []))
    }
    return trading_timestamp


def _get_period_timestamp(real_date_timestamp, period_str):
    """
    real_date_timestamp：period_str 所在真实日期的纳秒时间戳（如 period_str 为周一(周二)的夜盘,则real_date_timestamp为上周五(周一)的日期; period_str 为周一的白盘,则real_date_timestamp为周一的日期）
    period_str: quote["trading_time"]["day"] or quote["trading_time"]["night"]
    """
    period_timestamp = []
    for duration in period_str:  # 对于白盘（或夜盘）中的每一个可交易时间段
        start = [int(i) for i in duration[0].split(":")]  # 交易时间段起始点
        end = [int(i) for i in duration[1].split(":")]  # 交易时间段结束点
        period_timestamp.append([real_date_timestamp + (start[0] * 3600 + start[1] * 60 + start[2]) * 1000000000,
                                 real_date_timestamp + (end[0] * 3600 + end[1] * 60 + end[2]) * 1000000000])
    return period_timestamp


def _is_in_trading_time(quote, current_datetime, local_time_record):
    """ 判断是否在可交易时间段内，需在quote已收到行情后调用本函数"""
    # 只在需要用到可交易时间段时(即本函数中)才调用_get_trading_timestamp()
    trading_timestamp = _get_trading_timestamp(quote, current_datetime)
    now_ns_timestamp = _get_trade_timestamp(current_datetime, local_time_record)  # 当前预估交易所纳秒时间戳
    # 判断当前交易所时间（估计值）是否在交易时间段内
    for v in trading_timestamp.values():
        for period in v:
            if period[0] <= now_ns_timestamp < period[1]:
                return True
    return False


def _get_trade_timestamp(current_datetime, local_time_record):
    # 根据最新行情时间获取模拟的(预估的)当前交易所纳秒时间戳（tqsdk内部使用的时间戳统一为纳秒）
    # 如果local_time_record为nan，則不加时间差
    cur_nano = _str_to_timestamp_nano(current_datetime)
    mock_delay_nano = 0 if local_time_record != local_time_record else int((time.time() - local_time_record) * 1e6) * 1000
    return cur_nano + mock_delay_nano


def _get_expire_rest_days(expire_dt, current_dt):
    """
    获取当前时间到下市时间之间的天数
    expire_dt, current_dt 都以 s 为单位
    """
    delta = datetime.datetime.fromtimestamp(expire_dt, tz=_cst_tz).date() - datetime.datetime.fromtimestamp(current_dt, tz=_cst_tz).date()
    return delta.days
