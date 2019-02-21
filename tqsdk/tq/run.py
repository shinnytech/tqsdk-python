#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'yangyang'


'''
天勤主程序启动外部python进程的入口, 这样用:

run.py --source_file=C:\\tqsdk\\xx\\a.py --instance_id=ABCD --instance_file=c:\\tmp\\ABCD.json
'''

import os
import sys
import json
import argparse
import logging
import importlib

import tqsdk
from tqsdk.tq.utility import input_param
from tqsdk.api import TqApi, TqAccount


class TqRunLogger(logging.Handler):
    def __init__(self, chan, instance_id):
        logging.Handler.__init__(self)
        self.chan = chan
        self.instance_id = instance_id

    def emit(self, record):
        dt = int(record.created * 1000000000 + record.msecs * 1000000)
        self.chan.send_nowait({
            "aid": "log",
            "datetime": dt,
            "instance_id": self.instance_id,
            "level": str(record.levelname),
            "content": record.msg,
        })


def run():
    #获取命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--source_file')
    parser.add_argument('--instance_id')
    parser.add_argument('--instance_file')
    args = parser.parse_args()

    # api
    api = TqApi(TqAccount("", args.instance_id, ""), url="ws://127.0.0.1:7777/" + args.instance_id,
                    debug="C:\\tmp\\debug.log")
    # log
    logger = logging.getLogger("TQ")
    logger.setLevel(logging.INFO)
    th = TqRunLogger(api.send_chan, args.instance_id)
    th.setLevel(logging.INFO)
    logger.addHandler(th)

    try:
        #加载策略文件
        file_path, file_name = os.path.split(args.source_file)
        sys.path.insert(0, file_path)
        module_name = file_name[:-3]

        param_list = []
        # 加载或输入参数
        try:
            # 从文件读取参数表
            with open(args.instance_file, "rt") as param_file:
                instance = json.load(param_file)
                param_list = instance.get("param_list", [])
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
            except Exception:
                pass

            param_list = input_param(param_list)
            if param_list is None:
                return
            with open(args.instance_file, "wt") as param_file:
                json.dump({
                    "instance_id": args.instance_id,
                    "strategy_file_name": args.source_file,
                    "desc": json.dumps(param_list),
                    "param_list": param_list,
                }, param_file)
        api.send_chan.send_nowait({
            "aid": "status",
            "instance_id": args.instance_id,
            "status": "RUNNING",
            "desc": json.dumps(param_list)
        })
        # 拉起实例并直接执行
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


if __name__ == "__main__":
    run()
