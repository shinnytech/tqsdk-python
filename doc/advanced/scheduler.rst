.. _target_pos_scheduler:

基于时间维度目标持仓策略
=================================================

本篇文档假设您已经了解 :py:class:`~tqsdk.TargetPosTask` 的用法，文档参考 :ref:`targetpostask`。

简单来说，:py:class:`~tqsdk.TargetPosTask` 会创建 task，负责将指定合约调整到目标头寸（默认为账户的该合约净持仓）。

对于简单的大单拆分功能，可以在 :py:class:`~tqsdk.TargetPosTask` 类中设置拆分手数的上下限，:py:class:`~tqsdk.TargetPosTask` 实例在下单过程中就会将下单手数随机的拆分，以减少对市场冲击。

但是，对于比较复杂的下单策略，例如 twap（基于时间拆分手数），vwap（基于成交量拆分手数）等，使用 :py:class:`~tqsdk.TargetPosTask` 来构造策略不是很方便。

我们提供 :py:class:`~tqsdk.TargetPosScheduler` 类帮助用户完成复杂的下单策略，同时提供给用户极大的调整空间。


time_table 目标持仓任务列表
------------------------------------------------------------------

:py:class:`~tqsdk.TargetPosScheduler` 使用 ``time_table`` 参数来描述具体的下单策略。

``time_table`` 为 ``pandas.DataFrame`` 类型。每一行表示一项目标持仓任务，每项任务按照顺序一个个执行。其应该包含以下几列：

+ interval: 当前这项任务的持续时间长度，单位为秒，经过这么多秒之后，此项任务应该退出，剩余未调整到的目标持仓，会留到下一项任务中
    * 注意1：对于最后一项任务，会按照当前项参数，调整到目标持仓后立即退出（时间参数不对最后一项任务起作用）
    * 注意2：时间长度可以跨非交易时间段（可以跨小节等待），但是不可以跨交易日
+ target_pos: 当前这项任务的目标净持仓手数
+ price: 当前这项任务的下单价格模式，此列中非 None 的项，会作为创建 TargetPosTask 实例的 price 参数，支持以下几种参数：
    * None: 不下单，表示暂停一段时间
    * "PASSIVE" : 排队价下单
    * "ACTIVE": 对价下单
    * Callable (direction: str) -> Union[float, int]: 传入函数作为价格参数，函数参数为下单方向，函数返回值是下单价格。如果返回 nan，程序会抛错。



TargetPosScheduler 执行目标持仓任务列表
------------------------------------------------------------------

:py:class:`~tqsdk.TargetPosScheduler` 类创建 target_pos_scheduler 实例，首先会将 ``time_table`` 中 ``interval`` 间隔时间列转为 ``deadline``，即这项任务结束时间的纳秒数。

然后，依次为 ``time_table`` 中的每一项任务创建 :py:class:`~tqsdk.TargetPosTask` 实例，调整目标持仓，并在到达 ``deadline`` 时退出。每一项未完成的目标持仓都会留都下一项任务中。

需要注意的是，最后一项任务，是以手数达到目标的，会按照当前项参数，调整到目标持仓再退出。如果最后一项 ``price`` 参数为 ``None`` （表示不下单），由于无法调整持仓，那么会立即退出。


简单示例
------------------------------------------------------------------

简单示例及说明如下::

    time_table = DataFrame([
        [25, 10, "PASSIVE"]
        [5, 10, "ACTIVE"]
        [30, 18, "PASSIVE"]
        [5, 18, "ACTIVE"]
    ], columns=['interval', 'target_pos', 'price'])

    target_pos_scheduler = TargetPosScheduler(api, "SHFE.cu2112", time_table)

    # 这个 time_table 表示的下单策略依次是：
    # 1. 使用排队价下单，调整 "SHFE.cu2112" 到 10 手，到达 25s 时退出（无论目标手数是否达到，都不会继续下单）
    # 2. 使用对价下单，调整 "SHFE.cu2112" 到 10 手，到达 5s 时退出
    #    如果上一步结束时目标持仓已经达到 10 手，这一步什么都不会做，等待 5s 到下一步；
    #    如果上一步结束时目标持仓没有达到 10 手，这一步会继续调整目标持仓到 10 手
    # 3. 使用排队价下单，调整 "SHFE.cu2112" 到 18 手，到达 30s 时退出（无论目标手数是否达到，都不会继续下单）
    # 4. 使用对价下单，调整 "SHFE.cu2112" 到 18 手
    #    如果上一步结束时目标持仓已经达到 18 手，这一步什么都不会做，立即退出；
    #    如果上一步结束时目标持仓没有达到 18 手，这一步会继续调整目标持仓到 18 手后退出


到此为止，您可以根据您的具体策略构造出任意的 ``time_table`` 对象，然后调用 :py:class:`~tqsdk.TargetPosScheduler` 来执行。

为了方便用户使用，我们提供了 :py:meth:`~tqsdk.algorithm.time_table_generater.twap_table` 来生成一个默认的符合 twap 策略的 ``time_table`` 实例。


基于 TargetPosScheduler 的 twap 策略示例
------------------------------------------------------------------

我们在 :ref:`tqsdk.algorithm` 模块中提供了 :py:meth:`~tqsdk.algorithm.time_table_generater.twap_table`，可方便的生成一个基于 twap 策略的 ``time_table`` 实例。

在执行算法之前，您还可以定制化的调整 ``time_table`` 中的具体任务项。

一个完整的 twap 策略示例::

    from tqsdk import TqApi, TargetPosScheduler
    from tqsdk.algorithm import twap_table

    api = TqApi(auth="快期账户,用户密码")
    quote = api.get_quote("CZCE.MA109")

    # 设置 twap 任务参数，
    time_table = twap_table(api, "CZCE.MA105", -100, 600, 1, 5)  # 目标持仓 -100 手，600s 内完成

    # 定制化调整 time_table，例如希望第一项任务延迟 10s 再开始下单
    # 可以在 time_table 的头部加一行
    time_table = pandas.concat([
        DataFrame([[10, 10, None]], columns=['interval', 'target_pos', 'price']),
        time_table
    ], ignore_index=True)

    target_pos_sch = TargetPosScheduler(api, "CZCE.MA105", time_table)
    while not target_pos_sch.is_finished():
        api.wait_update()

    # 获取 target_pos_sch 实例所有的成交列表
    print(target_pos_sch.trades_df)

    # 利用成交列表，您可以计算出策略的各种表现指标，例如：
    average_trade_price = sum(scheduler.trades_df['price'] * scheduler.trades_df['volume']) / sum(scheduler.trades_df['volume'])
    print("成交均价:", average_trade_price)
    api.close()
