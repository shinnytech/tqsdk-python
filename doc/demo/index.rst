.. _demo:

示例程序
====================================================

示例按使用阶段划分，先看基础能力，再看策略和研究场景。

建议从 :ref:`tutorial-t10` （行情）、:ref:`tutorial-t30` （K 线）、:ref:`tutorial-t40` （委托）开始。每次先跑通一个完整示例，再修改参数。

.. note::

   运行前检查示例的账户类型、合约代码与回测日期。部分示例保留历史合约，实时运行时需要替换；初次尝试请使用 :py:class:`TqSim <tqsdk.TqSim>` 本地模拟账户。安装与账户配置见 :ref:`quickstart`。

基础示例
----------------------------------------------------

.. toctree::
    :maxdepth: 1

    base.rst
    option_base.rst

策略示例
----------------------------------------------------

.. toctree::
    :maxdepth: 1

    algorithm.rst
    strategy.rst

Notebook 示例
----------------------------------------------------

.. toctree::
    :maxdepth: 1

    jupyter.rst

