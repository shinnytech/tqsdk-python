#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试脚本：使用本地行情服务器进行回测
"""

import time
from datetime import date
import logging
# 必须导入 TargetPosTask
from tqsdk import TqApi, TqAuth, TqBacktest, TqSim, TargetPosTask 
from tqsdk.exceptions import BacktestFinished

LOCAL_INS_URL = "http://localhost:17788/symbols/latest.json"
LOCAL_MD_URL = "ws://localhost:17789"

logging.getLogger("TQSIM").setLevel(logging.WARNING)

def run_local_backtest():
    total_start = time.time()

    try:
        account=TqSim()
        api = TqApi(
            account=account,
            #backtest=TqBacktest(start_dt=date(2025, 1, 1), end_dt=date(2025, 1, 31)),
            backtest=TqBacktest(start_dt=date(2025, 1, 1), end_dt=date(2025, 12, 31)),
            auth=None,
            #auth=TqAuth("suolong33", "suolong33"),
            _ins_url=LOCAL_INS_URL,
            _md_url=LOCAL_MD_URL,
            disable_print=True,
        )
        #api = TqApi(
        #    account=TqSim(),
        #    backtest=TqBacktest(start_dt=date(2025, 3, 5), end_dt=date(2025, 3, 8)),
        #    auth=TqAuth("suolong33", "suolong33"),
        #    #_ins_url=LOCAL_INS_URL,
        #    #_md_url=LOCAL_MD_URL
        #)

        init_time = time.time() - total_start

        #symbol = "SHFE.rb2505"
        symbol1 = "KQ.m@SHFE.rb"
        symbol2 = "KQ.m@SHFE.au"
        
        # 尝试获取 K 线
        # 注意：在本地回测中，有时需要先 wait_update 一次让图表建立
        klines1 = api.get_kline_serial(symbol1, 60)
        klines2 = api.get_kline_serial(symbol2, 60)
        
        #if len(klines) > 0:
        #    print(klines.tail(3))

        target_pos1 = TargetPosTask(api, symbol1)
        target_pos2 = TargetPosTask(api, symbol2)
        
        loop_count = 0
        while True:
            api.wait_update()
            loop_count += 1
            
            # 简单的退出条件，防止死循环，实际由 BacktestFinished 异常退出
            #if loop_count > 100000: 
            #    break

            if api.is_changing(klines1):
                if len(klines1) >= 15:
                    last_close = klines1.close.iloc[-1]
                    ma = sum(klines1.close.iloc[-15:]) / 15
                    current_price = klines1.close.iloc[-1]
                    
                    # if loop_count % 500 == 0:
                    #     print(f"   ... 已处理 {loop_count} 次更新，最新价: {current_price}, MA: {ma:.2f}")
                    
                    if current_price > ma:
                        target_pos1.set_target_volume(5)
                    elif current_price < ma:
                        target_pos1.set_target_volume(0)

            if api.is_changing(klines2):
                if len(klines2) >= 15:
                    last_close = klines2.close.iloc[-1]
                    ma = sum(klines2.close.iloc[-15:]) / 15
                    current_price = klines2.close.iloc[-1]
                    
                    if current_price > ma:
                        target_pos2.set_target_volume(5)
                    elif current_price < ma:
                        target_pos2.set_target_volume(0)

    except BacktestFinished:
        total_time = time.time() - total_start
        print(f"\n✅ 回测正常结束!")
        print(f"")
        print(f"⏱️ 初始化时间: {init_time:.2f}s 回测时间: {total_time - init_time:.2f}s 总耗时: {total_time:.2f}s 循环次数: {loop_count}")
        # 打印最终账户情况
        print(api.get_account())

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            api.close()
        except:
            pass

if __name__ == "__main__":
    run_local_backtest()
