#!/usr/bin/env python
#  -*- coding: utf-8 -*-


import json
import lzma
import threading
import asyncio
import websockets
from aiohttp import web


class MockInsServer():
    def __init__(self, port):
        self.loop = asyncio.new_event_loop()
        self.port = port
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        self.stop_signal = self.loop.create_future()

    def close(self):
        self.loop.call_soon_threadsafe(lambda: self.stop_signal.set_result(0))
        self.thread.join()

    async def handle(self, request):
        data = {
            "SHFE.cu1901": {
                "class": "FUTURE",
                "instrument_id": "SHFE.cu1901",
                "exchange_id": "SHFE",
                "ins_id": "cu1901",
                "ins_name": "\u6caa\u94dc1901",
                "volume_multiple": 5,
                "price_tick": 10,
                "price_decs": 0,
                "sort_key": 20,
                "expired": True,
                "py": "ht,hutong,yinjitong",
                "product_id": "cu",
                "product_short_name": "\u6caa\u94dc",
                "delivery_year": 2019,
                "delivery_month": 1,
                "expire_datetime": 1547535600.0,
                "last_price": 46940.0,
                "pre_volume": 0,
                "open_interest": 0,
                "settlement_price": 46880.0,
                "max_market_order_volume": 0,
                "max_limit_order_volume": 500,
                "margin": 16247.0,
                "commission": 11.605,
                "mmsa": 1,
                "trading_time": {
                    "day": [["09:00:00", "10:15:00"], ["10:30:00", "11:30:00"], ["13:30:00", "15:00:00"]],
                    "night": [["21:00:00", "25:00:00"]]
                }
            }
        }
        return web.json_response(data)

    async def task_serve(self):
        app = web.Application()
        app.add_routes([web.get('/{tail:.*}', self.handle)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '127.0.0.1', self.port)
        await site.start()
        await self.stop_signal
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

    def close(self):
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
        while True:
            s = await self.connections["td"].recv()
            pack = json.loads(s)
            if pack["aid"] == "peek_message":
                continue
            await self.on_received("td", pack)

    def run(self, script_file_name):
        self.script_file_name = script_file_name
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    async def _server(self):
        async with websockets.serve(self._handler_md, "127.0.0.1", self.md_port) as self.server_md:
            async with websockets.serve(self._handler_td, "127.0.0.1", self.td_port) as self.server_td:
                await self.stop_signal

    def _run(self):
        self.script_file = lzma.open(self.script_file_name, "rt", encoding="utf-8")
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._server())

    async def _process_script(self):
        # 每次处理日志文件中的一行, 直至需要输入为止
        self._expecting = {}
        for line in self.script_file:
            # 2019-09-09 16:22:40,652 - DEBUG - websocket message sent to wss://openmd.shinnytech.com/t/md/front/mobile: {"aid": "subscribe_quote",
            item = {}
            if "websocket message sent" in line and "peek_message" not in line:
                item["type"] = "sent"
            elif "websocket message received" in line:
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
