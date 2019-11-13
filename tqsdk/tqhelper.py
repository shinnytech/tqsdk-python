#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'tianqin'

import os
import sys
import logging
import threading
import tempfile
import argparse
import datetime
import traceback
from functools import partial


class LogHandlerChan(logging.Handler):
    def __init__(self, chan, dt_func):
        logging.Handler.__init__(self)
        self.chan = chan
        self.dt_func = dt_func

    def emit(self, record):
        d = {
            "aid": "log",
            "datetime": self.dt_func(),
            "level": str(record.levelname),
            "content": record.msg % record.args,
        }
        if record.exc_info:
            ls = traceback.format_exception(record.exc_info[0], record.exc_info[1], record.exc_info[2])
            d["content"] += "".join(ls)
        self.chan.send_nowait(d)


class PrintWriterToLog:
    def __init__(self, logger):
        self.orign_stdout = sys.stdout
        self.line = ""
        self.logger = logger

    def write(self, text):
        if self.orign_stdout:
            self.orign_stdout.write(text)
        self.line += text
        if self.line[-1] == "\n":
            self.logger.info(self.line[:-1])
            self.line = ""

    def flush(self):
        if self.orign_stdout:
            self.orign_stdout.flush()


def exception_handler(api, orign_hook, type, value, tb):
    logging.getLogger("TQ").error("程序异常", exc_info=(type, value, tb))
    api.close()
    orign_hook(type, value, tb)


def write_snapshot(dt_func, tq_send_chan, account, positions):
    tq_send_chan.send_nowait({
        "aid": "snapshot",
        "datetime": dt_func(),
        "accounts": {
            "CNY": {k: v for k, v in account.items() if not k.startswith("_")},
        },
        "positions": {k: {pk: pv for pk, pv in v.items() if not pk.startswith("_")} for k, v in positions.items() if
                      not k.startswith("_")},
    })


async def account_watcher(api, dt_func, tq_send_chan):
    account = api.get_account()
    positions = api.get_position()
    try:
        async with api.register_update_notify() as update_chan:
            async for _ in update_chan:
                account_changed = api.is_changing(account, "static_balance")
                for d in api._diffs:
                    for oid in d.get("trade", {}).get(api._account.account_id, {}).get("orders", {}).keys():
                        order = api.get_order(oid)
                        if order._this_session is not True:
                            continue
                        account_changed = True
                        tq_send_chan.send_nowait({
                            "aid": "order",
                            "datetime": dt_func(),
                            "order": {k: v for k, v in order.items() if not k.startswith("_")},
                        })
                    for tid in d.get("trade", {}).get(api._account.account_id, {}).get("trades", {}).keys():
                        trade = api.get_trade(tid)
                        order = api.get_order(trade.order_id)
                        if order._this_session is not True:
                            continue
                        account_changed = True
                        tq_send_chan.send_nowait({
                            "aid": "trade",
                            "datetime": dt_func(),
                            "trade": {k: v for k, v in trade.items() if not k.startswith("_")},
                        })
                if account_changed:
                    write_snapshot(dt_func, tq_send_chan, account, positions)
    finally:
        write_snapshot(dt_func, tq_send_chan, account, positions)


class TqMonitorThread(threading.Thread):
    """
    监控天勤进程存活情况
    """

    def __init__(self, tq_pid):
        threading.Thread.__init__(self, daemon=True)
        self.tq_pid = tq_pid

    def run(self):
        # TODO: 如果发布 mac / linux 天勤客户端，未来还需要在 mac / linux 上实现同样的功能。
        if not sys.platform.startswith("win"):
            return
        import _winapi
        try:
            p = _winapi.OpenProcess(_winapi.PROCESS_ALL_ACCESS, False, self.tq_pid)
            os.waitpid(p, 0)
        except:
            pass
        finally:
            os._exit(0)


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


