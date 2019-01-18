Introduction
=================================================

TqSdk 是一套依托 `DIFF协议 (Differential Information Flow for Finance) <http://doc.shinnytech.com/diff/latest/index.html>`_ 的开源 python 框架. 它支持用户使用较少的工作量构建量化交易或分析程序.

与其它 python 框架相比, TqSdk 致力于在以下几方面为用户提供价值:

1. 用最低部署运行成本实现完整功能栈

    * 无需用户部署维护历史数据库, 直接提供所有期货品种的报价盘口, K线数据, Tick序列的实时推送
    * 支持通过CTP接口发送交易指令

2. 鼓励 Quick & Simple 的用户代码风格

    * 策略代码按线性逻辑编写, 避免复杂的回调函数/状态机
    * 策略运行中用到的所有数据都在内存中, 且不需读写锁, 避免读写过程引入延时
    * 所有行情及交易接口都返回 object refrence, 一次调用获取, 内容可自动更新
    * 统一易用的超时及异常管理机制

3. 可通过搭配天勤终端为用户代码提供支持, 避免用户在非核心功能上花费时间精力

    * 通过历史复盘及模拟交易功能, 将用户程序带回特定历史环境测试
    * 在天勤终端中构建自定义组合, 并获得组合的报价和K线数据
    * 提供委托单/成交/持仓情况监控的UI界面


TqSdk 主要包括的组件如下:

* api: 一个结合了网络通讯和全内存数据管理的接口, 提供了基础的行情和交易功能
* lib: 基于api构建的常用功能函数库(例如: 目标持仓模型)
* sim: 提供模拟交易功能, 并可输出交易报告
* backtest.py: 提供回测功能, 支持逐tick回测


Install
-------------------------------------------------
系统要求:

* Windows 或 Linux
* Python 3.6+

直接使用pip安装::

    pip install tqsdk

或从github下载 tqsdk::

    git clone https://github.com/shinnytech/tqsdk-python.git
    python setup.py install

另外如果希望使用自定义组合, 历史复盘等 **天勤终端** 提供的功能, 可以参见: `与天勤终端配合工作 <http://doc.shinnytech.com/pysdk/latest/tq/index.html>`_


Run
-------------------------------------------------
运行demo目录下的任一程序::

    python demo/t10.py

注意: TqSdk 使用了 python3 的原生协程和异步通讯库 asyncio，部分 IDE 不支持 asyncio，例如:

* spyder: 详见 https://github.com/spyder-ide/spyder/issues/7096
* jupyter: 详见 https://github.com/jupyter/notebook/issues/3397

可以直接运行示例代码(例如: "python demo/t10.py")，或使用支持 asyncio 的 IDE (例如: pycharm)
