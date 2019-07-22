.. _tq:

与天勤软件配合工作
=========================================================================
`天勤程序化交易软件 <https://www.shinnytech.com/tianqin>`_ 是一款基于TqSdk开发的程序化交易软件.

TqSdk并不需要依赖天勤软件即可运行。天勤软件为TqSdk用户提供了一些有用的附加功能。包括:

* 复盘支持
* 交易单元机制。在一个账户中执行多个策略时，每个策略的报单/持仓可以分开计算和管理
* 交易监控及报告
* 在行情图上绘制指标和其它图形
* 天勤软件中内置了完整的Python环境和TqSdk包。使用TqSdk开发的python程序，可以不加任何修改，放入天勤软件中运行或回测. 天勤将为策略程序运行提供一系列支持.

.. toctree::
    :maxdepth: 2

    quickstart.rst
    mdreplay.rst
    report.rst
    chart.rst
    onlytq.rst

