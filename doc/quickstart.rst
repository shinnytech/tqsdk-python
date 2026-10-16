.. _quickstart:

十分钟快速入门
=================================================

.. include:: _includes/tqsdk_ai_agent_intro.rst

.. container:: tq-lead

   希望快速开始使用天勤量化（TqSdk）？本页按“安装 → 登录 → 行情 → K 线 → 下单 → 回测”的顺序，带你跑通第一套程序。

如果已经熟悉其他量化框架，可以先对照 :ref:`for_ctp_user` 或 :ref:`for_vnpy_user`，再回到本页上手。想先了解开发包的整体能力，可以阅读 :ref:`intro`。

.. note::

   前面的示例默认使用 :py:class:`~tqsdk.TqSim` 本地模拟账户。快期账户用于登录服务，期货资金账户用于实盘交易，两者请分别填写。实盘接入放在本页最后介绍。

.. _tqsdk_install:

1. 安装 TqSdk
-------------------------------------------------

先在电脑上安装 Python 3.9 或更高版本，Windows、macOS 和 Linux 均可使用。

打开命令行窗口（Windows 可使用“命令提示符”或 PowerShell），输入下面的命令，按回车安装 TqSdk：

.. code-block:: console

   pip install tqsdk

如果下载较慢，可以改用下面的国内镜像命令安装：

.. code-block:: console

   pip install tqsdk -i https://pypi.tuna.tsinghua.edu.cn/simple

安装完成后，继续下面的步骤，准备快期账户并运行第一个行情程序。安装遇到问题时，可查看 :doc:`qa`。

.. _quickstart_0:

2. 准备快期账户
-------------------------------------------------

在 `快期账户中心 <https://account.shinnytech.com/>`_ 注册账户。:py:class:`TqAuth <tqsdk.TqAuth>` 接收快期账户的手机号、用户名或邮箱，以及对应密码，详细说明见 :ref:`shinny_account`。

将后面的 ``"快期账户"`` 和 ``"账户密码"`` 替换为你的登录信息。文件不要命名为 ``tqsdk.py``，以免遮蔽已安装的开发包。

.. _quickstart_1:

3. 打印一次行情
-------------------------------------------------

把下面代码保存为 ``hello_tqsdk.py``，然后运行 ``python hello_tqsdk.py``：

.. code-block:: python
   :caption: hello_tqsdk.py · 打印螺纹钢合约行情

   from tqsdk import TqApi, TqAuth

   api = TqApi(auth=TqAuth("快期账户", "账户密码"))
   quote = api.get_quote("SHFE.rb2701")
   print(quote)
   api.close()

运行后，终端会打印一次行情内容，然后程序结束。``SHFE.rb2701`` 表示上期所螺纹钢 2027 年 1 月合约；如果运行时该合约已到期，请换成仍在交易的合约代码。

这几行代码依次完成：导入开发包、登录服务、获取行情、打印行情、关闭连接。:py:class:`quote <tqsdk.objs.Quote>` 中包含行情时间、最新价、买卖价等字段，例如 :py:attr:`quote.last_price <tqsdk.objs.Quote.last_price>` 就是最新价。

接下来：让行情持续更新
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

如果想持续查看行情，把 ``hello_tqsdk.py`` 改成下面这样，再次运行：

.. code-block:: python
   :caption: hello_tqsdk.py · 持续打印行情时间和最新价

   from tqsdk import TqApi, TqAuth

   api = TqApi(auth=TqAuth("快期账户", "账户密码"))
   quote = api.get_quote("SHFE.rb2701")

   while True:
       api.wait_update()
       print(quote.datetime, quote.last_price)

``while True`` 让程序反复执行循环中的两行代码：

1. :py:meth:`api.wait_update() <tqsdk.TqApi.wait_update>` 等待业务数据更新，收到数据后更新 :py:class:`quote <tqsdk.objs.Quote>` 等对象，再继续往下执行。
2. ``print(...)`` 读取并打印此时的行情时间和最新价，然后回到下一轮等待。

:py:class:`quote <tqsdk.objs.Quote>` 是会更新的行情引用，因此 :py:meth:`get_quote() <tqsdk.TqApi.get_quote>` 只需在循环外调用一次。持续调用 :py:meth:`wait_update() <tqsdk.TqApi.wait_update>`，才能接收后续数据；只反复执行 ``print()`` 不会刷新行情。

**你会看到什么：** 收到业务数据更新后，终端打印行情时间和最新价。非交易时段可能暂时没有新输出；这不一定是程序出错。按 ``Ctrl+C`` 停止这个持续运行的示例。退出时释放连接的完整写法见 :ref:`framework`。

.. tip::

   :py:meth:`wait_update() <tqsdk.TqApi.wait_update>` 也会发送请求、推进后台任务。它返回并不意味着每个订阅都更新了，所以打印的最新价可能与上次相同。只想在这份行情变化时处理，可以用 :py:meth:`api.is_changing(quote) <tqsdk.TqApi.is_changing>` 判断。完整机制见 :ref:`framework`。

.. _quickstart_2:

