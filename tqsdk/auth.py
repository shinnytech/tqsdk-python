# !usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'

import json
import logging
import os

import jwt
import requests
from shinny_structlog import ShinnyLoggerAdapter

from tqsdk.constants import FUTURE_EXCHANGES, SPOT_EXCHANGES, KQ_EXCHANGES, KQD_EXCHANGES, STOCK_EXCHANGES
from tqsdk.__version__ import __version__
from tqsdk.datetime import _cst_tz, datetime


class TqAuth(object):
    """信易用户认证类"""

    def __init__(self, user_name: str = "", password: str = ""):
        """
        创建快期用户认证类

        Args:
            user_name (str): [必填]快期账户，可以是 邮箱、用户名、手机号

            password (str): [必填]快期账户密码


        Example::

            # 使用实盘帐号直连行情和交易服务器
            from tqsdk import TqApi, TqAccount, TqAuth
            api = TqApi(TqAccount("H海通期货", "022631", "123456"), auth=TqAuth("快期账户", "账户密码"))

        """
        self._user_name = user_name
        self._password = password
        self._auth_url = os.getenv("TQ_AUTH_URL", "https://auth.shinnytech.com")
        self._access_token = ""
        self._refresh_token = ""
        self._auth_id = ""
        self._mode = "real"  # 行情模式 real bt
        self._grants = {
            "features": [],
            "accounts": []
        }
        self._expire_datetime = None
        self._expire_days_left = None
        self._product_type = None
        self._logger = ShinnyLoggerAdapter(logging.getLogger("TqApi.TqAuth"), headers=self._base_headers, grants=self._grants)

    @property
    def _base_headers(self):
        return {
            "User-Agent": "tqsdk-python %s" % __version__,
            "Accept": "application/json",
            "Authorization": "Bearer %s" % self._access_token
        }

    @property
    def expire_datetime(self):
        """
        返回快期账户授权到期时间

        Returns:
            datetime.datetime : datetime 模块中的 datetime 类型时间
                * 返回授权到期时间，如果查询失败则抛出异常。
                * 时区是东八区。

            注意:
            1. 对于免费用户，将返回到期时间："2099-12-31 23:59:59+08:00"，代表权限永不到期。

            2. 当用户升级版本或者续费后，将在下一次使用时获取最新到期时间。


        Example::

            from tqsdk import TqApi, TqAuth

            auth = TqAuth("快期账户", "账户密码")
            api = TqApi(auth=auth)
            print(auth.expire_datetime)  # 快期账户授权到期时间
            api.close()

        """
        if self._expire_datetime is None or self._expire_days_left is None or self._product_type is None:
            url = f"{self._auth_url}/auth/realms/shinnytech/rest/get-grant/tq"
            self._logger.debug("get auth expire datetime", url=url, method="GET")
            response = requests.get(url=url, headers=self._base_headers, timeout=30)
            self._logger.debug("get auth expire datetime result", url=response.url, status_code=response.status_code, headers=response.headers, reason=response.reason, text=response.text)
            try:
                content = json.loads(response.content)
                self._expire_datetime = datetime.datetime.fromtimestamp(content["exp"], tz=_cst_tz)
                self._expire_days_left = content["daysleft"]
                self._product_type = content["account_type"]
            except Exception:
                raise Exception("查询快期账户授权到期日期失败") from None
        return self._expire_datetime

    def init(self, mode="real"):
        self._mode = mode

    def login(self):
        self._logger.debug("login", user_name=self._user_name)
        self._access_token, self._refresh_token = self._request_token({
            "grant_type": "password",
            "username": self._user_name,
            "password": self._password
        })
        content = jwt.decode(self._access_token, options={"verify_signature": False})
        self._grants = content["grants"]
        self._auth_id = content["sub"]
        self._logger = self._logger.bind(headers=self._base_headers, grants=self._grants)

    def _request_token(self, payload):
        data = {"client_id": "shinny_tq", "client_secret": "be30b9f4-6862-488a-99ad-21bde0400081"}
        data.update(payload)
        url = f"{self._auth_url}/auth/realms/shinnytech/protocol/openid-connect/token"
        self._logger.debug("request token", url=url, params=data, method="POST")
        response = requests.post(url=url, headers=self._base_headers, data=data, timeout=30)
        self._logger.debug("request token result", url=response.url, status_code=response.status_code, headers=response.headers, reason=response.reason, text=response.text)
        if response.status_code == 200:
            content = json.loads(response.content)
            return content["access_token"], content["refresh_token"]
        else:
            raise Exception("用户权限认证失败 (%d,%s)" % (response.status_code, json.loads(response.content)))

    def _add_account(self, account_id):
        if self._has_account(account_id):
            return True
        url = f"{self._auth_url}/auth/realms/shinnytech/rest/update-grant-accounts/{account_id}"
        self._logger.debug("add account", account_id=account_id, url=url, method="PUT")
        response = requests.put(url=url, headers=self._base_headers, timeout=30)
        self._logger.debug("add account result", url=response.url, status_code=response.status_code, headers=response.headers, reason=response.reason, text=response.text)
        if response.status_code == 200:
            self._access_token, self._refresh_token = self._request_token({
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            })
            content = jwt.decode(self._access_token, options={"verify_signature": False})
            self._grants.update(content["grants"])
            self._logger = self._logger.bind(headers=self._base_headers, grants=self._grants)
        else:
            raise Exception(f"添加期货账户失败。{response.status_code}, {json.loads(response.content)}")

    def _get_td_url(self, broker_id, account_id):
        """获取交易网关地址"""
        url = f"https://files.shinnytech.com/{broker_id}.json"
        params = {
            "account_id": account_id,
            "auth": self._user_name
        }
        self._logger.debug("request td url", url=url, params=params, method="POST")
        response = requests.get(url=url, params=params, headers=self._base_headers, timeout=30)
        self._logger.debug("request td url result", url=response.url, status_code=response.status_code,
                           headers=response.headers, reason=response.reason, text=response.text)
        if response.status_code != 200:
            raise Exception(f"不支持该期货公司 - {broker_id}，请联系期货公司。")
        broker_list = json.loads(response.content)
        if "TQ" not in broker_list[broker_id]["category"]:
            raise Exception(f"该期货公司 - {broker_id} 暂不支持 TqSdk 登录，请联系期货公司。")

        return broker_list[broker_id]["url"], broker_list[broker_id].get('broker_type', 'FUTURE'), broker_list[broker_id].get('smtype'), broker_list[broker_id].get('smconfig')

    def _get_md_url(self, stock, backtest):
        """获取行情网关地址"""
        url = f"https://api.shinnytech.com/ns"
        params = {"stock": str(stock).lower(), "backtest": str(backtest).lower()}
        self._logger.debug("request md url", url=url, params=params, method="POST")
        response = requests.get(url=url, params=params, headers=self._base_headers, timeout=30)
        self._logger.debug("request md url result", url=response.url, status_code=response.status_code,
                           headers=response.headers, reason=response.reason, text=response.text)
        if response.status_code == 200:
            content = json.loads(response.content)
            if "mdurl" in content:
                return content["mdurl"]
            else:
                raise Exception(f"调用名称服务失败: {content}")
        else:
            raise Exception(f"调用名称服务失败: {response.status_code}, {response.content}")

    def _has_feature(self, feature):
        if self._mode == "bt" and feature in ["futr", "sec", "lmt_idx"]:
            # 在回测模式中所有用户都有 futr sec lmt_idx 权限
            return True
        return feature in self._grants["features"]

    def _has_account(self, account):
        return account in self._grants["accounts"]

    def _has_md_grants(self, symbol):
        symbol_list = symbol if isinstance(symbol, list) else [symbol]
        for symbol in symbol_list:
            if symbol.split('.', 1)[0] in (FUTURE_EXCHANGES + SPOT_EXCHANGES + KQ_EXCHANGES + KQD_EXCHANGES) and self._has_feature("futr"):
                continue
            elif symbol.split('.', 1)[0] in (["CSI"] + STOCK_EXCHANGES) and self._has_feature("sec"):
                continue
            elif symbol in ["SSE.000016", "SSE.000300", "SSE.000905", "SSE.000852"] and self._has_feature("lmt_idx"):
                continue
            else:
                raise Exception(f"您的账户不支持查看 {symbol} 的行情数据，需要购买后才能使用。升级网址：https://www.shinnytech.com/tqsdk-buy/")
        return True

    def _has_td_grants(self, symbol):
        # 对于 opt / cmb / adv 权限的检查由 OTG 做
        if symbol.split('.', 1)[0] in STOCK_EXCHANGES and self._has_feature("sec"):
            return True
        if symbol.split('.', 1)[0] in (FUTURE_EXCHANGES + KQ_EXCHANGES) and self._has_feature("futr"):
            return True
        raise Exception(f"您的账户不支持交易 {symbol}，需要购买后才能使用。升级网址：https://www.shinnytech.com/tqsdk-buy/")
