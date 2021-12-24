#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'mayanqiong'

import asyncio
from abc import abstractmethod


class TqModule(object):

    async def _run(self, api, api_send_chan, api_recv_chan, *args):
        """
        可以接入 n 个上游，1 个下游
        """
        assert len(args) % 2 == 0 and len(args) > 0
        self._diffs = []
        self._up_chans = [{"send_chan": args[i], "recv_chan": args[i + 1]} for i in range(0, len(args), 2)]
        self._up_pending_peek = [False for _ in self._up_chans]  # 是否有发给上游的 peek_message，未收到过回复
        self._pending_peek = False  # 是否有下游收到未处理的 peek_message
        up_handle_tasks = [
            api.create_task(self._up_handler(api_send_chan, item["recv_chan"], chan_index=i))
            for i, item in enumerate(self._up_chans)
            ]
        try:
            async for pack in api_send_chan:
                if pack["aid"] == "peek_message":
                    # 处理下游发送的 peek_message
                    self._pending_peek = True
                    await self._send_diff(api_recv_chan)
                    if self._pending_peek:
                        for i, pending_peek in enumerate(self._up_pending_peek):
                            if pending_peek is False:
                                # 控制"peek_message"发送: 下游发送了 peek_message，并且上游没有 pending_peek 才会发送
                                await self._up_chans[i]["send_chan"].send({"aid": "peek_message"})
                                self._up_pending_peek[i] = True
                elif pack.get('_up_chan_index', None) is not None:
                    # 处理上游发送的数据包
                    _up_chan_index = pack.pop("_up_chan_index")
                    await self._handle_recv_data(pack, self._up_chans[_up_chan_index]["recv_chan"])
                    await self._send_diff(api_recv_chan)
                else:
                    # 处理下游发送的其他请求
                    await self._handle_req_data(pack)
                    await self._send_diff(api_recv_chan)
        finally:
            [task.cancel() for task in up_handle_tasks]
            await asyncio.gather(*up_handle_tasks, return_exceptions=True)

    async def _up_handler(self, api_send_chan, recv_chan, chan_index):
        async for pack in recv_chan:
            pack['_up_chan_index'] = chan_index
            if pack['aid'] == 'rtn_data':
                self._up_pending_peek[chan_index] = False
            await api_send_chan.send(pack)

    async def _send_diff(self, api_recv_chan):
        pk = self._pending_peek
        if self._pending_peek and self._diffs:
            rtn_data = {
                "aid": "rtn_data",
                "data": self._diffs,
            }
            self._diffs = []
            self._pending_peek = False
            await api_recv_chan.send(rtn_data)
        await self._on_send_diff(pk)

    @abstractmethod
    async def _handle_recv_data(self, pack, chan):
        """
        处理所有上游收到的数据包，这里应该将需要发送给下游的数据 append 到 self._diffs
        pack: 收到的数据包
        chan: 收到此数据包的 channel
        """
        pass

    @abstractmethod
    async def _handle_req_data(self, pack):
        """
        处理所有下游发送的非 peek_message 数据包
        这里应该将发送的请求转发到指定的某个上游 channel
        """
        pass

    async def _on_send_diff(self, peeding_pk):
        """
        TqModule 调用 _send_diff 时，最后会执行的回调函数；
        TqModule 处理所有 pack 都会调用 self._send_diff()，可以在此处处理额外业务逻辑。
        pending_peek 表示调用 _send_diff 时，self._pending_peek 的值
        """
        pass
