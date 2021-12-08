#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'

import asyncio
import sys
from logging import Logger
from typing import Any, TYPE_CHECKING, Union

from shinny_structlog import ShinnyLoggerAdapter

if TYPE_CHECKING:
    from tqsdk.api import TqApi


class TqChan(asyncio.Queue):
    """
    用于协程间通讯的channel
    默认 TqChan._level = 0 ，打印日志时，tqsdk 内部 chan 发送的数据不会打印在日志文件中；
    测试或开发需要打印 chan 内部数据，可以在代码开始增加
    ```
    from tqsdk import TqChan
    TqChan._level = 10
    ```
    """

    _chan_id: int = 0
    _level: int = 0

    def __init__(self, api: 'TqApi', last_only: bool = False, logger: Union[Logger, ShinnyLoggerAdapter, None] = None,
                 chan_name: str = "") -> None:
        """
        创建channel实例

        Args:
            api (tqsdk.api.TqApi): TqApi 实例

            last_only (bool): 为True时只存储最后一个发送到channel的对象
        """
        logger = logger if logger else api._logger
        if isinstance(logger, Logger):
            self._logger = ShinnyLoggerAdapter(logger, chan_id=TqChan._chan_id, chan_name=chan_name)
        elif isinstance(logger, ShinnyLoggerAdapter):
            self._logger = logger.bind(chan_id=TqChan._chan_id, chan_name=chan_name)
        TqChan._chan_id += 1
        py_ver = sys.version_info
        asyncio.Queue.__init__(self, loop=api._loop) if (py_ver.major == 3 and py_ver.minor < 10) else asyncio.Queue.__init__(self)
        self._last_only = last_only
        self._closed = False

    def _logger_bind(self, **kwargs):
        self._logger = self._logger.bind(**kwargs)

    async def close(self) -> None:
        """
        关闭channel

        关闭后send将不起作用,recv在收完剩余数据后会立即返回None
        """
        if not self._closed:
            self._closed = True
            await asyncio.Queue.put(self, None)

    async def send(self, item: Any) -> None:
        """
        异步发送数据到channel中

        Args:
            item (any): 待发送的对象
        """
        if not self._closed:
            if self._last_only:
                while not self.empty():
                    asyncio.Queue.get_nowait(self)
            await asyncio.Queue.put(self, item)
            self._logger.log(TqChan._level, "tqchan send", item=item)

    def send_nowait(self, item: Any) -> None:
        """
        尝试立即发送数据到channel中

        Args:
            item (any): 待发送的对象

        Raises:
            asyncio.QueueFull: 如果channel已满则会抛出 asyncio.QueueFull
        """
        if not self._closed:
            if self._last_only:
                while not self.empty():
                    asyncio.Queue.get_nowait(self)
            asyncio.Queue.put_nowait(self, item)
            self._logger.log(TqChan._level, "tqchan send_nowait", item=item)

    async def recv(self) -> Any:
        """
        异步接收channel中的数据，如果channel中没有数据则一直等待

        Returns:
            any: 收到的数据，如果channel已被关闭则会立即收到None
        """
        if self._closed and self.empty():
            return None
        item = await asyncio.Queue.get(self)
        self._logger.log(TqChan._level, "tqchan recv", item=item)
        return item

    def recv_nowait(self) -> Any:
        """
        尝试立即接收channel中的数据

        Returns:
            any: 收到的数据，如果channel已被关闭则会立即收到None

        Raises:
            asyncio.QueueFull: 如果channel中没有数据则会抛出 asyncio.QueueEmpty
        """
        if self._closed and self.empty():
            return None
        item = asyncio.Queue.get_nowait(self)
        self._logger.log(TqChan._level, "tqchan recv_nowait", item=item)
        return item

    def recv_latest(self, latest: Any) -> Any:
        """
        尝试立即接收channel中的最后一个数据

        Args:
            latest (any): 如果当前channel中没有数据或已关闭则返回该对象

        Returns:
            any: channel中的最后一个数据
        """
        while (self._closed and self.qsize() > 1) or (not self._closed and not self.empty()):
            latest = asyncio.Queue.get_nowait(self)
        self._logger.log(TqChan._level, "tqchan recv_latest", item=latest)
        return latest

    def __aiter__(self):
        return self

    async def __anext__(self):
        value = await asyncio.Queue.get(self)
        if self._closed and self.empty():
            raise StopAsyncIteration
        self._logger.log(TqChan._level, "tqchan recv_next", item=value)
        return value

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
