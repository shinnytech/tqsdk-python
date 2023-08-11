.. _multi_instance:

交易策略的多实例运行
=================================================
我们可能会将一个策略应用于不同的目标品种, 不同品种使用的策略参数也不同.

以简单的双均线策略为例. 一个简单的双均线策略代码大致是这样::

    SYMBOL = "SHFE.bu1912"  # 合约代码
    SHORT = 30  # 短周期
    LONG = 60  # 长周期

    api = TqApi(auth=TqAuth("快期账户", "账户密码"))

    klines = api.get_kline_serial(SYMBOL, duration_seconds=60, data_length=LONG + 2)
    target_pos = TargetPosTask(api, SYMBOL)

    while True:
        api.wait_update()
        if api.is_changing(klines.iloc[-1], "datetime"):
            short_avg = ma(klines["close"], SHORT)
            long_avg = ma(klines["close"], LONG)
            if long_avg.iloc[-2] < short_avg.iloc[-2] and long_avg.iloc[-1] > short_avg.iloc[-1]:
                target_pos.set_target_volume(-3)
                print("均线下穿，做空")
            if short_avg.iloc[-2] < long_avg.iloc[-2] and short_avg.iloc[-1] > long_avg.iloc[-1]:
                target_pos.set_target_volume(3)
                print("均线上穿，做多")

我们可能需要将这个策略运行多份, 每份的 SYMBOL, LONG, SHORT 都不同.

TqSdk 为这类需求提供两种解决方案, 您可任意选择一种.


每个进程执行一个策略实例
-------------------------------------------------
最简单的办法是直接将上面的程序复制为N个文件, 手工修改每个文件中的 SYMBOL, SHORT, LONG 的值, 再把N个程序分别启动运行即可达到目的.

如果觉得代码复制N份会导致修改不方便, 可以简单的剥离一个函数文件, 每个策略实例文件引用它::

    在函数文件 mylib.py 中:

    def ma(SYMBOL, SHORT, LONG):
        api = TqApi(TqSim())

        klines = api.get_kline_serial(SYMBOL, duration_seconds=60, data_length=LONG + 2)
        target_pos = TargetPosTask(api, SYMBOL)

        while True:
            api.wait_update()
            if api.is_changing(klines.iloc[-1], "datetime"):
                short_avg = ma(klines["close"], SHORT)
                long_avg = ma(klines["close"], LONG)
                if long_avg.iloc[-2] < short_avg.iloc[-2] and long_avg.iloc[-1] > short_avg.iloc[-1]:
                    target_pos.set_target_volume(-3)
                    print("均线下穿，做空")
                if short_avg.iloc[-2] < long_avg.iloc[-2] and short_avg.iloc[-1] > long_avg.iloc[-1]:
                    target_pos.set_target_volume(3)
                    print("均线上穿，做多")

    --------------------------------------------------
    在策略文件 ma-股指.py 中:

    from mylib import ma
    ma("CFFEX.IF1906", 30, 60)

    --------------------------------------------------
    在策略文件 ma-玉米.py 中:

    from mylib import ma
    ma("DCE.c1906", 10, 20)


习惯使用命令行的同学也可以做命令行参数::

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--SYMBOL')
    parser.add_argument('--SHORT')
    parser.add_argument('--LONG')
    args = parser.parse_args()

    api = TqApi(TqSim())
    klines = api.get_kline_serial(args.SYMBOL, duration_seconds=60, data_length=args.LONG + 2)
    target_pos = TargetPosTask(api, args.SYMBOL)
    while True:
        api.wait_update()
        if api.is_changing(klines.iloc[-1], "datetime"):
            short_avg = ma(klines["close"], args.SHORT)
            long_avg = ma(klines["close"], args.LONG)
            if long_avg.iloc[-2] < short_avg.iloc[-2] and long_avg.iloc[-1] > short_avg.iloc[-1]:
                target_pos.set_target_volume(-3)
                print("均线下穿，做空")
            if short_avg.iloc[-2] < long_avg.iloc[-2] and short_avg.iloc[-1] > long_avg.iloc[-1]:
                target_pos.set_target_volume(3)
                print("均线上穿，做多")

使用时在命令行挂参数::

    python ma.py --SYMBOL=SHFE.cu1901 --LONG=30 --SHORT=20
    python ma.py --SYMBOL=SHFE.rb1901 --LONG=50 --SHORT=10

优点:

* 思路简单, 好学好做, 不易出错
* 每个单独策略可以分别启动/停止
* 策略代码最简单, 调试方便

缺点:

* 每个策略进程要建立一个单独的服务器连接, 数量过大时可能无法连接成功


.. _multi_async_task:

