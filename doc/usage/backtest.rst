.. _backtest:

策略程序回测
=================================================

执行策略回测
-------------------------------------------------
使用 TqSdk 编写的策略程序，不需要修改策略代码，只需要在创建 api 实例时给backtest参数传入 :py:class:`~tqsdk.backtest.TqBacktest` , 策略就会进入历史回测模式::

  from datetime import date
  from tqsdk import TqApi, TqSim, TqBacktest

  api = TqApi(TqSim(), backtest=TqBacktest(start_dt=date(2018, 5, 1), end_dt=date(2018, 10, 1)))

使用tqsdk在回测结束后会输出交易记录和每日收盘时的账户资金情况，以及最大回撤、夏普比率等指标，这些数据可以导入到 excel 中或使用其他分析工具进一步处理。

回测示例程序：:ref:`tutorial_backtest`


在回测结束时获取回测详细信息
-------------------------------------------------
要在回测结束时调用您自己写的代码, 可以使用 try/except 机制捕获回测结束信号 BacktestFinished, 像这样::

  from tqsdk import BacktestFinished

  acc = TqSim()

  try:
    api = TqApi(acc, backtest=TqBacktest(start_dt=date(2018, 5, 1), end_dt=date(2018, 10, 1)))
    #策略代码在这里
    #...

  except BacktestFinished as e:
    # 回测结束时会执行这里的代码
    print(acc.trade_log)

回测的详细信息保存在回测所用的模拟账户 TqSim 中, 可以直接访问它的成员变量 trade_log(格式为 日期->交易记录及收盘时的权益及持仓).

.. _backtest_rule:

回测时的成交规则和推进
-------------------------------------------------
策略回测时使用内置模拟账户 :py:class:`~tqsdk.sim.TqSim` , 撮合成交规则为对价成交. 即限价单的价格达到对手盘价格时判定为成交. 不会出现委托单部分成交的情况.

回测时策略程序报单, 会立即做一次成交判定. 

回测框架的规则是当没有新的事件需要用户处理时才推进到下一个行情, 也就是这样::

  q = api.get_quote("SHFE.cu1901")
  api.wait_update()                     # 这个 wait_update 更新了行情
  api.insert_order("SHFE.cu1901", ...)  # 程序下单
  api.wait_update()                     # 这个 wait_update 只会更新委托单状态, 行情还是停在原处
  api.insert_order("SHFE.cu1901", ...)  # 如果又下了一个单
  api.wait_update()                     # 这个 wait_update 还是只会更新委托单状态, 行情还是停在原处
  api.wait_update()                     # 这个 wait_update 更新了行情

  
回测使用多行情序列的策略程序
-------------------------------------------------
TqSdk 允许一个策略程序中使用多个行情序列, 比如这样::

  #... 策略程序代码
  ka1 = api.get_kline_serial("SHFE.cu1901", 60)
  ka2 = api.get_kline_serial("SHFE.cu1901", 3600)
  kb  = api.get_kline_serial("CFFEX.IF1901", 3600)
  tsa  = api.get_tick_serial("CFFEX.IF1901")
  qa = api.get_quote("DCE.a1901")
  #... 策略程序代码

TqSdk回测框架使用一套复杂的规则来推进行情：

规则1: tick 序列(例如上面例子中的tsa) 总是按逐 tick 推进::

  tsa  = api.get_tick_serial("CFFEX.IF1901")
  print(tsa.datetime.iloc[-1])             # 2018/01/01 09:30:00.000
  api.wait_update()                           # 推进一个tick
  print(tsa.datetime.iloc[-1])             # 2018/01/01 09:30:00.500
  
