#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk import TqApi, TqSim, TargetPosTask

'''
价差回归
当近月-远月的价差大于200时做空近月，做多远月
当价差小于150时平仓
'''
api = TqApi(TqSim())
quote_near = api.get_quote("SHFE.rb1910")
quote_deferred = api.get_quote("SHFE.rb2001")
# 创建 rb1910 的目标持仓 task，该 task 负责调整 rb1910 的仓位到指定的目标仓位
target_pos_near = TargetPosTask(api, "SHFE.rb1910")
# 创建 rb2001 的目标持仓 task，该 task 负责调整 rb2001 的仓位到指定的目标仓位
target_pos_deferred = TargetPosTask(api, "SHFE.rb2001")

while True:
    api.wait_update()
    if api.is_changing(quote_near) or api.is_changing(quote_deferred):
        spread = quote_near["last_price"] - quote_deferred["last_price"]
        print("当前价差:", spread)
        if spread > 250:
            print("目标持仓: 空近月，多远月")
            # 设置目标持仓为正数表示多头，负数表示空头，0表示空仓
            target_pos_near.set_target_volume(-1)
            target_pos_deferred.set_target_volume(1)
        elif spread < 200:
            print("目标持仓: 空仓")
            target_pos_near.set_target_volume(0)
            target_pos_deferred.set_target_volume(0)
