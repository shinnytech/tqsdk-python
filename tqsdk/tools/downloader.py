#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'yangyang'

import csv
from datetime import datetime


class DataDownloader:
    """
    历史数据下载器, 输出到csv文件

    多合约按时间横向对齐
    """
    def __init__(self, api, symbol_list, dur_sec, start_dt, end_dt, csv_file_name):
        """
        创建历史数据下载器实例

        Args:
            api (TqApi): TqApi实例，该下载器将使用指定的api下载数据

            symbol_list (str/list of str): 需要下载数据的合约代码，当指定多个合约代码时将其他合约按第一个合约的交易时间对齐

            dur_sec (int): 数据周期，以秒为单位。例如: 1分钟线为60,1小时线为3600,日线为86400,Tick数据为0

            start_dt (datetime): 起始时间

            end_dt (datetime): 结束时间

            csv_file_name (str): 输出csv的文件名
        """
        self.api = api
        self.start_dt_nano = int(start_dt.timestamp()) * 1000000000
        self.end_dt_nano = int(end_dt.timestamp()) * 1000000000
        self.current_dt_nano = self.start_dt_nano
        self.symbol_list = symbol_list if isinstance(symbol_list, list) else [symbol_list]
        self.dur_nano = dur_sec * 1000000000
        if self.dur_nano == 0 and len(self.symbol_list) != 1:
            raise Exception("Tick序列不支持多合约")
        self.csv_file_name = csv_file_name
        self.task = self.api.create_task(self._download_data())

    def is_finished(self):
        """
        判断是否下载完成

        Returns:
            bool: 如果数据下载完成则返回 True, 否则返回 False.
        """
        return self.task.done()

    def get_progress(self):
        """
        获得下载进度百分比

        Returns:
            float: 下载进度,100表示下载完成
        """
        return 100.0 if self.task.done() else (self.current_dt_nano - self.start_dt_nano) / (self.end_dt_nano - self.start_dt_nano) * 100

    async def _download_data(self):
        """下载数据, 多合约横向按时间对齐"""
        chart_info = {
            "aid": "set_chart",
            "chart_id": self.api._generate_chart_id(self.symbol_list, self.dur_nano),
            "ins_list": ",".join(self.symbol_list),
            "duration": self.dur_nano,
            "view_width": 2000,
            "focus_datetime": self.start_dt_nano,
            "focus_position": 0,
        }
        # 还没有发送过任何请求, 先请求定位左端点
        self.api._send_json(chart_info)
        chart = self.api._get_obj(self.api.data, ["charts", chart_info["chart_id"]])
        current_id = None  # 当前数据指针
        csv_header = []
        data_cols = ["open", "high", "low", "close", "volume", "open_oi", "close_oi"] if self.dur_nano != 0 else \
            ["last_price", "highest", "lowest", "bid_price1", "bid_volume1", "ask_price1", "ask_volume1", "volume", "amount", "open_interest"]
        serials = []
        for symbol in self.symbol_list:
            path = ["klines", symbol, str(self.dur_nano)] if self.dur_nano != 0 else ["ticks", symbol]
            serial = self.api._get_obj(self.api.data, path)
            serials.append(serial)
        try:
            with open(self.csv_file_name, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile, dialect='excel')
                async with self.api.register_update_notify() as update_chan:
                    async for _ in update_chan:
                        if not (chart_info.items() <= self.api._get_obj(chart, ["state"]).items()):
                            # 当前请求还没收齐回应, 不应继续处理
                            continue
                        left_id = chart.get("left_id", -1)
                        right_id = chart.get("right_id", -1)
                        if left_id == -1 or right_id == -1 or self.api.data.get("mdhis_more_data", True):
                            # 定位信息还没收到, 或数据序列还没收到
                            continue
                        # 检查副合约的数据是否收到
                        binding_data = True
                        for i in range(1, len(self.symbol_list)):
                            symbol = self.symbol_list[i]
                            if symbol not in serials[0].get("binding", {}):
                                binding_data = False
                        if not binding_data:
                            continue
                        if current_id is None:
                            current_id = left_id
                        while current_id <= right_id:
                            item = serials[0]["data"].get(str(current_id), {})
                            if item.get("datetime", 0) == 0 or item['datetime'] > self.end_dt_nano:
                                # 当前 id 已超出 last_id 或k线数据的时间已经超过用户限定的右端
                                return
                            if len(csv_header) == 0:
                                # 写入文件头
                                csv_header = ["datetime"]
                                for symbol in self.symbol_list:
                                    for col in data_cols:
                                        csv_header.append(symbol+"."+col)
                                csv_writer.writerow(csv_header)
                            row = [self._nano_to_str(item["datetime"])]
                            for col in data_cols:
                                row.append(self._get_value(item, col))
                            for i in range(1, len(self.symbol_list)):
                                symbol = self.symbol_list[i]
                                tid = serials[0]["binding"][symbol].get(str(current_id), -1)
                                k = {} if tid == -1 else serials[i]["data"].get(str(tid), {})
                                for col in data_cols:
                                    row.append(self._get_value(k, col))
                            csv_writer.writerow(row)
                            current_id += 1
                            self.current_dt_nano = item['datetime']
                        # 当前 id 已超出订阅范围, 需重新订阅后续数据
                        chart_info.pop("focus_datetime", None)
                        chart_info.pop("focus_position", None)
                        chart_info["left_kline_id"] = current_id
                        self.api._send_json(chart_info)
        finally:
            # 释放chart资源
            self.api._send_json({
                "aid": "set_chart",
                "chart_id": chart_info["chart_id"],
                "ins_list": "",
                "duration": self.dur_nano,
                "view_width": 2000,
            })

    @staticmethod
    def _get_value(obj, key):
        if key not in obj:
            return "#N/A"
        if isinstance(obj[key], str):
            return float("nan")
        return obj[key]

    @staticmethod
    def _nano_to_str(nano):
        dt = datetime.fromtimestamp(nano // 1000000000)
        s = dt.strftime('%Y-%m-%d %H:%M:%S')
        s += '.' + str(int(nano % 1000000000)).zfill(9)
        return s
