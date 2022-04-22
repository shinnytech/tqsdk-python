# !usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'

import datetime
import os

import psutil

DEBUG_DIR = os.path.join(os.path.expanduser('~'), ".tqsdk/logs")


def _get_log_name():
    """返回默认 debug 文件生成的位置"""
    if not os.path.exists(DEBUG_DIR):
        os.makedirs(os.path.join(os.path.expanduser('~'), ".tqsdk/logs"), exist_ok=True)
    return os.path.join(DEBUG_DIR, f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}-{os.getpid()}.log")


def _get_disk_free():
    free = psutil.disk_usage(DEBUG_DIR).free
    return free / 1e9


def _log_path_list():
    # 获取所有日志文件路径，并按照修改时间递减排序
    path_list = [os.path.join(DEBUG_DIR, log) for log in os.listdir(DEBUG_DIR)]
    path_list.sort(key=lambda x: _stat_dt(x))
    return path_list


def _stat_dt(path):
    try:
        return datetime.datetime.fromtimestamp(os.stat(path).st_mtime)
    except:
        return datetime.datetime.now()


def _remove_log(path):
    try:
        os.remove(path)
    except:
        pass  # 忽略抛错


def _clear_logs():
    """清除最后修改时间是 n 天前的日志"""
    if not os.path.exists(DEBUG_DIR):
        return
    n = os.getenv("TQ_SAVE_LOG_DAYS", 30)
    # 清除最后修改时间是 n 天前的日志
    # 清空日志保证剩余空间大于 3G，但是最近 3 个自然日的一定不会清除，保证最近的一个交易日不会被清除日志
    dt30 = datetime.datetime.now() - datetime.timedelta(days=int(n))
    dt3 = datetime.datetime.now() - datetime.timedelta(days=int(3))
    for path in _log_path_list():
        if _stat_dt(path) < dt30 or (_get_disk_free() < 3 and _stat_dt(path) < dt3):
            _remove_log(path)
        else:
            break
