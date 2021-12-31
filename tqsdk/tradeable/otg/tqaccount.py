#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'

import base64
import ctypes
import hashlib
import logging
import os
from pathlib import Path
import sys
import uuid
from typing import Optional

from tqsdk.tradeable.otg.base_otg import BaseOtg
from tqsdk.tradeable.mixin import FutureMixin


class TqAccount(BaseOtg, FutureMixin):
    """天勤实盘账户类"""

    def __init__(self, broker_id: str, account_id: str, password: str, front_broker: Optional[str] = None,
                 front_url: Optional[str] = None, td_url: Optional[str] = None, **kwargs) -> None:
        """
        创建天勤实盘账户实例

        Args:
            broker_id (str): 期货公司，支持的期货公司列表 https://www.shinnytech.com/blog/tq-support-broker/

            account_id (str): 帐号

            password (str): 密码

            td_url(str): [可选]用于指定账户连接的交易服务器地址, eg: "tcp://1.2.3.4:1234/"
        """
        if bool(front_broker) != bool(front_url):
            raise Exception("front_broker 和 front_url 参数需同时填写")
        self._front_broker = front_broker
        self._front_url = front_url
        self._app_id = "SHINNY_TQ_1.0"

        account_type = kwargs["account_type"] if "account_type" in kwargs else "FUTURE"
        if account_type == "SPOT":
            raise Exception("account_type 账户类型指定错误，目前只支持 FUTURE")
        kwargs.pop("account_type", None)
        if len(kwargs) > 0:
            raise TypeError(f"不支持以下参数 {[kwargs.keys()]}")

        super(TqAccount, self).__init__(broker_id, account_id, password, td_url)

    def _get_account_key(self):
        s = self._broker_id + self._account_id
        s += self._front_broker if self._front_broker else ""
        s += self._front_url if self._front_url else ""
        s += self._td_url if self._td_url else ""
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    @property
    def _account_info(self):
        info = super(TqAccount, self)._account_info
        info.update({
            "account_type": self._account_type
        })
        return info

    def _get_system_info(self):
        try:
            l = ctypes.c_int(344)
            buf = ctypes.create_string_buffer(l.value)
            path = Path(__file__, '../../../ctpse')
            lib_path = path.resolve()  # Make the path absolute, resolving any symlinks. A new path object is returned
            if sys.platform.startswith("win") or sys.platform.startswith("linux"):
                if sys.platform.startswith("win"):
                    if ctypes.sizeof(ctypes.c_voidp) == 4:
                        selib = ctypes.cdll.LoadLibrary(os.path.join(lib_path, "WinDataCollect32.dll"))
                        ret = getattr(selib, "?CTP_GetSystemInfo@@YAHPADAAH@Z")(buf, ctypes.byref(l))
                    else:
                        selib = ctypes.cdll.LoadLibrary(os.path.join(lib_path, "WinDataCollect64.dll"))
                        ret = getattr(selib, "?CTP_GetSystemInfo@@YAHPEADAEAH@Z")(buf, ctypes.byref(l))
                else:
                    selib = ctypes.cdll.LoadLibrary(os.path.join(lib_path, "LinuxDataCollect64.so"))
                    ret = selib._Z17CTP_GetSystemInfoPcRi(buf, ctypes.byref(l))
                if ret == 0:
                    return base64.b64encode(buf.raw[:l.value]).decode("utf-8")
                else:
                    raise Exception("错误码: %d" % ret)
            else:
                logging.getLogger("TqApi.TqAccount").debug("ctpse error", error="不支持该平台")
        except Exception as e:
            self._api._print(f"采集穿透式监管客户端信息失败: {e}", level="ERROR")
            logging.getLogger("TqApi.TqAccount").error("ctpse error", error=e)
        return ""

    async def _send_login_pack(self):
        req = {
            "aid": "req_login",
            "bid": self._broker_id,
            "user_name": self._account_id,
            "password": self._password,
        }
        mac = f"{uuid.getnode():012X}"
        req["client_mac_address"] = "-".join([mac[e:e + 2] for e in range(0, 11, 2)])
        system_info = self._get_system_info()
        if system_info:
            req["client_app_id"] = self._app_id
            req["client_system_info"] = system_info
        if self._front_broker:
            req["broker_id"] = self._front_broker
            req["front"] = self._front_url
        await self._td_send_chan.send(req)
        await self._td_send_chan.send({
            "aid": "confirm_settlement"
        })  # 自动发送确认结算单