单线程创建多个异步任务
-------------------------------------------------
TqSdk 内核支持以异步方式实现多任务。 如果用户策略代码实现为一个异步任务, 即可在单线程内执行多个策略。

TqSdk（2.6.1 版本）对几个常用接口 :py:meth:`~tqsdk.TqApi.get_quote`, :py:meth:`~tqsdk.TqApi.get_quote_list`, :py:meth:`~tqsdk.TqApi.get_kline_serial`, :py:meth:`~tqsdk.TqApi.get_tick_serial` 支持协程中调用。

对于 :py:meth:`~tqsdk.TqApi.get_quote` 接口，在异步代码中可以写为 ``await api.get_quote('SHFE.cu2110')``，代码更加紧凑，可读性更好。

示例代码如下::

    # 协程示例，为每个合约创建 task
    from tqsdk import TqApi

    async def demo(SYMBOL):
        quote = await api.get_quote(SYMBOL)  # 支持 await 异步，这里会订阅合约，等到收到合约行情才返回
        print(f"quote: {SYMBOL}", quote.datetime, quote.last_price)  # 这一行就会打印出合约的最新行情

        ##############################################################################
        # 以上代码和下面的代码是等价的，强烈建议在异步中用上面的写法
        # quote = api.get_quote(SYMBOL)  # 这里还是同步写法，仅仅返回 quote 的引用，还没有订阅合约，会在下次调用 api.wait_update() 时才发出订阅合约请求
        # print(f"quote: {SYMBOL}", quote.datetime, quote.last_price)  # 这一行不会打印出合约的信息
        #
        # async with api.register_update_notify() as update_chan:
        #    async for _ in update_chan:
        #        if quote.datetime != "":  # 当收到 datetime 字段时，可以判断收到了合约行情
        #            print(SYMBOL, quote.datetime, quote.last_price)  # 此时会打印出行情
        #            break
        ##############################################################################

        async with api.register_update_notify() as update_chan:
            async for _ in update_chan:
                if api.is_changing(quote):
                    print(SYMBOL, quote.datetime, quote.last_price)
                # ... 策略代码 ...

    api = TqApi(auth=TqAuth("快期账户", "账户密码"))
    # 为每个合约创建异步任务
    api.create_task(demo("SHFE.rb2107"))
    api.create_task(demo("DCE.m2109"))

    while True:
        api.wait_update()


下面是一个更完整的示例，用异步方式实现为每个合约创建双均线策略，示例代码如下::

    # 协程示例，为每个合约创建 task
    from tqsdk import TqApi

    api = TqApi(auth=TqAuth("快期账户", "账户密码"))  # 构造 api 实例

    async def demo(SYMBOL, SHORT, LONG):
        """
        双均线策略 -- SYMBOL: 合约, SHORT: 短周期, LONG: 长周期
        """
        data_length = LONG + 2  # k线数据长度
        # get_kline_serial 支持 await 异步写法，这里会订阅 K 线，等到收到 k 线数据才返回
        klines = await api.get_kline_serial(SYMBOL, duration_seconds=60, data_length=data_length)
        target_pos = TargetPosTask(api, SYMBOL)
        async with api.register_update_notify() as update_chan:
            async for _ in update_chan:
                if api.is_changing(klines.iloc[-1], "datetime"):
                    short_avg = ma(klines["close"], SHORT)  # 短周期
                    long_avg = ma(klines["close"], LONG)  # 长周期
                    if long_avg.iloc[-2] < short_avg.iloc[-2] and long_avg.iloc[-1] > short_avg.iloc[-1]:
                        target_pos.set_target_volume(-3)
                        print("均线下穿，做空")
                    if short_avg.iloc[-2] < long_avg.iloc[-2] and short_avg.iloc[-1] > long_avg.iloc[-1]:
                        target_pos.set_target_volume(3)
                        print("均线上穿，做多")

    # 为每个合约创建异步任务
    api.create_task(demo("SHFE.rb2107", 30, 60))
    api.create_task(demo("DCE.m2109", 30, 60))
    api.create_task(demo("DCE.jd2109", 30, 60))

    while True:
        api.wait_update()


优点:

* 单线程内执行多个策略, 只消耗一份网络连接
* 没有线程或进程切换成本, 性能高, 延时低, 内存消耗小, 性能最优

缺点:

* 用户需熟练掌握 asyncio 异步编程, 学习成本高


example 中的 `gridtrading_async.py <https://github.com/shinnytech/tqsdk-python/blob/master/tqsdk/demo/example/gridtrading_async.py>`_ 就是一个完全按异步框架实现的网格交易策略. 有意学习的同学可以与 gridtrading.py 对比一下
