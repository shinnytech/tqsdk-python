.. _demo_algorithm:

算法模块示例
====================================================

这两组示例面向已经理解 :ref:`targetpostask`、下单/撤单和 :py:meth:`~tqsdk.TqApi.wait_update` 主循环的读者。

如果你还没接触过拆单和时间表任务，建议先看 :ref:`tutorial-t40`、:ref:`targetpostask` 和 :ref:`target_pos_scheduler`，再阅读本页。

.. contents:: 目录


.. _demo-algorithm-twap:

twap_table - 时间平均加权算法
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tqsdk/demo/algorithm/twap.py
  :language: python


.. _demo-algorithm-vwap:

vwap_table - 交易量平均加权算法
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tqsdk/demo/algorithm/vwap.py
  :language: python
