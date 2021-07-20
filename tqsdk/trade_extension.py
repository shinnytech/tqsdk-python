#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'


from tqsdk.datetime import _get_trading_day_end_time, _get_trading_day_from_timestamp, _get_expire_rest_days
from tqsdk.datetime_state import TqDatetimeState
from tqsdk.diff import _simple_merge_diff, _merge_diff
from tqsdk.entity import Entity
from tqsdk.utils import _query_for_quote


class CustomDict(Entity):
    """ Position / Order / Trade 对象 """

    def __init__(self, api, new_objs_list):
        self._api = api
        self._new_objs_list = new_objs_list

    def __setitem__(self, key, value):
        self._new_objs_list.append(value)
        return super(CustomDict, self).__setitem__(key, value)


class TradeExtension():
    """
    为持仓、委托单、成交对象添加 合约信息

    * 为期权合约相应的持仓、委托单、成交，添加以下字段
        + option_class 代表期权方向 CALL or PUT，非期权合约该处显示为NONE
        + underlying_symbol
        + strike_price
        + expire_rest_days 距离到期日剩余天数

    """

    def __init__(self, api):
        self._api = api
        self._data = Entity()  # 交易业务信息截面，需要定于数据原型，使用 Entity 类型 和 _merge_diff
        self._data._instance_entity([])
        self._new_objs_list = []
        self._prototype = {
            "trade": {
                "*": {
                    "@": CustomDict(self._api, self._new_objs_list)
                }
            }
        }
        self._data_quotes = {}  # 行情信息截面，只需要 quotes 数据。这里不需要定义数据原型，使用普通 dict 和 _simple_merge_diff
        self._diffs = []
        self._all_trade_symbols = set()  # 所有持仓、委托、成交中的合约
        self._query_symbols = set()  # 已经发送合约信息请求 + 已经知道合约信息的合约
        self._need_wait_symbol_info = set()  # 需要发送合约信息请求 + 不知道合约信息的合约

    async def _run(self, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan):
        self._logger = self._api._logger.getChild("TradeExtension")
        self._api_send_chan = api_send_chan
        self._api_recv_chan = api_recv_chan
        self._md_send_chan = md_send_chan
        self._md_recv_chan = md_recv_chan
        self._datetime_state = TqDatetimeState()
        self._trading_day_end = None
        md_task = self._api.create_task(self._md_handler())
        self._pending_peek = False  # True 表示收到下游的 peek_message ，并且没有发给过下游回复；False 表示发给过下游回复，没有 pending_peek_message
        self._pending_peek_md = False  # True 表示发给过上游 peek_message；False 表示对上游没有 pending_peek_message
        try:
            async for pack in api_send_chan:
                if "_md_recv" in pack:
                    self._pending_peek_md = False
                    await self._md_recv(pack)
                    await self._send_diff()
                    if self._pending_peek and self._pending_peek_md is False:
                        self._pending_peek_md = True
                        await self._md_send_chan.send({"aid": "peek_message"})
                elif pack["aid"] == "peek_message":
                    self._pending_peek = True
                    await self._send_diff()
                    if self._pending_peek and self._pending_peek_md is False:
                        self._pending_peek_md = True
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
        1 生成增量业务截面, 该截面包含期权补充的字段
        """
        for d in pack.get("data", {}):
            self._datetime_state.update_state(d)
            _simple_merge_diff(self._data_quotes, d.get('quotes', {}))
            _merge_diff(self._data, {"trade": d.get('trade', {})}, prototype=self._prototype, persist=False)
            self._diffs.append(d)  # 添加至 self._diff 等待被发送

        for obj in self._new_objs_list:
            # 新添加的 Position / Order / Trade  节点
            if hasattr(obj, '_path') and obj['_path'][2] in ['positions', 'trades', 'orders']:
                symbol = f"{obj.get('exchange_id', '')}.{obj.get('instrument_id', '')}"
                if symbol not in self._all_trade_symbols:
                    self._all_trade_symbols.add(symbol)
                    self._need_wait_symbol_info.add(symbol)  # 需要发送合约信息请求

        for s in self._need_wait_symbol_info.copy():
            if self._data_quotes.get(s, {}).get("price_tick", 0) > 0:
                self._need_wait_symbol_info.remove(s)  # 需要发送合约信息请求 + 不知道合约信息的合约

        # 不知道合约信息 并且未发送请求查询合约信息
        unknown_symbols = self._need_wait_symbol_info - self._query_symbols
        if len(unknown_symbols) > 0:
            self._query_symbols = self._query_symbols.union(unknown_symbols)  # 所有发送过ins_query的合约
            query_pack = _query_for_quote(list(unknown_symbols))
            await self._md_send_chan.send(query_pack)

    def _generate_pend_diff(self):
        """"
        补充期权额外字段
        此函数在 send_diff() 才会调用， self._datetime_state.data_ready 一定为 True，
        调用 self._datetime_state.get_current_dt() 一定有正确的当前时间
        """
        pend_diff = {}
        account_keys = list(self._data.get('trade', {}).keys())
        objs_keys = ['positions', 'trades', 'orders']

        # 如果有新添加的合约, 只填充一次即可
        if self._new_objs_list:
            pend_diff.setdefault('trade', {k: {o_k: {} for o_k in objs_keys} for k in account_keys})
            for obj in self._new_objs_list:
                # 新添加的 Position / Order / Trade  节点
                if hasattr(obj, '_path') and obj['_path'][2] in objs_keys:
                    account_key = obj['_path'][1]
                    obj_key = obj['_path'][2]
                    item_id = obj['_path'][3]
                    quote = self._data_quotes.get(f"{obj.get('exchange_id', '')}.{obj.get('instrument_id', '')}", {})
                    if quote.get('ins_class', '').endswith('OPTION'):
                        pend_diff_item = pend_diff['trade'][account_key][obj_key].setdefault(item_id, {})
                        pend_diff_item['option_class'] = quote.get('option_class')
                        pend_diff_item['strike_price'] = quote.get('strike_price')
                        pend_diff_item['underlying_symbol'] = quote.get('underlying_symbol')
                        if quote.get('expire_datetime'):
                            pend_diff_item['expire_rest_days'] = _get_expire_rest_days(quote.get('expire_datetime'),
                                                                                       self._datetime_state.get_current_dt() / 1e9)
            self._new_objs_list.clear()

        # 如果有切换交易日，所有合约都需要修改 expire_rest_days
        current_dt = self._datetime_state.get_current_dt()
        if self._trading_day_end is None or current_dt > self._trading_day_end:
            pend_diff.setdefault('trade', {k: {o_k: {} for o_k in objs_keys} for k in account_keys})
            for account_key, account_node in self._data.get('trade', {}).items():
                for k in objs_keys:
                    for item_id, item in account_node.get(k, {}).items():
                        quote = self._data_quotes.get(f"{item['exchange_id']}.{item['instrument_id']}", {})
                        if quote.get('ins_class', '').endswith('OPTION') and quote.get('expire_datetime'):
                            pend_diff_item = pend_diff['trade'][account_key][k].setdefault(item_id, {})
                            # 剩余到期日字段，每天都会更新，每次都重新计算
                            pend_diff_item['expire_rest_days'] = _get_expire_rest_days(quote.get('expire_datetime'),
                                                                                       current_dt / 1e9)
            self._trading_day_end = _get_trading_day_end_time(_get_trading_day_from_timestamp(current_dt))
        return pend_diff

    async def _send_diff(self):
        if self._datetime_state.data_ready and self._pending_peek and self._diffs and len(self._need_wait_symbol_info) == 0:
            # 生成增量业务截面, 该截面包含期权补充的字段，只在真正需要给下游发送数据时，才将需要发送的数据放在 _diffs 中
            pend_diff = self._generate_pend_diff()
            self._diffs.append(pend_diff)
            rtn_data = {
                "aid": "rtn_data",
                "data": self._diffs,
            }
            self._diffs = []
            self._pending_peek = False
            await self._api_recv_chan.send(rtn_data)
