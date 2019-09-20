.. _gui:

与Gui库共同工作
=================================================
某些情况下, 我们可能需要在一个 Python GUI 程序中使用TqSdk库. TqSdk 可以与Tkinter, PyQt, WxPython, PySimpleGui 等大多数常见 Python Gui 库配合工作.

下面以 PySimpleGui 为例, 介绍 Gui 库与 TqSdk 组合使用的方式.


先后使用GUI库和TqSdk
-------------------------------------------------
参见示例程序 param_input.py. 这个程序先使用 PySimpleGui 创建一个参数输入对话框, 用户输入参数后, 关闭对话框, 开始使用 TqSdk:

.. literalinclude:: ../../tqsdk/demo/gui/param_input.py
  :language: python


在两个线程中分别运行Gui和TqSdk
-------------------------------------------------
参见示例程序 multi_thread.py.

.. literalinclude:: ../../tqsdk/demo/gui/multi_thread.py
  :language: python


在TqSdk任务中驱动Gui消息循环
-------------------------------------------------
参见示例程序 loop_integrate.py.

.. literalinclude:: ../../tqsdk/demo/gui/loop_integrate.py
  :language: python

