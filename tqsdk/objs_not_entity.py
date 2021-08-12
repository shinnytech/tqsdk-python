#:!/usr/bin/env python
#:  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'

from collections import namedtuple
from typing import Callable, Union, Tuple

from pandas import DataFrame

from tqsdk.objs import Quote
from tqsdk.diff import _get_obj
from tqsdk.utils import _query_for_quote, query_all_fields, _generate_uuid

"""
这两个类只在 api 中用到，主要为了支持用户异步中 await 
没有继承 Entity 类
"""


async def ensure_quote(api, quote):
    if quote.price_tick > 0 and quote.datetime != "":
        return quote
    async with api.register_update_notify(quote) as update_chan:
        async for _ in update_chan:
            if quote.price_tick > 0 and quote.datetime != "":
                return quote


async def ensure_quote_with_underlying(api, quote):
    await ensure_quote(api, quote)
    if quote.underlying_symbol:
        await ensure_quote(api, quote.underlying_quote)
    return quote


class QuoteList(list):
    """
    请求合约信息和行情信息，self._task 完成时，所有的合约已经收到了合约信息和行情信息
    """

    def __init__(self, api, quotes):
        self._api = api
        list.__init__(self, quotes)
        self._task = api.create_task(self._ensure_quotes(), _caller_api=True)
        for quote in quotes:
            # 为每个 quote 对象创建 _task
            if not hasattr(quote, '_task'):
                quote._task = api.create_task(ensure_quote_with_underlying(api, quote), _caller_api=True)

    async def _ensure_symbols(self):
        if all([q.price_tick > 0 for q in self]):
            return
        query_symbols = [q._path[-1] for q in self if not q.price_tick > 0]
        query_pack = _query_for_quote(query_symbols)
        self._api._send_pack(query_pack)
        async with self._api.register_update_notify(self) as update_chan:
            async for _ in update_chan:
                if all([q.price_tick > 0 for q in self]):
                    return

    async def _ensure_quotes(self):
        await self._ensure_symbols()
        self._api._auth._has_md_grants([q._path[-1] for q in self])  # 权限检查
        # 发送的请求会请求到所有字段，如果是期权也会请求标的的合约信息
        underlying_symbols = set([q.underlying_symbol for q in self if q.underlying_symbol])
        need_quotes = set([q._path[-1] for q in self]).union(underlying_symbols)
        if need_quotes - self._api._requests["quotes"] != set():
            self._api._requests["quotes"] = self._api._requests["quotes"].union(need_quotes)
            self._api._send_pack({
                "aid": "subscribe_quote",
                "ins_list": ",".join(self._api._requests["quotes"]),
            })
        if all([q.datetime != "" for q in self]):
            return self
        all_quotes = self + [_get_obj(self._api._data, ["quotes", s], self._api._prototype["quotes"]["#"]) for s in underlying_symbols]
        async with self._api.register_update_notify(self) as update_chan:
            async for _ in update_chan:
                if all([q.datetime != "" for q in all_quotes]):
                    return self

    def __await__(self):
        return self._task.__await__()


async def _query_graphql_async(api, query_id, query, variables):
    api._send_pack({
        "aid": "ins_query",
        "query_id": query_id,
        "query": query,
        "variables": variables
    })
    symbols = _get_obj(api._data, ["symbols"])
    async with api.register_update_notify(symbols) as update_chan:
        async for _ in update_chan:
            s = symbols.get(query_id, {})
            if s.get("query") == query and s.get("variables") == variables:
                break


class SymbolList(list):
    """
    query 系列函数返回对象
    """

    def __init__(self, api, query_id: str, query: str, variables: dict, filter: Callable[[dict], list]):
        self._api = api
        self._query_id = query_id
        self._query = query
        self._variables = variables
        self._filter = filter
        list.__init__(self, [])
        self._task = api.create_task(self._query_graphql(), _caller_api=True)

    async def _query_graphql(self):
        pack = {
            "query": self._query,
            "variables": self._variables
        }
        symbols = _get_obj(self._api._data, ["symbols"])
        query_result = None
        for symbol in symbols.values():
            if symbol.items() >= pack.items():  # 检查是否发送过相同的请求
                query_result = symbol
        if query_result is None:
            await _query_graphql_async(self._api, self._query_id, self._query, self._variables)
            query_result = symbols.get(self._query_id)
        self += self._filter(query_result)
        if self._variables.get('timestamp'):  # 回测时，清空缓存的请求
            self._api._send_pack({
                "aid": "ins_query",
                "query_id": self._query_id,
                "query": "",
                "variables": {}
            })
        return self

    def __await__(self):
        return self._task.__await__()


