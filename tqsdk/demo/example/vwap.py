#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

'''
Volume Weighted Average Price策略 (难度：高级)
参考: https://www.shinnytech.com/blog/vwap
注: 该示例策略仅用于功能示范, 实盘时请根据自己的策略/经验进行修改
'''

import datetime
from tqsdk import TqApi, TqAuth, TargetPosTask

TIME_CELL = 5 * 60  # 等时长下单的时间单元, 单位: 秒
TARGET_VOLUME = 300  # 目标交易手数 (>0: 多头, <0: 空头)
SYMBOL = "DCE.jd2001"  # 交易合约代码
HISTORY_DAY_LENGTH = 20  # 使用多少天的历史数据用来计算每个时间单元的下单手数
START_HOUR, START_MINUTE = 9, 35  # 计划交易时段起始时间点
END_HOUR, END_MINUTE = 10, 50  # 计划交易时段终点时间点

api = TqApi(auth=TqAuth("信易账户", "账户密码"))
print("策略开始运行")
# 根据 HISTORY_DAY_LENGTH 推算出需要订阅的历史数据长度, 需要注意history_day_length与time_cell的比例关系以避免超过订阅限制
time_slot_start = datetime.time(START_HOUR, START_MINUTE)  # 计划交易时段起始时间点
time_slot_end = datetime.time(END_HOUR, END_MINUTE)  # 计划交易时段终点时间点
klines = api.get_kline_serial(SYMBOL, TIME_CELL, data_length=int(10 * 60 * 60 / TIME_CELL * HISTORY_DAY_LENGTH))
target_pos = TargetPosTask(api, SYMBOL)
position = api.get_position(SYMBOL)  # 持仓信息


def get_kline_time(kline_datetime):
    """获取k线的时间(不包含日期)"""
    kline_time = datetime.datetime.fromtimestamp(kline_datetime // 1000000000).time()  # 每根k线的时间
    return kline_time


def get_market_day(kline_datetime):
    """获取k线所对应的交易日"""
    kline_dt = datetime.datetime.fromtimestamp(kline_datetime // 1000000000)  # 每根k线的日期和时间
    if kline_dt.hour >= 18:  # 当天18点以后: 移到下一个交易日
        kline_dt = kline_dt + datetime.timedelta(days=1)
    while kline_dt.weekday() >= 5:  # 是周六或周日,移到周一
        kline_dt = kline_dt + datetime.timedelta(days=1)
    return kline_dt.date()


# 添加辅助列: time及date, 分别为K线时间的时:分:秒和其所属的交易日
klines["time"] = klines.datetime.apply(lambda x: get_kline_time(x))
klines["date"] = klines.datetime.apply(lambda x: get_market_day(x))

# 获取在预设交易时间段内的所有K线, 即时间位于 time_slot_start 到 time_slot_end 之间的数据
if time_slot_end > time_slot_start:  # 判断是否类似 23:00:00 开始， 01:00:00 结束这样跨天的情况
    klines = klines[(klines["time"] >= time_slot_start) & (klines["time"] <= time_slot_end)]
else:
    klines = klines[(klines["time"] >= time_slot_start) | (klines["time"] <= time_slot_end)]

# 由于可能有节假日导致部分天并没有填满整个预设交易时间段
# 因此去除缺失部分交易时段的日期(即剩下的每个日期都包含预设的交易时间段内所需的全部时间单元)
date_cnt = klines["date"].value_counts()
max_num = date_cnt.max()  # 所有日期中最完整的交易时段长度
need_date = date_cnt[date_cnt == max_num].sort_index().index[-HISTORY_DAY_LENGTH - 1:-1]  # 获取今天以前的预设数目个交易日的日期
df = klines[klines["date"].isin(need_date)]  # 最终用来计算的k线数据

# 计算每个时间单元的成交量占比, 并使用算数平均计算出预测值
datetime_grouped = df.groupby(['date', 'time'])['volume'].sum()  # 将K线的volume按照date、time建立多重索引分组
# 计算每个交易日内的预设交易时间段内的成交量总和(level=0: 表示按第一级索引"data"来分组)后,将每根k线的成交量除以所在交易日内的总成交量,计算其所占比例
volume_percent = datetime_grouped / datetime_grouped.groupby(level=0).sum()
predicted_percent = volume_percent.groupby(level=1).mean()  # 将历史上相同时间单元的成交量占比使用算数平均计算出预测值
print("各时间单元成交量占比: %s" % predicted_percent)

# 计算每个时间单元的成交量预测值
predicted_volume = {}  # 记录每个时间单元需调整的持仓量
percentage_left = 1  # 剩余比例
volume_left = TARGET_VOLUME  # 剩余手数
for index, value in predicted_percent.items():
    volume = round(volume_left * (value / percentage_left))
    predicted_volume[index] = volume
    percentage_left -= value
    volume_left -= volume
print("各时间单元应下单手数: %s" % predicted_volume)

# 交易
current_volume = 0  # 记录已调整持仓量
while True:
    api.wait_update()
    # 新产生一根K线并且在计划交易时间段内: 调整目标持仓量
    if api.is_changing(klines.iloc[-1], "datetime"):
        t = datetime.datetime.fromtimestamp(klines.iloc[-1]["datetime"] // 1000000000).time()
        if t in predicted_volume:
            current_volume += predicted_volume[t]
            print("到达下一时间单元,调整持仓为: %d" % current_volume)
            target_pos.set_target_volume(current_volume)
    # 用持仓信息判断是否完成所有目标交易手数
    if api.is_changing(position, "volume_long") or api.is_changing(position, "volume_short"):
        if position["volume_long"] - position["volume_short"] == TARGET_VOLUME:
            break

api.close()
