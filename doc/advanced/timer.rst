.. _timer:

定时器
=================================================

在 TqSdk 里，定时逻辑通常不是单独开一个 ``sleep`` 循环，而是和 :py:meth:`~tqsdk.TqApi.wait_update` 结合在同一个主循环里执行。这样可以保证订阅、下单、撤单以及后台任务仍然持续被驱动。

优先使用“行情时间”而不是本机时间
-------------------------------------------------

如果你的逻辑和交易时段、收盘前平仓、定时检查等场景有关，优先使用 ``quote.datetime`` 代表的行情时间::

    from datetime import datetime
    from tqsdk import TqApi, TqAuth, TargetPosTask

    api = TqApi(auth=TqAuth("快期账户", "账户密码"))
    quote = api.get_quote("SHFE.rb2405")
    target_pos = TargetPosTask(api, "SHFE.rb2405")
    close_hour, close_minute = 14, 50

    while True:
        api.wait_update()
        if api.is_changing(quote, "datetime"):
            now_time = datetime.strptime(quote.datetime, "%Y-%m-%d %H:%M:%S.%f")
            if now_time.hour == close_hour and now_time.minute >= close_minute:
                print("临近收盘，平仓")
                target_pos.set_target_volume(0)
                break

这种方式的好处是：你的定时判断和交易所时间保持一致，不依赖本机时钟是否漂移。

用 deadline 做“等待一段时间后继续”
-------------------------------------------------

:py:meth:`~tqsdk.TqApi.wait_update` 提供了 ``deadline`` 参数。它接收的是 ``time.time()`` 风格的 unix 时间戳，适合做“最多再等多久”的控制::

    import time
    from tqsdk import TqApi, TqAuth

    api = TqApi(auth=TqAuth("快期账户", "账户密码"))
    quote = api.get_quote("SHFE.rb2405")

    while True:
        api.wait_update()
        if api.is_changing(quote, "datetime"):
            print("收到一次关键更新，接下来最多再等 60 秒")
            deadline = time.time() + 60
            while api.wait_update(deadline=deadline):
                pass
            print("等待结束，继续执行后续逻辑")

这类写法适合：

* 收盘前平仓后再等待一小段时间，确认撤单和回报处理完毕
* 给某个阶段性任务一个最长等待时间，避免长时间阻塞
* 在同步主循环里做简单的“超时退出”控制

常见误区
-------------------------------------------------

* 不要在主循环里频繁使用 ``time.sleep()``, 否则会阻塞 ``wait_update``，数据和后台任务都会停下来
* ``deadline`` 是 unix 时间戳，不是“秒数”本身；通常写成 ``time.time() + 60``
* 如果你在定时逻辑里调用了 ``insert_order`` 或 ``TargetPosTask.set_target_volume``，后面仍然要继续调用 ``wait_update``，否则报单不会真正发出
* 如果策略已经采用协程任务，优先考虑 :py:meth:`~tqsdk.TqApi.register_update_notify`，不要把同步和异步等待方式混在一起

