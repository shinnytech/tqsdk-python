#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'

import asyncio

from tqsdk.objs import Quote


class TqSymbols(object):
    """
    天勤合约服务类
    """

    async def _run(self, api, sim_send_chan, sim_recv_chan, md_send_chan, md_recv_chan):
        """回测task"""
        self._api = api
        self._sim_send_chan = sim_send_chan
        self._sim_recv_chan = sim_recv_chan
        self._md_send_chan = md_send_chan
        self._md_recv_chan = md_recv_chan
        self._etf_options = set()
        self._quotes_all_keys = set(Quote(None).keys())
        self._quotes_all_keys = self._quotes_all_keys.union({'margin', 'commission'})
        # 以下字段合约服务也会请求，但是不应该记在 quotes 中，quotes 中的这些字段应该有行情服务负责
        self._quotes_all_keys.difference_update({'pre_open_interest', 'pre_close', 'upper_limit', 'lower_limit'})
        sim_task = self._api.create_task(self._sim_handler())
        try:
            async for pack in self._md_recv_chan:
                if pack.get("aid") == "rtn_data":
                    data = pack.setdefault("data", [])
                    # 对于收到的数据，全部转发给下游
                    # 对于合约服务信息，query_id 为 PYSDK_quote_xxx 开头的，一定是请求了合约的全部合约信息，需要转为 quotes 转发给下游
                    updated_quotes = {}  # 合约服务内容转为的 quotes 对象
                    # 分两次循环，第一次循环找到所有的 SSE 期权，第二次循环将从行情收到的 SSE 期权的 pre_settlement 删掉
                    # 最终将 updated_quotes 发送给下游
                    for d in data:
                        for query_id, query_result in d.get("symbols", {}).items():
                            if query_result:
                                if query_result.get("error", None):
                                    raise Exception(f"查询合约服务报错 {query_result['error']}")
                                elif query_id.startswith("PYSDK_quote"):
                                    quotes = self._api._symbols_to_quotes(query_result, self._quotes_all_keys)
                                    for quote in quotes.values():
                                        if quote["ins_class"] == "OPTION" and quote["exchange_id"] in ["SSE", "SZSE"]:
                                            self._etf_options.add(quote["instrument_id"])
                                        else:
                                            # quotes 中的 pre_settlement 字段应该由行情服务负责，行情没有上交所期权的 pre_settlement，需要从合约服务取，其他合约不变
                                            quote.pop("pre_settlement", None)
                                    updated_quotes.update(quotes)
                                    self._md_send_chan.send_nowait({
                                        "aid": "ins_query",
                                        "query_id": query_id,
                                        "query": ""
                                    })
                    for d in data:
                        for symbol, quote in d.get("quotes", {}).items():
                            if symbol in self._etf_options:
                                quote.pop("pre_settlement", None)
                    data.append({"quotes": updated_quotes})
                await self._sim_recv_chan.send(pack)
        finally:
            sim_task.cancel()
            await asyncio.gather(sim_task, return_exceptions=True)

    async def _sim_handler(self):
        # 下游发来的数据包，直接转发到上游
        async for pack in self._sim_send_chan:
            await self._md_send_chan.send(pack)
