#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'mayanqiong'

from tqsdk.exceptions import TqRiskRuleError


class TqRiskManager(list):

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
