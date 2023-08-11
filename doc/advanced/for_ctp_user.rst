.. _for_ctp_user:

TqSdk与使用Ctp接口开发策略程序有哪些差别
=================================================
如果您曾经直接使用CTP接口开发过交易策略程序, 目前刚开始接触 TqSdk, 下面的信息将帮助您尽快理解 TqSdk.


系统整体架构
-------------------------------------------------
CTP接口直接连接到期货公司交易系统, 从期货公司系统获取行情并执行交易指令.

TqSdk 则使用基于网络协作的组件设计. 如下图:

.. raw:: html

  <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="761px" viewBox="-0.5 -0.5 761 261" style="max-width:100%;max-height:261px;"><defs/><g><path d="M 620 60 L 620 40" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><a xlink:href="https://github.com/shinnytech/open-md-gateway"><rect x="480" y="60" width="280" height="40" fill="#fff2cc" stroke="#d6b656"/><g transform="translate(569.5,66.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="100" height="26" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 102px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;"><div><a href="https://github.com/shinnytech/open-md-gateway">Open Md Gateway</a></div><div><a href="https://github.com/shinnytech/open-md-gateway">行情网关</a></div></div></div></foreignObject><text x="50" y="19" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">[Not supported by viewer]</text></switch></g></a><a xlink:href="https://github.com/shinnytech/open-trade-gateway"><rect x="0" y="60" width="280" height="40" fill="#fff2cc" stroke="#d6b656"/><g transform="translate(82.5,66.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="114" height="26" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 116px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;"><a href="https://github.com/shinnytech/open-trade-gateway">Open Trade Gateway<br />交易中继网关</a><br /></div></div></foreignObject><text x="57" y="19" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">[Not supported by viewer]</text></switch></g></a><rect x="0" y="0" width="280" height="40" fill="#eeeeee" stroke="#36393d"/><g transform="translate(84.5,6.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="110" height="26" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 110px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">期货公司交易系统<br />CTP / FEMAS / UFX<br /></div></div></foreignObject><text x="55" y="19" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">期货公司交易系统&lt;br&gt;CTP / FEMAS / UFX&lt;br&gt;</text></switch></g><rect x="480" y="0" width="280" height="40" fill="#eeeeee" stroke="#36393d"/><g transform="translate(577.5,13.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="84" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 85px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">交易所行情系统<br /></div></div></foreignObject><text x="42" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">交易所行情系统&lt;br&gt;</text></switch></g><path d="M 140 60 L 140 40" fill="none" stroke="#000000" stroke-miterlimit="10"/><path d="M 380 120 L 140 100" fill="none" stroke="#000000" stroke-miterlimit="10"/><path d="M 380 120 L 620 100" fill="none" stroke="#000000" stroke-miterlimit="10"/><a xlink:href="http://doc.shinnytech.com/diff/latest/"><rect x="0" y="120" width="760" height="40" rx="6" ry="6" fill="#f8cecc" stroke="#b85450"/><g transform="translate(352.5,133.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="54" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 55px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;"><a href="https://github.com/shinnytech/diff">DIFF 协议</a></div></div></foreignObject><text x="27" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">[Not supported by viewer]</text></switch></g></a><path d="M 380 180 L 380 160" fill="none" stroke="#000000" stroke-miterlimit="10"/><a xlink:href="http://www.shinnytech.com/tianqin"><rect x="320" y="180" width="120" height="40" fill="#dae8fc" stroke="#6c8ebf"/><g transform="translate(355.5,193.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="48" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 49px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;"><a href="http://www.tq18.cn">天勤终端</a></div></div></foreignObject><text x="24" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">[Not supported by viewer]</text></switch></g></a><a xlink:href="https://github.com/shinnytech/tqsdk-python"><rect x="320" y="220" width="120" height="40" fill="#dae8fc" stroke="#6c8ebf"/><g transform="translate(362.5,233.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="34" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 36px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;"><a href="https://github.com/shinnytech/tqsdk-python">TqSdk</a><br /></div></div></foreignObject><text x="17" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">[Not supported by viewer]</text></switch></g></a></g></svg>


如图所示, 整个系统结构包括这些关键组件:

* 行情网关 (Open Md Gateway) 负责提供实时行情和历史数据
* 交易中继网关 (Open Trade Gateway) 负责连接到期货公司交易系统
* 上面两个网关统一以 Diff 协议对下方提供服务
* 天勤终端和TqSdk按照Diff协议连接到行情网关和交易中继网关, 实现行情和交易功能


这样的结构可以给用户带来一些好处:

* TqSdk 很小, 安装也很方便, 只要简单 pip install tqsdk 即可
* 官方专门运维行情数据库, 用户可以直接使用, 不需要自己接收和存储数据
* 交易相关接口被大幅度简化, 不再需要处理CTP接口的复杂回调, 也不需要发起任何查询请求
* 任何语言只要支持websocket协议, 都可以用来进行策略开发

