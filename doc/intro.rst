.. _intro:

TqSdk 介绍
=================================================

源码仓库：`GitHub <https://github.com/shinnytech/tqsdk-python>`_ · `Gitee <https://gitee.com/tianqin_quantification_tqsdk/tqsdk-python>`_

TqSdk是什么
-------------------------------------------------

TqSdk 是由信易科技发起并贡献主要代码的开源 Python 库。依托快期的行情和交易服务，它支持用较少的代码构建各种类型的量化交易策略程序。

从历史数据、实时行情，到开发调试、策略回测、模拟交易、实盘交易，再到运行监控与风险管理，TqSdk 提供了完整的策略开发能力。

先创建 API 和数据引用，然后用 :py:meth:`wait_update() <tqsdk.TqApi.wait_update>` 持续驱动更新。下面的程序只读取行情：

.. code-block:: python

   from tqsdk import TqApi, TqAuth, TqSim

   with TqApi(TqSim(), auth=TqAuth("快期账户", "账户密码")) as api:
       quote = api.get_quote("KQ.m@SHFE.rb")
       while True:
           api.wait_update()
           if api.is_changing(quote, "last_price"):
               print(quote.datetime, quote.last_price)

:py:class:`quote <tqsdk.objs.Quote>` 会随业务数据更新，不需要每次重新获取。K 线、账户、持仓和委托也通过类似的引用方式访问；程序结构详见 :ref:`framework`。

要快速了解如何使用 TqSdk，可以阅读 :ref:`quickstart`，从安装、登录和获取行情开始。

系统架构
----------------------------------------------------
.. raw:: html

  <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="761px" viewBox="-0.5 -0.5 761 221" style="max-width:100%;max-height:221px;"><defs/><g><path d="M 620 60 L 620 40" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><rect x="480" y="60" width="280" height="40" fill="none" stroke="#d6b656"/><g transform="translate(569.5,66.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="100" height="26" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 102px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;"><div>Open Md Gateway</div><div>行情网关</div></div></div></foreignObject><text x="50" y="19" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">[Not supported by viewer]</text></switch></g><rect x="0" y="60" width="280" height="40" fill="none" stroke="#d6b656"/><g transform="translate(82.5,66.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="114" height="26" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 116px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">Open Trade Gateway<br />交易中继网关<br /></div></div></foreignObject><text x="57" y="19" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">[Not supported by viewer]</text></switch></g><rect x="0" y="0" width="280" height="40" fill="none" stroke="#36393d"/><g transform="translate(84.5,6.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="110" height="26" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 110px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">期货公司交易系统<br />CTP / FEMAS / UFX<br /></div></div></foreignObject><text x="55" y="19" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">期货公司交易系统&lt;br&gt;CTP / FEMAS / UFX&lt;br&gt;</text></switch></g><rect x="480" y="0" width="280" height="40" fill="none" stroke="#36393d"/><g transform="translate(577.5,13.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="84" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 85px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">交易所行情系统<br /></div></div></foreignObject><text x="42" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">交易所行情系统&lt;br&gt;</text></switch></g><path d="M 140 60 L 140 40" fill="none" stroke="#000000" stroke-miterlimit="10"/><path d="M 380 120 L 140 100" fill="none" stroke="#000000" stroke-miterlimit="10"/><path d="M 380 120 L 620 100" fill="none" stroke="#000000" stroke-miterlimit="10"/><rect x="0" y="120" width="760" height="40" rx="6" ry="6" fill="none" stroke="#b85450"/><g transform="translate(352.5,133.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="54" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 55px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">DIFF 协议</div></div></foreignObject><text x="27" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">[Not supported by viewer]</text></switch></g><path d="M 380 180 L 380 160" fill="none" stroke="#000000" stroke-miterlimit="10"/><a xlink:href="https://github.com/shinnytech/tqsdk-python"><rect x="320" y="180" width="120" height="40" fill="#dae8fc" stroke="#6c8ebf"/><g transform="translate(362.5,193.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="34" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 36px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;"><a href="https://github.com/shinnytech/tqsdk-python">TqSdk</a><br /></div></div></foreignObject><text x="17" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">[Not supported by viewer]</text></switch></g></a></g></svg>
  
* 行情网关 (Open Md Gateway) 负责提供实时行情和历史数据
* 交易中继网关 (Open Trade Gateway) 负责连接到期货公司交易系统
* 这两个网关统一以 `Diff协议 <https://doc.shinnytech.com/diff/latest>`_ 对下方提供服务
* TqSdk按照Diff协议连接到行情网关和交易中继网关, 实现行情和交易功能

功能要点
----------------------------------------------------
TqSdk 提供的功能可以支持从简单到复杂的各类策略程序。

* **行情数据**：提供 :ref:`Tick 数据和 K 线数据 <mddatas>`，可用范围取决于合约历史与账户权限。
* **实盘交易**：支持数十家期货公司的 `实盘接入 <https://www.shinnytech.com/articles/reference/tqsdk-brokers>`_，账户与委托管理见 :ref:`trade`。
* **模拟交易**：支持 :py:class:`~tqsdk.TqSim` 本地模拟账户与 :py:class:`~tqsdk.TqKq` 快期模拟账户。
* **策略回测**：支持 :ref:`Tick 级、K 线级及复杂策略回测 <backtest>`。
* **指标计算**：提供近百个 :ref:`技术指标函数及源码 <ta>`。
* **数据更新**：行情和交易数据通过内存中的引用对象访问，并随 :py:meth:`~tqsdk.TqApi.wait_update` 更新。
* **数据处理**：支持 pandas 和 numpy 库，方便进一步分析行情与策略结果。
* **策略组织**：无强制框架结构，可在一个策略程序中使用多个品种的 K 线、实时行情并交易多个品种。

不同账户的数据和交易权限可能不同，接入前可查阅 :ref:`profession` 与 :ref:`shinny_account`。

.. _linear_framework:

编程风格
----------------------------------------------------
TqSdk使用单线程异步模型, 它支持构建各类复杂结构的策略程序, 同时保持高性能及高可读性. 要了解 TqSdk 的编程框架, 请参见 :ref:`framework`

如果您曾经使用并熟悉过其它量化交易开发工具, 这些文件可以帮助您尽快了解TqSdk与它们的差异:

* :ref:`for_ctp_user`
* :ref:`for_vnpy_user`

.. _ai:

使用 AI 辅助开发时，可以将 :ref:`TqSdk Skills <tqsdk_skills>` 交给你的 AI 编码工具，让它先阅读使用规则和示例。

License
-------------------------------------------------
TqSdk 在 Apache License 2.0 协议下提供, 使用者可在遵循此协议的前提下自由使用本软件.
