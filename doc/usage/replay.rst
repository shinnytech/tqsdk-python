.. _replay:

策略程序复盘
=================================================

执行策略复盘
-------------------------------------------------
复盘模式下会100%回放当天历史数据，并帮助你实现全天24小时开发 TqSdk 程序需求

使用 TqSdk 编写的策略程序，不需要修改策略代码，只需要在创建 api 实例时给 backtest 参数传入 :py:class:`~tqsdk.backtest.TqReplay` 指定复盘日期, 策略就会进入复盘模式:: 

  from datetime import date
  from tqsdk import TqApi, TqReplay

  api = TqApi(backtest = TqReplay(date(2019,12,23)


此外我们认为复盘模式结合图形化界面会有更好的体验，可以参考 :ref:`web_gui` 

同时在图形化界面下，你可以通过点击复盘速度控制按钮对复盘行情速度进行控制

.. figure:: ../images/replay.png


**在使用复盘模式时需要注意以下几点：**

1.指定复盘日期需要有行情，否则提示无法创建复盘服务器

2.订阅合约在复盘日期时已经上市或还未下市



