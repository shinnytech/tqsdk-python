.. _entry:

策略程序的多种入口场景
====================================================
基于TqSdk开发的策略程序可能在多种场景下运行

用户自己在独立python环境下执行策略程序
----------------------------------------------------
一种常见的运行方式是用户自己运行python策略程序, 象这样::

    $python3 my_prog.py

在这种场景下，用户需要在TqApi创建时提供必要的参数

TqApi 独立运行模拟交易
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
创建 TqApi 实例时传入 TqSim ::

    from tqsdk import TqApi, TqAuth, TqSim
    api = TqApi(TqSim(), auth=TqAuth("快期账户", "账户密码"))

或者不填其他参数, 默认为使用TqSim::

    api = TqApi(auth=TqAuth("快期账户", "账户密码"))


TqApi 独立运行实盘交易
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
创建 TqApi 实例时传入 TqAccount ::

    from tqsdk import TqApi, TqAuth, TqAccount
    api = TqApi(TqAccount("H海通期货", "022631", "123456"), auth=TqAuth("快期账户", "账户密码"))

特别的, 如果需要连接到期货公司的特定服务器, 可以在 TqAccount 中指定::

    api = TqApi(TqAccount("H海通期货", "022631", "123456", front_broker="8888", front_url="tcp://134.232.123.33:41205"), auth=TqAuth("快期账户", "账户密码"))

如果要连接到自己架设的交易网关, 可以使用::

    api = TqApi(TqAccount("H海通期货", "022631", "123456"), url="ws://202.33.21.34:7878/", auth=TqAuth("快期账户", "账户密码"))


TqApi 独立运行回测
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
创建 TqApi 实例时传入 TqBacktest ::

    from tqsdk import TqApi, TqAuth, TqSim, TqBacktest
    api = TqApi(TqSim(), backtest=TqBacktest(start_dt=date(2018, 5, 1), end_dt=date(2018, 10, 1)), auth=TqAuth("快期账户", "账户密码"))


由天勤拉起策略进程
----------------------------------------------------
策略程序由天勤拉起执行时, TqApi始终使用默认构造函数, 由天勤提供命令行参数设定策略程序运行方式. 命令行参数包括这些:

* _action : run/backtest/mdreplay, 指定运行方式
* _tq_pid : int, 天勤进程ID. 策略进程会监控天勤进程的存活情况, 天勤进程退出时所有由天勤创建的策略进程都会自行终止
* _tq_url : str, 天勤ws入口. 策略进程通过此端口与天勤通讯

当 _action == run 时, 策略程序按正常交易模式运行, 其它参数:

* _broker_id : str, 期货公司代码
* _account_id : str, 用户账号
* _password : str, 用户密码

当 _action == backtest 时, 策略程序按回测模式运行, 其它参数:

* _dt_start : YYYYMMDD, 回测起始日期
* _dt_end : YYYYMMDD, 回测结束日期

当 _action == mdreplay 时, 策略程序按复盘模式运行, 其它参数:

* _ins_url : url, 合约服务地址
* _md_url : url, 行情服务地址


天勤发起实盘运行(含快期模拟)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
天勤通过命令行参数传递交易账户信息给策略进程::

    $ python3 my_prog.py --_action=run --_tq_pid=3233 --_tq_url=ws://127.0.0.1:7777 --_broker_id=快期模拟 --_account_id=13012345678 --_password=123456


天勤发起回测
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
天勤通过命令行参数传递交易账户信息给策略进程::

    $ python3 my_prog.py --_action=backtest --_tq_pid=3233 --_tq_url=ws://127.0.0.1:7777 --_dt_start=20180101 --_dt_end=20180630


天勤发起复盘
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
天勤先创建好复盘服务器, 再传递::

    $ python3 my_prog.py --_action=mdreplay --_tq_pid=3233 --_tq_url=ws://127.0.0.1:7777 --_md_url=ws://239.12.212.34:43232/... --ins_url=http://123.23.12.34/...


更复杂的情形
----------------------------------------------------

将独立运行的策略进程连接到天勤作监控
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
暂未支持


