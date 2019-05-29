.. _sub_account:

同一账户下的多策略隔离
=================================================
TqSdk 可以通过交易单元机制支持同一个账户下的多策略交易结果隔离. 

使用交易单元机制
-------------------------------------------------
要使用交易单元机制, 只需在账号后附加一个 "." 号, 后跟交易单元名即可. 假定交易账户为海通期货的 4003212 账号::
  
  # 策略程序A
  from tqsdk.api import TqApi, TqAccount
  
  api = TqApi(TqAccount("H海通期货", "4003212.mystrategyA", "123456"))  # mystrategyA 就是交易单元名
  q = api.get_quote("DCE.a1901")
  pos = api.get_position("DCE.a1901")
  while api.wait_update():
    api.insert_order("DCE.a1901", "BUY", "OPEN", volume=1)              # 这里下单都会算作 mystrategyA的
    print(pos.volume_long)


策略程序A运行后会不断买开 DCE.a1901, 可以看到持仓量不断上升. 我们再启动策略程序B::
    
  # 策略程序B
  from tqsdk.api import TqApi, TqAccount
  
  api = TqApi(TqAccount("H海通期货", "4003212.other", "123456"))        # other 是另一个交易单元名
  q = api.get_quote("DCE.a1901")
  pos = api.get_position("DCE.a1901")                                   # 取 DCE.a1901 持仓, 拿到的是自己这个交易单元的持仓
  print(pos.volume_long)                                             # 取持仓手数, 即使策略程序A已经开了很多仓, 还是会返回0

可以看到, 策略程序B认为 DCE.a1901 的持仓手数为0.


策略程序如果使用交易单元机制, 需要注意以下事项:

* 只有TqAccount支持在账号后附加交易单元名的方式, TqSim不支持
* 策略程序中调用 get_position 获取的持仓记录是本交易单元的持仓记录. 策略程序启动时总是处于 "没有持仓" 的状态. 只有策略程序自己的开仓单成交后, 才会出现持仓.
* 策略程序中调用 get_order 函数，获得的是本策略的委托单信息
* 策略程序中调用 get_account 获取的账户资金信息, 依然是整个账户的数据, 并不按交易单元切分
* 策略程序中使用 TargetPosition 设置目标持仓, 不影响其它策略程序


在天勤软件中使用交易单元机制
-------------------------------------------------
在天勤软件中启动策略程序, 默认都会自动分配一个交易单元. 详见 :ref:`tq`
