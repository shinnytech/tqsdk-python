#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'mayanqiong'


from tqsdk.baseModule import TqModule
from tqsdk.tradeable.interface import IFuture


class Tradeable(TqModule):

    def __init__(self, broker_id, account_id) -> None:
        """这里的几项属性为每一种可交易的类都应该有的属性"""
        if not isinstance(broker_id, str):
            raise Exception("broker_id 参数类型应该是 str")
        if not isinstance(account_id, str):
            raise Exception("account_id 参数类型应该是 str")
        self._broker_id = broker_id.strip()  # 期货公司（用户登录 rsp_login 填的） / TqSim / TqSimStock
        self._account_id = account_id.strip()  # 期货账户 （用户登录 rsp_login 填的） / TQSIM(user-defined)
        self._account_key = self._get_account_key()   # 每个账户的唯一标识

    @property
    def _account_name(self):
        # 用于界面展示的用户信息
        return self._account_id

    def _get_account_key(self):
        return str(id(self))

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

    def _get_baseinfo(self):
        # 用于 web_helper 获取初始账户信息
        return {
            "broker_id": self._broker_id,
            "account_id": self._account_id,
            "account_key": self._account_key,
            "account_name": self._account_name,
            "account_type": "FUTURE" if isinstance(self, IFuture) else "STOCK"
        }
