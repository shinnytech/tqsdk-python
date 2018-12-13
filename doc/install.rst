.. _install:

安装
=================================================
这一部分文档介绍 TqSdk 的安装. 在安装 TqSdk 前, 你需要先准备适当的环境和Python包管理工具, 包括:

* Python 3.6 或以上版本
* Windows 7 以上版本, 或 Linux

如果你的电脑上还没有安装适当版本的python, 请参考 `Python 安装指南 <https://docs.python-guide.org/starting/installation/>`_

你可以选择使用 pip 命令安装 TqSdk, 或者下载源代码安装. 对于一般用户, 我们推荐采用 pip 命令安装.


通过 `pip` 命令安装
-------------------------------------------------
要安装 TqSdk, 只需简单的在终端或命令行环境下运行::

    pip install tqsdk


下载源码安装
-------------------------------------------------
TqSdk 的源代码库托管在 GitHub, 点击 `这里 <https://github.com/shinnytech/tqsdk-python>`_ 直达版本库.

你可以 clone 整个项目库::

    $ git clone https://github.com/shinnytech/tqsdk-python.git

或者, 可以下载源码压缩包::

    $ curl -OL https://github.com/shinnytech/tqsdk-python/tarball/master
    # optionally, zipball is also available (for Windows users).

一旦你获得了 TqSdk 的源码, 可以通过以下命令安装::

    $ cd tqsdk-python
    $ python setup.py install


