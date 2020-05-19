高级委托指令
=================================================

在实盘交易中, 除常见的限价委托指令外, tqsdk 提供了 FAK / FOK 两种高级市价指令。

insert_order 为用户提供了 limit_price，advance 两个参数指定下单指令，两个参数支持的值的组合为：

=========== ======== ====================================================================
limit_price advance  memo
=========== ======== ====================================================================
指定价格     None     限价单，任意手数成交，当日有效
指定价格     FAK      限价单，任意手数成交，剩余撤单
指定价格     FOK      限价单，要么全部成交，否则全部撤单
None        None     市价单，任意手数成交，剩余撤单
None        FAK      市价单，任意手数成交，剩余撤单
None        FOK      市价单，要么全部成交，否则全部撤单
BEST        None     最优市价单，与对手最有一档价格成交，任意手数成交，剩余撤单
BEST        FAK      最优市价单，与对手最有一档价格成交，任意手数成交，剩余撤单
FIVELEVEL   None     五档市价单，与对手五档价格成交，任意手数成交，剩余撤单
FIVELEVEL   FAK      五档市价单，与对手五档价格成交，任意手数成交，剩余撤单
=========== ======== ====================================================================

* limit_price 默认值为 ``None``
* advance 默认值为 ``None``
* 对于市价单、最优市价单、五档市价单，``advance="FAK"`` 与默认参数 ``None`` 的实际报单请求一样。


例如::

  from tqsdk import TqApi

  api = TqApi()
  # 当日有效限价单
  api.insert_order("SHFE.cu2009", "BUY", "OPEN", 3, limit_price=14200)
  # FAK 限价单
  api.insert_order("SHFE.cu2009", "BUY", "OPEN", 3, limit_price=14200, advance="FAK")
  # FOK 限价单
  api.insert_order("SHFE.cu2009", "BUY", "OPEN", 3, limit_price=14200, advance="FOK")

  # 市价单
  api.insert_order("DCE.m2009", "BUY", "OPEN", 3)
  # FOK 市价单
  api.insert_order("DCE.m2009", "BUY", "OPEN", 3, advance="FOK")

  # BEST
  api.insert_order("CFFEX.T2003", "BUY", "OPEN", 3, limit_price="BEST")
  # FIVELEVEL
  api.insert_order("CFFEX.T2003", "BUY", "OPEN", 3, limit_price="FIVELEVEL")


不同交易所支持的高级指令参数组合：

======== ============ ================== ============
交易所    品种         limit_price        advance
======== ============ ================== ============
郑商所    期货          指定价格 / None    None / FAK
郑商所    期权          指定价格 / None    None / FAK / FOK
大商所    期货          指定价格 / None    None / FAK / FOK
大商所    期权          指定价格           None / FAK / FOK
上期所    期货/期权     指定价格            None / FAK / FOK
中金所    期货/期权     指定价格            None / FAK / FOK
中金所    期货/期权     BEST / FIVELEVEL   None / FAK
======== ============ ================== ============
