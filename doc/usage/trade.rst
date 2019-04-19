.. _trade:

账户与交易
====================================================

设定交易账户
----------------------------------------------------
TqSdk 要求在创建 TqApi 时指定交易账户。一旦TqApi创建成功，后续所有通过TqApi发出的交易指令均在此账户中进行::

    api = TqApi(TqAccount("H海通期货", "320102", "123456"))

如果您需要使用模拟账户进行测试，我们提供无需注册的一次性模拟账户::

    api = TqApi(TqSim())

在配合天勤终端使用时，TqSdk 还支持在账号后附加交易单元标识，便于管理同一账号中的多个策略. 详见 :ref:`tq`


获取账户情况
----------------------------------------------------
TqApi 提供以下函数来获取交易账户相关信息:

* :py:meth:`tqsdk.api.TqApi.get_account` - 获取账户资金情况
* :py:meth:`tqsdk.api.TqApi.get_position` - 获取持仓情况
* :py:meth:`tqsdk.api.TqApi.get_order` - 获取委托单

以上函数返回的都是dict, 并会在 wait_update 时更新


交易指令
----------------------------------------------------
要在交易账户中发出一个委托单, 使用 :py:meth:`tqsdk.api.TqApi.insert_order` 函数::

    order = api.insert_order(symbol="SHFE.rb1901", direction="BUY", offset="OPEN", limit_price=4310, volume=2)
    print(order)

这个函数调用后会立即返回一个指向此委托单的引用对象, 它是一个dict, 内容如下::

    {
        "order_id": "",  # "123" (委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的)
        "exchange_order_id": "",  # "1928341" (交易所单号)
        "exchange_id": "",  # "SHFE" (交易所)
        "instrument_id": "",  # "rb1901" (交易所内的合约代码)
        "direction": "",  # "BUY" (下单方向, BUY=买, SELL=卖)
        "offset": "",  # "OPEN" (开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今)
        "volume_orign": 0,  # 10 (总报单手数)
        "volume_left": 0,  # 5 (未成交手数)
        "limit_price": float("nan"),  # 4500.0 (委托价格, 仅当 price_type = LIMIT 时有效)
        "price_type": "",  # "LIMIT" (价格类型, ANY=市价, LIMIT=限价)
        "volume_condition": "",  # "ANY" (手数条件, ANY=任何数量, MIN=最小数量, ALL=全部数量)
        "time_condition": "",  # "GFD" (时间条件, IOC=立即完成，否则撤销, GFS=本节有效, GFD=当日有效, GTC=撤销前有效, GFA=集合竞价有效)
        "insert_date_time": 0,  # 1501074872000000000 (下单时间(按北京时间)，自unix epoch(1970-01-01 00:00:00 GMT)以来的纳秒数)
        "status": "",  # "ALIVE" (委托单状态, ALIVE=有效, FINISHED=已完)
        "last_msg": "",  # "报单成功" (委托单状态信息)
    }

与其它所有数据一样, 委托单的信息也会在 api.wait_update() 时被自动更新::

    order = api.insert_order(symbol="SHFE.rb1901", direction="BUY", offset="OPEN", limit_price=4310,volume=2)
    while order["status"] != "FINISHED":
        api.wait_update()
        print("委托单状态: %s, 未成交手数: %d 手" % (order["status"], order["volume_left"]))

要撤销一个委托单, 使用 :py:meth:`tqsdk.api.TqApi.cancel_order` 函数::

    api.cancel_order(order)


交易辅助工具
----------------------------------------------------
除 insert_order 和 cancel_order 外, TqSdk 提供了一些更强的交易辅助工具. 使用这些工具, 可以简化交易逻辑的编码工作.

:py:class:`tqsdk.lib.TargetPosTask` 是按照目标持仓手数自动调仓的工具, 使用示例如下::

    target_pos = TargetPosTask(api, "SHFE.rb1901")      #创建一个自动调仓工具, 负责调整SHFE.rb1901的持仓
    target_pos.set_target_volume(5)                     #要求自动调仓工具将持仓调整到5手
    do_something_else()                                 #现在你可以做别的事了, 自动调仓工具将会在后台自动下单/撤单/跟单, 直到持仓手数达到5手为止

下面是一个更实际的价差交易例子::

    # 创建 rb1810 的目标持仓 task，该 task 负责调整 rb1810 的仓位到指定的目标仓位
    target_pos_near = TargetPosTask(api, "SHFE.rb1810")
    # 创建 rb1901 的目标持仓 task，该 task 负责调整 rb1901 的仓位到指定的目标仓位
    target_pos_deferred = TargetPosTask(api, "SHFE.rb1901")

    while True:
        api.wait_update()
        if api.is_changing(quote_near) or api.is_changing(quote_deferred):
            spread = quote_near["last_price"] - quote_deferred["last_price"]
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


使用 TargetPosTask 时, 需注意以下要点:

* 为每个合约只创建一个 TargetPosTask 实例. 一旦创建好后, 可以调用任意多次 set_target_volume 函数, 它总是以最后一次 set_target_volume 设定的手数为工作目标
* TargetPosTask 在工作时, 会负责下单和追单, 直至持仓手数达到目标为止
* TargetPosTask 在 set_target_volume 时并不下单或撤单. 它的下单和撤单动作, 是在之后的每次 wait_update 时执行的. 因此, 需保证 set_target_volume 后还会继续调用wait_update
* 不要试图在程序运行中销毁 TargetPosTask 实例.


:py:class:`tqsdk.lib.InsertOrderUntilAllTradedTask` 是追价下单task, 该task会在行情变化后自动撤单重下，直到全部成交
