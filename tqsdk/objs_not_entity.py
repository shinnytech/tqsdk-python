#:!/usr/bin/env python
#:  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'


from pandas import DataFrame

from tqsdk.utils import _query_for_quote

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
                quote._task = api.create_task(ensure_quote(api, quote), _caller_api=True)

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
        if set([q._path[-1] for q in self]) - self._api._requests["quotes"] != set():
            self._api._requests["quotes"] = self._api._requests["quotes"].union(set([q._path[-1] for q in self]))
            self._api._send_pack({
                "aid": "subscribe_quote",
                "ins_list": ",".join(self._api._requests["quotes"]),
            })
        if all([q.datetime != "" for q in self]):
            return self
        async with self._api.register_update_notify(self) as update_chan:
            async for _ in update_chan:
                if all([q.datetime != "" for q in self]):
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

    def __init__(self, api, quotes_list,  *args, **kwargs):
        self.__dict__["_api"] = api
        self.__dict__["_quotes_list"] = quotes_list
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
        super(TqSymbolDataFrame, self).__init__(data=self.__dict__["_quotes_list"], columns=self.__dict__["_columns"])
        self.__dict__["_task"] = api.create_task(self.async_update(), _caller_api=True)
        self.__dict__["_ready"] = all([q.price_tick > 0 for q in self.__dict__["_quotes_list"]])

    async def async_update(self):
        if self.__dict__["_ready"]:
            return self
        query_symbols = [q._path[-1] for q in self.__dict__["_quotes_list"] if not q.price_tick > 0]
        query_pack = _query_for_quote(query_symbols)
        self._api._send_pack(query_pack)
        async with self._api.register_update_notify(self.__dict__["_quotes_list"]) as update_chan:
            async for _ in update_chan:
                self.__dict__["_ready"] = all([q.price_tick > 0 for q in self.__dict__["_quotes_list"]])
                if self.__dict__["_ready"]:
                    return self._quotes_to_dataframe()

    def _quotes_to_dataframe(self):
        for col in self.__dict__["_columns"]:
            self.loc[:, col] = [q[col] for q in self.__dict__["_quotes_list"]]
        return self

    def __await__(self):
        return self.__dict__["_task"].__await__()
