.. _why_tqsdk:

为何需要 TqSdk
====================================================
通常一个交易系统的演化流程如下图所示:

.. figure:: ../_static/trading_system.svg
    :width: 500px
    :figwidth: 80%
    :alt: trading system

整个流程可能会迭代多次，最初可能只是一个简单的想法，这时需要能快速实现一个原型，具体细节不需太在意，但是需要能尽快实现并付诸测试，
然后根据测试结果修改设计，调整代码，再重新测试，迭代多次后就从一个简单的想法逐步细化为一个完整的交易系统。

作为一套程序化交易框架，重点解决的是实现和测试这两个阶段，最好能直观的将交易逻辑转变为代码，能快速的检验交易逻辑，能尽可能少的修改代码以实现调整后的交易逻辑。
目前市面上现有的框架很少有能将这几点都做好的，因此才有了 `TqSdk`_，接下来介绍 `TqSdk`_ 是如何处理这几个问题的。


直观的将交易逻辑转变为代码
----------------------------------------------------
如果不能直观的编码交易逻辑，会导致写出来的代码很难说和预期的交易逻辑是等价的，代码中的bug不容易被发现，也不好修复，因为很难确认修改后的代码就能符合预期的交易逻辑，
`TqSdk`_ 没有使用目前市面上流行的回调框架(OnBar/OnTick/OnOrder...)就是为了能直观的体现交易逻辑，减少编码环节引入的坑。


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


快速的检验交易逻辑
----------------------------------------------------
使用 `TqSdk`_ 编写的策略，不需要修改策略代码，只需要调整创建 api 时填写的参数就可以进行历史回测或历史复盘。


历史回测
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
在创建 api 实例时传入 `TqBacktest`_ 策略就会进入历史回测模式::

    from datetime import date
    from tqsdk import TqApi, TqSim, TqBacktest

    api = TqApi(TqSim(), backtest=TqBacktest(start_dt=date(2018, 5, 1), end_dt=date(2018, 10, 1)))

`TqSdk`_ 会自动根据策略所用到的数据自动选择回测的行情采样频率，例如::

    klines = api.get_kline_serial("SHFE.rb1901", 60)

获取了 SHFE.rb1901 的分钟线，因此 SHFE.rb1901 的行情更新频率就是每分钟更新一次，如果使用::

    ticks = api.get_tick_serial("SHFE.rb1901")

获取了 tick 数据的话，行情就是逐 tick 更新的。另外回测框架的设计保证了从 api 取出的数据不会出现未来函数。

回测结束后会输出交易记录和每日收盘时的账户资金情况，以及最大回撤、夏普比率等指标，这些数据可以导入到 excel 中或使用其他分析工具进一步处理。


历史复盘
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
上面提到的回测解决的是用来评价一个策略整体是否有效，但在回测过程中可能还会遇到交易时点和预期的不符，或者极端行情下策略表现异常等问题。
这个时候可能需要看看当时的行情具体是怎么走的，策略具体是怎么执行的，或者在策略实现阶段需要在非交易时间调试，这时就可以使用由天勤终端提供的历史复盘功能。
只需指定任一交易日，天勤终端将回到那一天，并完整重演全天的行情变化。在此过程中，使用 `TqSdk`_ 对接到天勤终端之后获取的数据都是所指定日期的数据，
一切都有如真正回到那天一样。并可在回放过程中可以任意暂停或加减速。

首先打开天勤终端并进入复盘模式，然后在创建 api 实例时帐号填写为 "SIM" 策略就会进入历史复盘模式::

    api = TqApi("SIM")

之后策略的所有交易操作都可以在天勤终端中看到，并会标注到行情图上。同时也可以加减速或暂停行情回放，仔细分析策略执行情况。


尽可能少的修改代码以实现调整后的交易逻辑
----------------------------------------------------
`TqSdk`_ 的目标是能尽可能减少编码环节引入的坑，而交易逻辑本身的坑则需要用户自己填，如果每次调整交易逻辑都需要大规模的代码重构会严重阻碍交易系统的演化。

`TqSdk`_ 鼓励使用线性的编码风格，因此可以做到小调交易逻辑只需小改，只有大调交易逻辑时才需要大改。以 `R-Breaker`_ 策略为例，
第一版是留仓过夜，回测下来可能发现留仓过夜引入了很大的风险，却没有获得与风险对应的收益，因此修改交易策略，收盘前清仓离场，
对应代码的修改只需在主循环中加入判断是否接近收盘并平仓::

    if api.is_changing(quote, "datetime"):
        now = datetime.strptime(quote["datetime"], "%Y-%m-%d %H:%M:%S.%f")
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

更多的用例可以参见: http://doc.shinnytech.com/pysdk/latest/demo.html


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
