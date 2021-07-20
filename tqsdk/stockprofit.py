#!/usr/bin/env python
#  -*- coding: utf-8 -*-
import math
from tqsdk.entity import Entity
from tqsdk.diff import _simple_merge_diff, _get_obj


class TqStockProfit():
    """
    股票盈亏计算模块

    * 订阅已有持仓股票合约和行情
    * 计算股票持仓与资产的盈亏

    """
    def __init__(self, api):
        self._api = api
        self._data = Entity()  # 业务信息截面
        self._data._instance_entity([])
        self._diffs = []
        self._all_subscribe = set()


    async def _run(self, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan):

        self._logger = self._api._logger.getChild("TqStockProfit")
        self._api_send_chan = api_send_chan
        self._api_recv_chan = api_recv_chan
        self._md_send_chan = md_send_chan
        self._md_recv_chan = md_recv_chan
        md_task = self._api.create_task(self._md_handler())
        self._pending_peek = False
        try:
            async for pack in api_send_chan:
                if "_md_recv" in pack:
                    await self._md_recv(pack)
                    await self._send_diff()
                    if not self._is_diff_complete():
                        await self._md_send_chan.send({"aid": "peek_message"})
                elif pack["aid"] == "subscribe_quote":
                    await self._subscribe_quote(set(pack["ins_list"].split(",")))
                elif pack["aid"] == "peek_message":
                    self._pending_peek = True
                    await self._send_diff()
                    if self._pending_peek:
                        await self._md_send_chan.send(pack)
                else:
                    await self._md_send_chan.send(pack)
        finally:
            md_task.cancel()


    async def _md_handler(self):
        """0 接收上游数据包 """
        async for pack in self._md_recv_chan:
            pack["_md_recv"] = True
            await self._api_send_chan.send(pack)


    async def _md_recv(self, pack):
        """ 处理下行数据包
        0 将行情数据和交易数据合并至 self._data
        1 生成增量业务截面, 该截面包含 持仓盈亏和资产盈亏信息
        """
        for d in pack.get("data", {}):
            if "quotes" in d:
                # 行情数据仅仅合并沪深两市的行情数据
                stock_quote = {k: v for k, v in d.get('quotes').items() if k.startswith("SSE") or k.startswith("SZSE")}
                _simple_merge_diff(self._data, {"quotes": stock_quote})
            if "trade" in d:
                _simple_merge_diff(self._data, d)
            # 添加至 self._diff 等待被发送
            self._diffs.append(d)

        # 计算持仓和账户资产的盈亏增量截面
        pend_diff = await self._generate_pend_diff()
        self._diffs.append(pend_diff)


    async def _generate_pend_diff(self):
        """" 盈亏计算 """
        pend_diff = {}
        pend_diff.setdefault('trade', {k: {'accounts': {'CNY': {}}, 'positions': {}} for k in self._data.get('trade', {})})
        # 计算持仓盈亏
        for account_key in self._data.get('trade', {}):
            # 盈亏计算仅仅计算股票账户
            if self._data['trade'].get(account_key, {}).get("account_type", "FUTURE") == "FUTURE":
                continue
            for symbol, _ in self._data['trade'][account_key].get('positions', {}).items():
                await self._subscribe_quote(symbol)
                last_price = self._data["quotes"].get(symbol, {}).get('last_price', float("nan"))
                if not math.isnan(last_price):
                    diff = self._update_position(account_key, symbol, last_price)
                    pend_diff['trade'][account_key]['positions'][symbol] = diff
                    _simple_merge_diff(self._data["trade"][account_key]["positions"], {symbol: diff}, reduce_diff=False)

        # 当截面完整时, 全量刷新所有账户的资产盈亏
        if self._is_diff_complete():
            for account_key in self._data.get('trade', {}):
                if self._data['trade'].get(account_key, {}).get("account_type", "FUTURE") == "FUTURE":
                    continue
                all_position =self._data["trade"][account_key].get("positions", {})
                pend_diff['trade'][account_key]['accounts']['CNY']['float_profit'] = \
                    sum([v.get('float_profit', 0) for k, v in all_position.items()])

        return pend_diff

    async def _send_diff(self):
        if self._pending_peek and self._is_diff_complete() and self._diffs:
            rtn_data = {
                "aid": "rtn_data",
                "data": self._diffs,
            }
            self._diffs = []
            self._pending_peek = False
            await self._api_recv_chan.send(rtn_data)

    async def _subscribe_quote(self, symbols: [set, str]):
        """这里只会增加订阅合约，不会退订合约"""
        symbols = symbols if isinstance(symbols, set) else {symbols}
        if symbols - self._all_subscribe:
            self._all_subscribe |= symbols
            await self._md_send_chan.send({
                "aid": "subscribe_quote",
                "ins_list": ",".join(self._all_subscribe)
            })


    def _update_position(self, key, symbol, last_price):
        """更新持仓盈亏"""
        diff = {}
        position = self._data["trade"][key]["positions"][symbol]
        diff["last_price"] = last_price
        diff["cost"] = position['cost_price'] * position['volume']
        diff["float_profit"] = (last_price - position['cost_price']) * position['volume']
        return diff


    def _is_diff_complete(self):
        """当前账户截面是否已经完全处理完整, 即当所有股票的最新价不为空时"""
        for account_key in self._data.get('trade', {}):
            for symbol, _ in self._data['trade'][account_key].get('positions', {}).items():
                quote = self._data["quotes"].get(symbol, {})
                if math.isnan(quote.get('last_price', float("nan"))):
                    return False
        return True
