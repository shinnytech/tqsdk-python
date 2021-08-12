<p align="center">
  <img src ="https://raw.githubusercontent.com/shinnytech/tqsdk-python/master/doc/images/tqsdk_new_logo.png"/>
</p>
<p align="center">
    <img src ="https://img.shields.io/pypi/v/tqsdk?color=blueviolet">
    <img src ="https://img.shields.io/badge/platform-windows|linux|macos-green.svg"/>
    <img src ="https://img.shields.io/badge/python-3.6+-blue.svg" />
    <img src ="https://img.shields.io/pypi/dm/tqsdk?color=yellowgreen">
    <img src ="https://img.shields.io/github/license/shinnytech/tqsdk-python.svg?color=orange"/>
</p>

TqSdk 天勤量化交易策略程序开发包
====================================
TqSdk 是一个由[信易科技](https://www.shinnytech.com)发起并贡献主要代码的开源 python 库. 
依托[快期多年积累成熟的交易及行情服务器体系](https://www.shinnytech.com/diff), TqSdk 支持用户使用极少的代码量构建各种类型的量化交易策略程序, 
并提供包含期货、期权、股票的 历史数据-实时数据-开发调试-策略回测-模拟交易-实盘交易-运行监控-风险管理 全套解决方案.

``` {.sourceCode .python}
from tqsdk import TqApi, TqAuth, TqAccount, TargetPosTask

api = TqApi(TqAccount("H海通期货", "4003242", "123456"), auth=TqAuth("信易账户", "账户密码"))      # 创建 TqApi 实例, 指定交易账户
q_1910 = api.get_quote("SHFE.rb1910")                         # 订阅近月合约行情
t_1910 = TargetPosTask(api, "SHFE.rb1910")                    # 创建近月合约调仓工具
q_2001 = api.get_quote("SHFE.rb2001")                         # 订阅远月合约行情
t_2001 = TargetPosTask(api, "SHFE.rb2001")                    # 创建远月合约调仓工具

while True:
  api.wait_update()                                           # 等待数据更新
  spread = q_1910["last_price"] - q_2001["last_price"]        # 计算近月合约-远月合约价差
  print("当前价差:", spread)
  if spread > 250:
    print("价差过高: 空近月，多远月")                            
    t_1910.set_target_volume(-1)                              # 要求把1910合约调整为空头1手
    t_2001.set_target_volume(1)                               # 要求把2001合约调整为多头1手
  elif spread < 200:
    print("价差回复: 清空持仓")                               # 要求把 1910 和 2001合约都调整为不持仓
    t_1910.set_target_volume(0)
    t_2001.set_target_volume(0)
```

要快速了解如何使用TqSdk, 可以访问我们的 [十分钟快速入门指南](https://doc.shinnytech.com/tqsdk/latest/quickstart.html).


Architecture
---------------
<img alt="系统架构图" src="https://raw.githubusercontent.com/shinnytech/tqsdk-python/master/doc/arch.svg?sanitize=true">

* [行情网关 (Open Md Gateway)](https://github.com/shinnytech/open-md-gateway) 负责提供实时行情和历史数据
* [交易中继网关 (Open Trade Gateway)](https://github.com/shinnytech/open-trade-gateway) 负责连接到期货公司交易系统
* 这两个网关统一以 [Diff协议](https://doc.shinnytech.com/diff/latest) 对下方提供服务
* TqSdk按照Diff协议连接到行情网关和交易中继网关, 实现行情和交易功能


Features
---------------
TqSdk 提供的功能可以支持从简单到复杂的各类策略程序.

* **公司级数据运维**，提供当前所有可交易合约从上市开始的 **全部Tick数据和K线数据**
* 支持市场上90%的期货公司 **实盘交易**
* 支持 **模拟交易**
* 支持 **Tick级和K线级回测**, 支持 **复杂策略回测**
* 提供近百个 **技术指标函数及源码**
* 用户无须建立和维护数据库, 行情和交易数据全在 **内存数据库** , 无访问延迟
* 优化支持 **pandas** 和 **numpy** 库
* 无强制框架结构, 支持任意复杂度的策略, 在一个交易策略程序中使用多个品种的K线/实时行情并交易多个品种
* 配合开发者支持工具，能够进行**交易信号打点**，支持**自定义指标画图**

Installation
-------------------------------------------------
TqSdk 仅支持 Python 3.6 及更高版本. 要安装 TqSdk, 可使用 pip:

``` {.sourceCode .bash}
$ pip install tqsdk
```


Documentation
-------------------------------------------------
在线阅读HTML版本文档: https://doc.shinnytech.com/tqsdk/latest

在线问答社区: https://www.shinnytech.com/qa

知乎账户【天勤量化】：https://www.zhihu.com/org/tian-qin-liang-hua/activities

用户交流QQ群: **619870862** (目前只允许给我们点过STAR的同学加入, 加群时请提供github用户名)

	
Gui
-------------------------------------------------
TqSdk本身自带的web_gui功能，简单一行参数即可支持调用图形化界面，详情参考[web_gui](https://doc.shinnytech.com/pysdk/latest/usage/web_gui.html) 
<img alt="TqSdk web_gui" src="https://raw.githubusercontent.com/shinnytech/tqsdk-python/master/doc/images/web_gui_backtest.png">

About us
-------------------------------------------------
[信易科技](https://www.shinnytech.com) 是专业的期货软件供应商和交易所授权行情服务商. 旗下的快期系列产品已为市场服务超过10年. TqSdk 是[公司开源计划](https://www.shinnytech.com/diff)的一部分. 

