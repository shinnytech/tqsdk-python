.. _shinny_account:

快期账户
=================================================
在使用 TqSdk 之前，用户需要先注册自己的 **快期账户** ，传入快期账户是使用任何 TqSdk 程序的前提

如需注册，请点击  `注册快期账户 <https://account.shinnytech.com/>`_ ::

    from tqsdk import TqApi, TqAuth
    api = TqApi(auth=TqAuth("快期账户", "账户密码"))

用快期账户来模拟交易
-------------------------------------------------
注册完成的快期账户的【手机号】/【邮箱地址】/【用户名】和【密码】可以作为 快期模拟 账号，通过 :py:class:`~tqsdk.api.TqKq` 对 auth 传入参数进行登录，这个 快期模拟 账户在快期APP、快期专业版  和天勤量化上是互通的::

    from tqsdk import TqApi, TqAuth, TqKq
    api = TqApi(TqKq(), auth=TqAuth("快期账户", "账户密码"))


用快期账户来实盘交易
-------------------------------------------------
对于 TqSdk 免费版，每个快期账户支持最多绑定一个实盘账户，而天勤量化专业版支持一个快期账户绑定任意多个实盘账户

快期账户会在用户使用实盘账户时自动进行绑定，直到该快期账户没有能绑定实盘账户的名额(自动绑定功能需要 TqSdk 版本> 1.8.3)::

    from tqsdk import TqApi, TqAccount, TqAuth, TqKq
    api = TqApi(TqAccount("H海通期货", "320102", "123456"), auth=TqAuth("快期账户", "账户密码"))

如果需要注册快期账户或者修改您的快期账户绑定的实盘账户请参见  :ref:`user_center`


.. _user_center:

登录用户管理中心
-------------------------------------------------
点击 `登录用户管理中心 <https://www.shinnytech.com/register-intro/>`_ ，可以注册快期账户或者修改您的快期账户绑定的实盘账户

登录成功后显示如下，在下方红框处,用户可以自行解绑/绑定实盘账户，其中解绑操作每天限定一次

.. figure:: ../images/user_web_management.png

如需一个快期账户支持更多的实盘账户，请联系工作人员进行批量购买 `天勤量化专业版 <https://www.shinnytech.com/tqsdk-buy/>`_




