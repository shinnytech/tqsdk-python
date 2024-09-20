.. _enterprise:

TqSdk 企业版
=================================================
除了 TqSdk 专业版以外，我们还提供 TqSdk 企业版本

企业版和专业版相比的主要区别是柜台支持上的区别，企业版支持直连 CTP/融航/杰宜斯等柜台，专业版只能通过中继的方式去进行连接

如果想使用 TqSdk 企业版功能，可以点击 `个人中心 <https://account.shinnytech.com/>`_ 申请15天试用或购买


TqSdk 直连功能
-------------------------------------------------
在 TqSdk 企业版支持用户通过直连模式接入任意一家指定期货公司

除了接入指定期货公司的优点以外，直连模式还带来了一下好处:

* 交易指令直达期货公司，省去中继服务器路径，交易延迟平均减少10ms左右
* 减少了交易服务器依赖，程序运行稳定性提升

TqSdk 直连CTP模式的详细介绍，请点击 :py:class:`~tqsdk.TqCtp`


.. _tqjees:

TqSdk 连接平台功能
-------------------------------------------------
TqSdk 提供了资管平台的对接支持，支持用户连接到指定资管平台，例如杰宜斯或者融航资管系统等

以连融航的模拟服务器为例::

   from tqsdk import TqApi, TqRohon, TqAuth

   account = TqRohon(account_id="融航账户", password="融航密码", front_broker="融航柜台代码", front_url="融航柜台地址", app_id="融航 AppID", auth_code="融航 AuthCode")
   api = TqApi(account, auth=TqAuth("快期账户", "账户密码"))

其中融航的 **模拟账户** 、 **模拟账户密码** 、 **app_id** 和 **auth_code** 需要自行和融航联系获取，其他参数在融航模拟下为

front_url="tcp://129.211.138.170:10001"

front_broker="RohonDemo"

融航实盘情况下将对应信息换成实盘信息即可

融航资管平台连接模式的详细介绍，请点击 :py:class:`~tqsdk.TqRohon`
