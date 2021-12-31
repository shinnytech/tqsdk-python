#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'


from typing import Optional, Union

from tqsdk.diff import _get_obj
from tqsdk.entity import Entity
from tqsdk.objs import Account, Order, Trade, Position, SecurityAccount, SecurityOrder, SecurityTrade, SecurityPosition


def _get_api_instance(self):
    if hasattr(self, '_api'):
        return self._api
    import inspect
    raise Exception(f"未初始化 TqApi。请在 api 初始化后调用 {inspect.stack()[1].function}。")


class FutureMixin:

    _account_type = "FUTURE"

    def get_account(self) -> Account:
        """
        获取用户账户资金信息

        Returns:
            :py:class:`~tqsdk.objs.Account`: 返回一个账户对象引用. 其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新

        Example1::

            # 获取当前浮动盈亏
            from tqsdk import TqApi, TqAuth

            tqacc = TqAccount("N南华期货", "123456", "123456")
            api = TqApi(account=tqacc, auth=TqAuth("信易账户", "账户密码"))
            account = tqacc.get_account()
            print(account.float_profit)

            # 预计的输出是这样的:
            2180.0
            ...

        Example2::

            # 多账户模式下, 分别获取各账户浮动盈亏
            from tqsdk import TqApi, TqAuth, TqMultiAccount, TqAccount, TqKq, TqSim

            account = TqAccount("N南华期货", "123456", "123456")
            tqkq = TqKq()
            tqsim = TqSim()
            api = TqApi(TqMultiAccount([account, tqkq, tqsim]), auth=TqAuth("信易账户", "账户密码"))
            account1 = account.get_account()
            account2 = tqkq.get_account()
            account3 = tqsim.get_account()
            print(f"账户 1 浮动盈亏 {account1.float_profit}, 账户 2 浮动盈亏 {account2.float_profit}, 账户 3 浮动盈亏 {account3.float_profit}")
            api.close()

        """
        api = _get_api_instance(self)
        return _get_obj(api._data, ["trade", self._account_key, "accounts", "CNY"], Account(api))

    def get_position(self, symbol: Optional[str] = None) -> Union[Position, Entity]:
        """
        获取用户持仓信息

        Args:
            symbol (str): [可选]合约代码, 不填则返回所有持仓

        Returns:
            :py:class:`~tqsdk.objs.Position`: 当指定了 symbol 时, 返回一个持仓对象引用。
            其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新。

            不填 symbol 参数调用本函数, 将返回包含用户所有持仓的一个 ``tqsdk.objs.Entity`` 对象引用, 使用方法与dict一致, \
            其中每个元素的 key 为合约代码, value 为 :py:class:`~tqsdk.objs.Position`。

            注意: 为保留一些可供用户查询的历史信息, 如 volume_long_yd(本交易日开盘前的多头持仓手数) 等字段, 因此服务器会返回当天已平仓合约( pos_long 和 pos_short 等字段为0)的持仓信息

        Example1::

            # 获取 DCE.m2109 当前浮动盈亏
            from tqsdk import TqApi, TqAuth, TqAccount

            tqacc = TqAccount("N南华期货", "123456", "123456")
            api = TqApi(account=tqacc, auth=TqAuth("信易账户", "账户密码"))
            position = tqacc.get_position("DCE.m2109")
            print(position.float_profit_long + position.float_profit_short)
            while api.wait_update():
                print(position.float_profit_long + position.float_profit_short)

            # 预计的输出是这样的:
            300.0
            330.0
            ...

        Example2::

            # 多账户模式下, 分别获取各账户浮动盈亏
            from tqsdk import TqApi, TqAuth, TqMultiAccount, TqAccount, TqKq, TqSim

            account = TqAccount("N南华期货", "123456", "123456")
            tqkq = TqKq()
            tqsim = TqSim()
            api = TqApi(TqMultiAccount([account, tqkq, tqsim]), auth=TqAuth("信易账户", "账户密码"))
            position1 = account.get_position("DCE.m2101")
            position2 = tqkq.get_position("DCE.m2101")
            position3 = tqsim.get_position("DCE.m2101")
            print(f"账户 1 'DCE.m2101' 浮动盈亏 {position1.float_profit_long + position1.float_profit_short}, ",
                  f"账户 2 'DCE.m2101' 浮动盈亏 {position2.float_profit_long + position2.float_profit_short}, ",
                  f"账户 3 'DCE.m2101' 浮动盈亏 {position3.float_profit_long + position3.float_profit_short}")
            api.close()

        """
        api = _get_api_instance(self)
        if symbol:
            return _get_obj(api._data, ["trade", self._account_key, "positions", symbol], Position(api))
        return _get_obj(api._data, ["trade", self._account_key, "positions"])

    def get_order(self, order_id: Optional[str] = None) -> Union[Order, Entity]:
        """
        获取用户委托单信息

        Args:
            order_id (str): [可选]单号, 不填单号则返回所有委托单

        Returns:
            :py:class:`~tqsdk.objs.Order`: 当指定了 order_id 时, 返回一个委托单对象引用。 \
            其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新。

            不填 order_id 参数调用本函数, 将返回包含用户所有委托单的一个 ``tqsdk.objs.Entity`` 对象引用, \
            使用方法与dict一致, 其中每个元素的key为委托单号, value为 :py:class:`~tqsdk.objs.Order`

            注意: 在刚下单后, tqsdk 还没有收到回单信息时, 此对象中各项内容为空

        Example1::

            # 获取当前总挂单手数
            from tqsdk import TqApi, TqAuth

            tqacc = TqAccount("N南华期货", "123456", "123456")
            api = TqApi(account=tqacc, auth=TqAuth("信易账户", "账户密码"))
            orders = tqacc.get_order()
            while True:
                api.wait_update()
                print(sum(order.volume_left for oid, order in orders.items() if order.status == "ALIVE"))

            # 预计的输出是这样的:
            3
            3
            0
            ...

        Example2::

            # 多账户模式下, 分别获取各账户挂单手数
            from tqsdk import TqApi, TqAuth, TqMultiAccount, TqAccount, TqKq, TqSim

            account = TqAccount("N南华期货", "123456", "123456")
            tqkq = TqKq()
            tqsim = TqSim()
            api = TqApi(TqMultiAccount([account, tqkq, tqsim]), auth=TqAuth("信易账户", "账户密码"))
            orders1 = account.get_order()
            orders2 = tqkq.get_order()
            orders3 = tqsim.get_order()
            print(f"账户 1 挂单手数 {sum(order.volume_left for order in orders1.values() if order.status == "ALIVE")}, ",
                  f"账户 2 挂单手数 {sum(order.volume_left for order in orders2.values() if order.status == "ALIVE")}, ",
                  f"账户 3 挂单手数 {sum(order.volume_left for order in orders3.values() if order.status == "ALIVE")}")

            order = account.get_order(order_id="订单号")
            print(order)
            api.close()

        """
        api = _get_api_instance(self)
        if order_id:
            return _get_obj(api._data, ["trade", self._account_key, "orders", order_id], Order(api))
        return _get_obj(api._data, ["trade", self._account_key, "orders"])

    def get_trade(self, trade_id: Optional[str] = None) -> Union[Trade, Entity]:
        """
        获取用户成交信息

        Args:
            trade_id (str): [可选]成交号, 不填成交号则返回所有委托单

        Returns:
            :py:class:`~tqsdk.objs.Trade`: 当指定了trade_id时, 返回一个成交对象引用. \
            其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新.

            不填trade_id参数调用本函数, 将返回包含用户当前交易日所有成交记录的一个tqsdk.objs.Entity对象引用, 使用方法与dict一致, \
            其中每个元素的key为成交号, value为 :py:class:`~tqsdk.objs.Trade`

            推荐优先使用 :py:meth:`~tqsdk.objs.Order.trade_records` 获取某个委托单的相应成交记录, 仅当确有需要时才使用本函数.

        Example::

            # 多账户模式下, 分别获取各账户的成交记录
            from tqsdk import TqApi, TqAuth, TqMultiAccount

            account = TqAccount("N南华期货", "123456", "123456")
            tqkq = TqKq()
            tqsim = TqSim()
            api = TqApi(TqMultiAccount([account, tqkq, tqsim]), auth=TqAuth("信易账户", "账户密码"))
            trades1 = account.get_trade()
            trades2 = tqkq.get_trade()
            trades3 = tqsim.get_trade()
            print(trades1)
            print(trades2)
            print(trades3)
            api.close()
        """
        api = _get_api_instance(self)
        if trade_id:
            return _get_obj(api._data, ["trade", self._account_key, "trades", trade_id], Trade(api))
        return _get_obj(api._data, ["trade", self._account_key, "trades"])


