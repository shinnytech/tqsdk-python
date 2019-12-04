.. _multi_instance:

交易策略的多实例运行
=================================================
我们可能会将一个策略应用于不同的目标品种, 不同品种使用的策略参数也不同.

以简单的双均线策略为例. 一个简单的双均线策略代码大致是这样::

    SYMBOL = "SHFE.bu1912"  # 合约代码
    SHORT = 30  # 短周期
    LONG = 60  # 长周期

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

我们可能需要将这个策略运行多份, 每份的 SYMBOL, LONG, SHORT 都不同.

TqSdk 为这类需求提供三种解决方案, 您可任意选择一种.


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


单进程中多线程, 每个线程执行一个策略实例
-------------------------------------------------
一般情况下, 我们推荐用户使用上一方案. 仅当用户策略实例很多, 导致网络连接数无法容纳时, 可以考虑使用本方案.

* 首先需要正常创建一个 TqApi 实例 api_master, 并用 TqApi.copy 函数获得多个slave副本
* 启动多个线程, 每个线程中使用一个 TqApi 实例副本.
* 主线程中的 api_master 仍然需要持续调用 wait_update
* 每个线程中的策略代码可以如常工作

示例代码如下::

    import threading

    class WorkerThread(threading.Thread):
        def __init__(self, api, symbol):
            threading.Thread.__init__(self)
            self.api = api
            self.symbol = symbol

        def run(self):
            SHORT = 30  # 短周期
            LONG = 60  # 长周期
            data_length = LONG + 2  # k线数据长度
            klines = self.api.get_kline_serial(self.symbol, duration_seconds=60, data_length=data_length)
            target_pos = TargetPosTask(self.api, self.symbol)

            while True:
                self.api.wait_update()
                if self.api.is_changing(klines.iloc[-1], "datetime"):  # 产生新k线:重新计算SMA
                    short_avg = ma(klines["close"], SHORT)  # 短周期
                    long_avg = ma(klines["close"], LONG)  # 长周期
                    if long_avg.iloc[-2] < short_avg.iloc[-2] and long_avg.iloc[-1] > short_avg.iloc[-1]:
                        target_pos.set_target_volume(-3)
                        print("均线下穿，做空")
                    if short_avg.iloc[-2] < long_avg.iloc[-2] and short_avg.iloc[-1] > long_avg.iloc[-1]:
                        target_pos.set_target_volume(3)
                        print("均线上穿，做多")


    if __name__ == "__main__":
        api_master = TqApi(TqSim())

        # Create new threads
        thread1 = WorkerThread(api_master.copy(), "SHFE.cu1901")
        thread2 = WorkerThread(api_master.copy(), "SHFE.rb1901")

        # Start new Threads
        thread1.start()
        thread2.start()

        while True:
            api_master.wait_update()


单线程创建多个异步任务
-------------------------------------------------
TqSdk 内核支持以异步方式实现多任务. 如果用户策略代码实现为一个异步任务, 即可在单线程内执行多个策略.

优点:

* 单线程内执行多个策略, 只消耗一份网络连接
* 没有线程或进程切换成本, 性能高, 延时低, 内存消耗小, 性能最优

缺点:

* 用户需熟练掌握 asyncio 异步编程, 学习成本高


example 中的 `gridtrading_async.py <https://github.com/shinnytech/tqsdk-python/blob/master/tqsdk/demo/example/gridtrading_async.py>`_ 就是一个完全按异步框架实现的网格交易策略. 有意学习的同学可以与 gridtrading.py 对比一下
