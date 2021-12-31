#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'mayanqiong'

from abc import ABC, abstractmethod

from tqsdk.baseModule import TqModule


class Tradeable(ABC, TqModule):

    def __init__(self):
        self._account_key = self._get_account_key()  # 每个账户的唯一标识，在账户初始化时就确定下来，后续只读不写

    def _get_account_key(self):
        return str(id(self))

    @property
    @abstractmethod
    def _account_name(self):
        # 用于界面展示的用户信息
        raise NotImplementedError

    @property
    def _account_info(self):
        # 用于 web_helper 获取初始账户信息
        return {
            "account_key": self._account_key,
            "account_name": self._account_name
        }

    def _is_self_trade_pack(self, pack):
        """是否是当前交易实例应该处理的交易包"""
        if pack["aid"] in ["insert_order", "cancel_order", "set_risk_management_rule"]:
            assert "account_key" in pack, "发给交易请求的包必须包含 account_key"
            if pack["account_key"] != self._account_key:
                return False
            else:
                pack.pop("account_key", None)
                return True
        return False
