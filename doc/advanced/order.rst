.. _advanced_order:

高级委托指令
=================================================

在实盘交易中, 除常见的限价委托指令外, tqsdk 提供了 FAK / FOK 两种高级市价指令。

insert_order 为用户提供了 limit_price，advanced 两个参数指定下单指令，两个参数支持的值的组合为：

=========== ======== ====================================
limit_price advanced  memo
=========== ======== ====================================
指定价格     None     限价指令，即时成交，当日有效
指定价格     FAK      限价指令，即时成交剩余撤销
指定价格     FOK      限价指令，即时全部成交或撤销
None        None     市价指令，即时成交剩余撤销
None        FAK      市价指令，即时成交剩余撤销
None        FOK      市价指令，即时全部成交或撤销
BEST        None     最优一档即时成交剩余撤销指令
BEST        FAK      最优一档即时成交剩余撤销指令
FIVELEVEL   None     最优五档即时成交剩余撤销指令
FIVELEVEL   FAK      最优五档即时成交剩余撤销指令
=========== ======== ====================================

* limit_price 默认值为 ``None``
* advance 默认值为 ``None``
* 对于市价单、BEST、FIVELEVEL，``advanced="FAK"`` 与默认参数 ``None`` 的实际报单请求一样。


例如::

  from tqsdk import TqApi, TqAuth

  api = TqApi(auth=TqAuth("快期账户", "账户密码"))
  # 当日有效限价单
  api.insert_order("SHFE.cu2009", "BUY", "OPEN", 3, limit_price=14200)
  # FAK 限价单
  api.insert_order("SHFE.cu2009", "BUY", "OPEN", 3, limit_price=14200, advanced="FAK")
  # FOK 限价单
  api.insert_order("SHFE.cu2009", "BUY", "OPEN", 3, limit_price=14200, advanced="FOK")

  # 市价单
  api.insert_order("DCE.m2009", "BUY", "OPEN", 3)
  # FOK 市价单
  api.insert_order("DCE.m2009", "BUY", "OPEN", 3, advanced="FOK")

  # BEST
  api.insert_order("CFFEX.T2003", "BUY", "OPEN", 3, limit_price="BEST")
  # FIVELEVEL
  api.insert_order("CFFEX.T2003", "BUY", "OPEN", 3, limit_price="FIVELEVEL")


不同交易所支持的高级指令参数组合：

======== ============== ==================== ====================
交易所    品种           limit_price          advance
======== ============== ==================== ====================
郑商所    期货            指定价格 / None      None / FAK
郑商所    期权            指定价格 / None      None / FAK / FOK
大商所    期货            指定价格 / None      None / FAK / FOK
大商所    期权            指定价格             None / FAK / FOK
上期所    期货/期权       指定价格              None / FAK / FOK
中金所    期货/期权       指定价格              None / FAK / FOK
中金所    期货/期权       BEST / FIVELEVEL     None / FAK
上交所    ETF期权         指定价格              None / FOK
深交所    ETF期权         指定价格              None / FOK
======== ============== ==================== ====================
