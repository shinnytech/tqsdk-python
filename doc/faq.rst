.. _faq:

常见问题
====================================================

.. _faq-prepare:

运行 TqSdk 的系统要求是什么？
--------------------------------------------------------------------------------------------------------
操作系统: Windows/Linux

Python 3.6+

另外可搭配 **天勤终端** 使用, **天勤终端** 提供了 `自定义组合`_ 、`历史复盘`_ 等功能，`天勤客户端下载地址`_ 。


.. _faq-pip-install-files-location:

运行 `pip install tqsdk` 之后，如何找到安装的文件？
--------------------------------------------------------------------------------------------------------

可以运行以下命令行查看安装包的位置：

.. code-block:: bash

    pip show --files tqsdk

.. figure:: _static/faq1.png
    :width: 500px
    :figwidth: 80%
    :alt: 示例t10截图

安装包位于 `Location` 位置的 `tqsdk/` 目录下，所有源文件都在这里，`tqsdk/demo/` 下是所有示例文件。

参考链接： `pip文档`_


.. _faq-event-loop-already-running:

运行示例代码后提示 "RuntimeError: Cannot run the event loop while another loop is running"
--------------------------------------------------------------------------------------------------------

TqSdk 使用了 python3 的原生协程和异步通讯库 asyncio，部分 IDE 不支持 asyncio，例如:
 * spyder: 详见 https://github.com/spyder-ide/spyder/issues/7096
 * jupyter: 详见 https://github.com/jupyter/notebook/issues/3397

可以直接运行示例代码(例如: "python demo/t10.py")，或使用支持 asyncio 的 IDE (例如: pycharm)


.. _faq-CLOSE-CLOSETODAY:

关于平今平昨怎么处理？
--------------------------------------------------------------------------------------------------------

+ 直接使用 api.insert_order 下单，在 offset 字段上可以直接指定平今平昨（`CLOSETODAY`/`CLOSE`）。

.. literalinclude:: ../tqsdk/demo/t41.py
    :caption: python demo/t41.py
    :language: python
    :linenos:


+ 使用 TargetPosTask，目标持仓模型下单，通过参数 `offset_priority` 设置平今平昨优先级。

.. literalinclude:: ../tqsdk/demo/t71.py
    :caption: python demo/t71.py
    :language: python
    :linenos:


.. _faq-backtesting:

如何回测策略？
--------------------------------------------------------------------------------------------------------

在创建 TqApi 实例时可以传入 TqBacktest 启用回测功能

.. literalinclude:: ../tqsdk/demo/backtest.py
    :caption: python demo/backtest.py
    :language: python
    :linenos:


.. _faq-sim:

模拟交易的成交规则是什么？
--------------------------------------------------------------------------------------------------------
限价单要求报单价格达到或超过对手盘价格才能成交, 成交价为报单价格, 如果没有对手盘(涨跌停)则无法成交

市价单使用对手盘价格成交, 如果没有对手盘(涨跌停)则自动撤单

模拟交易不会有部分成交的情况, 要成交就是全部成交


.. _faq-real:

如何进行实盘交易？
--------------------------------------------------------------------------------------------------------

在创建 TqApi 实例时传入 TqAccount 即可进行实盘交易::

    api = TqApi(TqAccount("H海通期货", "022631", "123456"))

如果想连接天勤终端进行实盘交易可以只填写帐号，并先在天勤终端内登录交易::

    api = TqApi("022631")


.. _faq-disconnect:

网络断线怎么处理？
--------------------------------------------------------------------------------------------------------
TqSdk 会自动重连服务器, 不需要特殊处理。但是断线时报的单可能会丢掉，因此应尽量确保网络稳定


.. _faq-debug:

我想在周末或晚上开发交易程序, 但是行情不跳, 有什么办法么?
--------------------------------------------------------------------------------------------------------
您可以使用天勤终端提供的复盘功能：

 * 从 `天勤客户端下载地址`_ 下载并安装 **天勤终端**
 * 参见: `历史复盘`_ 进入复盘模式
 * 创建 TqApi 实例时 account 参数填写 "SIM" 即可在所选的历史日期下测试策略


.. _faq-pycharm-windows-stop-finally:

在 Pycharm 中停止正在运行的海龟策略，为何不能保存持仓状态？
--------------------------------------------------------------------------------------------------------
因为在 Windows 下的 PyCharm 中终止正在运行中的程序,不会执行程序代码文件里 finally 代码段(在Linux中或在Windows的命令行下则无此问题)

可以在运行策略前对 PyCharm 进行相关设置:

 * 单击 "Run" 设置按钮
 * 选择 "Edit Configurations..." 选项
 * 在左侧导航栏中选中该策略代码的py文件
 * 勾选 "Emulate terminal in output console"
 * 点击 "OK" 确认


.. _pip文档: https://pip.pypa.io/en/stable/quickstart/
.. _天勤客户端下载地址: https://www.shinnytech.com/tianqin
.. _历史复盘: https://doc.shinnytech.com/tq/latest/usage/mdreplay.html
.. _自定义组合: https://doc.shinnytech.com/tq/latest/usage/custom_combine.html
