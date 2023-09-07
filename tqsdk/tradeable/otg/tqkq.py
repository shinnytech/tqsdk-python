#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'

from typing import Optional

from tqsdk.tradeable.otg.base_otg import BaseOtg
from tqsdk.tradeable.mixin import FutureMixin, StockMixin


class TqKq(BaseOtg, FutureMixin):
    """天勤快期模拟账户类"""

    def __init__(self, td_url: Optional[str] = None, number: Optional[int] = None):
        """
        创建快期模拟账户实例

        快期模拟的账户和交易信息可以在快期专业版查看，可以点击 `快期专业版 <https://www.shinnytech.com/qpro/>`_ 进行下载

        Args:
            td_url (str): [可选]指定交易服务器的地址, 默认使用快期账户对应的交易服务地址

            number (int): [可选]模拟交易账号编号, 默认为主模拟账号, 可以通过指定 1~99 的数字来使用辅模拟帐号, 各个帐号的数据完全独立, 使用该功能需要购买专业版的权限, 且对应的辅账户可以在快期专业版上登录并进行观察

        Example1::

            from tqsdk import TqApi, TqAuth, TqKq

            tq_kq = TqKq()
            api = TqApi(account=tq_kq, auth=TqAuth("快期账户", "账户密码"))
            quote = api.get_quote("SHFE.cu2206")
            print(quote)
            # 下单限价单
            order = api.insert_order(symbol="SHFE.cu2206", direction='BUY', offset='OPEN', limit_price=quote.last_price, volume=1)
            while order.status == 'ALIVE':
                api.wait_update()
                print(order)  # 打印委托单信息

            print(tq_kq.get_account())  # 打印快期模拟账户信息

            print(tq_kq.get_position("SHFE.cu2206"))  # 打印持仓信息

            for trade in order.trade_records.values():
                print(trade)  # 打印委托单对应的成交信息
            api.close()

        Example2::

            from tqsdk import TqApi, TqAuth, TqKq, TqMultiAccount

            # 创建快期模拟账户和辅模拟账户001
            tq_kq = TqKq()
            tq_kq001= TqKq(number=1)

            # 使用多账户模块同时登录这两个模拟账户
            api = TqApi(account=TqMultiAccount([tq_kq,tq_kq001]), auth=TqAuth("快期账户", "账户密码"))

            print(tq_kq.get_account())  # 打印快期模拟账户信息

            print(tq_kq001.get_account())  # 打印快期模拟001账户信息

            api.close()


        """
        super().__init__("快期模拟", str(number) if number else "", "", td_url=td_url)
        self._account_no = number

    @property
    def _account_name(self):
        # 用于界面展示的用户信息
        if self._account_no:
            return f'{self._api._auth._user_name}:{self._account_no:03d}'
        else:
            return self._api._auth._user_name

    @property
    def _account_info(self):
        info = super(TqKq, self)._account_info
        info.update({
            "account_type": self._account_type
        })
        return info

    @property
    def _account_auth(self):
        return {
            "feature": "tq_ma" if self._account_no else None,
            "account_id": None,
            "auto_add": False,
        }

    def _update_otg_info(self, api):
        self._account_id = f'{api._auth._auth_id}{self._account_no:03d}' if self._account_no else api._auth._auth_id
        self._password = f'shinnytech{self._account_no:03d}' if self._account_no else api._auth._auth_id
        super(TqKq, self)._update_otg_info(api)


class TqKqStock(BaseOtg, StockMixin):
    """天勤实盘类"""

    def __init__(self, td_url: Optional[str] = None, number: Optional[int] = None):
        """
        创建快期股票模拟账户实例

        快期股票模拟为专业版功能，可以点击 `天勤量化专业版 <https://www.shinnytech.com/tqsdk_professional/>`_ 申请试用或购买

        Args:
            td_url (str): [可选]指定交易服务器的地址, 默认使用快期账户对应的交易服务地址

            number (int): [可选]模拟交易账号编号, 默认为主模拟账号, 可以通过指定 1~99 的数字来使用辅模拟帐号, 各个帐号的数据完全独立

        Example::

            from tqsdk import TqApi, TqAuth, TqKqStock, TqChan

            tq_kq_stock = TqKqStock()
            api = TqApi(account=tq_kq_stock, auth=TqAuth("快期账户", "账户密码"))
            quote = api.get_quote("SSE.688529")
            print(quote)
            # 下单限价单
            order = api.insert_order("SSE.688529", volume=200, direction="BUY", limit_price=quote.ask_price1)
            while order.status == 'ALIVE':
                api.wait_update()
                print(order)  # 打印委托单信息

            print(tq_kq_stock.get_account())  # 打印快期股票模拟账户信息

            print(tq_kq_stock.get_position("SSE.688529"))  # 打印持仓信息

            for trade in order.trade_records.values():
                print(trade)  # 打印委托单对应的成交信息
            api.close()

        """
        super().__init__("快期股票模拟", str(number) if number else "", "", td_url=td_url)
        self._account_no = number

    @property
    def _account_name(self):
        # 用于界面展示的用户信息
        if self._account_no:
            return f'{self._api._auth._user_name}_stock:{self._account_no:03d}'
        else:
            return self._api._auth._user_name + "_stock"

    @property
    def _account_info(self):
        info = super(TqKqStock, self)._account_info
        info.update({
            "account_type": self._account_type
        })
        return info

    @property
    def _account_auth(self):
        return {
            "feature": "tq_ma" if self._account_no else None,
            "account_id": self._auth_account_id,
            "auto_add": False,
        }

    def _update_otg_info(self, api):
        self._auth_account_id = api._auth._auth_id + "-sim-securities"
        self._account_id = f'{api._auth._auth_id}{self._account_no:03d}-sim-securities' if self._account_no else self._auth_account_id
        self._password = f'shinnytech{self._account_no:03d}' if self._account_no else api._auth._auth_id
        super(TqKqStock, self)._update_otg_info(api)