4. 读取 K 线
-------------------------------------------------

:py:meth:`get_kline_serial() <tqsdk.TqApi.get_kline_serial>` 返回持续更新的 :py:class:`pandas.DataFrame <pandas.DataFrame>`。沿用上面的固定合约，下面单独运行一个简单程序，请求它的 10 秒 K 线：

.. code-block:: python

   from tqsdk import TqApi, TqAuth

   api = TqApi(auth=TqAuth("快期账户", "账户密码"))
   klines = api.get_kline_serial("SHFE.rb2701", 10)

   while True:
       api.wait_update()
       print("最后一根 K 线的收盘价：", klines.close.iloc[-1])

``iloc[-1]`` 表示最后一根 K 线，其收盘价在形成过程中仍会变化。需要上一根已完成 K 线时，使用 ``iloc[-2]``。更多用法见 :ref:`tutorial-t30` 与 :ref:`ta`。

.. _quickstart_4:
.. _quickstart_5:

5. 用目标持仓运行模拟策略
-------------------------------------------------

先用 :py:class:`~tqsdk.TargetPosTask` 表达“希望持有多少手”，由它管理下单和撤单。下面程序在启动时选择螺纹钢当前主力合约：上一根收盘价高于最近 15 根已完成 K 线的均价时，目标为多头 1 手；否则目标为空仓。

这里开始使用 ``KQ.m@SHFE.rb``，它是螺纹钢的主连代码，用来查看当前主力合约行情。**主连本身不能下单**，所以先通过 :py:attr:`quote.underlying_symbol <tqsdk.objs.Quote.underlying_symbol>` 取得对应的实际合约，再用于 K 线订阅和模拟交易。合约代码详见 :ref:`mddatas`。

.. code-block:: python
   :caption: ma_sim.py · 在本地模拟账户运行

   from tqsdk import TqApi, TqAuth, TargetPosTask
   from tqsdk.tafunc import ma

   api = TqApi(auth=TqAuth("快期账户", "账户密码"))
   quote = api.get_quote("KQ.m@SHFE.rb")
   symbol = quote.underlying_symbol  # 主力对应的实际合约
   klines = api.get_kline_serial(symbol, 60)
   target = TargetPosTask(api, symbol)

   while True:
       api.wait_update()
       if api.is_changing(klines.iloc[-1], "datetime"):  # 新 K 线开始
           ma15 = ma(klines.close, 15)  # 15 周期均线
           if klines.close.iloc[-2] > ma15.iloc[-2]:  # 用上一根已完成 K 线判断
               target.set_target_volume(1)  # 目标：多头 1 手
           else:
               target.set_target_volume(0)  # 目标：空仓

**这里的 1 是最终目标持仓，不是每次再买 1 手。** 条件持续满足时，反复设置同一个目标不会把目标累加。调用后仍需继续 :py:meth:`wait_update() <tqsdk.TqApi.wait_update>`，调仓任务才会运行。

:py:func:`~tqsdk.tafunc.ma` 直接计算均线，``15`` 表示每次用连续 15 根 K 线的收盘价求平均。``iloc[-2]`` 取倒数第 2 项，也就是上一根已完成 K 线；收盘价和均线都取这个位置，就不会把最后一根尚未完成的 K 线用于判断。

此教学示例只在启动时选择一次合约，不处理跨交易日换月。它用于说明程序结构，策略效果需要另行评估。目标持仓详见 :ref:`targetpostask`，跨品种示例见 :ref:`tutorial-t80`。

.. _quickstart_3:

6. 了解账户、下单与撤单
-------------------------------------------------

下面用几个短片段介绍账户和委托接口。请单独创建一个本地模拟会话，不要把这些片段加到前面的目标持仓程序中：

.. code-block:: python

   from tqsdk import TqApi, TqAuth

   api = TqApi(auth=TqAuth("快期账户", "账户密码"))
   symbol = api.get_quote("KQ.m@SHFE.rb").underlying_symbol

通过 :py:meth:`~tqsdk.TqApi.get_account` 和 :py:meth:`~tqsdk.TqApi.get_position` 获取
:py:class:`account <tqsdk.objs.Account>` 和 :py:class:`position <tqsdk.objs.Position>` 引用，并读取字段：

.. code-block:: python

   account = api.get_account()
   position = api.get_position(symbol)
   print("可用资金：", account.available, "净持仓：", position.pos)

使用 :py:meth:`~tqsdk.TqApi.insert_order` 发送一笔限价委托，得到 :py:class:`order <tqsdk.objs.Order>` 引用，并在循环中查看状态：

.. code-block:: python

   order = api.insert_order(symbol, "BUY", "OPEN", volume=1, limit_price=3000)
   while order.status == "ALIVE":
       api.wait_update()
       print("委托状态：", order.status, "未成交手数：", order.volume_left)

这里的 ``3000`` 只是演示价格，不保证成交；委托没有成交时，上面的循环会持续等待。需要演示 :py:meth:`~tqsdk.TqApi.cancel_order` 撤单时，可以在 :py:meth:`insert_order() <tqsdk.TqApi.insert_order>` 之后使用下面的片段，替换上面的等待循环：

