# !usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'

import datetime
import os


DEBUG_DIR = os.path.join(os.path.expanduser('~'), ".tqsdk/logs")


def _get_log_name():
    """返回默认 debug 文件生成的位置"""
    if not os.path.exists(DEBUG_DIR):
        os.makedirs(os.path.join(os.path.expanduser('~'), ".tqsdk/logs"), exist_ok=True)
    return os.path.join(DEBUG_DIR, f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}-{os.getpid()}.log")


def _clear_logs():
    """清除最后修改时间是 n 天前的日志"""
    if not os.path.exists(DEBUG_DIR):
        return
    n = os.getenv("TQ_SAVE_LOG_DAYS", 30)
    dt = datetime.datetime.now() - datetime.timedelta(days=int(n))
    for log in os.listdir(DEBUG_DIR):
        path = os.path.join(DEBUG_DIR, log)
        try:
            if datetime.datetime.fromtimestamp(os.stat(path).st_mtime) < dt:
                os.remove(path)
        except:
            pass  # 忽略抛错
