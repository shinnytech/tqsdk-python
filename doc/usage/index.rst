.. _usage:

使用 TqSdk
========================================

这一部分面向已经跑通 :ref:`quickstart` 的读者，建议先理解 TqSdk 的运行模型和账户体系，再进入行情、交易、回测与工具部分。

.. list-table:: 按任务选择阅读路径
   :header-rows: 1
   :widths: 25 50 25

   * - 当前任务
     - 建议顺序
     - 读完后可以
   * - 写第一个策略
     - :ref:`framework` → :ref:`mddatas` → :ref:`targetpostask`
     - 把数据更新与目标持仓串起来
   * - 接入已有账户
     - :ref:`shinny_account` → :ref:`trade`
     - 区分认证账户、模拟账户和实盘账户
   * - 检验策略逻辑
     - :ref:`backtest` → :ref:`web_gui`
     - 运行历史回测并查看结果
   * - 进行数据研究
     - :ref:`mddatas` → :ref:`ta` → :doc:`jupyter`
     - 获取序列、计算指标与交互分析

基础概念与账户
----------------------------------------

.. toctree::
    :maxdepth: 1

    framework.rst
    shinny_account.rst

行情与数据
----------------------------------------

.. toctree::
    :maxdepth: 1

    mddatas.rst
    kqd_symbol.rst
    ta.rst

交易与回测
----------------------------------------

.. toctree::
    :maxdepth: 1

    trade.rst
    option_trade.rst
    targetpostask.rst
    backtest.rst

运行工具
----------------------------------------

.. toctree::
    :maxdepth: 1

    web_gui.rst
    jupyter.rst
