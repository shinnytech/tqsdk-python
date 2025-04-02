.. _tq_trading_unit:

============================
tqsdk 多策略使用手册
============================

概述
====
`tqsdk` 提供了 `TqTradingUnit` 账户类型，支持一个实盘账号在多个策略中交易，每个策略交易数据相互隔离

系统配置要求
============
- **Windows**: >= Windows 10
- **Linux**: >= Ubuntu 22.04

安装
====
使用 `TqTradingUnit` 账户类型需要安装 `tqsdk-zq` 包，用来初始化本地环境::

    pip install tqsdk-zq

对于 Windows 用户，还需要安装 Microsoft Visual C++ Redistributable，下载地址：
`Microsoft Redistributable <https://aka.ms/vs/17/release/vc_redist.x64.exe>`_

使用流程
========

1. **初始化本地环境**::

    tqsdk-zq init --kq-name=xx --kq-password=xx --web-port=xx

- 初始化完成后，控制台会输出多策略管理页的账户、密码以及网址
- 打开浏览器，访问控制台输出的网址

2. **打印多策略控制台地址**::

    tqsdk-zq web

- 如果机器重启或者网页打不开了，请执行以上命令
- 进程重新拉起后，控制台会输出管理页网址

3. **访问多策略管理页**:

- 在多策略管理页添加策略组
- 在策略组中添加后端账号
- 在策略组中添加前端号并入金

4. **使用 TqTradingUnit 登录前端账户**::

    from tqsdk import TqApi, TqTradingUnit, TqAuth

    account = TqTradingUnit(account_id="前端账户", tags=["铜品种策略", "套利策略"])
    api = TqApi(account, auth=TqAuth("快期账户", "账户密码"))

