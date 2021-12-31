#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'


from typing import Optional

from tqsdk.tradeable.otg.base_otg import BaseOtg
from tqsdk.tradeable.mixin import FutureMixin, StockMixin


class TqKq(BaseOtg, FutureMixin):
    """天勤快期模拟账户类"""

    def __init__(self, td_url: Optional[str] = None):
        """
        创建快期模拟账户实例
        """
        super().__init__("快期模拟", "", "", td_url=td_url)

    @property
    def _account_name(self):
        # 用于界面展示的用户信息
        return self._api._auth._user_name

    @property
    def _account_info(self):
        info = super(TqKq, self)._account_info
        info.update({
            "account_type": self._account_type
        })
        return info

    def _update_otg_info(self, api):
        self._account_id = api._auth._auth_id
        self._password = api._auth._auth_id
        super(TqKq, self)._update_otg_info(api)


class TqKqStock(BaseOtg, StockMixin):
    """天勤实盘类"""

    def __init__(self, td_url: Optional[str] = None):
        """
        创建快期股票模拟账户实例

        快期股票模拟为专业版功能，可以点击 `天勤量化专业版 <https://www.shinnytech.com/tqsdk_professional/>`_ 申请试用或购买

        Example::

            from tqsdk import TqApi, TqAuth, TqKqStock, TqChan

            tq_kq_stock = TqKqStock()
            api = TqApi(account=tq_kq_stock, auth=TqAuth("信易账户", "账户密码"))
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
        super().__init__("快期股票模拟", "", "", td_url=td_url)

    @property
    def _account_name(self):
        # 用于界面展示的用户信息
        return self._api._auth._user_name + "_stock"

    @property
    def _account_info(self):
        info = super(TqKqStock, self)._account_info
        info.update({
            "account_type": self._account_type
        })
        return info

    def _update_otg_info(self, api):
        self._account_id = api._auth._auth_id + "-sim-securities"
        self._password = api._auth._auth_id
        super(TqKqStock, self)._update_otg_info(api)
