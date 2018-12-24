.. _framework:

TqSdk程序结构
====================================================

Api实例
----------------------------------------------------


业务逻辑
----------------------------------------------------
典型程序框架
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
以一个通常的策略流程为例：判断开仓条件，开仓，判断平仓条件，平仓，使用 `TqSdk`_ 写出的伪代码::

    from tqsdk import TqApi, TqSim, TargetPosTask

    api = TqApi(TqSim())
    klines = api.get_kline_serial("SHFE.rb1901", 60)
    target_pos = TargetPosTask(api, "SHFE.rb1901")

    while True:
        api.wait_update()
        if 开仓条件:
            target_pos.set_target_volume(1)
            break

    while True:
        api.wait_update()
        if 平仓条件:
            target_pos.set_target_volume(0)
            break

第一行代码::

    api = TqApi(TqSim())

是使用模拟交易(`TqSim`_)创建一个 api 实例，该实例负责和服务器通讯，获取行情数据，发送报单指令等等，`TqSdk`_ 的各个功能模块都是围绕该 api 实例运转的

第二行代码::

    klines = api.get_kline_serial("SHFE.rb1901", 60)

使用 `get_kline_serial`_ 获取 SHFE.rb1901 的分钟线数据

接下来::

    target_pos = TargetPosTask(api, "SHFE.rb1901")

这行代码是创建一个负责调整 SHFE.rb1901 的任务。考虑到实际的下单流程比较复杂，下单之后可能无法立即成交，需要撤单重下，还需处理部分成交的情况，
因此 `TqSdk`_ 提供了 `TargetPosTask`_ 用来调整持仓，使用时只需指定目标仓位，之后的下撤单都由 `TargetPosTask`_ 负责完成

之后就是判断开仓条件的主循环::

    while True:
        api.wait_update()
        if 开仓条件:
            target_pos.set_target_volume(1)
            break

`wait_update`_ 是等待业务数据更新。只要有任何业务数据变更(行情、账户资金、持仓、委托等)，`wait_update`_ 就会返回，接下来就是判断是否会触发开仓条件。
如果没有触发则继续等待下次业务数据更新后再判断；如果触发了，则通过 target_pos 将 SHFE.rb1901 的目标持仓设置为多头 1 手，
具体的调仓工作则由 target_pos 在后台完成，然后跳出开仓循环，进入下面的平仓循环::

    while True:
        api.wait_update()
        if 平仓条件:
            target_pos.set_target_volume(0)
            break

这段代码的结构和上面的开仓循环很相似，只是开仓条件换成了平仓条件，以及触发平仓条件后将 SHFE.rb1901 的目标持仓设置为 0 手(即空仓)

至此就完成一次完整的开平仓流程，如果平仓后还需再判断开仓条件可以把开仓循环和平仓循环再套到一个大循环中。


使用业务数据
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`TqSdk`_ 的另一个特点是使用了 `DIFF`_ 协议，所有业务数据都在内存中，并可随时使用，以获取账户资金为例::

    account = api.get_account()

`get_account`_ 只需调用一次，之后任何时刻都可以使用 account["balance"] 获得最新的账户权益。类似的 `get_quote`_ 返回行情报价，
`get_kline_serial`_ 返回K线数据等等。这些数据构成了业务信息截面，而业务截面的更新则是通过调用 `wait_update`_ 完成的，
当 `wait_update`_ 返回时业务截面即完成了从上一个时间截面推进到下一个时间截面。如果不调用 `wait_update`_ 则业务截面也不会更新，
因此在其他事情处理完后应第一时间调用 `wait_update`_。

这么做的好处是不需要策略手动保存感兴趣的业务数据。例如：策略希望在K线变化的时候使用盘口数据，如果使用 OnBar/OnTick 模型的话则需要策略在 OnTick
回调时手动保存 tick，然后在 OnBar 的时候再使用；另外用户无法控制 OnBar 和 OnTick 的回调顺序，因此可能出现没有触发 OnTick 就直接触发 OnBar，
导致访问不存在的 tick 数据。由于回调模型打乱了执行流程，因此这类问题并不是显而易见的，可能需要用户踩了坑之后才会意识到。

策略如果想知道 `wait_update`_ 到底更新了哪些业务数据可以调用 `is_changing`_ 函数判断感兴趣的业务对象是否有更新，例如::

    if api.is_changing(account):
        print("账户资金变化")

就会在任何账户资金信息变化的时候打出 "账户资金变化"。如果只关心其中某些账户信息，可以在调用 `is_changing`_ 时传入感兴趣的字段::

    if api.is_changing(account, "balance"):
        print("账户权益变化")

以上代码只会在账户权益发生变化的时候才会打出 "账户权益变化"。



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
.. _R-Breaker: https://github.com/shinnytech/tqsdk-python/blob/master/tqsdk/demo/rbreaker.py
