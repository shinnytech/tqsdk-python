.. _enterprise:

TqSdk2 企业版
=================================================
除了 TqSdk 专业版以外，我们还提供 TqSdk2 企业版本来供用户使用，如果想了解专业版和企业版的区别，`可以点击查看 TqSdk2 文档 <https://doc.shinnytech.com/tqsdk2/latest/advanced/for_tqsdk1_user.html#tqsdk2-tqsdk>`_

如果想使用 TqSdk2 企业版功能，可以点击 `个人中心 <https://account.shinnytech.com/>`_ 申请15天试用或购买

企业版本提供专业版的全部功能 :ref:`profession` ，且 TqSdk 和 TqSdk2 专业版权限通用，此外还包含如下功能

TqSdk2 直连功能
-------------------------------------------------
在 TqSdk2 中除了通过中继模式接入期货公司以外，还提供用户通过直连模式接入任意一家指定期货公司

除了接入指定期货公司的优点以外，直连模式还带来了一下好处:

* 交易指令直达期货公司，省去中继服务器路径，交易延迟平均减少10ms左右
* 减少了交易服务器依赖，程序运行稳定性提升


.. _tqjees:

TqSdk2 连接资管平台功能
-------------------------------------------------
TqSdk2 提供了资管平台的对接支持，支持用户连接到指定资管平台

以连接杰宜斯的模拟服务器为例::

  from tqsdk2 import TqApi, TqAuth, TqJees

  acc = TqJees(td_url="tcp://129.211.138.170:10001", broker_id="JeesDemo", app_id="shinny_tqsdk_01", auth_code= "0000000000000000", user_name="杰宜斯模拟账户", password="杰宜斯模拟账户密码")
  api = TqApi(acc,auth= TqAuth("快期账户","账户密码"))

其中杰宜斯的 **模拟账户** 和 **模拟账户密码** 需要自行和杰宜斯联系获取，其他参数在杰宜斯模拟下为

td_url="tcp://39.101.174.218:40205"

broker_id="JeesDemo"

app_id="shinny_tqsdk_01"

auth_code="0000000000000000"

杰宜斯实盘情况下将对应信息换成实盘信息即可

资管平台连接模式的详细介绍，请点击 :py:class:`~tqsdk2.api.TqJees` .


.. _tqrohon:

TqSdk2 连接资管平台功能
-------------------------------------------------
TqSdk2 提供了资管平台的对接支持，支持用户连接到指定资管平台

以连接融航的模拟服务器为例::

  from tqsdk2 import TqApi, TqAuth, TqRohon

  acc = TqRohon(td_url="tcp://129.211.138.170:10001", broker_id="RohonDemo", app_id="shinny_tqsdk_01", auth_code= "qZWmA7iTXaEO2w40", user_name="融航模拟账户", password="融航模拟账户密码")
  api = TqApi(acc,auth= TqAuth("快期账户","账户密码"))

其中融航模拟的 **模拟账户** 和 **模拟账户密码** 需要自行和融航联系获取，其他参数在融航模拟下为

td_url="tcp://129.211.138.170:10001"

broker_id="RohonDemo"

app_id="shinny_tqsdk_01"

auth_code="qZWmA7iTXaEO2w40"

融航实盘情况下将对应信息换成实盘信息即可

资管平台连接模式的详细介绍，请点击 :py:class:`~tqsdk2.api.TqRohon` .
