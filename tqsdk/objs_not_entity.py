#:!/usr/bin/env python
#:  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'

from collections import namedtuple
from datetime import datetime
from typing import Callable, Tuple

import aiohttp
from pandas import DataFrame, Series
from sgqlc.operation import Operation
from tqsdk.backtest import TqBacktest

from tqsdk.datetime import _get_expire_rest_days
from tqsdk.ins_schema import ins_schema, _add_all_frags
from tqsdk.objs import Quote
from tqsdk.diff import _get_obj
from tqsdk.utils import _query_for_quote, _generate_uuid
from tqsdk.tafunc import _get_t_series, get_impv, _get_d1, get_delta, get_theta, get_gamma, get_vega, get_rho

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


async def _query_graphql_async(api, query_id, query):
    api._send_pack({
        "aid": "ins_query",
        "query_id": query_id,
        "query": query
    })
    symbols = _get_obj(api._data, ["symbols"])
    async with api.register_update_notify(symbols) as update_chan:
        async for _ in update_chan:
            s = symbols.get(query_id, {})
            if s.get("query") == query:
                break


class SymbolList(list):
    """
    query 系列函数返回对象
    """

    def __init__(self, api, query_id: str, query: str, filter: Callable[[dict], list]):
        self._api = api
        self._query_id = query_id
        self._query = query
        self._filter = filter
        list.__init__(self, [])
        self._task = api.create_task(self._query_graphql(), _caller_api=True)

    async def _query_graphql(self):
        pack = {"query": self._query}
        symbols = _get_obj(self._api._data, ["symbols"])
        query_result = None
        for symbol in symbols.values():
            if symbol.items() >= pack.items():  # 检查是否发送过相同的请求
                query_result = symbol
        if query_result is None:
            await _query_graphql_async(self._api, self._query_id, self._query)
            query_result = symbols.get(self._query_id)
        self += self._filter(query_result)
        if isinstance(self._api._backtest, TqBacktest):  # 回测时，清空缓存的请求
            self._api._send_pack({
                "aid": "ins_query",
                "query_id": self._query_id,
                "query": ""
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

    def __init__(self, api, query_id: str, query: str, filter: Callable[[dict], Tuple[list, list, list]]):
        self._api = api
        self._query_id = query_id
        self._query = query
        self._filter = filter
        self._task = api.create_task(self._query_graphql(), _caller_api=True)

    async def _query_graphql(self):
        pack = {"query": self._query}
        symbols = _get_obj(self._api._data, ["symbols"])
        query_result = None
        for symbol in symbols.values():
            if symbol.items() >= pack.items():  # 检查是否发送过相同的请求
                query_result = symbol
        if query_result is None:
            await _query_graphql_async(self._api, self._query_id, self._query)
            query_result = symbols.get(self._query_id)
        l0, l1, l2 = self._filter(query_result)
        self[0].extend(l0)
        self[1].extend(l1)
        self[2].extend(l2)
        if isinstance(self._api._backtest, TqBacktest):  # 回测时，清空缓存的请求
            self._api._send_pack({
                "aid": "ins_query",
                "query_id": self._query_id,
                "query": ""
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
            "product_id",
            "expired",
            "expire_datetime",
            "expire_rest_days",
            "delivery_year",
            "delivery_month",
            "last_exercise_datetime",
            "exercise_year",
            "exercise_month",
            "option_class",
            "upper_limit",
            "lower_limit",
            "pre_settlement",
            "pre_open_interest",
            "pre_close",
            "trading_time_day",
            "trading_time_night"
        ]
        default_quote = Quote(None)
        data = [{k: (s if k == "instrument_id" else default_quote.get(k, None)) for k in self.__dict__["_columns"]} for s in symbol_list]
        super(TqSymbolDataFrame, self).__init__(data=data, columns=self.__dict__["_columns"], *args, **kwargs)
        self.__dict__["_task"] = api.create_task(self.async_update(), _caller_api=True)

    async def async_update(self):
        query_id = _generate_uuid("PYSDK_api")
        op = Operation(ins_schema.rootQuery)
        variables = {"instrument_id": self.__dict__["_symbol_list"]}
        if self.__dict__["_backtest_timestamp"]:
            variables["timestamp"] = self.__dict__["_backtest_timestamp"]
        query = op.multi_symbol_info(**variables)
        _add_all_frags(query)
        self.__dict__["_api"]._send_pack({
            "aid": "ins_query",
            "query_id": query_id,
            "query": op.__to_graphql__()
        })
        symbols = _get_obj(self.__dict__["_api"]._data, ["symbols"])
        async with self.__dict__["_api"].register_update_notify(symbols) as update_chan:
            async for _ in update_chan:
                query_result = symbols.get(query_id, {})
                if query_result:
                    all_keys = set(self.__dict__["_columns"])
                    all_keys.add('trading_time')
                    quotes = self.__dict__["_api"]._symbols_to_quotes(query_result, keys=all_keys)
                    self._quotes_to_dataframe(quotes)
                    if self.__dict__["_backtest_timestamp"]:
                        # 回测时这些字段应该为 nan
                        self.loc[:, ["upper_limit", "lower_limit", "pre_settlement", "pre_open_interest", "pre_close"]] = float('nan')
                        # 回测时清空请求，不缓存请求内容
                        self.__dict__["_api"]._send_pack({
                            "aid": "ins_query",
                            "query_id": query_id,
                            "query": ""
                        })
                    return self

    def _get_trading_time(self, quotes, symbol, key):
        v = quotes[symbol].get('trading_time', {'day': [], 'night': []}).get(key, [])
        return v if v else None

    def _quotes_to_dataframe(self, quotes):
        default_quote = Quote(None)
        for col in self.__dict__["_columns"]:
            if col == "expire_rest_days":
                current_dt = self._api._get_current_datetime().timestamp()
                self.loc[:, col] = [_get_expire_rest_days(quotes[s]['expire_datetime'], current_dt)
                                    if quotes[s].get('expire_datetime') else float('nan')
                                    for s in self.__dict__["_symbol_list"]]
            elif col == "trading_time_day" or col == "trading_time_night":
                k = 'day' if col == "trading_time_day" else 'night'
                self.loc[:, col] = Series([self._get_trading_time(quotes, s, k) for s in self.__dict__["_symbol_list"]])
            else:
                self.loc[:, col] = Series([quotes[s].get(col, default_quote[col]) for s in self.__dict__["_symbol_list"]])

    def __await__(self):
        return self.__dict__["_task"].__await__()


class TqSymbolRankingDataFrame(DataFrame):

    def __init__(self, api, symbol, ranking_type, days, start_dt, broker):
        self.__dict__["_api"] = api
        params = {'symbol': symbol}
        if days is not None:
            params['days'] = days
        if start_dt is not None:
            params['start_date'] = start_dt.strftime("%Y%m%d")
        if broker is not None:
            params['broker'] = broker
        self.__dict__["_params"] = params
        self.__dict__["_symbol"] = symbol
        self.__dict__["_ranking_type"] = f"{ranking_type.lower()}_ranking"
        self.__dict__["_columns"] = [
            "datetime",
            "symbol",
            "exchange_id",
            "instrument_id",
            "broker",
            "volume",
            "volume_change",
            "volume_ranking",
            "long_oi",
            "long_change",
            "long_ranking",
            "short_oi",
            "short_change",
            "short_ranking"
        ]
        super(TqSymbolRankingDataFrame, self).__init__(data=[], columns=self.__dict__["_columns"])
        self.__dict__["_task"] = api.create_task(self.async_update(), _caller_api=True)

    async def _get_ranking_data(self, ranking_id):
        # 下载持仓排名数据，并将数据发回到 api.recv_chan
        async with aiohttp.ClientSession(headers=self.__dict__["_api"]._base_headers) as session:
            url = "https://symbol-ranking-system-fc-api.shinnytech.com/srs"
            async with session.get(url, params=self.__dict__["_params"]) as response:
                response.raise_for_status()
                content = await response.json()
                await self.__dict__["_api"]._ws_md_recv_chan.send({
                    "aid": "rtn_data",
                    "data": [{
                        "_symbol_rankings": {
                            ranking_id: content
                        }
                    }]
                })

    async def async_update(self):
        ranking_id = _generate_uuid("PYSDK_rank")
        self.__dict__["_api"].create_task(self._get_ranking_data(ranking_id), _caller_api=True)  # 错误会抛给 api 处理
        symbol_rankings = _get_obj(self.__dict__["_api"]._data, ["_symbol_rankings"])
        async with self.__dict__["_api"].register_update_notify(symbol_rankings) as update_chan:
            async for _ in update_chan:
                content = symbol_rankings.get(ranking_id, None)
                if content is None:
                    continue
                data = self._content_to_list(content)
                for i, d in enumerate(data):
                    self.loc[i] = d
                self.dropna(subset=[self.__dict__["_ranking_type"]], inplace=True)
                self.sort_values(by=['datetime', self.__dict__["_ranking_type"]], inplace=True, ignore_index=True)
                # 读完数据，清空数据
                await self.__dict__["_api"]._ws_md_recv_chan.send({
                    "aid": "rtn_data",
                    "data": [{
                        "_symbol_rankings": {
                            ranking_id: None
                        }
                    }]
                })
                return self

    def _content_to_list(self, content):
        data = {}
        for dt in content.keys():
            for symbol in content[dt].keys():
                if content[dt][symbol] is None:
                    continue
                for data_type, rankings in content[dt][symbol].items():
                    for broker, rank_item in rankings.items():
                        item = data.setdefault((dt, symbol, broker), self._get_default_item(dt, symbol, broker))
                        if data_type == 'volume_ranking':
                            item['volume'] = rank_item['volume']
                            item['volume_change'] = rank_item['varvolume']
                            item['volume_ranking'] = rank_item['ranking']
                        elif data_type == 'long_ranking':
                            item['long_oi'] = rank_item['volume']
                            item['long_change'] = rank_item['varvolume']
                            item['long_ranking'] = rank_item['ranking']
                        elif data_type == 'short_ranking':
                            item['short_oi'] = rank_item['volume']
                            item['short_change'] = rank_item['varvolume']
                            item['short_ranking'] = rank_item['ranking']
        return data.values()

    def _get_default_item(self, dt, symbol, broker):
        return {
            "datetime": dt,
            "symbol": symbol,
            "exchange_id": symbol.split(".", maxsplit=1)[0],
            "instrument_id": symbol.split(".", maxsplit=1)[1],
            "broker": broker,
            "volume": float('nan'),
            "volume_change": float('nan'),
            "volume_ranking": float('nan'),
            "long_oi": float('nan'),
            "long_change": float('nan'),
            "long_ranking": float('nan'),
            "short_oi": float('nan'),
            "short_change": float('nan'),
            "short_ranking": float('nan')
        }

    def __await__(self):
        return self.__dict__["_task"].__await__()



class TqOptionGreeksDataFrame(DataFrame):

    def __init__(self, api, symbol_list, v_list, r):
        self.__dict__["_api"] = api
        self.__dict__["_symbol_list"] = symbol_list
        self.__dict__["_v_list"] = v_list
        self.__dict__["_r"] = r
        self.__dict__["_columns"] = [
            "instrument_id",
            "instrument_name",
            "option_class",
            "expire_rest_days",
            "expire_datetime",
            "underlying_symbol",
            "strike_price",
            "delta",
            "gamma",
            "theta",
            "vega",
            "rho"
        ]
        super(TqOptionGreeksDataFrame, self).__init__(data=[], columns=self.__dict__["_columns"])
        self.__dict__["_task"] = api.create_task(self.async_update(), _caller_api=True)

    async def async_update(self):
        symbol_list = self.__dict__["_symbol_list"]
        quotes = await self.__dict__["_api"].get_quote_list(symbol_list)
        if not all([q.ins_class.endswith("OPTION") for q in quotes]):
            raise Exception("quote 参数列表中元素必须是期权类型")
        for i, q in enumerate(quotes):
            self.loc[i] = {k: q.get(k, float('nan')) for k in self.__dict__["_columns"]}
        self._get_greeks(quotes)
        return self

    def _get_greeks(self, quotes):
        series_close = Series(data=[q.last_price for q in quotes])  # 期权最新价
        series_close1 = Series(data=[q.underlying_quote.last_price for q in quotes])  # 标的最新价
        series_o = Series(data=[q.option_class for q in quotes])
        series_datetime = Series(data=[datetime.strptime(q.datetime, "%Y-%m-%d %H:%M:%S.%f").timestamp() * 1000000000 for q in quotes])
        series_expire_datetime = Series(data=[q.expire_datetime for q in quotes])
        series_t = _get_t_series(series_datetime, 0, series_expire_datetime)  # 到期时间
        if self.__dict__["_v_list"] is None:
            series_v = get_impv(series_close1, series_close, self["strike_price"], self.__dict__["_r"], 0.3, series_t, series_o)
        else:
            series_v = Series(data=self.__dict__["_v_list"])
        series_d1 = _get_d1(series_close1, self["strike_price"], self.__dict__["_r"], series_v, series_t)
        self["delta"] = get_delta(series_close1, self["strike_price"], self.__dict__["_r"], series_v, series_t, series_o, series_d1)
        self["theta"] = get_theta(series_close1, self["strike_price"], self.__dict__["_r"], series_v, series_t, series_o, series_d1)
        self["gamma"] = get_gamma(series_close1, self["strike_price"], self.__dict__["_r"], series_v, series_t, series_d1)
        self["vega"] = get_vega(series_close1, self["strike_price"], self.__dict__["_r"], series_v, series_t, series_d1)
        self["rho"] = get_rho(series_close1, self["strike_price"], self.__dict__["_r"], series_v, series_t, series_o, series_d1)

    def __await__(self):
        return self.__dict__["_task"].__await__()
