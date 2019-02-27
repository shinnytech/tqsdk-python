#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from datetime import datetime
from contextlib import closing
from tqsdk import TqApi, TqSim
from tqsdk.tools import DataDownloader

api = TqApi(TqSim())
# 下载从 2018-01-01凌晨6点 到 2018-06-01下午4点 的 cu1805 分钟线数据
kd = DataDownloader(api, symbol_list="SHFE.cu1805", dur_sec=60,
                    start_dt=datetime(2018, 1, 1, 6, 0 ,0), end_dt=datetime(2018, 6, 1, 16, 0, 0), csv_file_name="kline.csv")
# 下载从 2018-05-01凌晨0点 到 2018-07-01凌晨0点 的 T1809 盘口Tick数据
td = DataDownloader(api, symbol_list="CFFEX.T1809", dur_sec=0,
                    start_dt=datetime(2018, 5, 1), end_dt=datetime(2018, 7, 1), csv_file_name="tick.csv")
# 使用with closing机制确保下载完成后释放对应的资源
with closing(api):
    while not kd.is_finished() or not td.is_finished():
        api.wait_update()
        print("progress: kline: %.2f%% tick:%.2f%%" % (kd.get_progress(), td.get_progress()))
