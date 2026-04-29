# -*- coding:utf-8 -*-
__author__ = 'chenli'

import hashlib
from dataclasses import dataclass

from tqsdk.tradeable.otg.base_otg import BaseOtg
from tqsdk.tradeable.mixin import FutureMixin


@dataclass
class O32Account:
    user: str  # 用户
    fund: str  # 基金
    asset_unit: str  # 资产单元
    portfolio: str  # 组合

    def __post_init__(self) -> None:
        if not isinstance(self.user, str):
            raise Exception("user 参数类型应该是 str")
        if not isinstance(self.fund, str):
            raise Exception("fund 参数类型应该是 str")
        if not isinstance(self.asset_unit, str):
            raise Exception("asset_unit 参数类型应该是 str")
        if not isinstance(self.portfolio, str):
            raise Exception("portfolio 参数类型应该是 str")

    @property
    def user_name(self) -> str:
        return ".".join([self.user, self.fund, self.asset_unit, self.portfolio])


class TqO32(BaseOtg, FutureMixin):
    """恒生 O32 账户类"""

    def __init__(self, account_id: O32Account, password: str, td_front_url: str, mc_front_url: str,
                 license_file: str, auth_code: str) -> None:
        """
        创建恒生 O32 账户实例

        Args:
            account_id (O32Account): O32 组合账户

            password (str): O32 用户密码

            td_front_url (str): O32 交易前置地址，格式如 112.54.165.180:9003

            mc_front_url (str): O32 查询前置地址，格式如 110.54.163.160:8003

            license_file (str): O32 许可证文件绝对路径

            auth_code (str): O32 授权码

        Example1::

            from tqsdk import TqApi, TqAuth, TqO32, O32Account
            
            def create_account():
                return TqO32(
                    account_id=O32Account(user="用户", fund="基金", asset_unit="资产单元", portfolio="组合"),
                    password="password",
                    td_front_url="trade_front_host:trade_front_port",
                    mc_front_url="query_front_host:query_front_port",
                    license_file="/path/to/license.dat",
                    auth_code="auth_code",
                )

            with TqApi(account=create_account(), auth=TqAuth("快期账户", "账户密码")) as api:
                account_info = api.get_account()
                positions = api.get_position()

                print("当前账户信息：", account_info)
                print("当前持仓信息：", positions)

        注意：
            1. 使用 TqO32 账户需要安装 tqsdk_zq_otg 包： pip install -U tqsdk_zq_otg
            2. td_front_url、mc_front_url、license_file 和 auth_code 信息需要向柜台方获取

        """
        if not isinstance(account_id, O32Account):
            raise Exception("account_id 参数类型应该是 O32Account")
        if not isinstance(td_front_url, str):
            raise Exception("td_front_url 参数类型应该是 str")
        if not isinstance(mc_front_url, str):
            raise Exception("mc_front_url 参数类型应该是 str")
        if not isinstance(license_file, str):
            raise Exception("license_file 参数类型应该是 str")
        if not isinstance(auth_code, str):
            raise Exception("auth_code 参数类型应该是 str")
        self._td_front_url = td_front_url
        self._mc_front_url = mc_front_url
        self._license_file = license_file
        self._auth_code = auth_code
        if not self._license_file:
            raise Exception("license_file 参数不能为空字符串")
        super(TqO32, self).__init__(broker_id="", account_id=account_id.user_name, password=password, td_url="zqotg://127.0.0.1:0/trade")

    @property
    def _account_auth(self):
        return {
            "feature": "tq_direct",
            "account_id": self._account_id,
            "auto_add": True,
        }

    def _get_account_key(self):
        s = self._broker_id + self._account_id
        s += self._td_front_url if self._td_front_url else ""
        s += self._mc_front_url if self._mc_front_url else ""
        s += self._license_file if self._license_file else ""
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    async def _send_login_pack(self):
        req = {
            "aid": "req_login",
            "backend": "o32",
            "user_name": self._account_id,
            "password": self._password,
            "trading_fronts": [self._td_front_url, self._mc_front_url],
            "license_file_addr": self._license_file,
            "auth_code": self._auth_code,
            "app_id": "tqsdk_o32",
        }
        await self._td_send_chan.send(req)
