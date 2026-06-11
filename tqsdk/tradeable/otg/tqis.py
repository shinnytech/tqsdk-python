# -*- coding:utf-8 -*-
__author__ = 'chenli'

import hashlib
from dataclasses import dataclass

from tqsdk.tradeable.otg.base_otg import BaseOtg
from tqsdk.tradeable.mixin import FutureMixin


@dataclass
class ISAccount:
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


class TqIS(BaseOtg, FutureMixin):
    """IS 柜台账户类"""

    def __init__(self, account_id: ISAccount, password: str, td_front_url: str, mc_front_url: str,
                 license_file: str, auth_code: str, app_id: str) -> None:
        """
        创建 IS 柜台账户实例

        Args:
            account_id (ISAccount): IS 组合账户

            password (str): IS 用户密码

            td_front_url (str): IS 交易前置地址，格式如 111.11.111.111:1111

            mc_front_url (str): IS 查询前置地址，格式如 110.10.110.110:1110

            license_file (str): IS 许可证文件路径

            auth_code (str): IS 授权码

            app_id (str): IS AppID

        Example1::

            from tqsdk import TqApi, TqAuth, TqIS, ISAccount

            account = TqIS(
                account_id=ISAccount(user="用户", fund="基金", asset_unit="资产单元", portfolio="组合"),
                password="IS 密码",
                td_front_url="trade_front_host:trade_front_port",
                mc_front_url="query_front_host:query_front_port",
                license_file="/path/to/licenseIS.dat",
                auth_code="auth_code",
                app_id="app_id",
            )
            api = TqApi(account=account, auth=TqAuth("快期账户", "账户密码"))

        注意：
            1. 使用 TqIS 账户需要安装 tqsdk_zq_otg 包： pip install -U tqsdk_zq_otg
            2. td_front_url、mc_front_url、license_file、auth_code 和 app_id 信息需要向柜台方获取

        """
        if not isinstance(account_id, ISAccount):
            raise Exception("account_id 参数类型应该是 ISAccount")
        if not isinstance(td_front_url, str):
            raise Exception("td_front_url 参数类型应该是 str")
        if not isinstance(mc_front_url, str):
            raise Exception("mc_front_url 参数类型应该是 str")
        if not isinstance(license_file, str):
            raise Exception("license_file 参数类型应该是 str")
        if not isinstance(auth_code, str):
            raise Exception("auth_code 参数类型应该是 str")
        if not isinstance(app_id, str):
            raise Exception("app_id 参数类型应该是 str")
        self._td_front_url = td_front_url
        self._mc_front_url = mc_front_url
        self._license_file = license_file
        self._auth_code = auth_code
        self._app_id = app_id
        if not self._license_file:
            raise Exception("license_file 参数不能为空字符串")
        super(TqIS, self).__init__(broker_id="", account_id=account_id.user_name, password=password, td_url="zqotg://127.0.0.1:0/trade")

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
            "backend": "is",
            "user_name": self._account_id,
            "password": self._password,
            "trading_fronts": [self._td_front_url, self._mc_front_url],
            "license_file_addr": self._license_file,
            "auth_code": self._auth_code,
            "app_id": self._app_id,
        }
        await self._td_send_chan.send(req)
