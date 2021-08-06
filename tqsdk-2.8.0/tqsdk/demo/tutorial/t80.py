#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk import TqApi, TqAuth, TargetPosTask

'''
价差回归
当近月-远月的价差大于250时做空近月，做多远月
当价差小于200时平仓
'''
api = TqApi(auth=TqAuth("信易账户", "账户密码"))
quote_near = api.get_quote("SHFE.rb2104")
quote_deferred = api.get_quote("SHFE.rb2105")
# 创建 rb2104 的目标持仓 task，该 task 负责调整 rb2104 的仓位到指定的目标仓位
target_pos_near = TargetPosTask(api, "SHFE.rb2104")
# 创建 rb2105 的目标持仓 task，该 task 负责调整 rb2105 的仓位到指定的目标仓位
target_pos_deferred = TargetPosTask(api, "SHFE.rb2105")

while True:
    api.wait_update()
    if api.is_changing(quote_near) or api.is_changing(quote_deferred):
        spread = quote_near.last_price - quote_deferred.last_price
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
