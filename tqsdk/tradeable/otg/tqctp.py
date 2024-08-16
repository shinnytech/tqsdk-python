#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'chenli'

import hashlib

from tqsdk.tradeable.otg.base_otg import BaseOtg
from tqsdk.tradeable.mixin import FutureMixin


class TqCtp(BaseOtg, FutureMixin):
    """直连 CTP 账户类"""

    def __init__(self, account_id: str, password: str, front_broker: str, front_url: str, app_id: str, auth_code: str) -> None:
        """
        创建直连 CTP 账户实例

        Args:
            account_id (str): 帐号

            password (str): 密码

            front_broker (str): CTP 柜台代码

            front_url (str): CTP 柜台地址

            app_id (str): CTP AppID

            auth_code (str): CTP AuthCode

        Example1::

            from tqsdk import TqApi, TqCtp
            account = TqCtp(account_id="CTP 账户", password="CTP 密码", front_broker="CTP 柜台代码", "front_url"="CTP 柜台地址", app_id="CTP AppID", auth_code="CTP AuthCode")
            api = TqApi(account, auth=TqAuth("快期账户", "账户密码"))

        """
        self._account_id = account_id
        self._front_broker = front_broker
        self._front_url = front_url
        self._app_id = app_id
        self._auth_code = auth_code
        super(TqCtp, self).__init__(broker_id="", account_id=account_id, password=password, td_url="zqotg://127.0.0.1:0/trade")

    @property
    def _account_auth(self):
        return {
            "feature": "tq_direct",
            "account_id": self._account_id,
            "auto_add": True,
        }

    def _get_account_key(self):
        s = self._broker_id + self._account_id
        s += self._front_broker if self._front_broker else ""
        s += self._front_url if self._front_url else ""
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    async def _send_login_pack(self):
        req = {
            "aid": "req_login",
            "bid": "tqsdk_zq_otg",
            "user_name": self._account_id,
            "password": self._password,
            "broker_id": self._front_broker,
            "front": self._front_url,
            "app_id": self._app_id,
            "auth_code": self._auth_code,
            "backend": "ctp"
        }
        await self._td_send_chan.send(req)
