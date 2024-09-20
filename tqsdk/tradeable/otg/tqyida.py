#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'chenli'

import hashlib

from tqsdk.tradeable.otg.base_otg import BaseOtg
from tqsdk.tradeable.mixin import FutureMixin


class TqYida(BaseOtg, FutureMixin):
    """易达账户类"""

    def __init__(self, account_id: str, password: str, front_url: str, app_id: str, auth_code: str) -> None:
        """
        创建易达账户实例

        Args:
            account_id (str): 帐号

            password (str): 密码

            front_url (str): 易达柜台地址

            app_id (str): 易达 AppID

            auth_code (str): 易达 AuthCode

        Example1::

            from tqsdk import TqApi, TqYida
            account = TqYida(account_id="易达账户", password="易达密码", front_url="易达柜台地址", app_id="易达 AppID", auth_code="易达 AuthCode")
            api = TqApi(account, auth=TqAuth("快期账户", "账户密码"))

        注意：
            1. 使用 TqYida 账户需要安装 tqsdk_zq_otg 包： pip install -U tqsdk_zq_otg
            2. front_url, app_id 和 auth_code 信息需要向易达申请程序化外接后取得

        """
        self._account_id = account_id
        self._front_url = front_url
        self._app_id = app_id
        self._auth_code = auth_code
        super(TqYida, self).__init__(broker_id="", account_id=account_id, password=password, td_url="zqotg://127.0.0.1:0/trade")

    @property
    def _account_auth(self):
        return {
            "feature": "tq_direct",
            "account_id": self._account_id,
            "auto_add": True,
        }

    def _get_account_key(self):
        s = self._broker_id + self._account_id
        s += self._front_url if self._front_url else ""
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    async def _send_login_pack(self):
        req = {
            "aid": "req_login",
            "bid": "tqsdk_zq_otg",
            "user_name": self._account_id,
            "password": self._password,
            "broker_id": "",
            "front": self._front_url,
            "app_id": self._app_id,
            "auth_code": self._auth_code,
            "backend": "yida"
        }
        await self._td_send_chan.send(req)