class Forwarding(object):
    """
    作为数据转发的中间模块, 创建与天勤的新连接, 并过滤TqApi向上游发送的数据.
    对于这个新连接: 发送所有的 set_chart_data 类型数据包,以及抄送所有的 subscribe_quote, set_chart类型数据包
    """

    def __init__(self, api, api_send_chan, api_recv_chan, upstream_send_chan, upstream_recv_chan, tq_send_chan,
                 tq_recv_chan):
        self.api = api
        self.api_send_chan = api_send_chan
        self.api_recv_chan = api_recv_chan
        self.upstream_send_chan = upstream_send_chan
        self.upstream_recv_chan = upstream_recv_chan
        self.tq_send_chan = tq_send_chan
        self.tq_recv_chan = tq_recv_chan
        self.subscribed = None
        self.order_symbols = set()

    async def _forward(self):
        to_downstream_task = self.api.create_task(
            self._forward_to_downstream(self.api_recv_chan, self.upstream_recv_chan))  # 转发给下游
        to_upstream_task = self.api.create_task(
            self._forward_to_upstream(self.api_send_chan, self.upstream_send_chan, self.tq_send_chan))  # 转发给上游
        try:
            async for pack in self.tq_recv_chan:
                pass
        finally:
            to_downstream_task.cancel()
            to_upstream_task.cancel()

    async def _forward_to_downstream(self, api_recv_chan, upstream_recv_chan):
        """转发给下游"""
        async for pack in upstream_recv_chan:
            await api_recv_chan.send(pack)

    async def _forward_to_upstream(self, api_send_chan, upstream_send_chan, tq_send_chan):
        """转发给上游"""
        async for pack in api_send_chan:
            if pack["aid"] == "set_chart_data":
                await tq_send_chan.send(pack)
            elif pack["aid"] == "insert_order":
                self.order_symbols.add(pack["exchange_id"] + "." + pack["instrument_id"])
                await self._send_subscribed_to_tq()
                await upstream_send_chan.send(pack)
            elif pack["aid"] == "set_chart" or pack["aid"] == "subscribe_quote":
                await self._send_subscribed_to_tq()
                await upstream_send_chan.send(pack)
            else:
                await upstream_send_chan.send(pack)

    async def _send_subscribed_to_tq(self):
        d = []
        for item in self.api._requests["klines"].keys():
            for symbol in item[0]:  # 如果同时订阅多个合约，分别发送给tq
                d.append({
                    "symbol": symbol,
                    "dur_nano": item[1] * 1000000000
                })
        for item in self.api._requests["ticks"].keys():
            d.append({
                "symbol": item[0],
                "dur_nano": 0
            })
        for symbol in self.api._requests["quotes"]:
            d.append({
                "symbol": symbol
            })
        for symbol in self.order_symbols:
            d.append({
                "symbol": symbol
            })
        if d != self.subscribed:
            self.subscribed = d
            await self.tq_send_chan.send({
                "aid": "subscribed",
                "subscribed": self.subscribed
            })


