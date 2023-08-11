.. _targetpostask:

交易辅助工具
====================================================

:py:class:`~tqsdk.TargetPosTask` 是按照目标持仓手数自动调整 账户持仓中某合约的净持仓 的工具, 使用示例如下::

    target_pos = TargetPosTask(api, "SHFE.rb1901")      #创建一个自动调仓工具, 负责调整SHFE.rb1901的持仓
    target_pos.set_target_volume(5)                     #要求自动调仓工具将持仓调整到5手
    do_something_else()                                 #现在你可以做别的事了, 自动调仓工具将会在后台自动下单/撤单/跟单, 直到持仓手数达到5手为止

下面是一个更实际的价差交易例子::

    from tqsdk import TqApi, TqAuth, TargetPosTask

    api = TqApi(auth=TqAuth("快期账户", "账户密码"))
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


**使用 TargetPosTask 时, 需注意以下要点：**

* 1. TargetPosTask 在 set_target_volume 时并不下单或撤单, 它的下单和撤单动作, 是在之后的每次 wait_update 时执行的. 因此, **需保证 set_target_volume 后还会继续调用wait_update()**
* 2. 为每个合约只创建一个 TargetPosTask 实例. 一旦创建好后, 可以调用任意多次 set_target_volume 函数, **它总是以最后一次 set_target_volume 设定的手数为工作目标。** 如::

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

* 3. TargetPosTask 在工作时, 会负责下单和追单, 直至持仓手数达到目标为止.
* 4. 在将净持仓调整到目标值后, 可能只持有其中一个方向的手数, 也可能同时有多/空头两个方向的持仓(原因有两个: 初始就持有多/空两个方向, 调整持仓时未平完某一方向; 或在调整目标持仓时禁止"平今"或"平昨",然后以开仓操作来调整净持仓).

    以当前持仓为 多头方向 且目标净持仓为0 为例, 对净持仓的调整逻辑为:
        * 如果 offset_priority 为默认值"今昨,开", 则: 先平多头今仓, (若平完今仓后未达到目标手数)再平多头昨仓, (若平完昨仓后未达到目标手数)再在空头方向开仓.
        * 如果 offset_priority 为"今开"(即禁止平昨仓), 则: 先平多头今仓, (若平完今仓后未达到目标手数)再在空头方向开仓. (禁止平今仓的"昨开"与此类似)
        * 如果 offset_priority 为"开"(即禁止平仓), 则: 直接在空头方向开仓以达到目标净持仓.

    **注意:**

    对于上期所和上海能源交易中心合约, 平仓时则直接根据今/昨的手数进行下单. 对于非上期所和能源交易中心: "今仓"和"昨仓" 是服务器按照今/昨仓的定义(本交易日开始时的持仓手数为昨仓, 之后下单的都为今仓)来计算的, 在平仓时, 则根据计算的今昨仓手数进行下单.

    如持有大商所某合约并且 offset_priority 为"今开", 而本交易日未下单(在今昨仓的概念上这是"昨仓", 则不进行平仓, 直接用开仓操作来调整净持仓以达到目标.
* 5. 如需要取消当前 TargetPosTask 任务，请参考  :ref:`targetpostask2` 。
* 6. 请勿在使用 TargetPosTask 的同时使用 insert_order() 函数, 否则将导致 TargetPosTask 报错或错误下单。



:py:class:`~tqsdk.InsertOrderUntilAllTradedTask` 是追价下单task, 该task会在行情变化后自动撤单重下，直到全部成交.

