.. _intro:

TqSdk 介绍
=================================================
TqSdk是什么
-------------------------------------------------
TqSdk 是一个由 `信易科技 <https://www.shinnytech.com>`_ 发起并贡献主要代码的开源 python 库. 
依托 `快期多年积累成熟的交易及行情服务器体系 <https://www.shinnytech.com/diff>`_ , TqSdk 支持用户使用很少的代码量构建各种类型的量化交易策略程序, 
并提供包含 历史数据-实时数据-开发调试-策略回测-模拟交易-实盘交易-运行监控-风险管理 的全套解决方案::

  from tqsdk import TqApi, TqAuth, TqAccount, TargetPosTask

  api = TqApi(TqAccount("H海通期货", "4003242", "123456"), auth=TqAuth("快期账户", "账户密码"))      # 创建 TqApi 实例, 指定交易账户
  q_1910 = api.get_quote("SHFE.rb1910")                         # 订阅近月合约行情
  t_1910 = TargetPosTask(api, "SHFE.rb1910")                    # 创建近月合约调仓工具
  q_2001 = api.get_quote("SHFE.rb2001")                         # 订阅远月合约行情
  t_2001 = TargetPosTask(api, "SHFE.rb2001")                    # 创建远月合约调仓工具

  while True:
    api.wait_update()                                           # 等待数据更新
    spread = q_1910.last_price - q_2001.last_price        # 计算近月合约-远月合约价差
    print("当前价差:", spread)
    if spread > 250:
      print("价差过高: 空近月，多远月")                            
      t_1910.set_target_volume(-1)                              # 要求把1910合约调整为空头1手
      t_2001.set_target_volume(1)                               # 要求把2001合约调整为多头1手
    elif spread < 200:
      print("价差回复: 清空持仓")                               # 要求把 1910 和 2001合约都调整为不持仓
      t_1910.set_target_volume(0)
      t_2001.set_target_volume(0)

要快速了解如何使用TqSdk, 可以访问我们的 :ref:`quickstart`


系统架构
----------------------------------------------------
.. raw:: html

  <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="761px" viewBox="-0.5 -0.5 761 221" style="max-width:100%;max-height:221px;"><defs/><g><path d="M 620 60 L 620 40" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><a xlink:href="https://github.com/shinnytech/open-md-gateway"><rect x="480" y="60" width="280" height="40" fill="none" stroke="#d6b656"/><g transform="translate(569.5,66.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="100" height="26" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 102px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;"><div><a href="https://github.com/shinnytech/open-md-gateway">Open Md Gateway</a></div><div><a href="https://github.com/shinnytech/open-md-gateway">行情网关</a></div></div></div></foreignObject><text x="50" y="19" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">[Not supported by viewer]</text></switch></g></a><a xlink:href="https://github.com/shinnytech/open-trade-gateway"><rect x="0" y="60" width="280" height="40" fill="none" stroke="#d6b656"/><g transform="translate(82.5,66.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="114" height="26" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 116px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;"><a href="https://github.com/shinnytech/open-trade-gateway">Open Trade Gateway<br />交易中继网关</a><br /></div></div></foreignObject><text x="57" y="19" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">[Not supported by viewer]</text></switch></g></a><rect x="0" y="0" width="280" height="40" fill="none" stroke="#36393d"/><g transform="translate(84.5,6.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="110" height="26" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 110px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">期货公司交易系统<br />CTP / FEMAS / UFX<br /></div></div></foreignObject><text x="55" y="19" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">期货公司交易系统&lt;br&gt;CTP / FEMAS / UFX&lt;br&gt;</text></switch></g><rect x="480" y="0" width="280" height="40" fill="none" stroke="#36393d"/><g transform="translate(577.5,13.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="84" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 85px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">交易所行情系统<br /></div></div></foreignObject><text x="42" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">交易所行情系统&lt;br&gt;</text></switch></g><path d="M 140 60 L 140 40" fill="none" stroke="#000000" stroke-miterlimit="10"/><path d="M 380 120 L 140 100" fill="none" stroke="#000000" stroke-miterlimit="10"/><path d="M 380 120 L 620 100" fill="none" stroke="#000000" stroke-miterlimit="10"/><a xlink:href="http://doc.shinnytech.com/diff/latest/"><rect x="0" y="120" width="760" height="40" rx="6" ry="6" fill="none" stroke="#b85450"/><g transform="translate(352.5,133.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="54" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 55px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;"><a href="https://github.com/shinnytech/diff">DIFF 协议</a></div></div></foreignObject><text x="27" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">[Not supported by viewer]</text></switch></g></a><path d="M 380 180 L 380 160" fill="none" stroke="#000000" stroke-miterlimit="10"/><a xlink:href="https://github.com/shinnytech/tqsdk-python"><rect x="320" y="180" width="120" height="40" fill="#dae8fc" stroke="#6c8ebf"/><g transform="translate(362.5,193.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="34" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 36px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;"><a href="https://github.com/shinnytech/tqsdk-python">TqSdk</a><br /></div></div></foreignObject><text x="17" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">[Not supported by viewer]</text></switch></g></a></g></svg>
  
* `行情网关 (Open Md Gateway) <https://github.com/shinnytech/open-md-gateway>`_ 负责提供实时行情和历史数据
* `交易中继网关 (Open Trade Gateway) <https://github.com/shinnytech/open-trade-gateway>`_ 负责连接到期货公司交易系统
* 这两个网关统一以 `Diff协议 <https://doc.shinnytech.com/diff/latest>`_ 对下方提供服务
* TqSdk按照Diff协议连接到行情网关和交易中继网关, 实现行情和交易功能


功能要点
----------------------------------------------------
TqSdk 提供的功能可以支持从简单到复杂的各类策略程序.

* 提供当前所有可交易合约从上市开始的 **全部Tick数据和K线数据**
* 支持数十家期货公司的 **实盘交易**
* 支持 **模拟交易**
* 支持 **Tick级和K线级回测**, 支持 **复杂策略回测**
* 提供近百个 **技术指标函数及源码**
* 用户无须建立和维护数据库, 行情和交易数据全在 **内存数据库** , 无访问延迟
* 优化支持 **pandas** 和 **numpy** 库
* 无强制框架结构, 支持任意复杂度的策略, 在一个交易策略程序中使用多个品种的K线/实时行情并交易多个品种


.. _linear_framework:

编程风格
----------------------------------------------------
TqSdk使用单线程异步模型, 它支持构建各类复杂结构的策略程序, 同时保持高性能及高可读性. 要了解 TqSdk 的编程框架, 请参见 :ref:`framework`

如果您曾经使用并熟悉过其它量化交易开发工具, 这些文件可以帮助您尽快了解TqSdk与它们的差异:

* :ref:`for_ctp_user`
* :ref:`for_vnpy_user`


License
-------------------------------------------------
TqSdk 在 Apache License 2.0 协议下提供, 使用者可在遵循此协议的前提下自由使用本软件.

