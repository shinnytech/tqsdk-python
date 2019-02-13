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
from contextlib import closing

from tqsdk import TqApi, TqSim, TqBacktest
from tqsdk.tq.utility import input_param_backtest, load_strategy_file
import tqsdk



class TqBacktestLogger(logging.Handler):
    def __init__(self, sim, out):
        logging.Handler.__init__(self)
        self.sim = sim
        self.out = out

    def emit(self, record):
        json.dump({
            "aid": "log",
            "datetime": self.sim._get_current_timestamp(),
            "level": str(record.levelname),
            "content": record.msg,
        }, self.out)
        self.out.write("\n")
        self.out.flush()

def write_snapshot(sim, out, account, positions):
    json.dump({
        "aid": "snapshot",
        "datetime": sim._get_current_timestamp(),
        "account": {k: v for k, v in account.items() if not k.startswith("_")},
        "positions": {k: {pk: pv for pk, pv in v.items() if  not pk.startswith("_")} for k, v in positions.items() if not k.startswith("_")},
    }, out)
    out.write("\n")
    out.flush()

async def account_watcher(api, sim, out):
    account = api.get_account()
    positions = api.get_position()
    trades = api._get_obj(api.data, ["trade", api.account_id, "trades"])
    try:
        async with api.register_update_notify() as update_chan:
            async for _ in update_chan:
                account_changed = api.is_changing(account, "static_balance")
                for d in api.diffs:
                    for oid in d.get("trade", {}).get(api.account_id, {}).get("orders", {}).keys():
                        account_changed = True
                        json.dump({
                            "aid": "order",
                            "datetime": sim._get_current_timestamp(),
                            "order": {k: v for k, v in api.get_order(oid).items() if not k.startswith("_")},
                        }, out)
                        out.write("\n")
                        out.flush()
                    for tid in d.get("trade", {}).get(api.account_id, {}).get("trades", {}).keys():
                        account_changed = True
                        json.dump({
                            "aid": "trade",
                            "datetime": sim._get_current_timestamp(),
                            "trade": {k: v for k, v in trades[tid].items() if not k.startswith("_")},
                        }, out)
                        out.write("\n")
                        out.flush()
                if account_changed:
                    write_snapshot(sim, out, account, positions)
    finally:
        write_snapshot(sim, out, account, positions)


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
    out = open(args.out, "a+")
    # api
    s = TqSim()
    api = TqApi(s, debug="C:\\tmp\\debug.log", backtest=TqBacktest(start_dt=bk_left, end_dt=bk_right))

    with closing(api):
        # log
        logger = logging.getLogger("TQ")
        logger.setLevel(logging.INFO)
        logger.addHandler(TqBacktestLogger(s, out))

        api.create_task(account_watcher(api, s, out))
        instance = t_class(api, param_list=param_list)
        print("api")


        # run
        try:
            instance.on_start()
            while True:
                api.wait_update()
                instance.on_data()
        except tqsdk.exceptions.BacktestFinished:
            print("finish")


if __name__ == "__main__":
    backtest()
