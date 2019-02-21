#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'yangyang'


'''
天勤主程序启动python策略回测的入口, 这样用:

backtest.py --source_file=a.py --output_file=1.json

此进程运行过程中, 持续将回测结果输出到 output_file, 回测结束时进程关闭
'''

import sys
import os
import argparse
import json
import logging
import importlib

import tqsdk
from tqsdk import TqApi, TqSim, TqBacktest
from tqsdk.tq.utility import input_param_backtest


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
        "accounts": {
            "CNY": {k: v for k, v in account.items() if not k.startswith("_")},
        },
        "positions": {k: {pk: pv for pk, pv in v.items() if not pk.startswith("_")} for k, v in positions.items() if not k.startswith("_")},
    }, out)
    out.write("\n")
    out.flush()


async def account_watcher(api, sim, out):
    account = api.get_account()
    positions = api.get_position()
    trades = api._get_obj(api.data, ["trade", api.account_id, "trades"])
    write_snapshot(sim, out, account, positions)
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
    parser.add_argument('--source_file')
    parser.add_argument('--output_file')
    args = parser.parse_args()

    # 加载策略文件
    file_path, file_name = os.path.split(args.source_file)
    sys.path.insert(0, file_path)
    module_name = file_name[:-3]

    # 输入参数
    param_list = []

    def _fake_api_for_param_list(*args, **kwargs):
        m = sys.modules[module_name]
        for k, v in m.__dict__.items():
            if k.upper() != k:
                continue
            param_list.append([k, v])
        raise Exception()

    tqsdk.TqApi = _fake_api_for_param_list
    try:
        importlib.import_module(module_name)
    except Exception:
        pass

    param_list, bk_left, bk_right = input_param_backtest(param_list)
    if param_list is None:
        return

    # 开始回测
    out = open(args.output_file, "a+")

    s = TqSim()
    api = TqApi(s, debug="C:\\tmp\\debug.log", backtest=TqBacktest(start_dt=bk_left, end_dt=bk_right))
    logger = logging.getLogger("TQ")
    logger.setLevel(logging.INFO)
    logger.addHandler(TqBacktestLogger(s, out))
    api.create_task(account_watcher(api, s, out))

    try:
        def _fake_api_for_launch(*args, **kwargs):
            m = sys.modules[module_name]
            for k, v in param_list:
                m.__dict__[k] = v
            return api

        tqsdk.TqApi = _fake_api_for_launch
        importlib.import_module(module_name)
    except ModuleNotFoundError:
        logger.exception("加载策略文件失败")
    except IndentationError:
        logger.exception("策略文件缩进格式错误")
    except tqsdk.exceptions.BacktestFinished:
        pass


if __name__ == "__main__":
    backtest()
