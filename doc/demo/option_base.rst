.. _demo_options:

期权基本使用
====================================================

这组示例默认你已经熟悉 :ref:`quickstart` 中的基础行情、K 线和主循环写法。第一次接触期权功能时，建议按下面的顺序阅读：

* 先看 :ref:`option_tutorial-t10`、:ref:`option_tutorial-t20`，熟悉期权行情和筛选接口
* 再看 :ref:`option_tutorial-t30`、:ref:`option_tutorial-t40`、:ref:`option_tutorial-t41`，理解实值/平值/虚值分类与希腊值计算
* 最后看 :ref:`option_tutorial-t60` 到 :ref:`option_tutorial-t74`，处理波动率曲面、套利和保证金计算

.. contents:: 目录


.. _option_tutorial-t10:

o10 - 获取期权实时行情
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tqsdk/demo/option_tutorial/o10.py
  :language: python


.. _option_tutorial-t20:

o20 - 查询符合要求的期权
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tqsdk/demo/option_tutorial/o20.py
  :language: python


.. _option_tutorial-t30:

o30 - 查询平值/虚值/实值期权
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tqsdk/demo/option_tutorial/o30.py
  :language: python


.. _option_tutorial-t40:

o40 - 计算期权的希腊字母
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tqsdk/demo/option_tutorial/o40.py
  :language: python


.. _option_tutorial-t41:

o41 - 计算期权隐含波动率和历史波动率
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tqsdk/demo/option_tutorial/o41.py
  :language: python


.. _option_tutorial-t60:

o60 - 获取期权波动率曲面
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tqsdk/demo/option_tutorial/o60.py
  :language: python

.. _option_tutorial-t70:

o70 - 期权套利策略
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tqsdk/demo/option_tutorial/o70.py
  :language: python

.. _option_tutorial-t71:

o71 - 获取一组期权和其对应行权价
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tqsdk/demo/option_tutorial/o71.py
  :language: python

.. _option_tutorial-t72:

o72 - 查询标的对应期权按虚值平值实值分类方法一
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tqsdk/demo/option_tutorial/o72.py
  :language: python

.. _option_tutorial-t73:

o73 - 查询标的对应期权按虚值平值实值分类方法二
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tqsdk/demo/option_tutorial/o73.py
  :language: python

.. _option_tutorial-t74:

o74 - 本地计算ETF期权卖方开仓保证金
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tqsdk/demo/option_tutorial/o74.py
  :language: python