.. code-block:: python

   api.cancel_order(order)
   while order.status == "ALIVE":
       api.wait_update()
   print("委托结束：", order.last_msg)

下单和撤单后都需要继续调用 :py:meth:`wait_update() <tqsdk.TqApi.wait_update>` 接收结果。完成这个短任务后调用 :py:meth:`api.close() <tqsdk.TqApi.close>`；需要限制等待时间时，参考 :doc:`qa` 中的超时示例。

.. note::

   :py:meth:`insert_order() <tqsdk.TqApi.insert_order>` 返回的是委托引用，不是成交确认。``FINISHED`` 表示委托结束，也可能是撤单或拒单；用 ``volume_orign - volume_left`` 了解已成交数量，用 :py:attr:`last_msg <tqsdk.objs.Order.last_msg>` 查看提示。不要同时对同一合约使用手动下单和目标持仓任务，避免相互干扰。

更完整的委托生命周期见 :ref:`trade`、:ref:`tutorial-t40`。

.. _quickstart_backtest:

7. 把策略放进历史回测
-------------------------------------------------

回测沿用前面的程序结构，只需要在创建 API 时传入 :py:class:`~tqsdk.TqBacktest`。下面先用一个简单例子观察历史 K 线如何更新：

.. code-block:: python
   :caption: kline_backtest.py · 查看历史 K 线

   from datetime import date
   from tqsdk import TqApi, TqAuth, TqBacktest, BacktestFinished

   api = TqApi(
       backtest=TqBacktest(start_dt=date(2025, 3, 3), end_dt=date(2025, 3, 7)),
       auth=TqAuth("快期账户", "账户密码"),
   )
   klines = api.get_kline_serial("SHFE.rb2505", 60)
   try:
       while True:
           api.wait_update()
           print("历史 K 线收盘价：", klines.close.iloc[-1])
   except BacktestFinished:
       print("回测结束")
   api.close()

:py:exc:`~tqsdk.exceptions.BacktestFinished` 表示历史数据回放结束，示例用 ``try / except`` 接住这个结束通知，再关闭 API。**合约的存续期需要覆盖回测区间**，因此示例合约和历史日期应一起调整。

回测仍需登录服务并获取历史数据，具体数据权限以账户为准。需要回测自己的交易逻辑时，把行情示例中的处理部分换成策略；完整说明与图形化报告见 :ref:`backtest`、:ref:`web_gui`。

.. _sim_trading:

选择适合的模拟账户
-------------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - 账户类型
     - 记录保存在哪里
     - 适合什么场景
   * - :py:class:`TqSim() <tqsdk.TqSim>`
     - 当前程序内；默认不跨进程保存
     - 入门、临时模拟、历史回测
   * - :py:class:`TqKq() <tqsdk.TqKq>`
     - 快期模拟服务；可在快期客户端查看
     - 希望持续跟踪模拟账户
   * - :py:class:`TqAccount(...) <tqsdk.TqAccount>`
     - 期货公司的实盘资金账户
     - 完成验证后的实盘接入

使用快期模拟账户：

.. code-block:: python

   from tqsdk import TqApi, TqAuth, TqKq

   api = TqApi(TqKq(), auth=TqAuth("快期账户", "账户密码"))
   # 订阅数据，并持续调用 api.wait_update()。
   # 程序退出时调用 api.close()。

如果省略账户参数，:py:class:`TqApi <tqsdk.TqApi>` 默认使用 :py:class:`TqSim <tqsdk.TqSim>`。这类模拟记录不会出现在快期 APP 等客户端。详情见 :ref:`shinny_account`。

.. _real_trading:

了解实盘接入
-------------------------------------------------

实盘需要显式传入 :py:class:`~tqsdk.TqAccount`。下方仅展示配置，填写的是期货公司提供的资金账号与交易密码：

.. code-block:: python

   from tqsdk import TqApi, TqAuth, TqAccount

   api = TqApi(
       TqAccount("期货公司名称", "期货资金账号", "期货交易密码"),
       auth=TqAuth("快期账户", "快期账户密码"),
   )

期货公司名称、接入要求与权限说明见 :ref:`trade`、:ref:`profession`。支持情况可在 `期货公司列表 <https://www.shinnytech.com/blog/tq-support-broker/>`_ 查询。

下一步
-------------------------------------------------

* **学习运行机制：** :ref:`framework`，理解数据引用和 :py:meth:`wait_update() <tqsdk.TqApi.wait_update>`。
* **选择完整示例：** :ref:`demo`，从行情、K 线和交易基础逐步深入。
* **遇到问题：** :doc:`qa`，按症状排查安装、登录、数据和委托问题。
* **使用 AI 开发：** :ref:`tqsdk_skills`，让 AI 先读取 TqSdk 技能包。
* **从其他框架迁移：** :ref:`for_ctp_user`、:ref:`for_vnpy_user`。
* **观看入门视频：** `TqSdk 学习视频 <https://www.shinnytech.com/tqsdkquickstart/>`_。
