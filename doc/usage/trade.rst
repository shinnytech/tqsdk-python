.. _trade:

账户与交易
====================================================

设定实盘交易账户
----------------------------------------------------
TqSdk 要求在创建 TqApi 时指定交易账户。一旦TqApi创建成功，后续所有通过TqApi发出的交易指令均在此账户中进行. 

要使用实盘交易账户, 请使用 :py:class:`~tqsdk.api.TqAccount` (注：使用前请先 import TqAccount) . ::

    api = TqApi(TqAccount("H海通期货", "320102", "123456"))

:py:class:`~tqsdk.api.TqAccount` 的三个参数分别为 期货公司名, 用户名和密码. 目前TqSdk支持的期货公司列表请参见 :ref:`broker_list`

如果您在期货公司的账户位于期货公司的其它席位上(非主席), 您可以在创建 TqAccount 时用 front_broker 和 front_url 参数指定次席服务器::

    api = TqApi(TqAccount("H海通期货", "320102", "123456", front_broker="3233", front_url="tcp://132.31.128.201:41205"))

TqApi 创建成功即代表相应账户已登录成功. 如果在60秒内无法完成登录, 会抛出超时异常, 用户代码可以此判定登录失败::

    try:
        api = TqApi(TqAccount("H海通期货", "320102", "123456"))
    except Exception as e:
        print("行情服务连不上, 或者期货公司服务器关了, 或者账号密码错了, 总之就是有问题")


设定模拟交易账户
----------------------------------------------------
如果您需要使用模拟账户进行测试，只需在创建TqApi时传入一个 :py:class:`~tqsdk.sim.TqSim` 的实例（不填写参数则默认为 TqSim() 模拟账号）::

    api = TqApi(TqSim())


如果需要使用能保存账户资金及持仓信息的模拟账户，请使用 "快期模拟" 账号, 账户申请及使用方法请参考 :ref:`sim_trading` 部分内容。


获取账户情况
----------------------------------------------------
TqApi 提供以下函数来获取交易账户相关信息:

* :py:meth:`~tqsdk.api.TqApi.get_account` - 获取账户资金情况
* :py:meth:`~tqsdk.api.TqApi.get_position` - 获取持仓情况
* :py:meth:`~tqsdk.api.TqApi.get_order` - 获取委托单

以上函数返回的都是dict, 并会在 wait_update 时更新


交易指令
----------------------------------------------------
要在交易账户中发出一个委托单, 使用 :py:meth:`~tqsdk.api.TqApi.insert_order` 函数::

    order = api.insert_order(symbol="SHFE.rb1901", direction="BUY", offset="OPEN", limit_price=4310, volume=2)
    print(order)

这个函数调用后会立即返回一个指向此委托单的对象引用, 使用方法与dict一致, 内容如下::

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
    while order.status != "FINISHED":
        api.wait_update()
        print("委托单状态: %s, 未成交手数: %d 手" % (order.status, order.volume_left))

要撤销一个委托单, 使用 :py:meth:`~tqsdk.api.TqApi.cancel_order` 函数::

    api.cancel_order(order)

* **除 insert_order 和 cancel_order 外, TqSdk 提供了一些更强的交易辅助工具比如** :py:class:`~tqsdk.lib.TargetPosTask`. **使用这些工具, 可以简化交易逻辑的编码工作.**

.. _broker_list:

TqSdk支持的期货公司列表
-----------------------------------------------------
=============== =============== =============== ====================
A安粮期货
B渤海期货       B宝城期货       B北京首创       B倍特期货
C长安期货       C长城期货       C长江期货       C创元期货
C财达期货
D大地期货       D大越期货       D东航期货       D大陆期货
D德盛期货       D东吴期货       D东证期货       D东华期货
D东方财富       D东海期货       D大有期货       D东方汇金
D东兴期货
F方正中期
G广发期货       G光大期货       G国际期货       G国投安信
G国盛期货       G国金期货       G国联期货       G国元期货
G广金期货       G格林大华       G国贸期货       G国泰君安
G广州期货       G国信期货       G国都期货       G国海良时
G冠通期货
H华安期货       H华泰期货       H海通期货       H海证期货
H华西期货       H混沌天成       H华鑫期货       H华信期货
H和合期货       H恒泰期货       H弘业期货       H徽商期货
H宏源期货       H海航期货       H华联期货       H华龙期货
H华创期货       H华闻期货       H华金期货       H华融期货
H红塔期货       H和融期货
J金石期货       J金元期货       J建信期货       J金瑞期货
J金信期货       J锦泰期货       J江海汇鑫       J金汇期货
L良运期货       L鲁证期货
M迈科期货       M美尔雅期货
N南华期货       N宁证期货
P平安期货
Q前海期货
R瑞达期货       R瑞奇期货
S申万期货       S上海中期       S上海东方       S上海东亚
S盛达期货       S山西三立       S神华期货       S首创京都
S山金期货
T铜冠金源       T天富期货       T通惠期货       T天鸿期货
T天风期货
W五矿经易
X先锋期货       X兴证期货       X兴业期货       X新湖期货
X新世纪期货     X先融期货       X西部期货       X西南期货
X信达期货       X新纪元期货      X鑫鼎盛期货      
Y银河期货       Y英大期货       Y永安期货       Y一德期货
Z中信建投       Z中融汇信       Z招金期货       Z中财期货
Z中钢期货       Z中辉期货       Z中信期货       Z中天期货
Z中粮期货       Z中州期货       Z中原期货       Z浙商期货
Z浙江中大       Z中投天琪       Z招商期货       Z中航期货
Z中衍期货
=============== =============== =============== ====================
