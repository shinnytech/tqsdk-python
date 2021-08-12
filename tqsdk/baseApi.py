#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'

import asyncio
import functools
import sys
import time
from typing import Optional, Coroutine


class TqBaseApi(object):
    """
    天勤基类，处理 EventLoop 相关的调用
    """

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """
        创建天勤接口实例

        Args:
            loop(asyncio.AbstractEventLoop): [可选] 使用指定的 IOLoop, 默认创建一个新的.
        """
        self._loop = asyncio.SelectorEventLoop() if loop is None else loop  # 创建一个新的 ioloop, 避免和其他框架/环境产生干扰
        self._event_rev, self._check_rev = 0, 0
        self._wait_timeout = False  # wait_update 是否触发超时
        self._tasks = set()  # 由api维护的所有根task，不包含子task，子task由其父task维护
        self._exceptions = []  # 由api维护的所有task抛出的例外
        # 回测需要行情和交易 lockstep, 而 asyncio 没有将内部的 _ready 队列暴露出来,
        # 因此 monkey patch call_soon 函数用来判断是否有任务等待执行
        self._loop.call_soon = functools.partial(self._call_soon, self._loop.call_soon)
        # Windows系统下asyncio不支持KeyboardInterrupt的临时补丁
        if sys.platform.startswith("win"):
            self._create_task(self._windows_patch())

    def _create_task(self, coro: Coroutine, _caller_api: bool = False) -> asyncio.Task:
        task = self._loop.create_task(coro)
        py_ver = sys.version_info
        current_task = asyncio.Task.current_task(loop=self._loop) if (py_ver.major == 3 and py_ver.minor < 7) else asyncio.current_task(loop=self._loop)
        if current_task is None or _caller_api:  # 由 api 创建的 task，需要 api 主动管理
            self._tasks.add(task)
            task.add_done_callback(self._on_task_done)
        return task

    def _call_soon(self, org_call_soon, callback, *args, **kargs):
        """ioloop.call_soon的补丁, 用来追踪是否有任务完成并等待执行"""
        self._event_rev += 1
        return org_call_soon(callback, *args, **kargs)

    def _run_once(self):
        """执行 ioloop 直到 ioloop.stop 被调用"""
        if not self._exceptions:
            self._loop.run_forever()
        if self._exceptions:
            raise self._exceptions.pop(0)

    def _run_until_idle(self):
        """执行 ioloop 直到没有待执行任务"""
        while self._check_rev != self._event_rev:
            check_handle = self._loop.call_soon(self._check_event, self._event_rev + 1)
            try:
                self._run_once()
            finally:
                check_handle.cancel()

    def _run_until_task_done(self, task: asyncio.Task, deadline=None):
        try:
            self._wait_timeout = False
            if deadline is not None:
                deadline_handle = self._loop.call_later(max(0, deadline - time.time()), self._set_wait_timeout)
            while not self._wait_timeout and not task.done():
                self._run_once()
        finally:
            if deadline is not None:
                deadline_handle.cancel()
            task.cancel()

    def _check_event(self, rev):
        self._check_rev = rev
        self._loop.stop()

    def _set_wait_timeout(self):
        self._wait_timeout = True
        self._loop.stop()

    def _on_task_done(self, task):
        """当由 api 维护的 task 执行完成后取出运行中遇到的例外并停止 ioloop"""
        try:
            exception = task.exception()
            if exception:
                self._exceptions.append(exception)
        except asyncio.CancelledError:
            pass
        finally:
            self._tasks.remove(task)
            self._loop.stop()

    async def _windows_patch(self):
        """Windows系统下asyncio不支持KeyboardInterrupt的临时补丁, 详见 https://bugs.python.org/issue23057"""
        while True:
            await asyncio.sleep(1)

    def _close(self) -> None:
        self._run_until_idle()  # 由于有的处于 ready 状态 task 可能需要报撤单, 因此一直运行到没有 ready 状态的 task
        for task in self._tasks:
            task.cancel()
        while self._tasks:  # 等待 task 执行完成
            self._run_once()
        self._loop.run_until_complete(self._loop.shutdown_asyncgens())
        self._loop.close()
