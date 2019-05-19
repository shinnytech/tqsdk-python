<p align="center">
  <img src ="./doc/logo.png"/>
</p>
<p align="center">
    <img src ="https://img.shields.io/badge/version-0.9.2-blueviolet.svg"/>
    <img src ="https://img.shields.io/badge/platform-windows|linux|macos-green.svg"/>
    <img src ="https://img.shields.io/badge/python-3.6+-blue.svg" />
    <img src ="https://img.shields.io/github/license/shinnytech/tqsdk-python.svg?color=orange"/>
</p>

TqSdk 量化交易策略程序开发包
====================================
TqSdk 是一个由[信易科技](https://www.shinnytech.com)发起并贡献主要代码的开源 python 库. 
依托[快期多年积累成熟的交易及行情服务器体系](https://www.shinnytech.com/diff), TqSdk 支持用户使用极少的代码量构建各种类型的量化交易策略程序, 
并提供包含 历史数据-实时数据-开发调试-策略回测-模拟交易-实盘交易-运行监控-风险管理 的全套解决方案

``` {.sourceCode .python}
>>> from tqsdk import TqApi
>>> r = requests.get('https://api.github.com/user', auth=('user', 'pass'))
>>> r.status_code
200
>>> r.headers['content-type']
'application/json; charset=utf8'
>>> r.encoding
'utf-8'
>>> r.text
u'{"type":"User"...'
>>> r.json()
{u'disk_usage': 368627, u'private_gists': 484, ...}
```

要快速了解如何使用TqSdk, 可以访问我们的 [十分钟快速入门指南](https://doc.shinnytech.com/tqsdk/latest/quickstart.html).


Architecture
---------------
<img alt="系统架构图" src="https://raw.githubusercontent.com/shinnytech/tqsdk-python/doc/doc/arch.svg?sanitize=true">

* [行情网关 (Open Md Gateway)](https://github.com/shinnytech/open-md-gateway) 负责提供实时行情和历史数据
* [交易中继网关 (Open Trade Gateway)](https://github.com/shinnytech/open-trade-gateway) 负责连接到期货公司交易系统
* 这两个网关统一以 [Diff协议](https://doc.shinnytech.com/diff/latest) 对下方提供服务
* TqSdk按照Diff协议连接到行情网关和交易中继网关, 实现行情和交易功能


Features
---------------
TqSdk 提供的功能可以支持从简单到复杂的各类策略程序.

* 提供当前所有可交易合约从上市开始的全部Tick数据和K线数据
* 支持数十家期货公司的实盘交易
* 支持模拟交易
* 支持Tick级和K线级回测
* 支持复杂策略回测
* 提供近百个技术指标函数
* 无强制框架结构, 支持任意复杂度的策略, 允许在一个交易策略程序中使用使用多个品种的K线/实时行情并交易多个品种


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

	
Gui
-------------------------------------------------
TqSdk本身不包含任何GUI组件. 免费的 [天勤软件](https://www.shinnytech.com/tianqin) 可以与TqSdk配合使用, 提供完整的图形界面.


