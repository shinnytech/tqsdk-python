#!/usr/bin/env python
#  -*- coding: utf-8 -*-


import json
import lzma
import os
import threading
import asyncio
import websockets
from aiohttp import web


class MockInsServer():
    def __init__(self, port):
        self.loop = asyncio.new_event_loop()
        self.port = port
        self.symbols_dir = os.path.join(os.path.dirname(__file__), 'symbols')
        self.stop_signal = self.loop.create_future()
        self.semaphore = threading.Semaphore(value=0)
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        self.semaphore.acquire()

    def close(self):
        self.loop.call_soon_threadsafe(lambda: self.stop_signal.set_result(0))
        self.thread.join()

    async def handle(self, request):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path, "symbols", request.url.name + ".lzma")
        file = lzma.open(file_path, "rt", encoding="utf-8")
        return web.json_response(json.loads(file.read()))

    async def task_serve(self):
        try:
            app = web.Application()
            app.add_routes([web.get('/t/md/symbols/{tail:.*}', self.handle)])
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '127.0.0.1', self.port)
            await site.start()
            self.semaphore.release()
            await self.stop_signal
        finally:
            await runner.shutdown()
            await runner.cleanup()

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.task_serve())


class MockServer():
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.connections = {}
        self.server_md = None
        self.server_td = None
        self.md_port = 5100
        self.td_port = 5200
        self._expecting = {}
        self.stop_signal = self.loop.create_future()
        self.semaphore = threading.Semaphore(value=0)

    def close(self):
        self.script_file.close()
        assert not self._expecting
        self.loop.call_soon_threadsafe(lambda: self.stop_signal.set_result(0))
        self.thread.join()

    async def _handler_md(self, connection, path):
        await self.on_connected("md", connection)
        try:
            while True:
                s = await self.connections["md"].recv()
                pack = json.loads(s)
                await self.on_received("md", pack)
        except websockets.exceptions.ConnectionClosedOK as e:
            assert e.code == 1000

    async def _handler_td(self, connection, path):
        await self.on_connected("td", connection)
        try:
            while True:
                s = await self.connections["td"].recv()
                pack = json.loads(s)
                if pack["aid"] == "peek_message":
                    continue
                await self.on_received("td", pack)
        except websockets.exceptions.ConnectionClosedOK as e:
            assert e.code == 1000

    def run(self, script_file_name):
        self.script_file_name = script_file_name
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        self.semaphore.acquire()

    async def _server(self):
        async with websockets.serve(self._handler_md, "127.0.0.1", self.md_port) as self.server_md:
            async with websockets.serve(self._handler_td, "127.0.0.1", self.td_port) as self.server_td:
                self.semaphore.release()
                await self.stop_signal

    def _run(self):
        if str.endswith(self.script_file_name, "lzma"):
            self.script_file = lzma.open(self.script_file_name, "rt", encoding="utf-8")
        else:  # 用于本地script还未压缩成lzma文件时运行测试用例
            self.script_file = open(self.script_file_name, "rt", encoding="utf-8")
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._server())

    async def _process_script(self):
        # 每次处理日志文件中的一行, 直至需要输入为止
        self._expecting = {}
        for line in self.script_file:
            # 2019-09-09 16:22:40,652 - DEBUG - websocket message sent to wss://openmd.shinnytech.com/t/md/front/mobile: {"aid": "subscribe_quote",
            item = {}
            if "websocket message sent" in line and "peek_message" not in line:  # 在api角度的sent
                item["type"] = "sent"
            elif "websocket message received" in line:  # 在api角度的received
                item["type"] = "received"
            else:
                continue
            if "openmd" in line:
                item["source"] = "md"
            elif "opentd" in line:
                item["source"] = "td"
            else:
                raise Exception()
            content_start_pos = line.find("{")
            content = line[content_start_pos:]
            item["content"] = json.loads(content)
            if item["type"] == "sent":
                self._expecting = item
                break
            elif item["type"] == "received":
                msg = json.dumps(item["content"])
                assert self.connections[item["source"]]
                await self.connections[item["source"]].send(msg)

    async def on_connected(self, source, connection):
        self.connections[source] = connection
        # self._process_script()
        # assert self._expecting["source"] == source
        # assert self._expecting["action"] == "connected"

    async def on_received(self, source, pack):
        if not self._expecting:
            await self._process_script()
        if pack["aid"] != "peek_message":
            assert self._expecting["source"] == source
            assert self._expecting["content"] == pack
            await self._process_script()
