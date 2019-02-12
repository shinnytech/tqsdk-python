#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'


'''
天勤主程序启动外部python进程的入口, 这样用:

backtest.py --ins_service=http://....  --md_service=ws://xxxxx --trade_service=ws://....

此进程持续运行
'''

import sys
import asyncio
import argparse
import datetime
import json
import logging

from tqsdk import TqApi, TqSim, TqBacktest
from tqsdk.tq.utility import input_param_backtest, load_strategy_file
import tqsdk


class TqBacktestLogger(logging.Handler):
    def __init__(self, chan):
        logging.Handler.__init__(self)
        self.records = []

    def emit(self, record):
        dt = record.created * 1000000000 + record.msecs * 1000000
        self.records.append({
            "datetime": dt,
            "level": str(record.levelname),
            "content": record.msg,
        })


def json_output(f, obj):
    json.dump(obj, f)
    f.write("\n")


def save_report_to_json_file(trade_log, logs, fn):
    with open(fn, "a+") as f:
        json_output(f, {
            "datetime": 0,
            "type": "INFO",
            "user_name": "abcdef",
        })
        for trading_day, daily_record in trade_log.items():
            trades = daily_record.get("trades", [])
            for trade in trades:
                rec = {
                    "datetime": trade["trade_date_time"],
                    "type": "TRADE",
                    "trade": trade,
                }
                json_output(f, rec)
            snap = {
                "datetime": 1524812399999999000,
                "type:": "SNAP",
                "accounts": daily_record.get("account", {}),
                "positions": daily_record.get("positions", {}),
            }
            json_output(f, snap)


def backtest():
    #获取命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--file')
    parser.add_argument('--out')
    args = parser.parse_args()
    print(0)
    #加载策略文件
    t_class = load_strategy_file(args.file)
    if not t_class:
        print(1)
        return

    # 输入参数
    param_list, bk_left, bk_right = input_param_backtest(t_class)
    print(3)
    if param_list is None:
        print(2)
        return
    print("dddd", bk_left, bk_right, param_list)
    # api
    s = TqSim()
    api = TqApi(s, debug="C:\\tmp\\debug.log", backtest=TqBacktest(start_dt=bk_left, end_dt=bk_right))
    instance = t_class(api, param_list=param_list)
    print("api")

    # log
    logger = logging.getLogger("TQ")
    logger.setLevel(logging.INFO)
    th = TqBacktestLogger(api.send_chan)
    th.setLevel(logging.INFO)
    th.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(th)

    # run
    try:
        instance.on_start()
        while True:
            api.wait_update()
            instance.on_data()
    except tqsdk.exceptions.BacktestFinished:
        print("finish")
        save_report_to_json_file(s.trade_log, th.records, args.out)

    api.close()

if __name__ == "__main__":
    backtest()
