#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'mayanqiong'


import asyncio
import json
import time
from datetime import date

import aiohttp
import requests

from tqsdk.channel import TqChan


class TqReplay(object):
    """天勤复盘类"""

    def __init__(self, replay_dt: date):
        """
        除了传统的回测模式以外，TqSdk 提供独具特色的复盘模式，它与回测模式有以下区别

        1.复盘模式为时间驱动，回测模式为事件驱动

        复盘模式下，你可以指定任意一天交易日，后端行情服务器会传输用户订阅合约的当天的所有历史行情数据，重演当天行情，而在回测模式下，我们根据用户订阅的合约周期数据来进行推送

        因此在复盘模式下K线更新和实盘一模一样，而回测模式下就算订阅了 Tick 数据，回测中任意周期 K 线最后一根的 close 和其他数据也不会随着 Tick 更新而更新，而是随着K线频率生成和结束时更新一次

        2.复盘和回测的行情速度

        因为两者的驱动机制不同，回测会更快，但是我们在复盘模式下也提供行情速度调节功能，可以结合web_gui来实现

        3.复盘目前只支持单日复盘

        因为复盘提供对应合约当日全部历史行情数据，对后端服务器会有较大压力，目前只支持复盘模式下选择单日进行复盘

        Args:
            replay_dt (date): 指定复盘交易日
        """
        if isinstance(replay_dt, date):
            self._replay_dt = replay_dt
        else:
            raise Exception("复盘时间(dt)类型 %s 错误, 请检查 dt 数据类型是否填写正确" % (type(replay_dt)))
        if self._replay_dt.weekday() >= 5:
            # 0~6, 检查周末[5,6] 提前抛错退出
            raise Exception("无法创建复盘服务器，请检查复盘日期后重试。")
        self._default_speed = 1
        self._api = None

    def _create_server(self, api):
        self._api = api
        self._logger = api._logger.getChild("TqReplay")  # 调试信息输出
        self._logger.debug('replay prepare', replay_dt=self._replay_dt)

        session = self._prepare_session()
        self._session_url = "http://%s:%d/t/rmd/replay/session/%s" % (
            session["ip"], session["session_port"], session["session"])
        self._ins_url = "http://%s:%d/t/rmd/replay/session/%s/symbol" % (
            session["ip"], session["session_port"], session["session"])
        self._md_url = "ws://%s:%d/t/rmd/front/mobile" % (session["ip"], session["gateway_web_port"])

        self._server_status = None
        self._server_status = self._wait_server_status("running", 60)
        if self._server_status == "running":
            self._logger.debug('replay start successed', replay_dt=self._replay_dt)
            return self._ins_url, self._md_url
        else:
            self._logger.debug('replay start failed', replay_dt=self._replay_dt)
            raise Exception("无法创建复盘服务器，请检查复盘日期后重试。")

    async def _run(self):
        try:
            self._send_chan = TqChan(self._api)
            self._send_chan.send_nowait({"aid": "ratio", "speed": self._default_speed})
            _senddata_task = self._api.create_task(self._senddata_handler())
            while True:
                await self._send_chan.send({"aid": "heartbeat"})
                await asyncio.sleep(30)
        finally:
            await self._send_chan.close()
            _senddata_task.cancel()
            await asyncio.gather(_senddata_task, return_exceptions=True)

    def _prepare_session(self):
        create_session_url = "http://replay.api.shinnytech.com/t/rmd/replay/create_session"
        response = requests.post(create_session_url,
                                 headers=self._api._base_headers,
                                 data=json.dumps({'dt': self._replay_dt.strftime("%Y%m%d")}),
                                 timeout=5)
        if response.status_code == 200:
            return json.loads(response.content)
        else:
            raise Exception("创建复盘服务器失败，请检查复盘日期后重试。")

    def _wait_server_status(self, target_status, timeout):
        """等服务器状态为 target_status，超时时间 timeout 秒"""
        deadline = time.time() + timeout
        server_status = self._get_server_status()
        while deadline > time.time():
            if target_status == server_status:
                break
            else:
                time.sleep(1)
                server_status = self._get_server_status()
        return server_status

    def _get_server_status(self):
        try:
            response = requests.get(self._session_url,
                                    headers=self._api._base_headers,
                                    timeout=5)
            if response.status_code == 200:
                return json.loads(response.content)["status"]
            else:
                raise Exception("无法创建复盘服务器，请检查复盘日期后重试。")
        except requests.exceptions.ConnectionError as e:
            # 刚开始 _session_url 还不能访问的时候～
            return None

    async def _senddata_handler(self):
        try:
            session = aiohttp.ClientSession(headers=self._api._base_headers)
            async for data in self._send_chan:
                await session.post(self._session_url, data=json.dumps(data))
        finally:
            await session.post(self._session_url, data=json.dumps({"aid": "terminate"}))
            await session.close()

    def set_replay_speed(self, speed: float = 10.0) -> None:
        """
        调整复盘服务器行情推进速度

        Args:
            speed (float): 复盘服务器行情推进速度, 默认为 10.0

        Example::

            from datetime import date
            from tqsdk import TqApi, TqAuth, TqReplay
            replay = TqReplay(date(2020, 9, 10))
            api = TqApi(backtest=replay, auth=("信易账户,账户密码"))
            replay.set_replay_speed(3.0)
            quote = api.get_quote("SHFE.cu2012")
            while True:
                api.wait_update()
                if api.is_changing(quote):
                    print("最新价", quote.datetime, quote.last_price)

        """
        if self._api:
            self._send_chan.send_nowait({"aid": "ratio", "speed": speed})
        else:
            # _api 未初始化，只记录用户设定的速度，在复盘服务器启动完成后，发动请求
            self._default_speed = speed

