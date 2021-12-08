#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'

from shinny_structlog import ShinnyLoggerAdapter

from tqsdk.baseModule import TqModule
from tqsdk.channel import TqChan
from tqsdk.connect import TqConnect, TsReconnectHandler

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
        await super(TqTradingStatus, self)._run(api, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan, self._ts_send_chan, self._ts_recv_chan)

    async def _handle_recv_data(self, pack, chan):
        """
        处理所有上游收到的数据包
        """
        if pack['aid'] == 'rtn_data':
            if chan == self._md_recv_chan:  # 从行情收到的数据包
                self._diffs.extend(pack.get('data', []))
            elif chan == self._ts_recv_chan:  # 从交易状态服务收到的数据包
                diffs = pack.get('data', [])
                for d in diffs:
                    for symbol, ts in d.get('trading_status', {}).items():
                        if ts['trade_status'] not in ["AUCTIONORDERING", "CONTINOUS"]:
                            ts['trade_status'] = "NOTRADING"
                self._diffs.extend(diffs)
        else:
            await self._api_recv_chan.send(pack)

    async def _handle_req_data(self, pack):
        """处理所有下游发送的非 peek_message 数据包"""
        if pack['aid'] == 'subscribe_trading_status':
            if self._init_ts_ws is False:
                self._init_ts_ws = True
                self._create_ts_run()
            await self._ts_send_chan.send(pack)
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
        self._api.create_task(conn._run(self._api, ts_url, ws_ts_send_chan, ws_ts_recv_chan), _caller_api=True)
        ts_reconnect = TsReconnectHandler(logger=ShinnyLoggerAdapter(self._logger.getChild("TsReconnect"), url=ts_url))
        self._ts_send_chan._logger_bind(chan_from="ts", url=ts_url)
        self._ts_recv_chan._logger_bind(chan_to="ts", url=ts_url)
        self._api.create_task(ts_reconnect._run(self._api, self._ts_send_chan, self._ts_recv_chan, ws_ts_send_chan, ws_ts_recv_chan), _caller_api=True)
