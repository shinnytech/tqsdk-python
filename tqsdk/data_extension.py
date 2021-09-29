#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'


from tqsdk.datetime import _get_expire_rest_days
from tqsdk.datetime_state import TqDatetimeState
from tqsdk.diff import _simple_merge_diff, _is_key_exist, _simple_merge_diff_and_collect_paths, _get_obj


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
                },
                orders: {
                    *: {
                        'is_dead': bool
                        'is_online': bool
                        'is_error': bool
                        'trade_price': float
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
        self._diffs_paths = set()
        self._prototype = {
            "trade": {
                "*": {
                    "orders": {
                        "*": {
                            "status": None,
                            "exchange_order_id": None
                        }
                    },
                    "trades": {
                        "*": None
                    },
                    "positions": {
                        "*": {
                            "pos_long_his": None,
                            "pos_long_today": None,
                            "pos_short_his": None,
                            "pos_short_today": None
                        }
                    }
                }
            }
        }

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
                    if pack['aid'] == 'rtn_data':
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
        for d in pack.get("data", []):
            self._datetime_state.update_state(d)
            if d.get('trade', None):
                _simple_merge_diff_and_collect_paths(
                    result=self._data['trade'],
                    diff=d['trade'],
                    path=('trade', ),
                    diff_paths=self._diffs_paths,
                    prototype=self._prototype['trade']
                )
            self._diffs.append(d)

    def _generate_ext_diff(self):
        """"
        补充 quote, position 额外字段
        此函数在 send_diff() 才会调用， self._datetime_state.data_ready 一定为 True，
        调用 self._datetime_state.get_current_dt() 一定有正确的当前时间
        """
        for d in self._diffs:
            if d.get('quotes', None):
                self._update_quotes(d)
        pend_diff = {}
        _simple_merge_diff(pend_diff, self._get_positions_pend_diff(), reduce_diff=False)
        orders_set = set()  # 计算过委托单，is_dead、is_online、is_error
        orders_price_set = set()  # 根据成交计算哪些 order 需要重新计算平均成交价 trade_price
        for path in self._diffs_paths:
            if path[2] == 'orders':
                _, account_key, _, order_id, _ = path
                if (account_key, order_id) not in orders_set:
                    orders_set.add((account_key, order_id))
                    order = _get_obj(self._data, ['trade', account_key, 'orders', order_id])
                    if order:
                        pend_order = pend_diff.setdefault('trade', {}).setdefault(account_key, {}).setdefault('orders', {}).setdefault(order_id, {})
                        pend_order['is_dead'] = order['status'] == "FINISHED"
                        pend_order['is_online'] = order['exchange_order_id'] != "" and order['status'] == "ALIVE"
                        pend_order['is_error'] = order['exchange_order_id'] == "" and order['status'] == "FINISHED"
            elif path[2] == 'trades':
                _, account_key, _, trade_id = path
                trade = _get_obj(self._data, path)
                order_id = trade.get('order_id', '')
                if order_id:
                    orders_price_set.add(('trade', account_key, 'orders', order_id))
        for path in orders_price_set:
            _, account_key, _, order_id = path
            trade_price = self._get_trade_price(account_key, order_id)
            if trade_price == trade_price:
                pend_order = pend_diff.setdefault('trade', {}).setdefault(account_key, {}).setdefault('orders', {}).setdefault(order_id, {})
                pend_order['trade_price'] = trade_price
        self._diffs_paths = set()
        return pend_diff

    def _update_quotes(self, diff):
        for symbol in diff['quotes']:
            if not _is_key_exist(diff, path=['quotes', symbol], key=['expire_datetime']):
                continue
            expire_datetime = diff['quotes'][symbol]['expire_datetime']
            if expire_datetime and expire_datetime == expire_datetime:  # 排除 None 和 nan
                # expire_rest_days 距离到期日的剩余天数（自然日天数），正数表示距离到期日的剩余天数，0表示到期日当天，负数表示距离到期日已经过去的天数
                # 直接修改在 diff 里面的数据，当 diffs 里有多个对同个合约的修改时，保持数据截面的一致
                expire_rest_days = _get_expire_rest_days(expire_datetime, self._datetime_state.get_current_dt() / 1e9)
                diff['quotes'][symbol]['expire_rest_days'] = expire_rest_days

    def _get_positions_pend_diff(self):
        pend_diff = {}
        for account_key in self._data['trade']:
            positions = self._data['trade'][account_key].get('positions', {})
            for symbol, pos in positions.items():
                paths = [('trade', account_key, 'positions', symbol) + (key, )
                         for key in ['pos_long_his', 'pos_long_today', 'pos_short_his', 'pos_short_today']]
                if any([p in self._diffs_paths for p in paths]):
                    pos_long = pos['pos_long_his'] + pos['pos_long_today']
                    pos_short = pos['pos_short_his'] + pos['pos_short_today']
                    pend_diff.setdefault(account_key, {}).setdefault('positions', {})
                    pend_diff[account_key]['positions'][symbol] = {
                        'pos_long': pos_long,
                        'pos_short': pos_short,
                        'pos': pos_long - pos_short
                    }
        return {'trade': pend_diff} if pend_diff else {}

    def _get_trade_price(self, account_key, order_id):
        # 计算某个 order_id 对应的成交均价
        trades = self._data['trade'][account_key]['trades']
        trade_id_list = [t_id for t_id in trades.keys() if trades[t_id]['order_id'] == order_id]
        sum_volume = sum([trades[t_id]['volume'] for t_id in trade_id_list])
        if sum_volume == 0:
            return float('nan')
        else:
            sum_amount = sum([trades[t_id]['volume'] * trades[t_id]['price'] for t_id in trade_id_list])
            return sum_amount / sum_volume

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
