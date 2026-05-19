# -*- coding:utf-8 -*-
__author__ = 'zhangyihang'

import hashlib
import platform

from tqsdk.tradeable.otg.base_otg import BaseOtg
from tqsdk.tradeable.mixin import FutureMixin


class TqXuntou(BaseOtg, FutureMixin):
    """Xuntou 账户类"""

    def __init__(self, account_id: str, password: str, front_url: str, app_id: str, auth_code: str, account_type: int = 1) -> None:
        """
        创建 Xuntou 账户实例

        Args:
            account_id (str): 帐号, 账号格式为 "迅投账户.子账号", 如 "test001.100555"

            password (str): 密码

            account_type (int): Xuntou 账户类型, 目前仅支持 1 - 期货账户(迅投已经将 1 - 期货账户 和 5 - 期货期权合并为一个账户类型，统一使用 1 来表示)

            front_url (str): Xuntou 柜台地址，格式为 ip:port, 如 129.211.138.170:10001

            app_id (str): Xuntou AppID

            auth_code (str): Xuntou AuthCode

        Example1::

            from tqsdk import TqApi, TqXuntou
            account = TqXuntou(account_id="Xuntou 账户", password="Xuntou 密码", front_url="Xuntou 柜台地址", app_id="Xuntou AppID", auth_code="Xuntou AuthCode")
            api = TqApi(account, auth=TqAuth("快期账户", "账户密码"))

        注意：
            1. 使用 TqXuntou 账户需要安装 tqsdk_zq_otg 包： pip install -U tqsdk_zq_otg
            2. TqXuntou 目前仅支持 Windows 环境
            3. 使用迅投柜台前，需要先在 $HOME/.tqsdk/otg_config/xuntou/config 目录下放置迅投提供的配置文件：
               server.crt、traderApi.ini、traderApi.log4xx
            4. xuntou api 会在 $HOME/.tqsdk/otg_config/xuntou/userdata 目录下写入文件，此目录由用户自行管理，管理策略请咨询迅投

        """
        if platform.system() != "Windows":
            raise Exception("TqXuntou 仅支持 Windows 环境")

        self._account_id = account_id
        self._account_type = account_type
        self._front_url = front_url
        self._app_id = app_id
        self._auth_code = auth_code
        super(TqXuntou, self).__init__(broker_id="", account_id=account_id, password=password, td_url="zqotg://127.0.0.1:0/trade")

    @property
    def _account_auth(self):
        return {
            "feature": "tq_direct",
            "account_id": self._account_id,
            "auto_add": True,
        }

    def _get_account_key(self):
        s = self._account_id
        s += str(self._account_type) if self._account_type else ""
        s += self._front_url if self._front_url else ""
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    async def _send_login_pack(self):
        req = {
            "aid": "req_login",
            "bid": "tqsdk_zq_otg",
            "user_name": self._account_id,
            "password": self._password,
            "account_type": self._account_type,
            "front": self._front_url,
            "app_id": self._app_id,
            "auth_code": self._auth_code,
            "backend": "xuntou"
        }
        await self._td_send_chan.send(req)
