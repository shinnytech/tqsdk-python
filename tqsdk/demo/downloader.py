#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from datetime import datetime
from contextlib import closing
from tqsdk.api import TqApi
from tqsdk.tools.downloader import DataDownloader

api = TqApi("SIM")
# 下载从 2018-01-01凌晨6点 到 2018-06-01下午4点 的 cu1805,cu1807,IC1803 分钟线数据，所有数据按 cu1805 的时间对齐
# 例如 cu1805 夜盘交易时段, IC1803 的各项数据为 N/A
# 例如 cu1805 13:00-13:30 不交易, 因此 IC1803 在 13:00-13:30 之间的K线数据会被跳过
kd = DataDownloader(api, symbol_list=["SHFE.cu1805", "SHFE.cu1807", "CFFEX.IC1803"], dur_sec=60,
                    start_dt=datetime(2018, 1, 1, 6, 0 ,0), end_dt=datetime(2018, 6, 1, 16, 0, 0), csv_file_name="kline.csv")
# 下载从 2018-05-01凌晨0点 到 2018-07-01凌晨0点 的 T1809 盘口Tick数据
td = DataDownloader(api, symbol_list=["CFFEX.T1809"], dur_sec=0,
                    start_dt=datetime(2018, 5, 1), end_dt=datetime(2018, 7, 1), csv_file_name="tick.csv")
# 使用with closing机制确保下载完成后释放对应的资源
with closing(api):
    while not kd.is_finished() or not td.is_finished():
        api.wait_update()
        print("progress: kline: %.2f%% tick:%.2f%%" % (kd.get_progress(), td.get_progress()))
