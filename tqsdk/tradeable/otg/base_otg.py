#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'

import hashlib
import base64
from urllib.parse import urlparse
from typing import Optional

from shinny_structlog import ShinnyLoggerAdapter

from tqsdk.tradeable.mixin import FutureMixin, StockMixin
from tqsdk.tradeable.tradeable import Tradeable
from tqsdk.channel import TqChan
from tqsdk.connect import TqConnect, TdReconnectHandler


class BaseOtg(Tradeable):
    def __init__(self, broker_id: str, account_id: str, password: str, td_url: Optional[str] = None, sm: bool = False) -> None:
        if not isinstance(broker_id, str):
            raise Exception("broker_id 参数类型应该是 str")
        if not isinstance(account_id, str):
            raise Exception("account_id 参数类型应该是 str")
        if not isinstance(password, str):
            raise Exception("password 参数类型应该是 str")
        self._broker_id = broker_id.strip()  # 期货公司（用户登录 rsp_login 填的）
        self._account_id = account_id.strip()  # 期货账户 （用户登录 rsp_login 填的）
        self._password = password
        self._td_url = td_url
        self._sm = sm

        super(BaseOtg, self).__init__()

    def _get_account_key(self):
        s = self._broker_id + self._account_id
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    @property
    def _account_name(self):
        return self._account_id

    @property
    def _account_info(self):
        info = super(BaseOtg, self)._account_info
        info.update({
            "broker_id": self._broker_id,
            "account_id": self._account_id
        })
        return info

    async def _send_login_pack(self):
        """发送登录请求"""
        req = {
            "aid": "req_login",
            "bid": self._broker_id,
            "user_name": self._account_id,
            "password": self._password
        }
        await self._td_send_chan.send(req)

    def _update_otg_info(self, api):
        """更新 otg 登录需要的基本信息"""
        if self._td_url:
            return
        if api._td_url:
            self._td_url = api._td_url
        else:
            self._td_url, account_type, sm_type, sm_config = api._auth._get_td_url(self._broker_id, self._account_id)
            if account_type == "FUTURE":
                assert isinstance(self, FutureMixin)
            else:
                assert isinstance(self, StockMixin)
            if self._sm and sm_type and sm_config:
                url_account = base64.urlsafe_b64encode(self._account_id.encode("utf-8")).decode("utf-8")
                url_password = base64.urlsafe_b64encode(self._password.encode("utf-8")).decode("utf-8")
                url_info = urlparse(self._td_url)
                # http://example.org -> http://example.org/smcfg/smuser/smpasswd
                # http://example.org/ -> http://example.org/smcfg/smuser/smpasswd/
                # http://example.org/foo/bar -> http://example.org/smcfg/smuser/smpasswd/foo/bar
                self._td_url = url_info._replace(scheme=sm_type, path=f"/{sm_config}/{url_account}/{url_password}{url_info.path}").geturl()

    def _connect_td(self, api, index: int) -> Optional[str]:
        # 连接交易服务器
        td_logger = ShinnyLoggerAdapter(api._logger.getChild("TqConnect"), url=self._td_url, broker_id=self._broker_id, account_id=self._account_id)
        conn_id = f"td_{index}"
        ws_td_send_chan = TqChan(api, chan_name=f"send to {conn_id}", logger=td_logger)
        ws_td_recv_chan = TqChan(api, chan_name=f"recv from {conn_id}", logger=td_logger)
        conn = TqConnect(td_logger, conn_id=conn_id)
        api.create_task(conn._run(api, self._td_url, ws_td_send_chan, ws_td_recv_chan))
        ws_td_send_chan._logger_bind(chan_from=f"td_reconn_{index}")
        ws_td_recv_chan._logger_bind(chan_to=f"td_reconn_{index}")

        td_handler_logger = ShinnyLoggerAdapter(api._logger.getChild("TdReconnect"), url=self._td_url, broker_id=self._broker_id, account_id=self._account_id)
        td_reconnect = TdReconnectHandler(td_handler_logger)
        self._td_send_chan = TqChan(api, chan_name=f"send to td_reconn_{index}", logger=td_handler_logger)
        self._td_recv_chan = TqChan(api, chan_name=f"recv from td_reconn_{index}", logger=td_handler_logger)
        api.create_task(td_reconnect._run(api, self._td_send_chan, self._td_recv_chan, ws_td_send_chan, ws_td_recv_chan))
        self._td_send_chan._logger_bind(chan_from=f"account_{index}")
        self._td_recv_chan._logger_bind(chan_to=f"account_{index}")
        return conn_id

    async def _run(self, api, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan):
        self._api = api
        self._api_send_chan = api_send_chan
        self._api_recv_chan = api_recv_chan
        self._md_send_chan = md_send_chan
        self._md_recv_chan = md_recv_chan
        await self._send_login_pack()
        await super(BaseOtg, self)._run(api, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan, self._td_send_chan, self._td_recv_chan)

    async def _handle_recv_data(self, pack, chan):
        """
        处理所有上游收到的数据包
        """
        if chan == self._md_recv_chan:  # 从行情收到的数据包
            if pack["aid"] == "rtn_data":
                self._diffs.extend(pack.get('data', []))
            else:
                await self._api_recv_chan.send(pack)  # 有可能是另一个 account 的 rsp_login
        elif chan == self._td_recv_chan:  # 从交易收到的数据包
            # 收到通知时，在通知里加上 account_name 信息
            if pack["aid"] == "rtn_data":
                for data in pack.get('data', []):
                    for notify_id, notify in data.get('notify', {}).items():
                        notify['_account_name'] = self._account_name
            self._td_handler(pack)

    async def _handle_req_data(self, pack):
        if self._is_self_trade_pack(pack):
            await self._td_send_chan.send(pack)
        else:
            await self._md_send_chan.send(pack)

    def _td_handler(self, pack):
        # OTG 返回业务信息截面 trade 中 account_key 为 user_id, 该值需要替换为 account_key
        if pack["aid"] == "rtn_data":
            pack_data = pack.get('data', [])
            for item in pack_data:
                if "trade" in item:
                    item["trade"][self._account_key] = item["trade"].pop(self._account_id)
            self._diffs.extend(pack_data)
