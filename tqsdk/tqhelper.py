#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'tianqin'


import os
import sys
import json
import logging
import threading
import tempfile


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
            logging.getLogger("TQ").info(self.line[:-1])
            self.line = ""

    def flush(self):
        pass


def exception_handler(type, value, tb):
    while tb.tb_next:
        tb = tb.tb_next
    msg = "程序异常: %s, line %d" % (str(value), tb.tb_lineno)
    logging.getLogger("TQ").error(msg)


def setup_output_file(report_file, dt_func):
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
                        order = api.get_order(oid)
                        if order._this_session is not True:
                            continue
                        account_changed = True
                        json.dump({
                            "aid": "order",
                            "datetime": dt_func(),
                            "order": {k: v for k, v in order.items() if not k.startswith("_")},
                        }, out)
                        out.write("\n")
                        out.flush()
                    for tid in d.get("trade", {}).get(api.account_id, {}).get("trades", {}).keys():
                        trade = api.get_trade(tid)
                        order = api.get_order(trade.order_id)
                        if order._this_session is not True:
                            continue
                        account_changed = True
                        json.dump({
                            "aid": "trade",
                            "datetime": dt_func(),
                            "trade": {k: v for k, v in trade.items() if not k.startswith("_")},
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
        try:
            p = _winapi.OpenProcess(_winapi.PROCESS_ALL_ACCESS, False, self.tq_pid)
            os.waitpid(p, 0)
        except:
            pass
        finally:
            os._exit(0)


def monitor_extern_process(tq_pid):
    TqMonitorThread(tq_pid).start()


if sys.platform != "win32":
    import fcntl


class SingleInstanceException(BaseException):
    pass


def get_self_full_name():
    s = os.path.abspath(sys.argv[0])
    return s[0].upper() + s[1:]

class SingleInstance(object):
    def __init__(self, flavor_id=""):
        self.initialized = False
        self.instance_id = get_self_full_name().replace(
            "/", "-").replace(":", "").replace("\\", "-") + '-%s' % flavor_id
        self.lockfile = os.path.normpath(
            tempfile.gettempdir() + '/' + self.instance_id + '.lock')

        if sys.platform == 'win32':
            try:
                # file already exists, we try to remove (in case previous
                # execution was interrupted)
                if os.path.exists(self.lockfile):
                    os.unlink(self.lockfile)
                self.fd = os.open(
                    self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except OSError:
                type, e, tb = sys.exc_info()
                if e.errno == 13:
                    raise SingleInstanceException()
                print(e.errno)
                raise
        else:  # non Windows
            self.fp = open(self.lockfile, 'w')
            self.fp.flush()
            try:
                fcntl.lockf(self.fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                raise SingleInstanceException()
        self.initialized = True

    def __del__(self):
        if not self.initialized:
            return
        try:
            if sys.platform == 'win32':
                if hasattr(self, 'fd'):
                    os.close(self.fd)
                    os.unlink(self.lockfile)
            else:
                fcntl.lockf(self.fp, fcntl.LOCK_UN)
                if os.path.isfile(self.lockfile):
                    os.unlink(self.lockfile)
        except Exception as e:
            sys.exit(-1)

