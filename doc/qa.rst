.. _faq:

常见问题与支持
=================================================

先按症状定位问题，再查看对应指南。提交问题时附上 SDK 版本、运行方式和完整异常，可以减少来回确认。

安装后仍提示找不到 tqsdk
-------------------------------------------------

通常先检查“安装用的 Python”和“运行脚本的 Python”是否一致。在运行脚本的同一终端或 IDE 解释器中执行：

.. code-block:: console

   python -m pip show tqsdk
   python -c "import sys, tqsdk; print(sys.executable); print(tqsdk.__version__); print(tqsdk.__file__)"

确认解释器、版本和导入路径正确，并检查当前文件或文件夹是否误命名为 ``tqsdk.py`` 或 ``tqsdk``。重新安装的步骤见 :ref:`tqsdk_install`。

快期账户与期货资金账户有什么区别
-------------------------------------------------

:py:class:`TqAuth <tqsdk.TqAuth>` 填快期账户，用于登录 TqSdk 服务；:py:class:`TqAccount <tqsdk.TqAccount>` 填期货公司、资金账号与交易密码，用于实盘账户接入。不要将两套账号混填。见 :ref:`shinny_account` 与 :ref:`trade`。

程序在 wait_update() 停住了
-------------------------------------------------

:py:meth:`wait_update() <tqsdk.TqApi.wait_update>` 会等待业务数据更新；没有新数据时等待是正常行为。先确认合约仍有效、处于交易时段、连接没有报错。需要等待截止时间时，使用绝对时间戳：

.. code-block:: python

   import time

   # 放在已经创建 api 的程序中。
   updated = api.wait_update(deadline=time.time() + 10)
   if not updated:
       print("本次等待期间没有业务数据更新")

返回 ``False`` 只表示本次到达截止时间仍没有业务数据更新，不能单独据此断定连接已断开。详见 :py:meth:`~tqsdk.TqApi.wait_update`。

行情为 NaN、K 线不更新
-------------------------------------------------

* **数据未就绪：** 初始化时部分字段可能为 ``NaN``；继续驱动更新并检查所需字段。
* **合约已到期：** 老示例里的固定月份合约不一定还在交易。看行情可以先使用 ``KQ.m@SHFE.rb`` 等主连代码。
* **更新判断不同：** :py:meth:`is_changing(klines.iloc[-1], "datetime") <tqsdk.TqApi.is_changing>` 只在新 K 线开始时触发，不会随每次最新价变化触发。
* **历史区间不匹配：** 回测时检查合约存续期与历史数据权限。

合约代码、主连与历史数据说明见 :ref:`mddatas`。

为什么模拟持仓在快期 APP 中看不到
-------------------------------------------------

默认的 :py:class:`TqSim <tqsdk.TqSim>` 是程序内的本地模拟账户，记录不会同步到快期客户端。希望在快期 APP、快期专业版等客户端查看模拟持仓时，使用 :py:class:`TqKq <tqsdk.TqKq>`。两种账户的区别和初始化方式见 :ref:`sim_trading`。

下单后没有成交，或者状态是 FINISHED
-------------------------------------------------

:py:meth:`insert_order() <tqsdk.TqApi.insert_order>` 返回委托引用，下单和撤单请求需要后续 :py:meth:`wait_update() <tqsdk.TqApi.wait_update>` 推进。委托未成交还可能与价格、交易时段、资金或拒单有关，请检查 :py:attr:`order.last_msg <tqsdk.objs.Order.last_msg>` 与 :py:attr:`order.volume_left <tqsdk.objs.Order.volume_left>`。

``FINISHED`` 表示委托生命周期结束，并不等于全部成交；成交数量为 ``volume_orign - volume_left``。完整说明见 :ref:`trade`。

回测报 BacktestFinished 是失败了吗
-------------------------------------------------

:py:exc:`~tqsdk.exceptions.BacktestFinished` 是回测正常结束的通知。在循环外捕获它，退出前关闭 API，再按需读取模拟账户统计。完整可复制示例见 :ref:`quickstart_backtest`。

到用户论坛提问
-------------------------------------------------

如果仍未解决，前往 `天勤用户论坛 <https://forum.shinnytech.com/>`_ 搜索相同问题或发帖。建议一起提供：

1. Python 与 TqSdk 版本、操作系统。
2. 运行模式：实时行情、本地模拟、快期模拟、历史回测或实盘。
3. 相关合约、回测日期、你期望的结果与实际结果。
4. 可复现的最小代码和完整异常堆栈，移除账号、密码、令牌及其他个人信息。

产品权限与接入问题请结合 :ref:`profession`、:ref:`enterprise` 查看。
