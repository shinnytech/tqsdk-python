#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'tianqin'


import os
import sys
import json
import logging
import datetime
import threading


class LogHandlerFile(logging.Handler):
    def __init__(self, out_file, dt_func):
        logging.Handler.__init__(self)
        self.out_file = out_file
        self.dt_func = dt_func

    def emit(self, record):
        json.dump({
            "aid": "log",
            "datetime": self.dt_func(),
            "level": str(record.levelname),
            "content": record.msg,
        }, self.out_file)
        self.out_file.write("\n")
        self.out_file.flush()


class PrintWriterFile:
    def __init__(self):
        self.line = ""

    def write(self, text):
        self.line += text
        if self.line[-1] == "\n":
            logging.getLogger("TQ").info(self.line)
            self.line = ""

    def flush(self):
        pass


def exception_handler(type, value, tb):
    while tb.tb_next:
        tb = tb.tb_next
    msg = "程序异常: %s, line %d" % (str(value), tb.tb_lineno)
    logging.getLogger("TQ").error(msg)


def setup_output_file(report_file, instance_id, dt_func):
    sys.stdout = PrintWriterFile()
    sys.excepthook = exception_handler
    logging.getLogger("TQ").addHandler(LogHandlerFile(report_file, dt_func=dt_func))


def write_snapshot(dt_func, out, account, positions):
    json.dump({
        "aid": "snapshot",
        "datetime": dt_func(),
        "accounts": {
            "CNY": {k: v for k, v in account.items() if not k.startswith("_")},
        },
        "positions": {k: {pk: pv for pk, pv in v.items() if not pk.startswith("_")} for k, v in positions.items() if not k.startswith("_")},
    }, out)
    out.write("\n")
    out.flush()


async def account_watcher(api, dt_func, out):
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
                            "datetime": dt_func(),
                            "order": {k: v for k, v in api.get_order(oid).items() if not k.startswith("_")},
                        }, out)
                        out.write("\n")
                        out.flush()
                    for tid in d.get("trade", {}).get(api.account_id, {}).get("trades", {}).keys():
                        account_changed = True
                        json.dump({
                            "aid": "trade",
                            "datetime": dt_func(),
                            "trade": {k: v for k, v in trades[tid].items() if not k.startswith("_")},
                        }, out)
                        out.write("\n")
                        out.flush()
                if account_changed:
                    write_snapshot(dt_func, out, account, positions)
    finally:
        write_snapshot(dt_func, out, account, positions)


class TqMonitorThread (threading.Thread):
    def __init__(self, tq_pid):
        threading.Thread.__init__(self, daemon=True)
        self.tq_pid = tq_pid

    def run(self):
        import _winapi
        p = _winapi.OpenProcess(_winapi.PROCESS_ALL_ACCESS, False, self.tq_pid)
        os.waitpid(p, 0)
        os._exit(0)


def monitor_extern_process(tq_pid):
    TqMonitorThread(tq_pid).start()

