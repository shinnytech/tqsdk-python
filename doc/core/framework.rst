.. _framework:

TqSdk程序结构
====================================================

TqApi
----------------------------------------------------
`TqApi`_ 是 `TqSdk`_ 的核心类. 通常情况下, 每个使用了 `TqSdk`_ 的程序都应该包括一个 `TqApi`_ 实例::

    api = TqApi(TqSim())

`TqApi`_ 实例负责:

* 建立websocket连接到服务器(或天勤终端).
* 在内存中建立数据存储区, 接收行情和交易业务数据包, 并自动维护数据更新.
* 发出交易指令.
* 管理协程任务.
* 执行策略回测.

`TqApi`_ 创建时, 必须提供一个account参数. 它可以是:

* 一个 `TqAccount`_ 实例: 使用实盘帐号, 直连行情和交易服务器(不通过天勤终端), 需提供期货公司/帐号/密码
* 一个 `TqSim`_ 实例: 使用 Api 自带的模拟功能, 直连行情服务器或连接天勤终端(例如使用历史复盘进行测试)接收行情数据
* 一个字符串: 连接天勤终端, 实盘交易填写期货公司提供的帐号, 使用天勤终端内置的模拟交易填写"SIM", 需先在天勤终端内登录交易

`TqApi`_ 的其它参数请见这里(https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi)


动态数据引用与数据更新
----------------------------------------------------
`TqApi`_ 实例内存中保存了一份完整业务数据截面, 包括行情/K线和交易账户数据. 这些数据可以通过 `TqApi`_ 提供的数据引用函数获取，以获取资金账户为例::

    account = api.get_account()

值得注意的是, `get_account`_ 返回资金账户的一个动态引用, 而不是具体的数值.
因此只需调用一次 `get_account`_ 得到 account 引用，之后任何时刻都可以使用 account["balance"] 获得最新的账户权益.

`TqApi`_ 提供的数据引用函数还包括:

* `get_quote`_ (获取指定合约的盘口行情引用)
* `get_kline_serial`_ (获取k线序列数据引用)
* `get_tick_serial`_ (获取tick序列数据引用)
* `get_account`_ (获取用户账户资金信息引用)
* `get_position`_ (获取用户持仓信息引用)
* `get_order`_ (获取用户委托单信息引用)


`TqApi`_ 实例内存中的数据更新是通过调用 `wait_update`_ 完成的.
`TqApi`_ 每次调用 `wait_update`_ 时, 会尝试从服务器接收一个数据包, 并用收到的数据包更新内存中的业务数据截面.
当 `wait_update`_ 函数返回时业务截面即完成了从上一个时间截面推进到下一个时间截面。

注意: 如果不调用 `wait_update`_, 内存中的所有数据都不会更新. 所以程序中一般会将 `wait_update`_ 放在一个循环中反复调用::

    while True:             #一个循环
        api.wait_update()   #总是调用 wait_update, 当数据有更新时 wait_update 函数返回, 执行下一句
        do_some_thing()     #每当数据有变更时, 执行自己的代码, 然后循环回去再做下一次 wait_update

`wait_update`_ 会在任何数据更新时返回. 如果想知道 `wait_update`_ 到底更新了哪些业务数据可以调用 `is_changing`_ 函数判断感兴趣的业务对象是否有更新，例如::

    if api.is_changing(account):
        print("资金账户变化")                    #任何资金账户中任意信息变化的时候打出 "资金账户变化"

    if api.is_changing(account, "balance"):
        print("账户权益变化")                    #只有资金账户中的权益值变化的时候打出 "账户权益变化"


交易指令
----------------------------------------------------
要在交易账户中发出一个委托单, 使用 `insert_order`_ 函数::

    order = api.insert_order(symbol="DCE.m1901", direction="BUY", offset="OPEN", volume=5)

这个函数调用后会立即返回一个指向此委托单的引用对象, 与其它所有数据一样, 委托单的信息也会在 `wait_update`_ 时被自动更新.

你总是可以通过 order 的成员变量来了解委托单的最新状态::

    print("委托单状态: %s, 未成交手数: %d 手" % (order["status"], order["volume_left"]))

要撤销一个委托单, 使用 `cancel_order`_ 函数::

    api.cancel_order(order)

交易指令的完整说明请见 `insert_order`_ 和 `cancel_order`_


自动工具
----------------------------------------------------
TqSdk 使用协程方式支持用户在自己的代码之外执行一些后台任务. 以自动调仓工具 `TargetPosTask`_ 为例::

    target_pos = TargetPosTask(api, "SHFE.rb1901")      #创建一个自动调仓工具, 负责调整SHFE.rb1901的持仓
    target_pos.set_target_volume(5)                     #要求自动调仓工具将持仓调整到5手
    do_something_else()                                 #现在你可以做别的事了, 自动调仓工具将会在后台自动下单/撤单/跟单, 直到持仓手数达到5手为止

其它的一些自动工具包括:

* `TargetPosTask`_ : 目标持仓 task, 该 task 可以将指定合约调整到目标头寸
* `InsertOrderUntilAllTradedTask`_ : 追价下单task, 该task会在行情变化后自动撤单重下，直到全部成交


一个典型程序的结构
----------------------------------------------------
以一个通常的策略流程为例：判断开仓条件，开仓，判断平仓条件，平仓，使用 `TqSdk`_ 写出的代码::

    from tqsdk import TqApi, TqSim, TargetPosTask

    api = TqApi(TqSim())
    klines = api.get_kline_serial("SHFE.rb1901", 60)
    target_pos = TargetPosTask(api, "SHFE.rb1901")

    while True:                                                 #判断开仓条件的主循环
        api.wait_update()                                       #等待业务数据更新
        if 开仓条件:
            target_pos.set_target_volume(1)                     #如果触发了，则通过 target_pos 将 SHFE.rb1901 的目标持仓设置为多头 1 手，具体的调仓工作则由 target_pos 在后台完成
            break                                               #跳出开仓循环，进入下面的平仓循环

    while True:                                                 #判断平仓条件的主循环
        api.wait_update()
        if 平仓条件:
            target_pos.set_target_volume(0)                     ##如果触发了，则通过 target_pos 将 SHFE.rb1901 的目标持仓设置为0手(即空仓)
            break

    #至此就完成一次完整的开平仓流程，如果平仓后还需再判断开仓条件可以把开仓循环和平仓循环再套到一个大循环中。




.. _TqSdk: https://doc.shinnytech.com/pysdk/latest/index.html
.. _TqApi: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi
.. _TqAccount: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqAccount
.. _TqSim: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.sim.TqSim
.. _TqBacktest: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.backtest.TqBacktest

.. _wait_update: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.wait_update
.. _is_changing: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.is_changing
.. _get_quote: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.get_quote
.. _get_kline_serial: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.get_kline_serial
.. _get_tick_serial: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.get_tick_serial
.. _get_account: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.get_account
.. _get_position: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.get_position
.. _get_order: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.get_order
.. _insert_order: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.insert_order
.. _cancel_order: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.api.TqApi.cancel_order

.. _TargetPosTask: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.lib.TargetPosTask
.. _InsertOrderUntilAllTradedTask: https://doc.shinnytech.com/pysdk/latest/reference.html#tqsdk.lib.InsertOrderUntilAllTradedTask

.. _DIFF: https://doc.shinnytech.com/diff/latest/index.html