class SymbolLevelList(namedtuple('SymbolLevel', ['in_money_options', 'at_money_options', 'out_of_money_options'])):
    """
    query 系列函数返回对象
    """

    def __new__(cls, *args, **kwargs):
        return super(SymbolLevelList, cls).__new__(cls, in_money_options=[], at_money_options=[], out_of_money_options=[])

    def __init__(self, api, query_id: str, query: str, variables: dict, filter: Callable[[dict], Tuple[list, list, list]]):
        self._api = api
        self._query_id = query_id
        self._query = query
        self._variables = variables
        self._filter = filter
        self._task = api.create_task(self._query_graphql(), _caller_api=True)

    async def _query_graphql(self):
        pack = {
            "query": self._query,
            "variables": self._variables
        }
        symbols = _get_obj(self._api._data, ["symbols"])
        query_result = None
        for symbol in symbols.values():
            if symbol.items() >= pack.items():  # 检查是否发送过相同的请求
                query_result = symbol
        if query_result is None:
            await _query_graphql_async(self._api, self._query_id, self._query, self._variables)
            query_result = symbols.get(self._query_id)
        l0, l1, l2 = self._filter(query_result)
        self[0].extend(l0)
        self[1].extend(l1)
        self[2].extend(l2)
        if self._variables.get('timestamp'):  # 回测时，清空缓存的请求
            self._api._send_pack({
                "aid": "ins_query",
                "query_id": self._query_id,
                "query": "",
                "variables": {}
            })
        return self

    def __await__(self):
        return self._task.__await__()


class TqDataFrame(DataFrame):

    def __init__(self, api, *args, **kwargs):
        super(TqDataFrame, self).__init__(*args, **kwargs)
        self.__dict__["_api"] = api
        self.__dict__["_task"] = api.create_task(self.async_update(), _caller_api=True)

    async def async_update(self):
        async with self._api.register_update_notify(self) as update_chan:
            async for _ in update_chan:
                if self._api._serials.get(id(self))["init"]:
                    return self

    def __await__(self):
        return self.__dict__["_task"].__await__()


class TqSymbolDataFrame(DataFrame):

    def __init__(self, api, symbol_list, backtest_timestamp, *args, **kwargs):
        self.__dict__["_api"] = api
        self.__dict__["_symbol_list"] = symbol_list
        self.__dict__["_backtest_timestamp"] = backtest_timestamp
        self.__dict__["_columns"] = [
            "ins_class",
            "instrument_id",
            "instrument_name",
            "price_tick",
            "volume_multiple",
            "max_limit_order_volume",
            "max_market_order_volume",
            "underlying_symbol",
            "strike_price",
            "exchange_id",
            "expired",
            "expire_datetime",
            "delivery_year",
            "delivery_month",
            "last_exercise_datetime",
            "exercise_year",
            "exercise_month",
            "option_class"
        ]
        default_quote = Quote(None)
        data = [{k: (s if k == "instrument_id" else default_quote[k]) for k in self.__dict__["_columns"]} for s in symbol_list]
        super(TqSymbolDataFrame, self).__init__(data=data, columns=self.__dict__["_columns"], *args, **kwargs)
        self.__dict__["_task"] = api.create_task(self.async_update(), _caller_api=True)

    async def async_update(self):
        query_id = _generate_uuid("PYSDK_api")
        variables = {"instrument_id": self.__dict__["_symbol_list"]}
        if self.__dict__["_backtest_timestamp"]:
            variables["timestamp"] = self.__dict__["_backtest_timestamp"]
            query = "query ($instrument_id:[String],$timestamp:Int64) {"
            query += "multi_symbol_info(instrument_id:$instrument_id,timestamp:$timestamp) {" + query_all_fields + "}}"
        else:
            query = "query ($instrument_id:[String]) {"
            query += "multi_symbol_info(instrument_id:$instrument_id) {" + query_all_fields + "}}"
        self.__dict__["_api"]._send_pack({
            "aid": "ins_query",
            "query_id": query_id,
            "query": query,
            "variables": variables
        })
        symbols = _get_obj(self.__dict__["_api"]._data, ["symbols"])
        async with self.__dict__["_api"].register_update_notify(symbols) as update_chan:
            async for _ in update_chan:
                query_result = symbols.get(query_id, {})
                if query_result:
                    quotes = self.__dict__["_api"]._symbols_to_quotes(query_result, keys=set(self.__dict__["_columns"]))
                    self._quotes_to_dataframe(quotes)
                    if self.__dict__["_backtest_timestamp"]:
                        # 回测时清空请求，不缓存请求内容
                        self.__dict__["_api"]._send_pack({
                            "aid": "ins_query",
                            "query_id": query_id,
                            "query": "",
                            "variables": {}
                        })
                    return self

    def _quotes_to_dataframe(self, quotes):
        default_quote = Quote(None)
        for col in self.__dict__["_columns"]:
            self.loc[:, col] = [quotes[s].get(col, default_quote[col]) for s in self.__dict__["_symbol_list"]]

    def __await__(self):
        return self.__dict__["_task"].__await__()
