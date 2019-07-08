#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'tianqin'


'''
'''

import sys
import os
import sys
import json
import argparse
import logging
import importlib
import datetime
import threading
import _winapi


class PrintWriterNet:
    def __init__(self, chan, instance_id):
        self.orign_stdout = sys.stdout
        self.chan = chan
        self.instance_id = instance_id
        self.line = ""

    def write(self, text):
        self.line += text
        if self.line[-1] == "\n":
            dt = int(datetime.datetime.now().timestamp() * 1e9)
            self.chan.send_nowait({
                "aid": "log",
                "datetime": dt,
                "instance_id": self.instance_id,
                "level": "INFO",
                "content": self.line[:-1],
            })
            self.line = ""

    def flush(self):
        pass


class LogHandlerNet(logging.Handler):
    def __init__(self, chan, instance_id):
        logging.Handler.__init__(self)
        self.chan = chan
        self.instance_id = instance_id

    def emit(self, record):
        dt = int(datetime.datetime.now().timestamp()*1e9)
        if record.exc_info:
            if record.exc_info[2].tb_next:
                msg = "%s, line %d, %s" % (record.msg, record.exc_info[2].tb_next.tb_lineno, str(record.exc_info[1]))
            else:
                msg = "%s, %s" % (record.msg, str(record.exc_info[1]))
        else:
            msg = record.msg
        self.chan.send_nowait({
            "aid": "log",
            "datetime": dt,
            "instance_id": self.instance_id,
            "level": str(record.levelname),
            "content": msg,
        })


def redirect_output_to_net(api, instance_id):
    sys.stdout = PrintWriterNet(api.send_chan, instance_id)
    logger = logging.getLogger("TQ")
    logger.setLevel(logging.INFO)
    th = LogHandlerNet(api.send_chan, instance_id)
    th.setLevel(logging.INFO)
    logger.addHandler(th)


class PrintWriterFile:
    def __init__(self, out_file, instance_id):
        self.orign_stdout = sys.stdout
        self.out_file = out_file
        self.instance_id = instance_id
        self.line = ""

    def write(self, text):
        self.line += text
        if self.line[-1] == "\n":
            dt = int(datetime.datetime.now().timestamp() * 1e9)
            json.dump({
                "aid": "log",
                "datetime": dt,
                "instance_id": self.instance_id,
                "level": "INFO",
                "content": self.line[:-1],
            }, self.out_file)
            self.line = ""
            self.out_file.write("\n")
            self.out_file.flush()

    def flush(self):
        pass


class TqBacktestLogger(logging.Handler):
    def __init__(self, sim, out):
        logging.Handler.__init__(self)
        self.sim = sim
        self.out = out

    def emit(self, record):
        if record.exc_info:
            if record.exc_info[2].tb_next:
                msg = "%s, line %d, %s" % (record.msg, record.exc_info[2].tb_next.tb_lineno, str(record.exc_info[1]))
            else:
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


def redirect_output_to_file(report_file, tqsim, instance_id):
    sys.stdout = PrintWriterFile(report_file, instance_id)
    logger = logging.getLogger("TQ")
    logger.setLevel(logging.INFO)
    logger.addHandler(TqBacktestLogger(tqsim, report_file))


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


class TqMonitorThread (threading.Thread):
    def __init__(self, tq_pid):
        threading.Thread.__init__(self)
        self.tq_pid = tq_pid

    def run(self):
        p = _winapi.OpenProcess(_winapi.PROCESS_ALL_ACCESS, False, self.tq_pid)
        os.waitpid(p, 0)
        os._exit(0)


def monitor_extern_process(tq_pid):
    TqMonitorThread(tq_pid).start()

