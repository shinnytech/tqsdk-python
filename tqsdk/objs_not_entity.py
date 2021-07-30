#:!/usr/bin/env python
#:  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'


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
                    # todo: api.wait_update 的实现限制，每次都需要重新发送请求，api.query_symbol_info 文档有记录
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
