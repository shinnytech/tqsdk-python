#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'chenli'

import hashlib
from typing import Optional, List
import inspect

from tqsdk.tradeable.otg.base_otg import BaseOtg
from tqsdk.tradeable.mixin import FutureMixin


class TqTradingUnit(BaseOtg, FutureMixin):
    """交易单元类"""

    def __init__(self, account_id: str, tags: Optional[List[str]]=None) -> None:
        """
        创建交易单元实例

        Args:
            account_id (str): 众期子账户

            tags (None/list of str): 策略标签, 默认为调用 TqTradingUnit 的文件名及 account_id

        Example1::

            from tqsdk import TqApi, TqTradingUnit, TqAuth
            account = TqTradingUnit(account_id="众期子账户", tags=["铜品种策略", "套利策略"])
            api = TqApi(account, auth=TqAuth("快期账户", "账户密码"))

        """
        self._tags = self._convert_tags(tags, account_id)
        super(TqTradingUnit, self).__init__(broker_id="", account_id=account_id, password="tqsdk_zq", td_url="zq://localhost/")

    def _convert_tags(self, tags: Optional[List[str]], account_id: str) -> list:
        if tags is None:
            frame = inspect.stack()[1]
            filename = frame.filename
            strategy_set = {filename, account_id}
        else:
            strategy_set = set(tags)
        return list(strategy_set)

    @property
    def _account_auth(self):
        return {
            "feature": "tq_trading_unit",
            "account_id": None,
            "auto_add": False,
        }

    def _get_account_key(self):
        s = self._account_id + self._td_url
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    async def _send_login_pack(self):
        req = {
            "aid": "req_login",
            "bid": "tqsdk_zq",
            "user_name": self._account_id,
            "password": "tqsdk_zq",
            "tags": self._tags
        }
        await self._td_send_chan.send(req)
