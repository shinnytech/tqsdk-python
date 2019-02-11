#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'


'''
天勤主程序启动外部python进程的入口, 这样用:

run.py --file=C:\\tqsdk\\xx\\a.py --symbol=SHFE.cu1801 --duration=30 --instance_id=ABCD --ins_service=http://....  --md_service=ws://xxxxx --trade_service=ws://....

此进程持续运行
'''

import os
import sys
import json
import asyncio
import argparse
import importlib
import inspect
import logging
from pathlib import Path

from tqsdk.tq.tqbase import TqBase
from tqsdk.tq.utility import input_param, load_strategy_file
from tqsdk.api import TqApi


class TqRunLogger(logging.Handler):
    def __init__(self, chan, instance_id):
        logging.Handler.__init__(self)
        self.chan = chan
        self.instance_id = instance_id

    def emit(self, record):
        print (record)
        self.chan.send_nowait({
            "aid": "log",
            "instance_id": self.instance_id,
            # "level": str(record.level),
            "content": self.format(record)
        })


def run():
    #获取命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--file')
    parser.add_argument('--instance_id')
    args = parser.parse_args()

    #加载策略文件
    t_class = load_strategy_file(args.file)
    if not t_class:
        return

    # 加载或输入参数
    param_file_name = os.path.join(str(Path.home()), args.instance_id + ".param")
    try:
        with open(param_file_name, "rt") as param_file:
            param_list = json.load(param_file)
    except IOError:
        param_list = input_param(t_class)
    if param_list is None:
        return
    with open(param_file_name, "wt") as param_file:
        json.dump(param_list, param_file)

    # api
    api = TqApi(args.instance_id, debug="C:\\tmp\\debug.log")
    instance = t_class(api, param_list=param_list)

    # log
    logger = logging.getLogger("TQ")
    logger.setLevel(logging.INFO)
    th = TqRunLogger(api.send_chan, args.instance_id)
    th.setLevel(logging.INFO)
    th.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(th)

    # run
    instance.on_start()
    while True:
        api.wait_update()
        instance.on_data()
    # try:
    #     instance.on_start()
    #     while True:
    #         api.wait_update()
    #         instance.on_data()
    # except Exception:
    #     pass
    #     # logger.log(...)


if __name__ == "__main__":
    run()
