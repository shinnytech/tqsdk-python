#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'mayanqiong'

from tqsdk.datetime import _get_trading_day_from_timestamp, _get_trading_day_end_time
from tqsdk.datetime_state import TqDatetimeState
from tqsdk.exceptions import TqRiskRuleError


class TqRiskManager(list):

    def __init__(self):
        self._datetime_state = TqDatetimeState()
        self._trading_day_end = 0
        super(TqRiskManager, self).__init__()

    def _on_recv_data(self, diffs):
        for d in diffs:
            self._datetime_state.update_state(d)

        current = self._datetime_state.get_current_dt()
        if current > self._trading_day_end:
            # 切换交易日
            self._trading_day_end = _get_trading_day_end_time(_get_trading_day_from_timestamp(current))
            [r._on_settle() for r in self]

    def append(self, rule):
        if rule not in self:
            super(TqRiskManager, self).append(rule)

    def remove(self, rule):
        if rule in self:
            super(TqRiskManager, self).remove(rule)

    def _could_insert_order(self, pack):
        # 是否可以下单
        for r in self:
            is_valid, err_msg = r._could_insert_order(pack)
            if not is_valid:
                raise TqRiskRuleError(err_msg)
        return True

    def _on_insert_order(self, pack):
        # 需要更新风控对象内部统计值
        for r in self:
            r._on_insert_order(pack)