class StockMixin:

    _account_type = "STOCK"

    def get_account(self) -> SecurityAccount:
        """
        获取用户账户资金信息

        Returns:
            :py:class:`~tqsdk.objs.SecurityAccount`: 返回一个账户对象引用. 其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新

        Example1::

            # 获取当前浮动盈亏
            from tqsdk import TqApi, TqAuth

            tqacc = TqAccount("N南华期货", "123456", "123456")
            api = TqApi(account=tqacc, auth=TqAuth("信易账户", "账户密码"))
            account = tqacc.get_account()
            print(account.float_profit)

            # 预计的输出是这样的:
            2180.0
            ...

        Example2::

            # 多账户模式下, 分别获取各账户浮动盈亏
            from tqsdk import TqApi, TqAuth, TqMultiAccount, TqAccount, TqKq, TqSim

            account = TqAccount("N南华期货", "123456", "123456")
            tqkq = TqKq()
            tqsim = TqSim()
            api = TqApi(TqMultiAccount([account, tqkq, tqsim]), auth=TqAuth("信易账户", "账户密码"))
            account1 = account.get_account()
            account2 = tqkq.get_account()
            account3 = tqsim.get_account()
            print(f"账户 1 浮动盈亏 {account1.float_profit}, 账户 2 浮动盈亏 {account2.float_profit}, 账户 3 浮动盈亏 {account3.float_profit}")
            api.close()

        """
        api = _get_api_instance(self)
        return _get_obj(api._data, ["trade", self._account_key, "accounts", "CNY"], SecurityAccount(api))

    def get_position(self, symbol: Optional[str] = None) -> Union[SecurityPosition, Entity]:
        """
        获取用户持仓信息

        Args:
            symbol (str): [可选]合约代码, 不填则返回所有持仓

        Returns:
            :py:class:`~tqsdk.objs.SecurityPosition`: 当指定了 symbol 时, 返回一个持仓对象引用。
            其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新。

            不填 symbol 参数调用本函数, 将返回包含用户所有持仓的一个 ``tqsdk.objs.Entity`` 对象引用, 使用方法与dict一致, \
            其中每个元素的 key 为合约代码, value 为 :py:class:`~tqsdk.objs.SecurityPosition`。


        Example::

            from tqsdk import TqApi, TqAuth, TqKqStock
            tqkqstock = TqKqStock()
            api = TqApi(account=tqkqstock, auth=TqAuth("信易账户", "账户密码"))
            position = tqkqstock.get_position('SSE.10003624')
            print(f"建仓日期 {position.create_date}, 持仓数量 {position.volume}")
            api.close()

        """
        api = _get_api_instance(self)
        if symbol:
            return _get_obj(api._data, ["trade", self._account_key, "positions", symbol], SecurityPosition(api))
        return _get_obj(api._data, ["trade", self._account_key, "positions"])

    def get_order(self, order_id: Optional[str] = None) -> Union[SecurityOrder, Entity]:
        """
        获取用户委托单信息

        Args:
            order_id (str): [可选]单号, 不填单号则返回所有委托单

        Returns:
            :py:class:`~tqsdk.objs.SecurityOrder`: 当指定了 order_id 时, 返回一个委托单对象引用。 \
            其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新。

            不填 order_id 参数调用本函数, 将返回包含用户所有委托单的一个 ``tqsdk.objs.Entity`` 对象引用, \
            使用方法与 dict 一致, 其中每个元素的 key 为委托单号, value为 :py:class:`~tqsdk.objs.SecurityOrder`

            注意: 在刚下单后, tqsdk 还没有收到回单信息时, 此对象中各项内容为空

        Example::

            from tqsdk import TqApi, TqAuth, TqKqStock
            tqkqstock = TqKqStock()
            api = TqApi(account=tqkqstock, auth=TqAuth("信易账户", "账户密码"))
            order = tqkqstock.get_order('委托单Id')
            print(f"委托股数 {order.volume_orign}, 剩余股数 {order.volume_left}")
            api.close()
        """
        api = _get_api_instance(self)
        if order_id:
            return _get_obj(api._data, ["trade", self._account_key, "orders", order_id], SecurityOrder(api))
        return _get_obj(api._data, ["trade", self._account_key, "orders"])

    def get_trade(self, trade_id: Optional[str] = None) -> Union[SecurityTrade, Entity]:
        """
        获取用户成交信息

        Args:
            trade_id (str): [可选]成交号, 不填成交号则返回所有委托单

        Returns:
            :py:class:`~tqsdk.objs.SecurityTrade`: 当指定了trade_id时, 返回一个成交对象引用. \
            其内容将在 :py:meth:`~tqsdk.api.TqApi.wait_update` 时更新.

            不填trade_id参数调用本函数, 将返回包含用户当前交易日所有成交记录的一个 ``tqsdk.objs.Entity`` 对象引用, 使用方法与dict一致, \
            其中每个元素的key为成交号, value为 :py:class:`~tqsdk.objs.SecurityTrade`

            推荐优先使用 :py:meth:`~tqsdk.objs.SecurityOrder.trade_records` 获取某个委托单的相应成交记录, 仅当确有需要时才使用本函数.

        Example::

            from tqsdk import TqApi, TqAuth, TqKqStock
            tqkqstock = TqKqStock()
            api = TqApi(account=tqkqstock, auth=TqAuth("信易账户", "账户密码"))
            trades = tqkqstock.get_trade('委托单Id')
            [print(trade.trade_id, f"成交股数 {trade.volume}, 成交价格 {trade.price}") for trade in trades]
            api.close()
        """
        api = _get_api_instance(self)
        if trade_id:
            return _get_obj(api._data, ["trade", self._account_key, "trades", trade_id], SecurityTrade(api))
        return _get_obj(api._data, ["trade", self._account_key, "trades"])