def link_tq(api):
    """
    处理py进程到天勤的连接

    根据天勤提供的命令行参数, 决定 TqApi 工作方式

    * 直接调整api的参数

    TqApi运行过程中的一批信息主动发送到天勤显示

    * 进程启动和停止
    * set_chart_data 指令全部发往天勤绘图
    * 所有 log / print 信息传递一份
    * exception 发送一份
    * 所有报单/成交记录抄送一份

    :return: (account, backtest, md_url)
    """
    from tqsdk.api import TqChan, TqAccount
    from tqsdk.sim import TqSim
    # 解析命令行参数
    parser = argparse.ArgumentParser()
    # 天勤连接基本参数
    parser.add_argument('--_action', type=str, required=False)
    parser.add_argument('--_tq_pid', type=int, required=False)
    parser.add_argument('--_tq_url', type=str, required=False)
    # action==run时需要这几个
    parser.add_argument('--_broker_id', type=str, required=False)
    parser.add_argument('--_account_id', type=str, required=False)
    parser.add_argument('--_password', type=str, required=False)
    # action==backtest时需要这几个
    parser.add_argument('--_start_dt', type=str, required=False)
    parser.add_argument('--_end_dt', type=str, required=False)
    parser.add_argument('--_init_balance', type=str, required=False)
    # action==mdreplay时需要这几个
    parser.add_argument('--_ins_url', type=str, required=False)
    parser.add_argument('--_md_url', type=str, required=False)
    args, unknown = parser.parse_known_args()

    # 非天勤启动时直接返回
    if args._action is None:
        return None, None
    if args._tq_pid is None:
        raise Exception("_tq_pid 参数缺失")
    if args._tq_url is None:
        raise Exception("_tq_url 参数缺失")
    if args._action == "run" and (not args._broker_id or not args._account_id or not args._password):
        raise Exception("run 必要参数缺失")
    if args._action == "backtest" and (not args._start_dt or not args._end_dt):
        raise Exception("backtest 必要参数缺失")
    if args._action == "mdreplay" and (not args._ins_url or not args._md_url):
        raise Exception("mdreplay 必要参数缺失")

    # 监控天勤进程存活情况
    TqMonitorThread(args._tq_pid).start()

    # 建立到天勤进程的连接
    tq_send_chan, tq_recv_chan = TqChan(api), TqChan(api)  # 连接到天勤的channel
    api.create_task(api._connect(args._tq_url, tq_send_chan, tq_recv_chan))  # 启动到天勤客户端的连接

    # 根据运行模式分别执行不同的初始化任务
    if args._action == "run":
        if isinstance(api._account, TqAccount) and (
                api._account.broker_id != args._broker_id or api._account.account_id != args._account_id):
            raise Exception("策略代码与设置中的账户参数冲突。可尝试删去代码中的账户参数 TqAccount，以终端或者插件设置的账户参数运行。")
        instance = SingleInstance(args._account_id)
        api._account = TqAccount(args._broker_id, args._account_id, args._password)
        api._backtest = None
        dt_func = lambda: int(datetime.datetime.now().timestamp() * 1e9)
        tq_send_chan.send_nowait({
            "aid": "register_instance",
            "instance_id": instance.instance_id,
            "full_path": get_self_full_name(),
            "instance_pid": os.getpid(),
            "instance_type": "RUN",
            "broker_id": args._broker_id,
            "account_id": args._account_id,
            "password": args._password,
        })
    elif args._action == "backtest":
        instance = SingleInstance("%s-%s" % (args._start_dt, args._end_dt))
        if args._init_balance:
            try:
                api._account = TqSim(float(args._init_balance))
            except ValueError:
                raise Exception("backtest 参数错误, _init_balance = " + args._init_balance + " 不是数字")
        elif not isinstance(api._account, TqSim):
            api._account = TqSim()
        from tqsdk.backtest import TqBacktest
        start_date = datetime.datetime.strptime(args._start_dt, '%Y%m%d')
        end_date = datetime.datetime.strptime(args._end_dt, '%Y%m%d')
        api._backtest = TqBacktest(start_dt=start_date, end_dt=end_date)
        dt_func = lambda: api._account._get_current_timestamp()
        tq_send_chan.send_nowait({
            "aid": "register_instance",
            "instance_id": instance.instance_id,
            "full_path": get_self_full_name(),
            "instance_pid": os.getpid(),
            "instance_type": "BACKTEST",
            "start_dt": args._start_dt,
            "end_dt": args._end_dt,
        })
    elif args._action == "mdreplay":
        instance = SingleInstance(args._account_id)
        api._account = TqSim(account_id=args._account_id)
        api._backtest = None
        api._md_url = args._md_url
        api._ins_url = args._ins_url
        dt_func = lambda: api._account._get_current_timestamp()
        tq_send_chan.send_nowait({
            "aid": "register_instance",
            "instance_id": instance.instance_id,
            "full_path": get_self_full_name(),
            "instance_pid": os.getpid(),
            "instance_type": "REPLAY",
            "account_id": "SIM",
        })
    else:
        raise Exception("_action 参数异常")

    # print输出, exception信息转发到天勤
    logger = logging.getLogger("TQ")
    logger.setLevel(logging.INFO)
    logger.addHandler(LogHandlerChan(tq_send_chan, dt_func=dt_func))  # log输出到天勤接口
    sys.stdout = PrintWriterToLog(logger)  # print信息转向log输出
    sys.excepthook = partial(exception_handler, api, sys.excepthook)  # exception信息转向log输出

    # 向api注入监控任务, 将账户交易信息主动推送到天勤
    api.create_task(account_watcher(api, dt_func, tq_send_chan))
    return tq_send_chan, tq_recv_chan
