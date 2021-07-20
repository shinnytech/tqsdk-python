#!usr/bin/env python3
#-*- coding:utf-8 -*-
__author__ = 'yanqiong'

import base64
import ctypes
import logging
import os
import sys
import uuid
from typing import Optional


class TqAccount(object):
    """天勤实盘类"""

    def __init__(self, broker_id: str, account_id: str, password: str, front_broker: Optional[str] = None,
                 front_url: Optional[str] = None, td_url: Optional[str] = None, account_type: str = "FUTURE") -> None:
        """
        创建天勤实盘实例

        Args:
            broker_id (str): 期货公司，支持的期货公司列表 https://www.shinnytech.com/blog/tq-support-broker/

            account_id (str): 帐号

            password (str): 密码

            td_url(str): [可选]用于指定账户连接的交易服务器地址, eg: "tcp://1.2.3.4:1234/"

            account_type(str): [可选]用于指定账户类型
                * FUTURE [默认]: 期货账户

                * SPOT: 股票现货账户
        """
        if bool(front_broker) != bool(front_url):
            raise Exception("front_broker 和 front_url 参数需同时填写")
        if not isinstance(broker_id, str):
            raise Exception("broker_id 参数类型应该是 str")
        if not isinstance(account_id, str):
            raise Exception("account_id 参数类型应该是 str")
        if not isinstance(password, str):
            raise Exception("password 参数类型应该是 str")
        if account_type not in ["FUTURE", "SPOT"]:
            raise Exception("account_type 账户类型指定错误")
        self._broker_id = broker_id.strip()
        self._account_type = account_type
        self._account_id = account_id.strip()
        self._sub_account_id = None
        self._account_key = str(id(self))
        self._password = password
        self._front_broker = front_broker
        self._front_url = front_url
        self._td_url = td_url
        self._app_id = "SHINNY_TQ_1.0"
        self._system_info = ""
        self._order_id = 0  #最新股票下单委托合同编号

    def _get_system_info(self):
        try:
            l = ctypes.c_int(344)
            buf = ctypes.create_string_buffer(l.value)
            lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ctpse")
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

    async def _run(self, api, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan, td_send_chan, td_recv_chan):
        req = {
            "aid": "req_login",
            "bid": self._broker_id,
            "user_name": self._account_id,
            "password": self._password,
        }
        self._api = api
        mac = f"{uuid.getnode():012X}"
        req["client_mac_address"] = "-".join([mac[e:e + 2] for e in range(0, 11, 2)])
        system_info = self._get_system_info()
        if system_info:
            req["client_app_id"] = self._app_id
            req["client_system_info"] = system_info
        if self._front_broker:
            req["broker_id"] = self._front_broker
            req["front"] = self._front_url
        await td_send_chan.send(req)
        if self._account_type == 'FUTURE':
            await td_send_chan.send({
                "aid": "confirm_settlement"
            })  # 自动发送确认结算单
        self._pending_peek = False  # 是否有下游收到未处理的 peek_message
        self._md_pending_peek = False  # 是否有发给上游的 peek_message，未收到过回复
        self._diffs = []
        md_task = api.create_task(self._md_handler(api_recv_chan, md_send_chan, md_recv_chan))
        td_task = api.create_task(self._td_handler(api_recv_chan, td_send_chan, td_recv_chan))
        try:
            async for pack in api_send_chan:
                if pack["aid"] == "subscribe_quote" or pack["aid"] == "set_chart" or pack["aid"] == "ins_query":
                    await md_send_chan.send(pack)
                elif pack["aid"] != "peek_message":
                    # 若交易指令包不为当前账户实例，传递给下一个账户实例
                    if "account_key" in pack and pack["account_key"] != self._account_key:
                        await md_send_chan.send(pack)
                    else:
                        if "account_key" in pack:
                            pack.pop("account_key", None)
                        await td_send_chan.send(pack)
                elif pack["aid"] == "peek_message":
                    self._pending_peek = True
                    await self._send_diff(api_recv_chan)
                    if self._pending_peek and self._md_pending_peek is False:  # 控制"peek_message"发送: 当没有新的事件需要用户处理时才推进到下一个行情
                        await md_send_chan.send(pack)
                        self._md_pending_peek = True
        finally:
            md_task.cancel()
            td_task.cancel()

    async def _send_diff(self, api_recv_chan):
        if self._pending_peek and self._diffs:
            rtn_data = {
                "aid": "rtn_data",
                "data": self._diffs,
            }
            self._diffs = []
            self._pending_peek = False
            await api_recv_chan.send(rtn_data)

    async def _md_handler(self, api_recv_chan, md_send_chan, md_recv_chan):
        async for pack in md_recv_chan:
            if pack["aid"] == "rtn_data":
                self._diffs.extend(pack.get('data', []))
            else:
                await api_recv_chan.send(pack)  # 有可能是另一个 account 的 rsp_login
            self._md_pending_peek = False
            await self._send_diff(api_recv_chan)

    async def _td_handler(self, api_recv_chan, td_send_chan, td_recv_chan):
        async for pack in td_recv_chan:
            # OTG 返回业务信息截面 trade 中 account_key 为 user_id, 该值需要替换为 account_key
            for _, slice_item in enumerate(pack["data"] if "data" in pack else []):
                if "trade" not in slice_item:
                    continue
                # 股票账户需要根据登录确认包确定客户号与资金账户
                if self._account_type != 'FUTURE' and self._sub_account_id is None:
                    self._sub_account_id = self._get_sub_account(slice_item["trade"])

                if self._account_id in slice_item["trade"]:
                    slice_item["trade"][self._account_key] = slice_item["trade"].pop(self._account_id)
                elif self._sub_account_id in slice_item["trade"]:
                    slice_item["trade"][self._account_key] = slice_item["trade"].pop(self._sub_account_id)
            if pack["aid"] == "rtn_data":
                self._diffs.extend(pack.get('data', []))
            else:
                await api_recv_chan.send(pack)
            await td_send_chan.send({
                "aid": "peek_message"
            })
            await self._send_diff(api_recv_chan)

    def _get_sub_account(self, trade):
        """ 股票账户
         OTG 登录确认包格式
         {'trade': {'sub_account_key': {'session': {'user_id': '', 'trading_day': ''}}}} 
         """
        for k, v in trade.items():
            if 'session' in v.keys() and v.get('session').get('user_id', '') == self._account_id:
                return k
        return None

    @property
    def _next_order_id(self):
        self._order_id += 1
        return self._order_id


class TqKq(TqAccount):
    def __init__(self, td_url: Optional[str] = None):
        """
        创建快期模拟账户实例
        """
        super().__init__("快期模拟", "", "", td_url=td_url)
