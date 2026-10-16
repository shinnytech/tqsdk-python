.. _tqsdk.api:

tqsdk.TqApi - 框架及核心业务
------------------------------------------------------------------

``TqApi`` 负责连接、订阅、数据更新与交易请求。下面按源码顺序列出构造参数和所有公开方法。

常用入口：:py:meth:`~tqsdk.TqApi.get_quote` · :py:meth:`~tqsdk.TqApi.get_kline_serial` · :py:meth:`~tqsdk.TqApi.wait_update` · :py:meth:`~tqsdk.TqApi.insert_order` · :py:meth:`~tqsdk.TqApi.get_position`

.. note::

   本页部分历史示例使用固定月份合约。实时运行前请替换为有效合约；历史回测应选择与回测日期匹配的合约。完整上手程序见 :ref:`quickstart`。

.. autoclass:: tqsdk.TqApi
    :members:

.. py:data:: tqsdk.api.UnionTradeable

    单个交易账户类型的联合别名，用于接口的 ``account`` 参数注解。
    支持的账户类型见 :py:class:`~tqsdk.TqApi` 的构造参数说明；
    多账户容器见 :py:class:`~tqsdk.TqMultiAccount`。