规则2: K线序列 (例如上面例子中的ka1, ka2) 总是按周期推进. 每根K线在创建时和结束时各更新一次::

  ka2 = api.get_kline_serial("SHFE.cu1901", 3600) # 请求小时线
  print(ka2.iloc[-1])                         # 2018/01/01 09:00:00.000, O=35000, H=35000, L=35000, C=35000 小时线刚创建
  api.wait_update()                           # 推进1小时, 前面一个小时线结束, 新开一根小时线
  print(ka2.iloc[-2])                         # 2018/01/01 09:00:00.000, O=35000, H=35400, L=34700, C=34900 9点这根小时线完成了
  print(ka2.iloc[-1])                         # 2018/01/01 10:00:00.000, O=34900, H=34900, L=34900, C=34900 10点的小时线刚创建
  
规则3: quote按照以下规则更新::

  if 策略程序中使用了这个合约的tick序列:
    每次tick序列推进时会更新quote的这些字段 datetime/ask&bid_price1/ask&bid_volume1/last_price/highest/lowest/average/volume/amount/open_interest/ price_tick/price_decs/volume_multiple/max&min_limit&market_order_volume/underlying_symbol/strike_price
  elif 策略程序中使用了这个合约的K线序列:
    每次K线序列推进时会更新quote. 使用 k线生成的 quote 的盘口由收盘价分别加/减一个最小变动单位, 并且 highest/lowest/average/amount 始终为 nan, volume 始终为0. 
    if 策略程序使用的K线周期大于1分钟:
      回测框架会隐式的订阅一个1分钟K线, 确保quote的更新周期不会超过1分钟
  else:
    回测框架会隐式的订阅一个1分钟K线, 确保quote的更新周期不会超过1分钟
  
规则4: 策略程序中的多个序列的更新, 按时间顺序合并推进. 每次 wait_update 时, 优先处理用户事件, 当没有用户事件时, 从各序列中选择下一次更新时间最近的, 更新到这个时间::

  ka = api.get_kline_serial("SHFE.cu1901", 10)              # 请求一个10秒线
  kb = api.get_kline_serial("SHFE.cu1902", 15)              # 请求一个15秒线
  print(ka.iloc[-1].datetime, kb.iloc[-1].datetime)   # 2018/01/01 09:00:00, 2018/01/01 09:00:00
  api.wait_update()                                         # 推进一步, ka先更新了, 时间推到 09:00:10
  print(ka.iloc[-1].datetime, kb.iloc[-1].datetime)   # 2018/01/01 09:00:10, 2018/01/01 09:00:00
  api.wait_update()                                         # 再推一步, 这次时间推到 09:00:15, kb更新了
  print(ka.iloc[-1].datetime, kb.iloc[-1].datetime)   # 2018/01/01 09:00:10, 2018/01/01 09:00:15
  api.wait_update()                                         # 再推一步, 这次时间推到 09:00:20, ka更新了
  print(ka.iloc[-1].datetime, kb.iloc[-1].datetime)   # 2018/01/01 09:00:20, 2018/01/01 09:00:15
  api.wait_update()                                         # 再推一步, 时间推到 09:00:30, ka, kb都更新了
  print(ka.iloc[-1].datetime, kb.iloc[-1].datetime)   # 2018/01/01 09:00:30, 2018/01/01 09:00:30


**注意** ：如果未订阅 quote，模拟交易在下单时会自动为此合约订阅 quote ，根据回测时 quote 的更新规则，如果此合约没有订阅K线或K线周期大于分钟线 **则会自动订阅一个分钟线** 。

另外，对 **组合合约** 进行回测时需注意：只能通过订阅 tick 数据来回测，不能订阅K线，因为K线是由最新价合成的，而交易所发回的组合合约数据中无最新价。

了解更多
-------------------------------------------------
* 如果策略回测的精度或仿真性不能满足你的要求, 那你可能需要 :ref:`replay` 
* 如果你要做大量回测, 或者试图做参数优化/参数搜索, 请看 :ref:`batch_backtest`
* 如果你在回测时需要图形化界面支持，我们提供 TqSdk 内置强大的图形化界面解决方案 :ref:`web_gui`

