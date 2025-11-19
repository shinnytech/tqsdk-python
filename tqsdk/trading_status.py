#!/usr/bin/env python3
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'

import math
from shinny_structlog import ShinnyLoggerAdapter

from tqsdk.baseModule import TqModule
from tqsdk.channel import TqChan
from tqsdk.connect import TqConnect, TsReconnectHandler
from tqsdk.entity import Entity
from tqsdk.objs import Quote
from tqsdk.utils import _query_for_quote
from tqsdk.diff import _get_obj, _merge_diff

class TqTradingStatus(TqModule):
    """
    交易状态模块，建立 websocket 连接
    """

    async def _run(self, api, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan):
        self._api = api
        self._logger = self._api._logger.getChild("TradingStatus")
        self._init_ts_ws = False
        self._api_send_chan = api_send_chan
        self._api_recv_chan = api_recv_chan
        self._md_send_chan = md_send_chan
        self._md_recv_chan = md_recv_chan
        self._ts_send_chan = TqChan(self._api, chan_name="send to ts_reconn")
        self._ts_recv_chan = TqChan(self._api, chan_name="recv from ts_reconn")
        self._data = Entity()
        self._data._instance_entity([])
        self._quote_chan = TqChan(self._api, last_only=True)
        self._prototype = {
            "quotes": {
                "#": Quote(self._api),  # 行情的数据原型
            }
        }
        self._quotes_ready = {}
        self._quotes_unready = {}
        self._tasks = [self._api.create_task(self._symbol_info_watcher())]
        try:
            await super(TqTradingStatus, self)._run(api, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan, self._ts_send_chan, self._ts_recv_chan)
        finally:
            await self._api._cancel_tasks(*self._tasks)

    async def _subscribe_trading_status(self):
        """订阅交易状态服务"""
        ins_list = set()
        for quote in self._quotes_ready.values():
            if quote.ins_class == "OPTION" and quote.underlying_symbol:
                ins_list.add(quote.underlying_symbol)
            else:
                ins_list.add(quote.instrument_id)

        ins_list_str = ",".join(ins_list)
        if ins_list_str:
            await self._ts_send_chan.send({"aid": "subscribe_trading_status", "ins_list": ins_list_str})

    def _extend_option_trading_status(self, diffs):
        """为期权扩展交易状态信息"""
        received_statuses = {
            k: v for d in diffs for k, v in d.get('trading_status', {}).items()
        }
        if not received_statuses:
            return

        extended_diffs = [
            {'trading_status': {
                quote.instrument_id: {
                    'symbol': quote.instrument_id,
                    'trade_status': received_statuses[quote.underlying_symbol]['trade_status']
                }
            }}
            for quote in self._quotes_ready.values()
            if quote.ins_class == 'OPTION' and quote.underlying_symbol in received_statuses
        ]
        diffs.extend(extended_diffs)

    def _normalize_trade_status(self, diffs):
        """标准化交易状态，将非交易状态统一为NOTRADING"""
        for d in diffs:
            for _, ts in d.get('trading_status', {}).items():
                if ts['trade_status'] not in ["AUCTIONORDERING", "CONTINOUS"]:
                    ts['trade_status'] = "NOTRADING"

    async def _query_symbol_info(self, symbols):
        """查询缺少合约信息的quotes"""
        for symbol in symbols:
            self._quotes_unready[symbol]["_listener"].add(self._quote_chan)
        for query_pack in _query_for_quote(list(symbols), self._api._pre20_ins_info.keys()):
            await self._md_send_chan.send(query_pack)

    async def _symbol_info_watcher(self):
        async for _ in self._quote_chan:
            for symbol in await self._unready_to_ready():
                self._quotes_ready[symbol]["_listener"].discard(self._quote_chan)

    async def _unready_to_ready(self):
        ready_delta = {symbol for symbol, quote in self._quotes_unready.items() if not math.isnan(quote.price_tick)}
        for symbol in ready_delta:
            quote = self._quotes_unready.pop(symbol)
            self._quotes_ready[symbol] = quote
        if ready_delta:
            await self._subscribe_trading_status()
        return ready_delta

    async def _handle_recv_data(self, pack, chan):
        """
        处理所有上游收到的数据包
        """
        if pack['aid'] == 'rtn_data':
            if chan == self._md_recv_chan:  # 从行情收到的数据包
                datas = pack.get("data", [])
                self._diffs.extend(datas)
                for d in datas:
                    quotes_diff = d.get("quotes", {})
                    _merge_diff(self._data, {"quotes": {k: quotes_diff[k] for k in quotes_diff.keys() & self._quotes_unready.keys()}}, self._prototype, persist=False, reduce_diff=False)
            elif chan == self._ts_recv_chan:  # 从交易状态服务收到的数据包
                diffs = pack.get('data', [])
                self._extend_option_trading_status(diffs)
                self._normalize_trade_status(diffs)
                self._diffs.extend(diffs)
        else:
            await self._api_recv_chan.send(pack)

    async def _handle_req_data(self, pack):
        """处理所有下游发送的非 peek_message 数据包"""
        if pack['aid'] == 'subscribe_trading_status':
            if self._init_ts_ws is False:
                self._init_ts_ws = True
                self._create_ts_run()
            unseen = set(pack["ins_list"].split(",")) - self._quotes_ready.keys() - self._quotes_unready.keys()
            for symbol in unseen:
                self._quotes_unready[symbol] = _get_obj(self._data, ["quotes", symbol], self._prototype["quotes"]["#"])
            await self._query_symbol_info(unseen - await self._unready_to_ready())
        else:
            await self._md_send_chan.send(pack)

    def _create_ts_run(self):
        ts_url = "wss://trading-status.shinnytech.com/status"
        conn_logger = self._api._logger.getChild("TqConnect")
        ws_ts_send_chan = TqChan(self._api, chan_name="send to ts")
        ws_ts_recv_chan = TqChan(self._api, chan_name="recv from ts")
        ws_ts_send_chan._logger_bind(chan_from="ts_reconn", url=ts_url)
        ws_ts_recv_chan._logger_bind(chan_to="ts_reconn", url=ts_url)
        conn = TqConnect(logger=ShinnyLoggerAdapter(conn_logger, url=ts_url), conn_id="ts")
        self._tasks.append(self._api.create_task(conn._run(self._api, ts_url, ws_ts_send_chan, ws_ts_recv_chan), _caller_api=True))
        ts_reconnect = TsReconnectHandler(logger=ShinnyLoggerAdapter(self._logger.getChild("TsReconnect"), url=ts_url))
        self._ts_send_chan._logger_bind(chan_from="ts", url=ts_url)
        self._ts_recv_chan._logger_bind(chan_to="ts", url=ts_url)
        self._tasks.append(self._api.create_task(ts_reconnect._run(self._api, self._ts_send_chan, self._ts_recv_chan, ws_ts_send_chan, ws_ts_recv_chan), _caller_api=True))