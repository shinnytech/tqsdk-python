#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'

import asyncio
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from tqsdk.api import TqApi


class TqChan(asyncio.Queue):
    """用于协程间通讯的channel"""

    def __init__(self, api: 'TqApi', last_only: bool = False) -> None:
        """
        创建channel实例

        Args:
            api (tqsdk.api.TqApi): TqApi 实例

            last_only (bool): 为True时只存储最后一个发送到channel的对象
        """
        asyncio.Queue.__init__(self, loop=api._loop)
        self._last_only = last_only
        self._closed = False

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

    async def recv(self) -> Any:
        """
        异步接收channel中的数据，如果channel中没有数据则一直等待

        Returns:
            any: 收到的数据，如果channel已被关闭则会立即收到None
        """
        if self._closed and self.empty():
            return None
        return await asyncio.Queue.get(self)

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
        return asyncio.Queue.get_nowait(self)

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
        return latest

    def __aiter__(self):
        return self

    async def __anext__(self):
        value = await asyncio.Queue.get(self)
        if self._closed and self.empty():
            raise StopAsyncIteration
        return value

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
