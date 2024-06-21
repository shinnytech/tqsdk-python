#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'

import hashlib

from tqsdk.tradeable.otg.base_otg import BaseOtg
from tqsdk.tradeable.mixin import FutureMixin


class TqZq(BaseOtg, FutureMixin):
    """众期账户类"""

    def __init__(self, account_id: str, password: str, td_url: str) -> None:
        """
        创建众期账户实例

        Args:
            account_id (str): 帐号

            password (str): 密码

            td_url (str): 众期交易服务器地址, eg: "ws://1.2.3.4:8765/"

        Example1::

            from tqsdk import TqApi, TqZq
            account = TqZq(account_id="众期账户", password="众期密码", td_url="众期柜台地址")
            api = TqApi(account, auth=TqAuth("快期账户", "账户密码"))

        """
        super(TqZq, self).__init__(broker_id="", account_id=account_id, password=password, td_url=td_url)

    def _get_account_key(self):
        s = self._account_id + self._td_url
        return hashlib.md5(s.encode('utf-8')).hexdigest()