也有一些不如直接使用CTP接口方便的地方:

* 由于交易指令经交易网关转发, 用户无法直接指定CTP服务器地址. 用户如果需要连接到官方交易网关不支持的期货公司, 需要自行部署交易网关.


K线数据与指标计算
-------------------------------------------------
Ctp接口不提供K线数据. 

在TqSdk中, K线数据和其它行情数据一样是由行情网关生成并推送的:

* 用户不再需要维护K线数据库. 用户电脑实时行情中断后, 也不再需要补历史数据
* 行情服务器生成K线时, 采用了按K线时间严格补全对齐的算法. 这与其它软件有明显区别, 详见 https://www.shinnytech.com/blog/why-our-kline-different/
* 行情数据只在每次程序运行时通过网络获取, 不在用户硬盘保存. 如果策略研究工作需要大量静态历史数据, 我们推荐使用数据下载工具, 另行下载csv文件使用.

TqSdk中的K线序列采用 pandas.DataFrame 格式. pandas 提供了 `非常丰富的数据处理函数 <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_ , 使我们可以非常方便的进行数据处理, 例如::

  ks = api.get_kline_serial("SHFE.cu1901", 60)
  print(ks.iloc[-1])            # <- 最后一根K线
  print(ks.close)               # <- 收盘价序列
  ks.high - ks.high.shift(1)    # <- 每根K线最高价-前一根K线最高价, 形成一个新序列

  
TqSdk 也通过 :py:mod:`tqsdk.tafunc` 提供了一批行情分析中常用的计算函数, 例如::
  
  from tqsdk import tafunc
  ks = api.get_kline_serial("SHFE.cu1901", 60)
  ms = tafunc.max(ks.open, ks.close)           # <- 取每根K线开盘价和收盘价的高者构建一个新序列
  median3 = tafunc.median(ks.close, 100)       # <- 求最近100根K线收盘价的中间值
  ss = tafunc.std(ks.close, 5)                 # <- 每5根K线的收盘价标准差


数据接收和更新
-------------------------------------------------
Ctp接口按照事件回调模型设计, 使用 CThostFtdcTraderSpi 的 OnXXX 回调函数进行行情数据和回单处理::

  class MySpiHandler
    : public CThostFtdcTraderSpi
  {
  public:
    ///当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。
    virtual void OnFrontConnected();

    ///报单通知
    virtual void OnRtnOrder(CThostFtdcOrderField *pOrder);

    ///成交通知
    virtual void OnRtnTrade(CThostFtdcTradeField *pTrade);
  }
    
TqSdk则不使用事件回调机制. :py:meth:`~tqsdk.TqApi.wait_update` 函数设计用来获取任意数据更新, 像这样::

  api = TqApi(auth=TqAuth("快期账户", "账户密码"))
  x = api.insert_order("SHFE.cu1901", direction="BUY", offset="OPEN", volume=1, limit_price=50000)
  
  while True:
    api.wait_update()       # <- 这个 wait_update 将尝试更新所有数据. 如果没有任何新信息, 程序会阻塞在这一句. 一旦有任意数据被更新, 程序会继续往下执行
    print(x)                # <- 显示委托单最新状态


一次 wait_update 可能更新多个实体, 在这种情况下, :py:meth:`~tqsdk.TqApi.is_changing` 被用来判断某个实体是否有变更::

  api = TqApi(auth=TqAuth("快期账户", "账户密码"))
  q = api.get_quote("SHFE.cu1901")
  ks = api.get_kline_serial("SHFE.cu1901", 60)
  x = api.insert_order("SHFE.cu1901", direction="BUY", offset="OPEN", volume=1, limit_price=50000)
  
  while True:
    api.wait_update()      # <- 这个 wait_update 将尝试更新所有数据. 如果没有任何新信息, 程序会阻塞在这一句. 一旦有任意数据被更新, 程序会继续往下执行
    if api.is_changing(q): # <- 这个 is_changing 用来判定这次更新是否影响到了q
      print(q)    
    if api.is_changing(x, "status"): # <- 这个 is_changing 用来判定这次更新是否影响到了报单的status字段
      print(x)


TqSdk针对行情数据和交易信息都采用相同的 wait_update/is_changing 方案. 用户需要记住的要点包括:

* get_quote, get_kline_serial, insert_order 等业务函数返回的是一个引用(refrence, not value), 它们的值总是在 wait_update 时更新.
* 用户程序除执行自己业务逻辑外, 需要反复调用 wait_update. 在两次 wait_update 间, 所有数据都不更新
* 用 insert_order 函数下单, 报单指令实际是在 insert_order 后调用 wait_update 时发出的. 
* 用户程序中需要避免阻塞, 不要使用 sleep 暂停程序

关于 wait_update 机制的详细说明, 请见 :ref:`framework`


