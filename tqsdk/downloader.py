# encoding: UTF-8

import json
import datetime
import uuid
import logging
import csv
from tqsdk.api import TqApi


class KlineDownloader(TqApi):
    """
    K线数据下载器, 输出到csv文件
    提供输出格式:

    * 多合约横向对齐
    """

    def __init__(self):
        TqApi.__init__(self)
        self.chart_id = "DOWNLOADER"
        # timestamp = dt.replace(tzinfo=timezone.utc).timestamp()
        self.current_id = None # 当前数据指针, 下一次调用front()时, 将返回此指针指向的数据
        self.subscribe_left = None  # 当前订阅的数据段的左端点
        self.subscribe_width = 1000  # 当前订阅的数据段的宽度
        self.chart_info = None
        self.serials = []

    def download_kline(self, start_dt, end_dt, symbol_list, dur_sec, csv_file_name):
        """
            下载数据, 多合约横向按时间对齐
        """
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.start_dt_nano = int(start_dt.timestamp()) * 1000000000
        self.end_dt_nano = int(end_dt.timestamp()) * 1000000000
        self.symbol_list = symbol_list
        self.dur_sec = dur_sec
        self.dur_nano = dur_sec * 1000000000
        self.serials = []
        for symbol in symbol_list:
            serial = self.data.setdefault("klines", {}).setdefault(symbol, {}).setdefault(str(self.dur_nano), {})
            self.serials.append(serial)
        with open(csv_file_name, 'w', newline='') as csvfile:
            self.csv_writer = csv.writer(csvfile, dialect='excel')
            csv_header = ["datetime"]
            for symbol in symbol_list:
                csv_header.append(symbol+".OPEN")
                csv_header.append(symbol+".HIGH")
                csv_header.append(symbol+".LOW")
                csv_header.append(symbol+".CLOSE")
                csv_header.append(symbol+".VOL")
                csv_header.append(symbol+".OI")
            self.csv_writer.writerow(csv_header)
            try:
                self.run(self.on_data_update)
            except Exception:
                print("finish")
                self.stop()

    def on_data_update(self):
        while True:
            if self.chart_info is None:
                # 还没有发送过任何请求, 先请求定位左端点
                self.chart_info = {
                    "ins_list": ",".join(self.symbol_list),
                    "duration": self.dur_nano,
                    "view_width": self.subscribe_width,
                    "focus_datetime": self.start_dt_nano,
                }
                self.send_json({
                    "aid": "set_chart",
                    "chart_id": self.chart_id,
                    "ins_list": ",".join(self.symbol_list),
                    "duration": self.dur_nano,
                    "view_width": self.subscribe_width,
                    "focus_datetime": self.start_dt_nano,
                    "focus_position": 0,
                })
                continue
            if self.set_default(True, "mdhis_more_data") \
                    or not self.all_match(self.chart_info,self.set_default({}, "charts", self.chart_id, "state")):
                # 当前请求还没收齐回应, 不应继续处理
                break
            last_id = self.serials[0].get("last_id", None)
            if self.current_id is None:
                chart_info = self.data.setdefault("charts", {}).setdefault(self.chart_id, {})
                if "left_id" in chart_info and chart_info["left_id"] != -1:
                    self.current_id = chart_info["left_id"]
                    self.subscribe_left = self.current_id
            if self.current_id is None or last_id is None:
                # 定位信息还没收到, 或数据序列还没收到
                break
            if self.current_id > last_id:
                # 当前 id 已超出 last_id, 明确没有后续数据
                raise Exception("FINISH")
            if self.subscribe_left + self.subscribe_width <= self.current_id:
                # 当前 id 已超出订阅范围, 需重新订阅后续数据
                self.subscribe_left = self.current_id
                self.chart_info = {
                    "ins_list": ",".join(self.symbol_list),
                    "duration": self.dur_nano,
                    "view_width": self.subscribe_width,
                    "left_kline_id": self.subscribe_left,
                }
                self.send_json({
                    "aid": "set_chart",
                    "chart_id": self.chart_id,
                    "ins_list": ",".join(self.symbol_list),
                    "duration": self.dur_nano,
                    "view_width": self.subscribe_width,
                    "left_kline_id": self.subscribe_left,
                })
                break
            item = self.serials[0]["data"].get(u"%d" % self.current_id, None)
            if not item:
                raise Exception("ERROR")
            if item['datetime'] > self.end_dt_nano:
                # k线数据的时间已经超过用户限定的右端, 明确没有后续数据
                raise Exception("FINISH")
            if item["datetime"] == 0:
                raise Exception("")
            row = []
            row.append(self.nano_to_str(item["datetime"]))
            row.append(item["open"])
            row.append(item["high"])
            row.append(item["low"])
            row.append(item["close"])
            row.append(item["volume"])
            row.append(item["close_oi"] - item["open_oi"])
            for i in range(1, len(self.symbol_list)):
                symbol = self.symbol_list[i]
                if symbol not in self.serials[0]["binding"]:
                    raise Exception("")
                tid = self.serials[0]["binding"][symbol].get(u"%d" % self.current_id, None)
                if tid:
                    k = self.serials[i]["data"].get(u"%d" % tid, None)
                    if not k:
                        raise Exception("%d" % tid)
                    row.append(k["open"])
                    row.append(k["high"])
                    row.append(k["low"])
                    row.append(k["close"])
                    row.append(k["volume"])
                    row.append(k["close_oi"] - k["open_oi"])
            self.csv_writer.writerow(row)
            print(self.subscribe_left, self.current_id)
            self.current_id += 1

    def all_match(self, source, target):
        # check if all fields in source are in target too
        for f in source:
            if f not in target or target[f] != source[f]:
                return False
        return True

    def nano_to_datetime(self, nano):
        dt = datetime.fromtimestamp(nano // 1000000000)
        return dt

    def nano_to_str(self, nano):
        dt = datetime.datetime.fromtimestamp(nano // 1000000000)
        s = dt.strftime('%Y-%m-%d %H:%M:%S')
        s += '.' + str(int(nano % 1000000000)).zfill(9)
        return s


if __name__ == "__main__":
    d = KlineDownloader()
    d.download_kline(symbol_list=["SHFE.cu1805", "SHFE.cu1807", "CFFEX.IC1803"], dur_sec=5, start_dt=datetime.datetime(2018, 1, 1), end_dt=datetime.datetime(2018, 5, 10), csv_file_name="1.csv")
