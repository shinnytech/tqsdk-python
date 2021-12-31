#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'mayanqiong'

import math
from abc import abstractmethod
from datetime import datetime
from typing import Callable

from tqsdk.datetime import _is_in_trading_time
from tqsdk.diff import _simple_merge_diff
from tqsdk.tradeable.sim.utils import _get_price_range


class SimTradeBase(object):
    """
    本模块为 TqSim 交易部分的子模块的基类，纯同步计算，不涉及连接行情的动态信息，所以对于接口的调用有一些需要注意的要求

    不同的账户类型继承本模块，并实现具体账户类型的计算

    对外提供的接口:

    + init_snapshot: 返回初始的账户截面信息
    + insert_order -> (diffs, orders_events): 处理下单请求，调用 TqSimAccount.insert_order 之前应该调用过 update_quote，保证收到过合约的行情；期权还应该确保收到了标的的行情
    + cancel_order -> (diffs, orders_events)：处理撤单请求
    + update_quote -> (diffs, orders_events)：处理行情更新
    + settle -> (diffs, _orders_events, trade_log)：处理结算请求

    注意：

    + diffs (list) : 每个元素都是符合 diff 协议中 trade 交易部分的数据包，且返回的都是完整字段的对象，比如：order成交时，返回的是order完整对象而不是有变化的字段
    + orders_events  (list) : 按照顺序记录 order 的更新，返回给调用方
    + trade_log (dict) : 是结算前的账户日志信息

    diffs 由子类负责调用 _append_to_diffs
    orders_events 由父类统一处理在 order 状态变化时，在 list 中追加委托单实例

    """

    def __init__(self, account_key: str, account_id: str = "", init_balance: float = 10000000.0,
                 get_trade_timestamp: Callable = None, is_in_trading_time: Callable = None) -> None:
        self._account_key = account_key
        self._account_id = account_id
        self._quotes = {}  # 会记录所有的发来的行情
        # 初始化账户结构
        self._account = self._generate_account(init_balance)
        self._positions = {}  # {symbol: position, ...}
        self._orders = {}  # {symbol: {order_id: order}, ...}
        self._trades = []  # list 类型，与重构之前代码保持一致，list 可以保留 trade 生产的顺序信息
        self._diffs = []
        self._orders_events = []  # 按照顺序记录 order 的更新，返回给调用方
        self._max_datetime = ""  # 所有 quotes 的最大行情更新时间
        # 本模块在计算成交时间、判断是否在交易时间段内，默认使用所有 quotes 的最大行情更新时间当作当前时间，并且没有模拟到交易时的时间差
        # 若外部调用模块需要更精确时间，则由外部模块提供函数支持
        self._get_trade_timestamp = get_trade_timestamp if get_trade_timestamp else self._default_get_trade_timestamp
        self._is_in_trading_time = is_in_trading_time if is_in_trading_time else self._default_is_in_trading_time

    @abstractmethod
    def _generate_account(self, init_balance: float) -> dict:
        """返回 account 账户结构"""
        pass

    @abstractmethod
    def _generate_order(self, pack: dict) -> dict:
        """返回 order 委托单结构"""
        pass

    @abstractmethod
    def _generate_trade(self, order, quote, price) -> dict:
        """返回 trade 成交对象结构"""
        pass

    @abstractmethod
    def _generate_position(self, symbol, quote, underlying_quote) -> dict:
        """返回 position 对象结构"""
        pass

    @abstractmethod
    def _check_insert_order(self, order, symbol, position, quote, underlying_quote):
        """检查是否可以下单，在 order 原对象上修改属性"""
        pass

    @abstractmethod
    def _on_insert_order(self, order, symbol, position, quote, underlying_quote):
        """将 order 记入 order_book 时调用"""
        pass

    @abstractmethod
    def _on_order_failed(self, symbol, order):
        """处理 order 变为 FINISHED，且没有成交，撤单"""
        pass

    @abstractmethod
    def _on_order_traded(self, order, trade, symbol, position, quote, underlying_quote):
        """处理 order 变为 FINISHED，且全部成交"""
        pass

    @abstractmethod
    def _on_update_quotes(self, symbol, position, quote, underlying_quote):
        """更新合约行情后，更行对应的持仓及账户信息"""
        pass

    @abstractmethod
    def _on_settle(self):
        """结算时，应该调整 委托单、持仓、账户"""
        pass

    def init_snapshot(self):
        """返回初始账户截面信息"""
        return {
            "trade": {
                self._account_key: {
                    "accounts": {"CNY": self._account.copy()},
                    "positions": {},
                    "orders": {},
                    "trades": {}
                }
            }
        }

    def insert_order(self, symbol, pack):
        quote, underlying_quote = self._get_quotes_by_symbol(symbol)
        position = self._ensure_position(symbol, quote, underlying_quote)
        order = self._generate_order(pack)
        self._orders_events.append(order.copy())
        self._check_insert_order(order, symbol, position, quote, underlying_quote)
        if order["status"] == "FINISHED":
            self._orders_events.append(order.copy())
        else:
            orders = self._orders.setdefault(symbol, {})
            orders[order["order_id"]] = order  # order 存入全局
            self._on_insert_order(order, symbol, position, quote, underlying_quote)
            self._match_order(order, symbol, position, quote, underlying_quote)
        return self._return_results()

    def cancel_order(self, symbol, pack):
        order = self._orders.get(symbol, {}).get(pack["order_id"], {})
        if order.get("status") == "ALIVE":
            order["last_msg"] = "已撤单"
            order["status"] = "FINISHED"
            self._on_order_failed(symbol, order)
            self._orders_events.append(order)
            del self._orders[symbol][order["order_id"]]  # 删除 order
        return self._return_results()

    def update_quotes(self, symbol, pack):
        for q in pack.get("quotes", {}).values():
            self._max_datetime = max(q.get("datetime", ""), self._max_datetime)
        _simple_merge_diff(self._quotes, pack.get("quotes", {}), reduce_diff=False)
        quote, underlying_quote = self._get_quotes_by_symbol(symbol)
        # 某些非交易时间段，ticks 回测是 quote 的最新价有可能是 nan，无效的行情直接跳过
        if math.isnan(quote["last_price"]):
            return [], []
        # 撮合委托单
        orders = self._orders.get(symbol, {})
        position = self._ensure_position(symbol, quote, underlying_quote)
        for order_id in list(orders.keys()):  # match_order 过程中可能会删除 orders 下对象
            self._match_order(orders[order_id], symbol, position, quote, underlying_quote)
        self._on_update_quotes(symbol, position, quote, underlying_quote)  # 调整持仓及账户信息
        return self._return_results()

    def _match_order(self, order, symbol, position, quote, underlying_quote=None):
        assert order["status"] == "ALIVE"
        status, last_msg, price = SimTradeBase.match_order(order, quote)
        if status == "FINISHED":
            order["last_msg"] = last_msg
            order["status"] = status
            if last_msg == "全部成交":
                trade = self._generate_trade(order, quote, price)
                self._trades.append(trade)
                self._on_order_traded(order, trade, symbol, position, quote, underlying_quote)
            else:
                self._on_order_failed(symbol, order)
            # 成交后记录 orders_event, 删除 order
            self._orders_events.append(order)
            del self._orders[symbol][order["order_id"]]

    def settle(self):
        trade_log = {
            "trades": self._trades,
            "account": self._account.copy(),
            "positions": {k: v.copy() for k, v in self._positions.items()}
        }
        # 为下一交易日调整账户
        self._trades = []
        self._on_settle()
        for symbol in self._orders:
            for order in self._orders[symbol].values():
                self._orders_events.append(order)
            self._orders[symbol] = {}
        diffs, orders_events = self._return_results()
        return diffs, orders_events, trade_log

    def _ensure_position(self, symbol, quote, underlying_quote):
        position = self._positions.get(symbol, None)
        if position is None:
            position = self._generate_position(symbol, quote, underlying_quote)
            self._positions[symbol] = position
        return position

    def _get_quotes_by_symbol(self, symbol):
        """返回指定合约及标的合约，在本模块执行过程中，应该保证一定有合约行情"""
        quote = self._quotes.get(symbol)
        assert quote and quote.get("datetime"), "未收到指定合约行情"
        underlying_quote = None
        if quote["ins_class"].endswith("OPTION"):
            underlying_quote = self._quotes.get(quote["underlying_symbol"])
            assert underlying_quote and underlying_quote.get("datetime"), "未收到指定合约的标的行情"
        return quote, underlying_quote

    def _append_to_diffs(self, path, obj):
        target = {}
        diff = {'trade': {self._account_key: target}}
        while len(path) > 0:
            k = path.pop(0)
            target[k] = obj.copy() if len(path) == 0 else {}
            target = target[k]
        self._diffs.append(diff)

    def _return_results(self):
        """
        返回两项内容：diffs: list, orders_events: list
        diffs 是截面的变更
        orders_events 是委托单变化
        """
        diffs, self._diffs = self._diffs, []
        orders_events, self._orders_events = self._orders_events, []
        return diffs, orders_events

    def _default_get_trade_timestamp(self):
        """获取交易时间的默认方法，为当前所有 quote 的最大行情时间"""
        return int(datetime.strptime(self._max_datetime, "%Y-%m-%d %H:%M:%S.%f").timestamp() * 1e6) * 1000

    def _default_is_in_trading_time(self, quote):
        """判断是否在交易时间段"""
        return _is_in_trading_time(quote, self._max_datetime, float("nan"))

    @staticmethod
    def match_order(order, quote) -> (str, str, float):
        """
        撮合交易规则：
        * 市价单使用对手盘价格成交, 如果没有对手盘(涨跌停)则自动撤单
        * 限价单要求报单价格达到或超过对手盘价格才能成交, 成交价为报单价格, 如果没有对手盘(涨跌停)则无法成交
        * 模拟交易只有全部成交
        returns: status, last_msg, price
        """
        status, last_msg = "ALIVE", ""
        ask_price, bid_price = _get_price_range(quote)
        # order 预期成交价格
        if order["price_type"] in ["ANY", "BEST", "FIVELEVEL"]:
            price = ask_price if order["direction"] == "BUY" else bid_price
        else:
            price = order["limit_price"]
        if order["price_type"] == "ANY" and math.isnan(price):
            status, last_msg = "FINISHED", "市价指令剩余撤销"
        if order.get("time_condition") == "IOC":  # IOC 立即成交，限价下单且不能成交的价格，直接撤单
            if order["direction"] == "BUY" and price < ask_price or order["direction"] == "SELL" and price > bid_price:
                status, last_msg = "FINISHED", "已撤单报单已提交"
        if order["direction"] == "BUY" and price >= ask_price or order["direction"] == "SELL" and price <= bid_price:
            status, last_msg = "FINISHED", "全部成交"
        return status, last_msg, price
