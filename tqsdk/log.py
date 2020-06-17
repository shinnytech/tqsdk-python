# !usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'

import datetime
import logging
import os
import warnings
from functools import wraps
from inspect import isclass, isroutine
from types import FunctionType

from .__version__ import __version__

DEBUG_DIR = os.path.join(os.path.expanduser('~'), ".tqsdk/logs")


def _get_log_format(is_backtest=None):
    """返回日志格式"""
    if is_backtest:
        return logging.Formatter(f'%(levelname)6s - %(message)s')
    else:
        return logging.Formatter(f'%(asctime)s - %(levelname)6s - %(message)s')


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


def _traced(*args):
    obj = args[0] if args else None
    if obj is None:  # treat `@_traced()' as equivalent to `@_traced'
        return _traced
    if isclass(obj):  # `@_traced' class
        return _install_traceable_methods(obj)
    elif isroutine(obj):  # `@_traced' function
        return _make_traceable_function(obj)


def _install_traceable_methods(class_):
    traceable_method_names = []
    for (name, member) in class_.__dict__.items():
        if isroutine(member) and (not name.startswith("_") or name == "__init__"):
            traceable_method_names.append(name)

    # replace each named method with a tracing proxy method
    for method_name in traceable_method_names:
        descriptor = class_.__dict__[method_name]
        descriptor_type = type(descriptor)

        if descriptor_type is FunctionType:
            tracing_proxy_descriptor = _make_traceable_instancemethod(descriptor, class_.__name__)
        elif descriptor_type is classmethod:
            tracing_proxy_descriptor = _make_traceable_classmethod(descriptor, class_.__name__)
        elif descriptor_type is staticmethod:
            tracing_proxy_descriptor = _make_traceable_staticmethod(descriptor, class_.__name__)
        else:
            # should be unreachable, but issue a warning just in case
            warnings.warn("tracing not supported for %r" % descriptor_type)
            continue

        # class_.__dict__ is a mapping proxy; direct assignment not supported
        setattr(class_, method_name, tracing_proxy_descriptor)

    return class_


def _make_traceable_function(function, class_name=None):
    @wraps(function)
    def traced_function_delegator(*args, **keywords):
        return traced_function_delegator._proxy(function, args, keywords)
    traced_function_delegator._proxy = _FunctionTracingProxy(function, class_name)
    return traced_function_delegator


def _make_traceable_instancemethod(unbound_function, class_name=None):
    @wraps(unbound_function)
    def traced_instancemethod_delegator(self_, *args, **keywords):
        method = unbound_function.__get__(self_, self_.__class__)
        return traced_instancemethod_delegator._proxy(method, args, keywords)
    traced_instancemethod_delegator._proxy = _FunctionTracingProxy(unbound_function, class_name)
    return traced_instancemethod_delegator


def _make_traceable_classmethod(method_descriptor, class_name=None):
    function = method_descriptor.__func__
    @wraps(function)
    def traced_classmethod_delegator(cls, *args, **keywords):
        method = method_descriptor.__get__(None, cls)
        return traced_classmethod_delegator._proxy(method, args, keywords)
    traced_classmethod_delegator._proxy = _FunctionTracingProxy(function, class_name)
    return classmethod(traced_classmethod_delegator)


def _make_traceable_staticmethod(method_descriptor, class_name=None):
    return staticmethod(_make_traceable_function(method_descriptor.__func__, class_name))


class _FunctionTracingProxy(object):

    _logger = logging.getLogger("TqApi.Trace")

    def __init__(self, function, class_name=None):
        """
        :arg function: the function being traced
        """
        func_code = function.__code__
        self._func_filename = func_code.co_filename
        self._func_lineno = func_code.co_firstlineno
        self._func_name = f"{(class_name + '.') if class_name else ''}{function.__name__}"

    def __call__(self, function, args, keywords):
        """Call *function*, tracing its arguments and return value.
        :arg tuple args: the positional arguments for *function*
        :arg dict keywords: the keyword arguments for *function*
        :return:
           the value returned by calling *function* with positional
           arguments *args* and keyword arguments *keywords*
        """
        self._logger.handle(logging.LogRecord(
            self._logger.name,  # name
            logging.DEBUG,  # level
            self._func_filename,  # pathname
            self._func_lineno,  # lineno
            "%s CALL *%r **%r",  # msg
            (self._func_name, args, keywords),  # args
            None,  # exc_info
        ))
        value = function(*args, **keywords)
        self._logger.handle(logging.LogRecord(
            self._logger.name,
            logging.DEBUG,
            self._func_filename,
            self._func_lineno,
            "%s RETURN %r",
            (self._func_name, value),
            None,
        ))
        return value
