#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'


'''
天勤主程序启动外部python进程的入口, 这样用:

run.py --file=C:\\tqsdk\\xx\\a.py --instance_id=ABCD --ins_service=http://....  --md_service=ws://xxxxx --trade_service=ws://....

此进程持续运行
'''

import os
import sys
import json
import argparse
import logging
import time
from pathlib import Path
from contextlib import closing

from tqsdk.tq.utility import input_param, load_strategy_file
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


async def desc_watcher(api, instance_id, desc_chan):
    async for desc in desc_chan:
        api.send_chan.send_nowait({
            "aid": "status",
            "datetime": int(time.time()*1e9),
            "instance_id": instance_id,
            "desc": desc,
        })


def run():
    #获取命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--file')
    parser.add_argument('--instance_id')
    args = parser.parse_args()

    # api
    api = TqApi(TqAccount("", args.instance_id, ""), url="ws://127.0.0.1:7777/" + args.instance_id, debug="C:\\tmp\\debug.log")
    with closing(api):
        # log
        logger = logging.getLogger("TQ")
        logger.setLevel(logging.INFO)
        th = TqRunLogger(api.send_chan, args.instance_id)
        th.setLevel(logging.INFO)
        logger.addHandler(th)

        try:
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

            # 创建策略实例
            instance = t_class(api, param_list=param_list)
            api.create_task(desc_watcher(api, args.instance_id, instance.desc_chan))

            # run
            instance.on_start()
            while True:
                api.wait_update()
                instance.on_data()
        except ModuleNotFoundError:
            logger.exception("加载策略文件失败")
        except IndentationError:
            logger.exception("策略文件缩进格式错误")


if __name__ == "__main__":
    run()
