介绍
=================================================

TqSdk是什么
-------------------------------------------------
TqSdk 是一套开源 python 框架. 依托Diff项目高度优化设计的 websocket/json 接口和服务器体系, TqSdk 支持用户使用较少的工作量构建量化交易或分析程序.

与其它 python 框架相比, TqSdk 致力于在以下几方面为用户提供价值:


1. 立即获得从行情到交易的完整功能

* 一分钟内 :ref:`完成安装 <install>`.
* 全部合约自上市起的 :ref:`Tick和K线数据 <quickstart_2>`，支持从1秒到1天的自定义K线周期
* 支持 模拟交易 和 :ref:`实盘交易 <faq-real>`
* 执行 :ref:`Tick或K线回测 <backtest>` ，支持多合约策略回测

2. 鼓励 Quick & Simple 的用户代码风格

* 用 :ref:`20行左右代码 <quickstart_5>` 完成一个完整的交易策略程序
* 所有行情及交易接口都返回 object refrence, 一次调用获取, 内容可自动更新, 无需查询
* 策略代码按 :ref:`线性逻辑 <linear_framework>` 编写, 避免复杂的回调函数/状态机

3. 搭配天勤终端获得更多功能

* 策略单元支持. 在一个账户下运行多个策略时, 可以实现仓位, 报单的相互隔离.
* 策略运行监控, 提供委托单/成交/持仓情况监控的UI界面, 手工下单干预
* 通过 `历史复盘 <https://doc.shinnytech.com/tq/latest/mdreplay.html>`_ 功能，在特定的历史场景测试您的程序，7*24小时可用


.. _linear_framework:

线性逻辑框架
----------------------------------------------------
如果不能直观的编码交易逻辑，会导致写出来的代码很难说和预期的交易逻辑是等价的，代码中的bug不容易被发现，也不好修复，因为很难确认修改后的代码就能符合预期的交易逻辑，
TqSdk 没有使用目前市面上流行的回调框架(OnBar/OnTick/OnOrder...)就是为了能直观的体现交易逻辑，减少编码环节引入的坑。

以一个通常的策略流程为例：判断开仓条件，开仓，判断平仓条件，平仓，使用 TqSdk 写出的伪代码::

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


全数据自动更新
----------------------------------------------------
TqSdk 的另一个特点是使用了 `DIFF`_ 协议，所有业务数据都在内存中，并可随时使用，以获取账户资金为例::

    account = api.get_account()
    print(account["balance"])

:py:meth:`~tqsdk.api.TqApi.get_account` 只需调用一次，之后任何时刻都可以使用 account["balance"] 获得最新的账户权益。类似的 :py:meth:`~tqsdk.api.TqApi.get_quote` 返回行情报价，
:py:meth:`~tqsdk.api.TqApi.get_kline_serial` 返回K线数据等等。这些数据构成了业务信息截面，而业务截面的更新则是通过调用 :py:meth:`~tqsdk.api.TqApi.wait_update` 完成的，
当 :py:meth:`~tqsdk.api.TqApi.wait_update` 返回时业务截面即完成了从上一个时间截面推进到下一个时间截面。如果不调用 :py:meth:`~tqsdk.api.TqApi.wait_update` 则业务截面也不会更新，
因此在其他事情处理完后应第一时间调用 :py:meth:`~tqsdk.api.TqApi.wait_update`。

这么做的好处是不需要策略手动保存感兴趣的业务数据。例如：策略希望在K线变化的时候使用盘口数据，如果使用 OnBar/OnTick 模型的话则需要策略在 OnTick
回调时手动保存 tick，然后在 OnBar 的时候再使用；另外用户无法控制 OnBar 和 OnTick 的回调顺序，因此可能出现没有触发 OnTick 就直接触发 OnBar，
导致访问不存在的 tick 数据。由于回调模型打乱了执行流程，因此这类问题并不是显而易见的，可能需要用户踩了坑之后才会意识到。

策略如果想知道 :py:meth:`~tqsdk.api.TqApi.wait_update` 到底更新了哪些业务数据可以调用 :py:meth:`~tqsdk.api.TqApi.is_changing` 函数判断感兴趣的业务对象是否有更新，例如::

    if api.is_changing(account):
        print("账户资金变化")

就会在任何账户资金信息变化的时候打出 "账户资金变化"。如果只关心其中某些账户信息，可以在调用 :py:meth:`~tqsdk.api.TqApi.is_changing` 时传入感兴趣的字段::

    if api.is_changing(account, "balance"):
        print("账户权益变化")

以上代码只会在账户权益发生变化的时候才会打出 "账户权益变化"。


License
-------------------------------------------------
TqSdk 在 Apache License 2.0 协议下提供, 使用者可在遵循此协议的前提下自由使用本软件.


.. _DIFF: https://doc.shinnytech.com/diff/latest/index.html

