.. _targetpostask:

交易辅助工具
====================================================

:py:class:`~tqsdk.TargetPosTask` 是按照目标持仓手数自动调整账户中某个合约净持仓的工具。如果你还没接触过这个模型，可以先阅读 :ref:`quickstart` 中“按照目标持仓自动交易”这一节。

使用示例如下::

    target_pos = TargetPosTask(api, "SHFE.rb1901")      #创建一个自动调仓工具, 负责调整SHFE.rb1901的持仓
    target_pos.set_target_volume(5)                     #要求自动调仓工具将持仓调整到5手
    do_something_else()                                 #现在你可以做别的事了, 自动调仓工具将会在后台自动下单/撤单/跟单, 直到持仓手数达到5手为止

下面是一个更实际的价差交易例子::

    from tqsdk import TqApi, TqAuth, TargetPosTask

    api = TqApi(auth=TqAuth("快期账户", "账户密码"))
    quote_near = api.get_quote("SHFE.rb1810")
    quote_deferred = api.get_quote("SHFE.rb1901")
    # 创建 rb1810 的目标持仓 task，该 task 负责调整 rb1810 的仓位到指定的目标仓位
    target_pos_near = TargetPosTask(api, "SHFE.rb1810")
    # 创建 rb1901 的目标持仓 task，该 task 负责调整 rb1901 的仓位到指定的目标仓位
    target_pos_deferred = TargetPosTask(api, "SHFE.rb1901")

    while True:
        api.wait_update()
        if api.is_changing(quote_near) or api.is_changing(quote_deferred):
            spread = quote_near.last_price - quote_deferred.last_price
            print("当前价差:", spread)
            if spread > 200:
                print("目标持仓: 空近月，多远月")
                # 设置目标持仓为正数表示多头，负数表示空头，0表示空仓
                target_pos_near.set_target_volume(-1)
                target_pos_deferred.set_target_volume(1)
            elif spread < 150:
                print("目标持仓: 空仓")
                target_pos_near.set_target_volume(0)
                target_pos_deferred.set_target_volume(0)


**使用 TargetPosTask 时，建议记住这几个要点：**

* ``set_target_volume()`` 只会更新目标仓位；实际的下单和撤单动作，会在之后每次 ``wait_update()`` 时执行。因此设置目标后，需要继续驱动主循环。
* 为每个合约只创建一个 :py:class:`~tqsdk.TargetPosTask` 实例。一旦创建完成，就可以重复调用 ``set_target_volume()`` 修改目标仓位，**它总是以最后一次设置的手数为工作目标。** 例如::

        from tqsdk import TqApi, TqAuth, TargetPosTask

        api = TqApi(auth=TqAuth("快期账户", "账户密码"))
        target_pos = TargetPosTask(api, "SHFE.rb2001")
        # 设定目标净持仓为空头1手
        target_pos.set_target_volume(-1)
        # 目标净持仓由空头1手改为多头1手
        target_pos.set_target_volume(1)

        while True:
            # 需在 set_target_volume 后调用 wait_update() 以发出指令
            # 当调整到目标净持仓后, 账户中此合约的净持仓为多头1手
            api.wait_update()

* TargetPosTask 在工作时，会负责下单、撤单和追单，直到净持仓达到目标为止。
* 在将净持仓调整到目标值后，账户里可能只保留单边持仓，也可能同时保留多头和空头两个方向的持仓。这通常发生在初始就持有双向持仓，或者在调整过程中由于 ``offset_priority`` 限制无法按预期平今/平昨。

    以当前持仓为 多头方向 且目标净持仓为0 为例, 对净持仓的调整逻辑为:
        * 如果 offset_priority 为默认值"今昨,开", 则: 先平多头今仓, (若平完今仓后未达到目标手数)再平多头昨仓, (若平完昨仓后未达到目标手数)再在空头方向开仓.
        * 如果 offset_priority 为"今开"(即禁止平昨仓), 则: 先平多头今仓, (若平完今仓后未达到目标手数)再在空头方向开仓. (禁止平今仓的"昨开"与此类似)
        * 如果 offset_priority 为"开"(即禁止平仓), 则: 直接在空头方向开仓以达到目标净持仓.

    **注意:**

    对于上期所和上海能源交易中心合约, 平仓时则直接根据今/昨的手数进行下单. 对于非上期所和能源交易中心: "今仓"和"昨仓" 是服务器按照今/昨仓的定义(本交易日开始时的持仓手数为昨仓, 之后下单的都为今仓)来计算的, 在平仓时, 则根据计算的今昨仓手数进行下单.

    如持有大商所某合约并且 offset_priority 为"今开", 而本交易日未下单(在今昨仓的概念上这是"昨仓", 则不进行平仓, 直接用开仓操作来调整净持仓以达到目标.
* 如需主动取消当前 TargetPosTask 任务，请参考 :ref:`targetpostask2` 。
* 请勿在使用 TargetPosTask 的同时混用 ``insert_order()``，否则容易导致 TargetPosTask 报错或出现错误下单。

最小开仓手数限制合约
----------------------------------------------------

默认情况下，``TargetPosTask`` 不支持交易所限制最小开仓手数的合约。若合约的
``open_min_market_order_volume`` 或 ``open_min_limit_order_volume`` 大于 1，
创建后的调仓任务会在后续 ``wait_update()`` 中抛出异常。

如果确认需要在这类合约上继续使用追单逻辑，可以在创建实例时设置
``support_open_min_volume=True`` 。启用后请注意：

* ``TargetPosTask`` 仍会根据行情变化撤单重报，但最终持仓只能保证满足
  ``|当前持仓手数 - 目标持仓手数| < quote.open_min_limit_order_volume``
* 当开仓追单剩余手数小于 ``quote.open_min_limit_order_volume`` 时，该次开仓追单会直接结束，不再继续报单
* 如果启用了大单拆分，``min_volume`` 和 ``max_volume`` 都必须大于等于 ``quote.open_min_limit_order_volume``
* 如果 ``offset_priority="开"`` 且本次需要开仓的总手数本身就小于 ``quote.open_min_limit_order_volume``，则不会发单，调仓任务会直接结束

示例::

    from tqsdk import TqApi, TqAuth, TargetPosTask

    api = TqApi(auth=TqAuth("快期账户", "账户密码"))
    quote = api.get_quote("GFEX.ps2704")
    target_pos = TargetPosTask(api, "GFEX.ps2704", support_open_min_volume=True)

    while True:
        api.wait_update()
        if quote.open_min_limit_order_volume > 1:
            print("最小限价开仓手数:", quote.open_min_limit_order_volume)



