#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'yangyang'


'''
天勤主程序启动python策略回测的入口

backtest.py --source_file=a.py --instance_id=x --instance_file=x.desc --output_file=1.json

此进程运行过程中, 持续将回测结果输出到 output_file, 回测结束时进程关闭
'''

import sys
import os
import argparse
import json
import logging
import importlib
import datetime
from contextlib import closing

import tqsdk
from tqsdk import TqApi, TqSim, TqBacktest
from tqsdk.tq.utility import input_param_backtest


class TqBacktestLogger(logging.Handler):
    def __init__(self, sim, out):
        logging.Handler.__init__(self)
        self.sim = sim
        self.out = out

    def emit(self, record):
        if record.exc_info:
            msg = "%s, %s" % (record.msg, str(record.exc_info[1]))
        else:
            msg = record.msg
        json.dump({
            "aid": "log",
            "datetime": self.sim._get_current_timestamp(),
            "level": str(record.levelname),
            "content": msg,
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
    parser.add_argument('--instance_id')
    parser.add_argument('--instance_file')
    parser.add_argument('--output_file')
    args = parser.parse_args()

    s = TqSim()
    out = open(args.output_file, "a+")
    logger = logging.getLogger("TQ")
    logger.setLevel(logging.INFO)
    logger.addHandler(TqBacktestLogger(s, out))

    # 加载策略文件
    file_path, file_name = os.path.split(args.source_file)
    sys.path.insert(0, file_path)
    module_name = file_name[:-3]

    # 加载或输入参数
    param_list = []
    try:
        # 从文件读取参数表
        with open(args.instance_file, "rt") as param_file:
            instance = json.load(param_file)
            param_list = instance.get("param_list", [])
            start_date = datetime.date(instance["start_date"]//10000, instance["start_date"]%10000//100, instance["start_date"]%100)
            end_date = datetime.date(instance["end_date"]//10000, instance["end_date"]%10000//100, instance["end_date"]%100)
    except IOError:
        # 获取用户代码中的参数表
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
        except ModuleNotFoundError:
            logger.exception("加载策略文件失败")
        except IndentationError:
            logger.exception("策略文件缩进格式错误")
        except Exception as e:
            pass

        param_list, start_date, end_date = input_param_backtest(param_list)
        if param_list is None:
            return
        with open(args.instance_file, "wt") as param_file:
            json.dump({
                "instance_id": args.instance_id,
                "strategy_file_name": args.source_file,
                "desc": json.dumps(param_list),
                "start_date": start_date.year * 10000 + start_date.month * 100 + start_date.day,
                "end_date": end_date.year * 10000 + end_date.month * 100 + end_date.day,
                "param_list": param_list,
            }, param_file)

    # 开始回测
    api = TqApi(s, backtest=TqBacktest(start_dt=start_date, end_dt=end_date))
    with closing(api):
        api.send_chan.send_nowait({
            "aid": "status",
            "instance_id": args.instance_id,
            "status": "RUNNING",
            "desc": json.dumps(param_list)
        })
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
            logger.info("策略回测结束")
        except Exception as e:
            logger.exception("策略执行中遇到异常", exc_info=True)


if __name__ == "__main__":
    backtest()
