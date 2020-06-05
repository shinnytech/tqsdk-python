#!usr/bin/env python3
#-*- coding:utf-8 -*-
__author__ = 'yanqiong'

import base64
import ctypes
import logging
import os
import sys
from typing import Optional


class TqAccount(object):
    """天勤实盘类"""

    def __init__(self, broker_id: str, account_id: str, password: str, front_broker: Optional[str] = None,
                 front_url: Optional[str] = None) -> None:
        """
        创建天勤实盘实例

        Args:
            broker_id (str): 期货公司，支持的期货公司列表 https://www.shinnytech.com/blog/tq-support-broker/

            account_id (str): 帐号

            password (str): 密码

            front_broker(str): [可选]CTP交易前置的Broker ID, 用于连接次席服务器, eg: "2020"

            front_url(str): [可选]CTP交易前置地址, 用于连接次席服务器, eg: "tcp://1.2.3.4:1234/"
        """
        if bool(front_broker) != bool(front_url):
            raise Exception("front_broker 和 front_url 参数需同时填写")

        self._broker_id = broker_id
        self._account_id = account_id
        self._password = password
        self._front_broker = front_broker
        self._front_url = front_url
        self._app_id = "SHINNY_TQ_1.0"
        self._system_info = ""
        try:
            l = ctypes.c_int(344)
            buf = ctypes.create_string_buffer(l.value)
            lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ctpse")
            if sys.platform.startswith("win"):
                if ctypes.sizeof(ctypes.c_voidp) == 4:
                    selib = ctypes.cdll.LoadLibrary(os.path.join(lib_path, "WinDataCollect32.dll"))
                    ret = getattr(selib, "?CTP_GetSystemInfo@@YAHPADAAH@Z")(buf, ctypes.byref(l))
                else:
                    selib = ctypes.cdll.LoadLibrary(os.path.join(lib_path, "WinDataCollect64.dll"))
                    ret = getattr(selib, "?CTP_GetSystemInfo@@YAHPEADAEAH@Z")(buf, ctypes.byref(l))
            elif sys.platform.startswith("linux"):
                selib = ctypes.cdll.LoadLibrary(os.path.join(lib_path, "LinuxDataCollect64.so"))
                ret = selib._Z17CTP_GetSystemInfoPcRi(buf, ctypes.byref(l))
            else:
                raise Exception("不支持该平台")
            if ret == 0:
                self._system_info = base64.b64encode(buf.raw[:l.value]).decode("utf-8")
            else:
                raise Exception("错误码: %d" % ret)
        except Exception as e:
            logging.getLogger("TqApi.TqAccount").debug("采集穿透式监管客户端信息失败: %s" % e)

    async def _run(self, api, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan, td_send_chan, td_recv_chan):
        req = {
            "aid": "req_login",
            "bid": self._broker_id,
            "user_name": self._account_id,
            "password": self._password,
        }
        if self._system_info:
            req["client_app_id"] = self._app_id
            req["client_system_info"] = self._system_info
        if self._front_broker:
            req["broker_id"] = self._front_broker
            req["front"] = self._front_url
        await td_send_chan.send(req)
        await td_send_chan.send({
            "aid": "confirm_settlement"
        })  # 自动发送确认结算单
        md_task = api.create_task(self._md_handler(api_recv_chan, md_send_chan, md_recv_chan))
        td_task = api.create_task(self._td_handler(api_recv_chan, td_send_chan, td_recv_chan))
        try:
            async for pack in api_send_chan:
                if pack["aid"] == "subscribe_quote" or pack["aid"] == "set_chart":
                    await md_send_chan.send(pack)
                elif pack["aid"] != "peek_message":
                    await td_send_chan.send(pack)
        finally:
            md_task.cancel()
            td_task.cancel()

    async def _md_handler(self, api_recv_chan, md_send_chan, md_recv_chan):
        async for pack in md_recv_chan:
            await md_send_chan.send({
                "aid": "peek_message"
            })
            await api_recv_chan.send(pack)

    async def _td_handler(self, api_recv_chan, td_send_chan, td_recv_chan):
        async for pack in td_recv_chan:
            await td_send_chan.send({
                "aid": "peek_message"
            })
            await api_recv_chan.send(pack)


class TqKuaiqi(TqAccount):

    def __init__(self):
        super().__init__("快期模拟", "", "")
