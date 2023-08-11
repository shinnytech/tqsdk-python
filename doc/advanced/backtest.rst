.. _batch_backtest:

批量回测, 参数搜索及其它
=================================================
在阅读本文档前, 请确保您已经熟悉了 :ref:`backtest` 

参数优化/参数搜索
-------------------------------------------------
TqSdk 并不提供专门的参数优化机制. 您可以按照自己的需求, 针对可能的每个参数值安排一个回测, 观察它们的回测结果, 以简单的双均线策略为例::

  from tqsdk import TqApi, TqAuth, TqSim, TargetPosTask, BacktestFinished, TqBacktest
  from tqsdk.tafunc import ma
  from datetime import date

  LONG = 60
  SYMBOL = "SHFE.cu1907"

  for SHORT in range(20, 40): # 短周期参数从20-40分别做回测
    acc = TqSim()             # 每次回测都创建一个新的模拟账户
    try:
      api = TqApi(acc, backtest=TqBacktest(start_dt=date(2019, 5, 6), end_dt=date(2019, 5, 10)), auth=TqAuth("快期账户", "账户密码"))
      account = api.get_account()
      klines = api.get_kline_serial(SYMBOL, duration_seconds=60, data_length=LONG + 2)
      target_pos = TargetPosTask(api, SYMBOL)
      while True:
        api.wait_update()
        if api.is_changing(klines.iloc[-1], "datetime"):
          short_avg = ma(klines.close, SHORT)
          long_avg = ma(klines.close, LONG)
          if long_avg.iloc[-2] < short_avg.iloc[-2] and long_avg.iloc[-1] > short_avg.iloc[-1]:
            target_pos.set_target_volume(-1)
          if short_avg.iloc[-2] < long_avg.iloc[-2] and short_avg.iloc[-1] > long_avg.iloc[-1]:
            target_pos.set_target_volume(1)
    except BacktestFinished:
      api.close()
      print("SHORT=", SHORT, "最终权益=", account["balance"])   # 每次回测结束时, 输出使用的参数和最终权益


多进程并发执行多个回测任务
-------------------------------------------------
如果您有大量回测任务想要尽快完成, 您首先需要一台给力的电脑(可以考虑到XX云上租一台32核的, 一小时几块钱). 然后您就可以并发执行N个回测了. 还是以上面的策略为例::

  from tqsdk import TqApi, TqAuth, TqSim, TargetPosTask, BacktestFinished, TqBacktest
  from tqsdk.tafunc import ma
  from datetime import date
  import multiprocessing
  from multiprocessing import Pool

  def MyStrategy(SHORT):
    LONG = 60
    SYMBOL = "SHFE.cu1907"
    acc = TqSim()
    try:
      api = TqApi(acc, backtest=TqBacktest(start_dt=date(2019, 5, 6), end_dt=date(2019, 5, 10)), auth=TqAuth("快期账户", "账户密码"))
      data_length = LONG + 2
      klines = api.get_kline_serial(SYMBOL, duration_seconds=60, data_length=data_length)
      target_pos = TargetPosTask(api, SYMBOL)
      while True:
        api.wait_update()
        if api.is_changing(klines.iloc[-1], "datetime"):
          short_avg = ma(klines.close, SHORT)
          long_avg = ma(klines.close, LONG)
          if long_avg.iloc[-2] < short_avg.iloc[-2] and long_avg.iloc[-1] > short_avg.iloc[-1]:
            target_pos.set_target_volume(-3)
          if short_avg.iloc[-2] < long_avg.iloc[-2] and short_avg.iloc[-1] > long_avg.iloc[-1]:
            target_pos.set_target_volume(3)
    except BacktestFinished:
      api.close()
      print("SHORT=", SHORT, "最终权益=", acc.account.balance)  # 每次回测结束时, 输出使用的参数和最终权益


  if __name__ == '__main__':
    multiprocessing.freeze_support()
    p = Pool(4)                               # 进程池, 建议小于cpu数
    for s in range(20, 40):
      p.apply_async(MyStrategy, args=(s,))  # 把20个回测任务交给进程池执行
    print('Waiting for all subprocesses done...')
    p.close()
    p.join()
    print('All subprocesses done.')

**注意: 由于服务器流控限制, 同时执行的回测任务请勿超过10个**
