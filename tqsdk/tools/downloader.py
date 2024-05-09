#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'yangyang'

import asyncio
import csv
import os
from datetime import date, datetime
from encodings.utf_8 import StreamWriter
from typing import Union, List, Optional
import lzma

import pandas

from tqsdk.api import TqApi
from tqsdk.datetime import _cst_tz, _convert_user_input_to_nano
from tqsdk.diff import _get_obj
from tqsdk.utils import _generate_uuid, _get_dividend_factor

try:
    file_path = os.path.split(os.path.abspath(__file__))[0]
    with lzma.open(os.path.join(file_path, "dead_ins.lzma"), "rt", encoding="utf-8") as dead_ins_file:
        DEAD_INS = {l.strip() for l in dead_ins_file}
except:
    DEAD_INS = {}


# 价格相关的字段，需要 format 数据格式
PRICE_KEYS = ["open", "high", "low", "close", "last_price", "highest", "lowest"] + [f"bid_price{i}" for i in range(1, 6)] + [f"ask_price{i}" for i in range(1, 6)]


class DataDownloader:
    """
    数据下载工具是 TqSdk 专业版中的功能，能让用户下载目前 TqSdk 提供的全部期货、期权和股票类的历史数据，下载数据支持 tick 级别精度和任意 kline 周期

    如果想使用数据下载工具，可以点击 `天勤量化专业版 <https://www.shinnytech.com/tqsdk_professional/>`_ 申请使用或购买

    历史数据下载器, 输出到csv文件

    多合约按时间横向对齐
    """

    def __init__(self, api: TqApi, symbol_list: Union[str, List[str]], dur_sec: int, start_dt: Union[date, datetime],
                 end_dt: Union[date, datetime], csv_file_name: Union[str, asyncio.StreamWriter], write_mode: str = "w",
                 adj_type: Union[str, None] = None) -> None:
        """
        创建历史数据下载器实例

        Args:
            api (TqApi): TqApi实例，该下载器将使用指定的api下载数据

            symbol_list (str/list of str): 需要下载数据的合约代码，当指定多个合约代码时将其他合约按第一个合约的交易时间对齐

            dur_sec (int): 数据周期，以秒为单位。例如: 1分钟线为60,1小时线为3600,日线为86400,Tick数据为0

            start_dt (date/datetime): 起始时间
                * date: 指的是交易日

                * datetime: 指的是具体时间点，如果没有指定时区信息，则默认为北京时间

            end_dt (date/datetime): 结束时间
                * date: 指的是交易日

                * datetime: 指的是具体时间点，如果没有指定时区信息，则默认为北京时间

            csv_file_name (str/StreamWriter): [必填]输出方式:
                * str : 输出 csv 的文件名

                * StreamWriter: 直接将内容输出到 StreamWriter

            write_mode (str): 写入模式，默认值为 "w"。"w" 表示覆盖写入，会写入标题行，再写入数据；"a" 表示追加写入，不写标题行，直接写入数据。

            adj_type (str/None): 复权计算方式，默认值为 None。"F" 为前复权；"B" 为后复权；None 表示不复权。只对股票、基金合约有效。

        Example::

            from datetime import datetime, date
            from contextlib import closing
            from tqsdk import TqApi, TqAuth, TqSim
            from tqsdk.tools import DataDownloader

            api = TqApi(auth=TqAuth("快期账户", "账户密码"))
            download_tasks = {}
            # 下载从 2018-01-01 到 2018-09-01 的 SR901 日线数据
            download_tasks["SR_daily"] = DataDownloader(api, symbol_list="CZCE.SR901", dur_sec=24*60*60,
                                start_dt=date(2018, 1, 1), end_dt=date(2018, 9, 1), csv_file_name="SR901_daily.csv")
            # 下载从 2017-01-01 到 2018-09-01 的 rb主连 5分钟线数据
            download_tasks["rb_5min"] = DataDownloader(api, symbol_list="KQ.m@SHFE.rb", dur_sec=5*60,
                                start_dt=date(2017, 1, 1), end_dt=date(2018, 9, 1), csv_file_name="rb_5min.csv")
            # 下载从 2018-01-01凌晨6点 到 2018-06-01下午4点 的 cu1805,cu1807,IC1803 分钟线数据，所有数据按 cu1805 的时间对齐
            # 例如 cu1805 夜盘交易时段, IC1803 的各项数据为 N/A
            # 例如 cu1805 13:00-13:30 不交易, 因此 IC1803 在 13:00-13:30 之间的K线数据会被跳过
            download_tasks["cu_min"] = DataDownloader(api, symbol_list=["SHFE.cu1805", "SHFE.cu1807", "CFFEX.IC1803"], dur_sec=60,
                                start_dt=datetime(2018, 1, 1, 6, 0 ,0), end_dt=datetime(2018, 6, 1, 16, 0, 0), csv_file_name="cu_min.csv")
            # 下载从 2018-05-01凌晨0点 到 2018-06-01凌晨0点 的 T1809 盘口Tick数据
            download_tasks["T_tick"] = DataDownloader(api, symbol_list=["CFFEX.T1809"], dur_sec=0,
                                start_dt=datetime(2018, 5, 1), end_dt=datetime(2018, 6, 1), csv_file_name="T1809_tick.csv")
            # 使用with closing机制确保下载完成后释放对应的资源
            with closing(api):
                while not all([v.is_finished() for v in download_tasks.values()]):
                    api.wait_update()
                    print("progress: ", { k:("%.2f%%" % v.get_progress()) for k,v in download_tasks.items() })
        """
        self._api = api
        if not self._api._auth._has_feature("tq_dl"):
            raise Exception("您的账户不支持下载历史数据功能，需要购买后才能使用。升级网址：https://www.shinnytech.com/tqsdk_professional/")
        self._start_dt_nano, self._end_dt_nano = _convert_user_input_to_nano(start_dt, end_dt)
        self._current_dt_nano = self._start_dt_nano
        self._symbol_list = symbol_list if isinstance(symbol_list, list) else [symbol_list]
        # 下载合约超时时间（默认 30s），已下市的没有交易的合约，超时时间可以设置短一点（2s），用户不希望自己的程序因为没有下载到数据而中断
        self._timeout_seconds = 2 if any([symbol in DEAD_INS for symbol in self._symbol_list]) else 30
        self._dur_nano = dur_sec * 1000000000
        if self._dur_nano == 0 and len(self._symbol_list) != 1:
            raise Exception("Tick序列不支持多合约")
        if adj_type not in [None, "F", "B", "FORWARD", "BACK"]:
            raise Exception("adj_type 参数只支持 None (不复权) ｜ 'F' (前复权) ｜ 'B' (后复权)")
        self._adj_type = adj_type[0] if adj_type else adj_type
        if isinstance(csv_file_name, str) or isinstance(csv_file_name, asyncio.StreamWriter):
            self._csv_file_name = csv_file_name
        else:
            raise Exception("csv_file_name 参数只支持 str ｜ StreamWriter 类型")
        if write_mode not in ["w", "a"]:
            raise Exception("write_mode 参数只支持 'w' ｜ 'a'")
        self._write_mode = write_mode
        self._csv_header = self._get_headers()
        # 缓存合约对应的复权系数矩阵，每个合约只计算一次
        # 含义为截止 datetime 之前(不包含) 应使用 factor 复权
        self._dividend_cache = {}
        self._data_series = None
        self._task = self._api.create_task(self._run())

    def is_finished(self) -> bool:
        """
        判断是否下载完成

        Returns:
            bool: 如果数据下载完成则返回 True, 否则返回 False.
        """
        return self._task.done()

    def get_progress(self) -> float:
        """
        获得下载进度百分比

        Returns:
            float: 下载进度,100表示下载完成
        """
        return 100.0 if self._task.done() else (self._current_dt_nano - self._start_dt_nano) / (
                self._end_dt_nano - self._start_dt_nano) * 100

    def _get_data_series(self) -> Optional[pandas.DataFrame]:
        """
        获取下载的 DataFrame 格式数据

        todo: 在 utils 中增加工具函数，返回与 kline 一致的数据结构

        Returns:
            pandas.DataFrame/None: 下载的 klines 或者 ticks 数据，DataFrame 格式。下载完成前返回 None。


        Example::

            from datetime import datetime, date
            rom tqsdk import TqApi, TqAuth
            from contextlib import closing
            from tqsdk.tools import DataDownloader

            api = TqApi(auth=TqAuth("快期账户", "账户密码"))
            # 下载从 2018-06-01 到 2018-09-01 的 SR901 日线数据
            download_task = DataDownloader(api, symbol_list="CZCE.SR901", dur_sec=24*60*60,
                                start_dt=date(2018, 6, 1), end_dt=date(2018, 9, 1), csv_file_name="klines.csv")
            # 使用with closing机制确保下载完成后释放对应的资源
            with closing(api):
                while not download_task.is_finished():
                    api.wait_update()
                    print(f"progress: {download_task.get_progress():.2} %")
                print(download_task._get_data_series())
        """
        if not self._task.done():
            return None
        if isinstance(self._csv_file_name, str):
            if not self._data_series:
                self._data_series = pandas.read_csv(self._csv_file_name)
            return self._data_series
        else:
            raise Exception('DataDownloader._get_data_series 接口仅支持 csv_file_name 參數为 str 时使用')

    async def _ensure_dividend_factor(self, quote, timestamp):
        if quote.instrument_id not in self._dividend_cache:
            df = await _get_dividend_factor(self._api, quote, timestamp, self._end_dt_nano, chart_id_prefix="PYSDK_downloader")
            # 插入结束时间这条记录, 因为可能存在行情时间等于 _end_dt_nano 的行情，因此这里 +1
            df = df.append({"datetime": self._end_dt_nano+1, "factor": 1.0}, ignore_index=True)
            if self._adj_type == "F":
                df["factor"] = df["factor"].iloc[::-1].cumprod().iloc[::-1]
            elif self._adj_type == "B":
                # 后复权按定义上应该从第一笔行情之后产生的复权事件开始
                # 第一笔行情时间一定小于 df["datetime"].iloc[0], 因此复权是从 df["datetime"].iloc[0] 开始
                df["factor"] = 1.0 / df["factor"].cumprod()
                # 至此 df 每行的含义为从 datetime 开始应使用 factor 复权
                # 该格式并不好用，需要改为截止 datetime 之前(不包含) 应使用 factor 复权
                df["factor"] = df["factor"].shift(1)
                df["factor"].iloc[0] = 1.0
            self._dividend_cache[quote.instrument_id] = {
                "df": df,
                "last_dt": 0,
                "factor": float("nan"),
            }

    async def _run(self):
        self._quote_list = await self._api.get_quote_list(self._symbol_list)
        # 下载数据的 async generator
        gen = self._download_data()
        # cols 是复权需要重新计算的列名
        index_datetime_nano = self._csv_header.index("datetime_nano")
        if self._dur_nano != 0:
            cols = ["open", "high", "low", "close"]
        else:
            cols = ["last_price", "highest", "lowest"]
            cols.extend(f"{x}{i}" for x in ["bid_price", "ask_price"] for i in range(1, 6))
        try:
            if isinstance(self._csv_file_name, asyncio.StreamWriter):
                writer = StreamWriter(self._csv_file_name)
            else:
                writer = open(self._csv_file_name, self._write_mode, newline='')
            csv_writer = csv.writer(writer, dialect='excel')
            if self._write_mode == "w":
                csv_writer.writerow(self._csv_header)
            async for item in gen:
                for quote in self._quote_list:
                    symbol = quote.instrument_id
                    if self._adj_type and quote.ins_class in ["STOCK", "FUND"]:
                        # 如果存在 STOCK / FUND 并且 adj_type is not None, 这里需要提前准备下载时间段内的复权因子
                        # 前复权需要提前计算除权因子
                        await self._ensure_dividend_factor(quote, item[index_datetime_nano])
                        dividend_cache = self._dividend_cache[symbol]
                        # dividend_df 和 _data_chan 中取出的数据都是按时间升序排列的，因此可以使用归并算法
                        if dividend_cache["last_dt"] <= item[index_datetime_nano]:
                            dividend_df = dividend_cache["df"]
                            dividend_df = dividend_df[dividend_df["datetime"].gt(item[index_datetime_nano])]
                            dividend_cache["df"] = dividend_df
                            dividend_cache["last_dt"] = dividend_df["datetime"].iloc[0]
                            dividend_cache["factor"] = dividend_df["factor"].iloc[0]
                        if dividend_cache["factor"] != 1:
                            item = item.copy()
                            for c in cols:  # datetime_nano
                                index = self._csv_header.index(f"{symbol}.{c}")
                                item[index] = item[index] * dividend_cache["factor"]
                csv_writer.writerow(item)
                if isinstance(self._csv_file_name, asyncio.StreamWriter):
                    await self._csv_file_name.drain()
        finally:
            if isinstance(self._csv_file_name, asyncio.StreamWriter):
                self._csv_file_name.write_eof()
            else:
                writer.close()
            # 这里 `await gen.aclose()` 实际测试代码与文档描述不符，无论文件全部下载完正常退出还是写文件过程中抛出例外退出，都没有再抛出任何例外
            # https://docs.python.org/3/reference/expressions.html#agen.aclose
            await gen.aclose()

    async def _download_data(self):
        """下载数据, 多合约横向按时间对齐"""
        chart_info = {
            "aid": "set_chart",
            "chart_id": _generate_uuid("PYSDK_downloader"),
            "ins_list": ",".join(self._symbol_list),
            "duration": self._dur_nano,
            "view_width": 2000,
            "focus_datetime": self._start_dt_nano,
            "focus_position": 0,
        }
        # 还没有发送过任何请求, 先请求定位左端点
        await self._api._send_chan.send(chart_info)
        chart = _get_obj(self._api._data, ["charts", chart_info["chart_id"]])
        current_id = None  # 当前数据指针
        data_cols = self._get_data_cols()
        serials = []
        for symbol in self._symbol_list:
            path = ["klines", symbol, str(self._dur_nano)] if self._dur_nano != 0 else ["ticks", symbol]
            serial = _get_obj(self._api._data, path)
            serials.append(serial)
        try:
            async with self._api.register_update_notify() as update_chan:
                async for _ in update_chan:
                    if not (chart_info.items() <= _get_obj(chart, ["state"]).items()):
                        # 当前请求还没收齐回应, 不应继续处理
                        continue
                    if chart.get("ready", False) is False:
                        continue  # 数据序列还没收到，包含主合约和所有副合约
                    if serials[0].get("last_id", -1) == -1:
                        return  # 没有数据，直接退出
                    left_id = chart.get("left_id", -1)
                    right_id = chart.get("right_id", -1)
                    if current_id is None:
                        current_id = max(left_id, 0)
                    while current_id <= right_id:
                        item = serials[0]["data"].get(str(current_id), {})
                        if item.get("datetime", 0) == 0 or item["datetime"] > self._end_dt_nano:
                            # 当前 id 已超出 last_id 或k线数据的时间已经超过用户限定的右端
                            return
                        row = [self._nano_to_str(item["datetime"]), item["datetime"]]
                        for col in data_cols:
                            row.append(self._get_value(item, col, self._quote_list[0]["price_decs"]))
                        for i in range(1, len(self._symbol_list)):
                            symbol = self._symbol_list[i]
                            tid = serials[0].get("binding", {}).get(symbol, {}).get(str(current_id), -1)
                            k = {} if tid == -1 else serials[i]["data"].get(str(tid), {})
                            for col in data_cols:
                                row.append(self._get_value(k, col, self._quote_list[i]["price_decs"]))
                        yield row
                        current_id += 1
                        self._current_dt_nano = item["datetime"]
                    # 当前 id 已超出订阅范围, 需重新订阅后续数据
                    chart_info.pop("focus_datetime", None)
                    chart_info.pop("focus_position", None)
                    chart_info["left_kline_id"] = current_id
                    await self._api._send_chan.send(chart_info)
        finally:
            # 释放chart资源
            await self._api._send_chan.send({
                "aid": "set_chart",
                "chart_id": chart_info["chart_id"],
                "ins_list": "",
                "duration": self._dur_nano,
                "view_width": 2000,
            })

    def _get_headers(self):
        data_cols = self._get_data_cols()
        return ["datetime", "datetime_nano"] + [f"{symbol}.{col}" for symbol in self._symbol_list for col in data_cols]

    def _get_data_cols(self):
        if self._dur_nano != 0:
            return ["open", "high", "low", "close", "volume", "open_oi", "close_oi"]
        else:
            cols = ["last_price", "highest", "lowest", "average", "volume", "amount", "open_interest"]
            price_range = 1
            for symbol in self._symbol_list:
                if symbol.split('.')[0] in {"SHFE", "INE", "SSE", "SZSE"}:
                    price_range = 5
                    break
            for i in range(price_range):
                cols.extend(f"{x}{i+1}" for x in ["bid_price", "bid_volume", "ask_price", "ask_volume"])
            return cols

    @staticmethod
    def _get_value(obj, key, price_decs):
        try:
            if key in PRICE_KEYS:
                return round(obj[key], price_decs)
            else:
                return obj[key]
        except KeyError:
            return "#N/A"
        except TypeError:
            return float("nan")

    @staticmethod
    def _nano_to_str(nano):
        # 这里为了保留 nano 精度，没有用 datetime._timestamp_nano_to_str
        dt = datetime.fromtimestamp(nano // 1000000000, tz=_cst_tz)
        return "%d-%02d-%02d %02d:%02d:%02d.%09d" % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, int(nano) % 1000000000)
