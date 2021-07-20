#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'yanqiong'

import csv
import os
from datetime import datetime

from tqsdk import TqApi, TqAuth, TqKq


"""
本示例用于下载账户当前交易日到目前位置的全部委托单、成交记录分别到 orders.csv、trades.csv 文件。

如果文件已经存在，会将记录追加到文件末尾。

用户可以在交易日结束之后，运行本示例，可以将当日的委托单、成交记录保存到本地。
"""


order_cols = ["order_id", "exchange_order_id", "exchange_id", "instrument_id", "direction", "offset", "status", "volume_orign", "volume_left", "limit_price", "price_type", "volume_condition", "time_condition", "insert_date_time", "last_msg"]
trade_cols = ["trade_id", "order_id", "exchange_trade_id", "exchange_id", "instrument_id", "direction", "offset", "price", "volume", "trade_date_time"]


def write_csv(file_name, cols, datas):
    file_exists = os.path.exists(file_name) and os.path.getsize(file_name) > 0
    with open(file_name, 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, dialect='excel')
        if not file_exists:
            csv_writer.writerow(['datetime'] + cols)
        for item in datas.values():
            if 'insert_date_time' in cols:
                dt = datetime.fromtimestamp(item['insert_date_time'] / 1e9).strftime('%Y-%m-%d %H:%M:%S.%f')
            elif 'trade_date_time' in cols:
                dt = datetime.fromtimestamp(item['trade_date_time'] / 1e9).strftime('%Y-%m-%d %H:%M:%S.%f')
            else:
                dt = None
            row = [dt] + [item[k] for k in cols]
            csv_writer.writerow(row)


with TqApi(TqKq(), auth=TqAuth("信易账户", "账户密码")) as api:
    # 将当前账户下全部委托单、成交信息写入 csv 文件中
    write_csv("orders.csv", order_cols, api.get_order())
    write_csv("trades.csv", trade_cols, api.get_trade())
