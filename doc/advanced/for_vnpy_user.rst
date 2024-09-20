.. _for_vnpy_user:

TqSdk 与 vn.py 有哪些差别
=================================================
TqSdk 与 vn.py 有非常多的差别. 如果您是一位有经验的 vn.py 用户, 刚开始接触 TqSdk, 下面的信息将帮助您尽快理解 TqSdk.


系统整体架构
-------------------------------------------------
vn.py 是一套 all-in-one 的结构, 在一个Python软件包中包含了数据库, 行情接收/存储, 交易接口, 图形界面等功能.

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


对于需要直连期货公司交易的用户, TqSdk 也提供了 :py:meth:`~tqsdk.TqCtp` 模块支持用户直连


每个策略是一个单独运行的py文件
-------------------------------------------------
在 vn.py 中, 要实现一个策略程序, 通常是从 CtaTemplate 等基类派生一个子类, 像这样::

  class DoubleMaStrategy(CtaTemplate):

    parameters = ["fast_window", "slow_window"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
      ...
        
    def on_tick(self, tick: TickData):
      ...

    def on_bar(self, bar: BarData):
      ...

这个 DoubleMaStrategy 类写好以后, 由vn.py的策略管理器负责加载运行. 整个程序结构中, vn.py作为调用方, 用户代码作为被调用方, 结构图是这样的:

.. raw:: html

  <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="689px" viewBox="-0.5 -0.5 689 208" style="max-width:100%;max-height:208px;"><defs/><g><rect x="0" y="87" width="680" height="40" rx="6" ry="6" fill="#f8cecc" stroke="#b85450" pointer-events="none"/><g transform="translate(297.5,100.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="84" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 86px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">Vnpy cta runner</div></div></foreignObject><text x="42" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">Vnpy cta runner</text></switch></g><path d="M 126 160.63 L 126 127" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 126 165.88 L 122.5 158.88 L 126 160.63 L 129.5 158.88 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(77.5,140.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="96" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">调用事件响应函数</div></div></foreignObject><text x="48" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">调用事件响应函数</text></switch></g><rect x="110" y="167" width="120" height="40" fill="#dae8fc" stroke="#6c8ebf" pointer-events="none"/><g transform="translate(154.5,180.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="30" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 32px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">策略1</div></div></foreignObject><text x="15" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">策略1</text></switch></g><path d="M 334.47 83.84 L 200 7" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 339.03 86.45 L 331.22 86.01 L 334.47 83.84 L 334.69 79.93 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(227.5,40.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="84" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">接收行情和回单</div></div></foreignObject><text x="42" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">接收行情和回单</text></switch></g><path d="M 474.47 10.16 L 340 87" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 479.03 7.55 L 474.69 14.07 L 474.47 10.16 L 471.22 7.99 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(373.5,40.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="72" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">发送交易指令</div></div></foreignObject><text x="36" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">发送交易指令</text></switch></g><path d="M 222 136.37 L 222 167" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 222 131.12 L 225.5 138.12 L 222 136.37 L 218.5 138.12 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(185.5,142.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="72" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">调用下单函数</div></div></foreignObject><text x="36" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">调用下单函数</text></switch></g><path d="M 336 160.63 L 336 127" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 336 165.88 L 332.5 158.88 L 336 160.63 L 339.5 158.88 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(287.5,140.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="96" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">调用事件响应函数</div></div></foreignObject><text x="48" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">调用事件响应函数</text></switch></g><rect x="320" y="167" width="120" height="40" fill="#dae8fc" stroke="#6c8ebf" pointer-events="none"/><g transform="translate(364.5,180.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="30" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 32px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">策略2</div></div></foreignObject><text x="15" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">策略2</text></switch></g><path d="M 432 136.37 L 432 167" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 432 131.12 L 435.5 138.12 L 432 136.37 L 428.5 138.12 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(395.5,142.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="72" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">调用下单函数</div></div></foreignObject><text x="36" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">调用下单函数</text></switch></g><path d="M 556 160.63 L 556 127" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 556 165.88 L 552.5 158.88 L 556 160.63 L 559.5 158.88 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(507.5,140.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="96" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">调用事件响应函数</div></div></foreignObject><text x="48" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">调用事件响应函数</text></switch></g><rect x="540" y="167" width="120" height="40" fill="#dae8fc" stroke="#6c8ebf" pointer-events="none"/><g transform="translate(584.5,180.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="30" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 32px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">策略3</div></div></foreignObject><text x="15" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">策略3</text></switch></g><path d="M 652 136.37 L 652 167" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 652 131.12 L 655.5 138.12 L 652 136.37 L 648.5 138.12 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(615.5,142.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="72" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">调用下单函数</div></div></foreignObject><text x="36" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">调用下单函数</text></switch></g></g></svg>


而在 TqSdk 中, 策略程序并没有一个统一的基类. TqSdk只是提供一些行情和交易函数, 用户可以任意组合它们来实现自己的策略程序, 还是以双均线策略为例::

  '''
  双均线策略
  '''
  from tqsdk import TqApi, TqAuth, TqSim, TargetPosTask
  from tqsdk.tafunc import ma

  SHORT = 30
  LONG = 60
  SYMBOL = "SHFE.bu1912"

  api = TqApi(auth=TqAuth("快期账户", "账户密码"))

  data_length = LONG + 2
  klines = api.get_kline_serial(SYMBOL, duration_seconds=60, data_length=data_length)
  target_pos = TargetPosTask(api, SYMBOL)

  while True:
      api.wait_update()

      if api.is_changing(klines.iloc[-1], "datetime"):  # 产生新k线:重新计算SMA
          short_avg = ma(klines.close, SHORT)  # 短周期
          long_avg = ma(klines.close, LONG)  # 长周期

          # 均线下穿，做空
          if long_avg.iloc[-2] < short_avg.iloc[-2] and long_avg.iloc[-1] > short_avg.iloc[-1]:
              target_pos.set_target_volume(-3)
              print("均线下穿，做空")

          # 均线上穿，做多
          if short_avg.iloc[-2] < long_avg.iloc[-2] and short_avg.iloc[-1] > long_avg.iloc[-1]:
              target_pos.set_target_volume(3)
              print("均线上穿，做多")
            
以上代码文件单独运行, 即可执行一个双均线交易策略. 整个程序结构中, 用户代码作为调用方, TqSdk库代码作为被调用方, 每个策略是完全独立的. 结构是这样:

.. raw:: html

  <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="576px" viewBox="-0.5 -0.5 576 209" style="max-width:100%;max-height:209px;"><defs/><g><rect x="7" y="80" width="160" height="40" rx="6" ry="6" fill="#f8cecc" stroke="#b85450" pointer-events="none"/><g transform="translate(69.5,93.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="34" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 36px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">TqSdk<br /></div></div></foreignObject><text x="17" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">TqSdk&lt;br&gt;</text></switch></g><rect x="7" y="0" width="160" height="40" fill="#dae8fc" stroke="#6c8ebf" pointer-events="none"/><g transform="translate(71.5,13.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="30" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 32px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">策略1</div></div></foreignObject><text x="15" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">策略1</text></switch></g><path d="M 82.5 124.5 L 7 200" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 86.21 120.79 L 83.73 128.22 L 82.5 124.5 L 78.78 123.27 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(4.5,153.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="84" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">接收行情和回单</div></div></foreignObject><text x="42" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">接收行情和回单</text></switch></g><path d="M 162.5 195.5 L 87 120" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 166.21 199.21 L 158.78 196.73 L 162.5 195.5 L 163.73 191.78 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(90.5,153.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="72" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">发送交易指令</div></div></foreignObject><text x="36" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">发送交易指令</text></switch></g><path d="M 87 73.63 L 87 40" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 87 78.88 L 83.5 71.88 L 87 73.63 L 90.5 71.88 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(62.5,53.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="48" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">调用函数</div></div></foreignObject><text x="24" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">调用函数</text></switch></g><rect x="207" y="80" width="160" height="40" rx="6" ry="6" fill="#f8cecc" stroke="#b85450" pointer-events="none"/><g transform="translate(269.5,93.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="34" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 36px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">TqSdk<br /></div></div></foreignObject><text x="17" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">TqSdk&lt;br&gt;</text></switch></g><rect x="207" y="0" width="160" height="40" fill="#dae8fc" stroke="#6c8ebf" pointer-events="none"/><g transform="translate(271.5,13.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="30" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 32px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">策略2</div></div></foreignObject><text x="15" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">策略2</text></switch></g><path d="M 282.5 124.5 L 207 200" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 286.21 120.79 L 283.73 128.22 L 282.5 124.5 L 278.78 123.27 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(204.5,153.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="84" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">接收行情和回单</div></div></foreignObject><text x="42" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">接收行情和回单</text></switch></g><path d="M 362.5 195.5 L 287 120" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 366.21 199.21 L 358.78 196.73 L 362.5 195.5 L 363.73 191.78 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(290.5,153.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="72" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">发送交易指令</div></div></foreignObject><text x="36" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">发送交易指令</text></switch></g><path d="M 287 73.63 L 287 40" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 287 78.88 L 283.5 71.88 L 287 73.63 L 290.5 71.88 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(262.5,53.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="48" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">调用函数</div></div></foreignObject><text x="24" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">调用函数</text></switch></g><rect x="407" y="80" width="160" height="40" rx="6" ry="6" fill="#f8cecc" stroke="#b85450" pointer-events="none"/><g transform="translate(469.5,93.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="34" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 36px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">TqSdk<br /></div></div></foreignObject><text x="17" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">TqSdk&lt;br&gt;</text></switch></g><rect x="407" y="0" width="160" height="40" fill="#dae8fc" stroke="#6c8ebf" pointer-events="none"/><g transform="translate(471.5,13.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="30" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 12px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; width: 32px; white-space: nowrap; overflow-wrap: normal; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;">策略3</div></div></foreignObject><text x="15" y="12" fill="#000000" text-anchor="middle" font-size="12px" font-family="Helvetica">策略3</text></switch></g><path d="M 482.5 124.5 L 407 200" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 486.21 120.79 L 483.73 128.22 L 482.5 124.5 L 478.78 123.27 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(404.5,153.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="84" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">接收行情和回单</div></div></foreignObject><text x="42" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">接收行情和回单</text></switch></g><path d="M 562.5 195.5 L 487 120" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 566.21 199.21 L 558.78 196.73 L 562.5 195.5 L 563.73 191.78 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(490.5,153.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="72" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">发送交易指令</div></div></foreignObject><text x="36" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">发送交易指令</text></switch></g><path d="M 487 73.63 L 487 40" fill="none" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><path d="M 487 78.88 L 483.5 71.88 L 487 73.63 L 490.5 71.88 Z" fill="#000000" stroke="#000000" stroke-miterlimit="10" pointer-events="none"/><g transform="translate(462.5,53.5)"><switch><foreignObject style="overflow:visible;" pointer-events="all" width="48" height="12" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml" style="display: inline-block; font-size: 11px; font-family: Helvetica; color: rgb(0, 0, 0); line-height: 1.2; vertical-align: top; white-space: nowrap; text-align: center;"><div xmlns="http://www.w3.org/1999/xhtml" style="display:inline-block;text-align:inherit;text-decoration:inherit;background-color:#ffffff;">调用函数</div></div></foreignObject><text x="24" y="12" fill="#000000" text-anchor="middle" font-size="11px" font-family="Helvetica">调用函数</text></switch></g></g></svg>

TqSdk将每个策略作为一个独立进程运行, 这样就可以:

* 在运行多策略时可以充分利用多CPU的计算能力
* 每个策略都可以随时启动/停止/调试/修改代码, 而不影响其它策略程序的运行
* 可以方便的针对单个策略程序进行调试

在策略程序中, 用户代码可以随意调用 TqSdk 包中的任意函数, 这带来了更大的自由度, 比如:

* 在一个策略程序中使用多个合约或周期的K线数据, 盘口数据和Tick数据. 对于某些类型的策略来说这是很方便的
* 对多个合约的交易指令进行精细管理
* 管理复杂的子任务
* 方便策略程序跟其它库或框架集成

以一个套利策略的代码为例::

  '''
  价差回归
  当近月-远月的价差大于200时做空近月，做多远月
  当价差小于150时平仓
  '''
  api = TqApi(auth=TqAuth("快期账户", "账户密码"))
  quote_near = api.get_quote("SHFE.rb1910")
  quote_deferred = api.get_quote("SHFE.rb2001")
  # 创建 rb1910 的目标持仓 task，该 task 负责调整 rb1910 的仓位到指定的目标仓位
  target_pos_near = TargetPosTask(api, "SHFE.rb1910")
  # 创建 rb2001 的目标持仓 task，该 task 负责调整 rb2001 的仓位到指定的目标仓位
  target_pos_deferred = TargetPosTask(api, "SHFE.rb2001")

  while True:
      api.wait_update()
      if api.is_changing(quote_near) or api.is_changing(quote_deferred):
          spread = quote_near.last_price - quote_deferred.last_price
          print("当前价差:", spread)
          if spread > 250:
              print("目标持仓: 空近月，多远月")
              # 设置目标持仓为正数表示多头，负数表示空头，0表示空仓
              target_pos_near.set_target_volume(-1)
              target_pos_deferred.set_target_volume(1)
          elif spread < 200:
              print("目标持仓: 空仓")
              target_pos_near.set_target_volume(0)
              target_pos_deferred.set_target_volume(0)
            
在这个程序中, 我们同时跟踪两个合约的行情信息, 并为两个合约各创建一个调仓任务, 可以方便的实现套利策略


K线数据与指标计算
-------------------------------------------------
使用vn.py时, K线是由vn.py接收实时行情, 并在用户电脑上生成K线, 存储于用户电脑上的数据库中.

而在TqSdk中, K线数据和其它行情数据一样是由行情网关生成并推送的. 这带来了一些差别:

* 用户不再需要维护K线数据库. 用户电脑实时行情中断后, 也不再需要补历史数据
* 行情服务器生成K线时, 采用了按K线时间严格补全对齐的算法. 这与vn.py或其它软件有明显区别, 详见 https://www.shinnytech.com/blog/why-our-kline-different/
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
vn.py按照事件回调模型设计, 使用 CtaTemplate 的 on_xxx 回调函数进行行情数据和回单处理::

  class DoubleMaStrategy(CtaTemplate):
    def on_tick(self, tick: TickData):
      ...
    def on_bar(self, bar: BarData):
      ...
    def on_order(self, order: OrderData):
      pass
    def on_trade(self, trade: TradeData):
      self.put_event()
 

TqSdk则不使用事件回调机制. :py:meth:`~tqsdk.TqApi.wait_update` 函数设计用来获取任意数据更新, 像这样::

  api = TqApi(auth=TqAuth("快期账户", "账户密码"))
  ks = api.get_kline_serial("SHFE.cu1901", 60)
  
  while True:
    api.wait_update()       # <- 这个 wait_update 将尝试更新所有数据. 如果没有任何新信息, 程序会阻塞在这一句. 一旦有任意数据被更新, 程序会继续往下执行
    print(ks.close.iloc[-1])      # <- 最后一根K线的收盘价


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


图形界面
-------------------------------------------------
TqSdk 提供  :ref:`web_gui` 来供有图形化需求的用户使用:

* 策略运行时, 交易记录和持仓记录自动在行情图上标记, 可以快速定位跳转, 可以跨周期缩放定位
* 策略回测时, 提供回测报告/图上标记和对应的回测分析报告.
* 策略运行和回测信息自动保存, 可事后随时查阅显示

TqSdk配合web_gui使用时, 还支持自定义绘制行情图表, 像这样::

  api = TqApi(auth=TqAuth("快期账户","账户密码"), web_gui=True)
  # 获取 cu1905 和 cu1906 的日线数据
  klines = api.get_kline_serial("SHFE.cu1905", 86400)
  klines2 = api.get_kline_serial("SHFE.cu1906", 86400)

  # 算出 cu1906 - cu1905 的价差，并以折线型态显示在副图
  klines["dif"] = klines2["close"] - klines["close"]
  klines["dif.board"] = "DIF"
  klines["dif.color"] = 0xFF00FF00
  klines["dif.width"] = 3


  

回测
-------------------------------------------------
使用TqSdk开发的策略可以回测:

* 提供Tick及K线级别的回测. 
* TqSdk 允许在一个策略中使用任意多个数据序列. 回测框架将正确识别并处理这种情况.
* 回测前不需要准备数据

关于策略回测的详细说明, 请见 :ref:`backtest`


推荐学习步骤
-------------------------------
要学习使用 TqSdk, 推荐从 :ref:`quickstart` 开始
使用过程中有任何问题可以  `询问天勤 AI 助手！ <https://udify.app/chat/im02prcHNEOVbPAx/>`_ ,尝试帮助解答用户以下问题：

* 具体函数的详细介绍
* 根据具体需求或策略提供天勤实现的示例
* 天勤或 Python 报错的可能解决方案

