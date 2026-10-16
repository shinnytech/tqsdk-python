.. _pysdk:
.. _tianqin-python-sdk-user-guide:

TqSdk 使用指南
========================================

.. raw:: html

   <div class="tq-home-hero">
     <p class="tq-eyebrow">PYTHON · 行情 · 交易 · 回测</p>
     <p class="tq-lead">TqSdk 是开源的 Python 量化交易开发包。<br>使用统一的 API 获取行情与历史数据，编写策略，进行回测、模拟和实盘交易。</p>
   </div>

本文档按“快速上手 → 常用功能与模块参考 → 进阶专题 → 产品与支持”的路径组织，方便按学习阶段和使用场景查阅。

.. raw:: html

     <div class="tq-actions">
       <a class="tq-button" href="quickstart.html">十分钟快速入门 →</a>
       <a class="tq-button tq-button-secondary" href="reference/index.html">查阅 API 参考</a>
     </div>
     <div class="tq-home-meta"><span>Python 3.9+</span><span>开源 Python SDK</span><span>从本地模拟开始</span></div>

选择你的起点
----------------------------------------

第一次接触 TqSdk，可以先了解它的能力，再运行第一个程序，之后按需查阅常用功能。

.. raw:: html

   <div class="tq-path-grid">
     <a class="tq-path" href="intro.html">
       <span class="tq-path-number">01 / INTRO</span>
       <strong>了解 TqSdk</strong>
       <p>了解开发包的主要能力、程序结构，以及行情、回测和交易如何配合。</p>
       <span class="tq-path-cta">阅读 TqSdk 介绍 →</span>
     </a>
     <a class="tq-path" href="quickstart.html">
       <span class="tq-path-number">02 / LEARN</span>
       <strong>跟着教程动手</strong>
       <p>运行第一个行情程序，理解更新循环，再尝试模拟交易和历史回测。</p>
       <span class="tq-path-cta">十分钟快速入门 →</span>
     </a>
     <a class="tq-path" href="usage/index.html">
       <span class="tq-path-number">03 / BUILD</span>
       <strong>使用常用功能</strong>
       <p>按任务学习行情、K 线、委托、目标持仓和回测，逐步构建自己的策略。</p>
       <span class="tq-path-cta">浏览使用指南 →</span>
     </a>
   </div>

运行第一个程序后，建议继续阅读 :ref:`framework` 和 :ref:`shinny_account`，再学习 :ref:`mddatas`、:ref:`trade` 与 :ref:`targetpostask`，最后按需进入进阶主题。

**配合 AI 开发：** 如果你使用 AI 编码工具，建议先给它加载 :ref:`tqsdk_skills`，再让它协助写代码或排错。使用说明页提供可直接复制的提示词和完整技能包。

按任务查找
----------------------------------------

.. raw:: html

   <div class="tq-topic-grid">
     <a class="tq-topic" href="usage/mddatas.html"><strong>获取行情与历史数据 →</strong><span>合约代码、实时行情、K 线与 Tick 数据。</span></a>
     <a class="tq-topic" href="usage/targetpostask.html"><strong>下单与管理目标持仓 →</strong><span>委托状态、撤单、自动调仓与持仓管理。</span></a>
     <a class="tq-topic" href="usage/backtest.html"><strong>运行策略回测 →</strong><span>选择历史区间、处理回测结束、查看回测结果。</span></a>
     <a class="tq-topic" href="demo/index.html"><strong>寻找完整示例 →</strong><span>从基础功能到交易策略，按场景选择示例程序。</span></a>
     <a class="tq-topic" href="ai_editor/index.html"><strong>与 AI 一起开发 →</strong><span>给 AI 提供 TqSdk 技能包与项目上下文。</span></a>
     <a class="tq-topic" href="qa.html"><strong>排查使用问题 →</strong><span>安装、登录、行情更新与模拟账户的常见疑问。</span></a>
   </div>

先理解这三个概念
----------------------------------------

* **TqApi** 负责连接服务、维护数据并驱动策略。
* **数据引用** 会持续更新；先订阅，再在循环里读取，无需反复创建订阅。
* **wait_update()** 推进数据、请求和后台任务；用 :py:meth:`is_changing() <tqsdk.TqApi.is_changing>` 判断关心的数据是否变化。

继续阅读 :ref:`framework`，或先了解 :ref:`intro`。

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: 入门
   :titlesonly:

   intro
   quickstart

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: 使用与示例
   :titlesonly:

   usage/index
   demo/index

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: API 参考

   reference/index

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: 进阶专题
   :titlesonly:

   advanced/index

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: AI 工具
   :titlesonly:

   ai_editor/index

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: 开发、产品与支持
   :titlesonly:

   dev_general
   dev_framework
   profession
   enterprise
   qa
   version
