#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'


from tqsdk.datetime import _get_expire_rest_days
from tqsdk.datetime_state import TqDatetimeState
from tqsdk.diff import _simple_merge_diff


class DataExtension(object):
    """
    为数据截面添加以下字段：
    {
        quotes: {
            *: {
                expire_rest_days: int
            }
        },
        trade: {
            *: {
                positions: {
                    *: {
                        'pos_long': int,
                        'pos_short': int,
                        'pos': int
                    }
                }
            }
        }
    }
    """

    def __init__(self, api):
        self._api = api
        self._data = {'trade': {}}  # 数据截面, 现在的功能只需要记录 trade
        self._diffs = []

    async def _run(self, api_send_chan, api_recv_chan, md_send_chan, md_recv_chan):
        self._logger = self._api._logger.getChild("DataExtension")
        self._api_send_chan = api_send_chan
        self._api_recv_chan = api_recv_chan
        self._md_send_chan = md_send_chan
        self._md_recv_chan = md_recv_chan
        self._datetime_state = TqDatetimeState()
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
        """将行情数据和交易数据合并至 self._data """
        for d in pack.get("data", {}):
            self._datetime_state.update_state(d)
            if d.get('trade', None):
                _simple_merge_diff(self._data['trade'], d['trade'], reduce_diff=False)
            self._diffs.append(d)

    def _generate_ext_diff(self):
        """"
        补充 quote, position 额外字段
        此函数在 send_diff() 才会调用， self._datetime_state.data_ready 一定为 True，
        调用 self._datetime_state.get_current_dt() 一定有正确的当前时间
        """
        pend_diff = {}
        for d in self._diffs:
            if d.get('quotes', None):
                _simple_merge_diff(pend_diff, self._update_quotes(d), reduce_diff=False)
            if d.get('trade', None):
                _simple_merge_diff(pend_diff, self._update_positions(d), reduce_diff=False)
        return pend_diff

    def _update_quotes(self, diff):
        pend_diff = {}
        for symbol in diff['quotes']:
            expire_datetime = diff['quotes'].get(symbol, {}).get('expire_datetime', float('nan'))
            if expire_datetime == expire_datetime:
                # expire_rest_days 距离到期日的剩余天数（自然日天数）
                # 正数表示距离到期日的剩余天数，0表示到期日当天，负数表示距离到期日已经过去的天数
                expire_rest_days = _get_expire_rest_days(expire_datetime, self._datetime_state.get_current_dt() / 1e9)
                pend_diff[symbol] = {'expire_rest_days': expire_rest_days}
        return {'quotes': pend_diff} if pend_diff else {}

    def _update_positions(self, diff):
        pend_diff = {}
        for account_key in diff['trade']:
            for symbol in diff['trade'].get(account_key, {}).get('positions', {}):
                pos = diff['trade'][account_key]['positions'][symbol]
                if 'pos_long_his' in pos or 'pos_long_today' in pos or 'pos_short_his' in pos or 'pos_short_today' in pos:
                    data_pos = self._data['trade'][account_key]['positions'][symbol]
                    pos_long = data_pos['pos_long_his'] + data_pos['pos_long_today']
                    pos_short = data_pos['pos_short_his'] + data_pos['pos_short_today']
                    pend_diff.setdefault(account_key, {})
                    pend_diff[account_key].setdefault('positions', {})
                    pend_diff[account_key]['positions'][symbol] = {
                        'pos_long': pos_long,
                        'pos_short': pos_short,
                        'pos': pos_long - pos_short
                    }
        return {'trade': pend_diff} if pend_diff else {}

    async def _send_diff(self):
        if self._datetime_state.data_ready and self._pending_peek and self._diffs:
            # 生成增量业务截面, 该截面包含补充的字段，只在真正需要给下游发送数据时，才将需要发送的数据放在 _diffs 中
            ext_diff = self._generate_ext_diff()
            rtn_data = {
                "aid": "rtn_data",
                "data": self._diffs + [ext_diff],
            }
            self._diffs = []
            self._pending_peek = False
            await self._api_recv_chan.send(rtn_data)
