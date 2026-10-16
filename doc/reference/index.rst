.. _tqsdk_apis:

TqSdk API 参考
====================================================================

按“想完成什么”找到接口，再查看下面的完整模块目录。API 说明由当前版本的源码生成；如果还不熟悉数据引用和更新循环，先阅读 :ref:`framework`。

常用接口速查
--------------------------------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 24 46 30

   * - 我想要
     - 从这些接口开始
     - 配套指南
   * - 获取行情与 K 线
     - :py:meth:`~tqsdk.TqApi.get_quote`、:py:meth:`~tqsdk.TqApi.get_kline_serial`
     - :ref:`mddatas`
   * - 驱动策略、判断更新
     - :py:meth:`~tqsdk.TqApi.wait_update`、:py:meth:`~tqsdk.TqApi.is_changing`
     - :ref:`framework`
   * - 查询账户与持仓
     - :py:meth:`~tqsdk.TqApi.get_account`、:py:meth:`~tqsdk.TqApi.get_position`
     - :ref:`trade`
   * - 下单与撤单
     - :py:meth:`~tqsdk.TqApi.insert_order`、:py:meth:`~tqsdk.TqApi.cancel_order`
     - :ref:`trade`
   * - 自动管理持仓
     - :py:class:`~tqsdk.TargetPosTask`
     - :ref:`targetpostask`
   * - 回测与本地模拟
     - :py:class:`~tqsdk.TqBacktest`、:py:class:`~tqsdk.TqSim`
     - :ref:`backtest`

完整模块目录
--------------------------------------------------------------------

.. toctree::
    :maxdepth: 1
    :caption: 核心接口

    tqsdk.api.rst
    tqsdk.auth.rst
    tqsdk.account.rst
    tqsdk.multiaccount.rst
    tqsdk.objs.rst
    tqsdk.channel.rst
    tqsdk.lib.rst
    tqsdk.backtest.rst
    tqsdk.algorithm.rst
    tqsdk.risk_rule.rst

.. toctree::
    :maxdepth: 1
    :caption: 账户接入

    tqsdk.tqkq.rst
    tqsdk.tqzq.rst
    tqsdk.tqctp.rst
    tqsdk.tqrohon.rst
    tqsdk.tqjees.rst
    tqsdk.tqyida.rst
    tqsdk.tqo32.rst
    tqsdk.tqis.rst
    tqsdk.tqxuntou.rst
    tqsdk.sim.rst

.. toctree::
    :maxdepth: 1
    :caption: 指标、工具与异常

    tqsdk.ta.rst
    tqsdk.tafunc.rst
    tqsdk.tools.download.rst
    tqsdk.exceptions.rst
    tqsdk.scenario.rst
