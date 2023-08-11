.. _targetpostask2:

TargetPosTask 高级功能
====================================================

本篇文档假设您已经了解 :py:class:`~tqsdk.TargetPosTask` 的用法，文档参考 :ref:`targetpostask`。

本篇文档主要介绍 :py:class:`~tqsdk.TargetPosTask` 的高级用法。如何使用\
:py:meth:`~tqsdk.TargetPosTask.cancel` 和 :py:meth:`~tqsdk.TargetPosTask.is_finished` 方法。


应用情景说明
----------------------------------------------------

任何时刻，每个账户下一个合约只能有一个 :py:class:`~tqsdk.TargetPosTask` 实例，并且其构造参数不能修改。

但是在某些情况下，用户会希望可以管理 :py:class:`~tqsdk.TargetPosTask` 实例。

比如说，用户使用 :py:class:`~tqsdk.TargetPosTask` 的 **PASSIVE** 模式进行下单，希望在收盘前取消所有挂单（包含 :py:class:`~tqsdk.TargetPosTask` 实例的未成委托单），并平仓。

如何实现这样的功能
----------------------------------------------------

:py:class:`~tqsdk.TargetPosTask` 类提供了 :py:meth:`~tqsdk.TargetPosTask.cancel` 和 :py:meth:`~tqsdk.TargetPosTask.is_finished` 方法。

+ :py:meth:`~tqsdk.TargetPosTask.cancel` 方法会取消当前 :py:class:`~tqsdk.TargetPosTask` 实例，会将该实例已经发出但还未成交的委托单撤单此实例的 set_target_volume 函数不会再生效，并且此实例的 set_target_volume 函数不会再生效。
+ :py:meth:`~tqsdk.TargetPosTask.is_finished` 方法可以获取当前 :py:class:`~tqsdk.TargetPosTask` 实例是否已经结束。已经结束实例的 set_target_volume 函数不会再接受参数，此实例不会再下单或者撤单。

下面是一个例子::

    from datetime import datetime, time
    from tqsdk import TqApi, TargetPosTask

    api = TqApi(auth=TqAuth("快期账户", "账户密码"))
    quote = api.get_quote("SHFE.rb2110")
    target_pos_passive = TargetPosTask(api, "SHFE.rb2110", price="PASSIVE")

    while datetime.strptime(quote.datetime, "%Y-%m-%d %H:%M:%S.%f").time() < time(14, 50):
        api.wait_update()
        # ... 策略代码 ...

    # 取消 TargetPosTask 实例
    target_pos_passive.cancel()

    while not target_pos_passive.is_finished():  # 此循环等待 target_pos_passive 处理 cancel 结束
        api.wait_update()  # 调用wait_update()，会对已经发出但还是未成交的委托单撤单

    # 创建新的 TargetPosTask 实例
    target_pos_active = TargetPosTask(api, "SHFE.rb2110", price="ACTIVE")
    target_pos_active.set_target_volume(0)  # 平所有仓位

    while True:
        api.wait_update()
        # ... 策略代码 ...

    api.close()

