.. _jupyter:

在 Jupyter Notebook 中使用 TqSdk
====================================================
本文档将介绍如何在 Jupyter Notebook 中使用 TqSdk。

当您的主要是希望使用 TqSdk 来进行行情分析和研究，并不涉及到交易时使用 Jupyter Notebook 可以带来一些潜在优势

1. 交互式编程
Jupyter Notebook 提供了一个交互式的环境，可以逐步执行代码块并立即查看输出结果。这种特性特别适合数据分析和探索性编程，使得用户可以实时查看数据处理和可视化的效果。

2. 内嵌可视化
Jupyter Notebook 支持在单元格中嵌入图表和图像，使得数据可视化变得非常方便。用户可以在一个文档中同时编写代码、生成图表和撰写分析报告，无需切换到其他工具或窗口。

安装 Jupyter Notebook
----------------------------------------------------

Jupyter Notebook 是一个开源项目，能够在交互式编程环境中提供丰富的可视化表达，可以创建和共享代码和文档。

可以使用以下命令安装 Jupyter Notebook：

```bash
pip install jupyter
```

更多 Jupyter Notebook 安装文档请参考

`Jupyter Notebook 安装文档 <https://jupyter.org/install/>`_ ::
`Jupyter Notebook 文档 <https://jupyter-notebook.readthedocs.io/en/latest//>`_ ::


安装 TqSdk
----------------------------------------------------

请参考 :ref:`安装文档 <tqsdk_install>` 。


在 Jupyter Notebook 中使用 TqSdk
----------------------------------------------------

请参考 :ref:`示例 <demo_jupyter>` 。


注意事项
----------------------------------------------------

* **不建议用户在 jupyter 里使用 tqsdk 的交易功能，因为 TqSdk 行情只有在调用 wait_update() 之后才会更新，但是在 jupyter 交互运行的环境中，无法及时调用 wait_update()，可能会导致行情延时**

* **不能在 jupyter 中异步的使用 tqsdk，jupyter 只能用 TqSdk 的同步代码的写法**

* **在 jupyter 中使用 wait_update() 时，建议增加 deadline 参数在函数里，避免长时间的阻塞**

