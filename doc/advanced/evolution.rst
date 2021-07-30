使用逐步完善的方式构建交易策略
=================================================
`TqSdk`_ 的目标是能尽可能减少编码环节引入的坑，而交易逻辑本身的坑则需要用户自己填，如果每次调整交易逻辑都需要大规模的代码重构会严重阻碍交易系统的演化。

`TqSdk`_ 鼓励使用线性的编码风格，因此可以做到小调交易逻辑只需小改，只有大调交易逻辑时才需要大改。以 `R-Breaker`_ 策略为例，
第一版是留仓过夜，回测下来可能发现留仓过夜引入了很大的风险，却没有获得与风险对应的收益，因此修改交易策略，收盘前清仓离场，
对应代码的修改只需在主循环中加入判断是否接近收盘并平仓::

    if api.is_changing(quote, "datetime"):
        now = datetime.strptime(quote.datetime, "%Y-%m-%d %H:%M:%S.%f")
        if now.hour == close_hour and now.minute >= close_minute:  # 到达平仓时间: 平仓
            print("临近本交易日收盘: 平仓")
            target_pos.set_target_volume(0)  # 平仓
            deadline = time.time() + 60
            while api.wait_update(deadline=deadline):  # 等待60秒
                pass
            api.close()
            break

上述代码在行情时间变化时判断是否接近收盘，如果是的话则将目标持仓设为0(即空仓)。由于下单之后不一定能立即成交，价格变化后可能还需撤单重下，
因此等待一分钟后再退出，通常交易的合约不是太冷门的话一分钟应该足够了，如果不放心的话可以改为判断持仓手数是否为0。

更多的用例可以参见: https://doc.shinnytech.com/pysdk/latest/demo.html




.. _TqSdk: https://doc.shinnytech.com/pysdk/latest/index.html
.. _TqSim: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.sim.TqSim
.. _get_kline_serial: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.get_kline_serial
.. _TargetPosTask: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.lib.TargetPosTask
.. _wait_update: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.wait_update
.. _DIFF: https://doc.shinnytech.com/diff/latest/index.html
.. _get_account: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.get_account
.. _get_quote: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.get_quote
.. _is_changing: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.is_changing
.. _TqBacktest: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.backtest.TqBacktest
.. _R-Breaker: https://github.com/shinnytech/tqsdk-python/blob/master/tqsdk/demo/example/rbreaker.py
