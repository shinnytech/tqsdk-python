.. _tqsdk_codebuddy:

=============================================
在 CodeBuddy 中高效学习和使用 TqSdk
=============================================



CodeBuddy：TqSdk 开发与学习的 AI 助手
======================================

CodeBuddy 简介
---------------

`CodeBuddy <https://www.codebuddy.ai/docs/ide/Introduction>`_ 是腾讯云推出的 AI 辅助编程工具，支持 IDE、插件和命令行等使用形态。对于 TqSdk 用户来说，CodeBuddy 更适合放在真实项目里使用：一边读取策略代码、TqSdk 源码和文档，一边协助解释 API、生成示例、排查报错和改造脚本。

CodeBuddy 官方文档：`https://www.codebuddy.ai/docs/ide/Introduction <https://www.codebuddy.ai/docs/ide/Introduction>`_

在 TqSdk 开发中使用 CodeBuddy 的好处
------------------------------------

对于 TqSdk 用户而言，使用 CodeBuddy 进行开发与学习具有以下优势：

* **结合项目上下文理解 TqSdk 用法**：
    * 可让 CodeBuddy 读取当前策略项目、TqSdk 源码和文档，减少只凭片段猜测 API 行为的情况。
    * 适合解释 ``TqApi``、``wait_update``、``TargetPosTask``、``TqBacktest`` 等接口的实际使用方式。
* **辅助生成和修改策略代码**：
    * 可用自然语言描述需求，让 CodeBuddy 生成行情订阅、K 线处理、下单、模拟交易或回测代码。
    * 对已有策略做小范围修改时，可以让它先读上下文，再只改指定文件。
* **帮助排查运行错误**：
    * 将报错堆栈、运行日志和相关代码一起提供给 CodeBuddy，通常能更快定位环境、数据、账户或代码逻辑问题。
* **适合文档和示例维护**：
    * 可以让 CodeBuddy 根据当前 TqSdk 版本检查示例是否过时，并在修改后执行最小验证。
* **支持更完整的协作流程**：
    * 对简单问题可使用对话模式；对跨文件修改可使用更强的任务规划或 Agent 能力。

开始使用 CodeBuddy
==================

选择合适的使用形态
------------------

CodeBuddy 常见使用方式包括：

* **CodeBuddy IDE**：适合想在一个完整 AI 开发环境中打开 TqSdk 源码或策略项目的用户。
* **CodeBuddy Plugin**：适合继续使用 VS Code、JetBrains 系列 IDE 等已有编辑器的用户。
* **CodeBuddy Code / CLI**：适合熟悉命令行，希望让 AI 辅助执行工程任务的用户。

如果您主要是学习 TqSdk、写策略、改示例或排查运行错误，建议优先从 CodeBuddy IDE 或插件开始。具体支持平台、安装方式和入口请以官方文档为准。

下载和安装 CodeBuddy
--------------------

1. 访问 `CodeBuddy 官方文档 <https://www.codebuddy.ai/docs/ide/Getting-Started/Installation>`_ 或官网入口。
2. 根据您的操作系统和使用方式选择 IDE、插件或 CLI。
3. 按向导完成安装，并根据产品要求完成登录。

初次启动与界面要点
------------------

打开 CodeBuddy IDE 后，通常需要先确认几个区域：

1. **项目入口**：用于打开本地文件夹、创建新项目或克隆远程仓库。
2. **代码编辑区**：用于查看和修改策略代码、示例脚本或 TqSdk 源码。
3. **终端/运行区域**：用于安装依赖、运行脚本和执行验证命令。
4. **AI 对话或 Agent 入口**：用于提问、引用上下文、生成代码或执行任务。

在 CodeBuddy 中配置 TqSdk 开发环境
===================================

创建或打开您的 TqSdk 项目
--------------------------

如果您已经有自己的策略项目，可以直接用 CodeBuddy 打开项目根目录。如果您想研究 TqSdk 源码，建议把 ``tqsdk-python`` 源码仓库也放到本地。

获取 TqSdk 源码
---------------

如果您需要解释 API 实现、排查行为差异或核对文档与代码是否一致，建议把 TqSdk 源码放到本地。可使用以下仓库地址：

* GitHub: `https://github.com/shinnytech/tqsdk-python <https://github.com/shinnytech/tqsdk-python>`_
* Gitee: `https://gitee.com/tianqin_quantification_tqsdk/tqsdk-python <https://gitee.com/tianqin_quantification_tqsdk/tqsdk-python>`_

在终端中可以执行：

.. code-block:: bash

    git clone https://github.com/shinnytech/tqsdk-python.git

如果 GitHub 访问不便，也可以使用 Gitee 镜像：

.. code-block:: bash

    git clone https://gitee.com/tianqin_quantification_tqsdk/tqsdk-python.git

如果您更习惯图形界面，也可以使用 CodeBuddy 的克隆入口。

配置 Python 解释器
------------------

确保 CodeBuddy 使用您期望的 Python 解释器或虚拟环境来运行 TqSdk 代码。常用做法：

1. 在 CodeBuddy 或您正在使用的编辑器中选择目标 Python 解释器。
2. 或在集成终端中激活虚拟环境，例如 ``venv/Scripts/activate`` 或 ``conda activate <env>``。
3. 在终端中执行 ``python --version`` 和 ``python -m pip --version``，确认 Python 与 pip 来自同一个环境。

安装 TqSdk 库
--------------

在 CodeBuddy 的集成终端中执行：

.. code-block:: bash

    python -m pip install tqsdk

安装完成后，可用以下命令验证：

.. code-block:: bash

    python -c "import tqsdk; print(tqsdk.__version__)"

如果您是在本地克隆的 TqSdk 源码仓库中工作，也可以在仓库根目录执行：

.. code-block:: bash

    python -m pip install -r requirements.txt
    python -m pip install -e .

让 CodeBuddy 深度理解 TqSdk：打开源码与资料
=============================================

将 TqSdk 源码、当前策略项目和必要文档一起加入 CodeBuddy 工作区，能明显提升回答质量。建议准备以下内容：

1. **TqSdk 源码**：用于解释接口实现和行为细节。
2. **您的策略项目**：用于结合业务代码排查问题。
3. **最小运行命令**：用于让 CodeBuddy 修改后能自己验证。
4. **TqSdk Skills**：用于补充接口选择、账户类型、行情数据和回测规则等背景。

可选：接入 TqSdk Skills
-----------------------

如果您希望 CodeBuddy 更稳定地理解 TqSdk 的接口边界，可以下载并解压 :ref:`TqSdk Skills 压缩包与使用说明 <tqsdk_skills>`。使用方式可以根据 CodeBuddy 当前版本选择：

* 若 CodeBuddy 支持项目级 skills，可将技能说明放入项目约定的 skills 目录中。
* 若当前环境不方便配置 skills，可在任务开头明确要求 CodeBuddy 先阅读 ``SKILL.md`` 和 ``references/``。
* 如果只是临时提问，也可以直接把 ``SKILL.md`` 中与当前问题相关的部分贴给 CodeBuddy。

在 CodeBuddy 中提问和学习 TqSdk
===============================

如何提问？
-----------

打开 CodeBuddy 的 AI 对话或 Agent 面板后，您可以：

* **直接提问**：输入关于 TqSdk 的概念、接口和示例问题。
* **引用上下文后提问**：引用当前文件、文件夹、工作区或代码片段，让 CodeBuddy 基于真实上下文回答。
* **带着验证要求提问**：如果让它修改脚本，应同时告诉它改完后运行哪条命令确认结果。

提问示例
---------

**基础概念与用法：**

* “TqSdk 中 ``TqApi`` 与 ``TqAccount`` 的关系是什么？请结合一个最小示例解释。”
* “如何订阅 ``SHFE.rb2610`` 的 1 分钟 K 线？请给出可运行代码。”
* “``TargetPosTask`` 和直接调用 ``insert_order`` 的区别是什么？”

**结合源码提问：**

* “请阅读当前工作区里的 ``tqsdk/api.py``，解释 ``wait_update()`` 什么时候返回。”
* “请检查这个回测脚本为什么一直没有成交，只分析原因，先不要修改文件。”

**让 CodeBuddy 修改并验证：**

.. code-block:: text

    请阅读当前策略文件，给下单逻辑增加一个最小止损条件。
    只修改 strategy.py，不改 TqSdk 源码。
    修改后请运行：
    python -m py_compile strategy.py
    并说明验证结果。

利用 CodeBuddy 进行 TqSdk 代码生成与修改
-----------------------------------------

* **生成最小示例**：
    * “写一个最小脚本，订阅 ``SHFE.rb2610`` 的 quote 并打印最新价。”
    * “写一个只使用 ``TqSim`` 的模拟交易示例，不连接实盘账户。”
* **修改现有策略**：
    * “只在当前文件中增加参数校验，不改变原有开平仓逻辑。”
    * “把行情处理和下单决策拆成两个函数，并保持输出结果不变。”
* **排查运行错误**：
    * “这是完整报错和策略代码，请判断是环境问题、账户问题、行情数据问题，还是代码逻辑问题。”

推荐工作流
==========

1. 先打开完整项目
-----------------

不要只打开单个脚本。对于 TqSdk 项目，建议让 CodeBuddy 同时看到：

* 当前策略文件。
* 依赖文件或配置文件。
* TqSdk 源码或已安装包路径。
* README、运行说明和验证命令。

2. 一次只给一个清晰任务
-----------------------

对 TqSdk 来说，下面这种表达通常更好：

* “请解释当前脚本为什么只打印一次行情后就退出。”
* “请把这个示例改成模拟交易版本，只使用 ``TqSim``。”
* “请检查文档里的参数说明是否和当前 TqSdk 源码一致。”

不太推荐这种过宽的任务：

* “帮我优化整个策略。”
* “把这个项目改好。”

3. 明确写出完成标准
-------------------

建议把完成标准写得具体一点，例如：

* 脚本能通过语法检查。
* 示例能正常导入 ``tqsdk``。
* 文档修改后能通过 Sphinx dummy 构建。
* 只修改指定文件，不调整公共接口。
* 最终说明改了什么、验证了什么、还剩什么风险。

4. 要求它自己执行验证
---------------------

如果您让 CodeBuddy 修改代码或文档，建议在任务里直接写明验证命令。例如：

.. code-block:: text

    修改后请运行：
    python -m py_compile demo.py
    python -c "import tqsdk"

如果是在维护文档，可以要求：

.. code-block:: text

    修改后请运行：
    python -m sphinx -q -b dummy doc build/sphinx_dummy

5. 对复杂任务先让它列计划
-------------------------

如果任务涉及多个文件、回测结果或文档同步，建议先让 CodeBuddy 说明它准备检查哪些文件、怎么验证、哪些地方不会改。确认范围后，再让它执行。

适合直接复制的提示词模板
========================

模板一：写最小示例
------------------

.. code-block:: text

    请在当前项目里写一个最小 TqSdk 示例。
    目标：订阅 SHFE.rb2610 的 1 分钟 K 线并打印最后一根 K 线。
    只新增一个 demo 文件，不修改其他文件。
    写完后请运行语法检查，并说明如何运行。

模板二：排查策略问题
--------------------

.. code-block:: text

    请检查当前 TqSdk 策略为什么没有成交。
    先阅读策略文件和相关配置，再判断原因。
    先不要改代码，先给出证据和下一步建议。

模板三：小范围修改并验证
------------------------

.. code-block:: text

    请给当前策略增加一个固定止损条件。
    只修改 strategy.py，保持原有开仓和平仓语义不变。
    修改后请运行 python -m py_compile strategy.py。
    最后说明改了什么和验证结果。

模板四：维护文档
----------------

.. code-block:: text

    请更新当前 TqSdk 文档中的示例说明。
    保持现有文档风格，不写成通用 IDE 教程。
    修改后请运行 Sphinx dummy 构建，并报告结果。

使用 CodeBuddy 时的注意事项
============================

对于 TqSdk 项目，下面几点尤其重要：

* **不要提供真实交易凭证**：账号、密码、CTP 凭证、私钥应使用占位符或环境变量。
* **先说明账户类型**：明确当前是实盘、模拟、回测还是只读行情。
* **把数据来源说清楚**：如果脚本依赖外部行情、历史数据或内网服务，要提前说明。
* **优先做最小修改**：策略代码对行为变化很敏感，尽量不要让 AI 大范围重构。
* **总是要求验证**：没有实际验证的代码建议，不应直接用于交易。

常见问题（FAQ）
===============

* “CodeBuddy 回答不贴合当前 TqSdk 版本？”——把 TqSdk 源码或已安装包路径加入工作区，并要求它先读取相关文件。
* “运行用错 Python 环境？”——在集成终端里执行 ``python --version``、``python -m pip --version`` 和 ``python -c "import tqsdk; print(tqsdk.__version__)"``。
* “AI 修改范围过大？”——重新给出文件边界，例如“只修改 demo.py，不改公共库，不重构目录结构”。
* “排查交易问题时结论不确定？”——补充账户类型、合约、时间段、完整报错和最小复现代码。

官方入口与参考资料
==================

如果您准备进一步了解 CodeBuddy 本身，可以参考这些官方资料：

* `CodeBuddy 介绍 <https://www.codebuddy.ai/docs/ide/Introduction>`_
* `CodeBuddy 安装与登录 <https://www.codebuddy.ai/docs/ide/Getting-Started/Installation>`_
* `CodeBuddy 快速开始 <https://www.codebuddy.ai/docs/ide/Getting-Started/Quickstart>`_
* `CodeBuddy IDE 概览 <https://www.codebuddy.ai/docs/ide/User-guide/Overview>`_

总结
====

对于 TqSdk 用户，CodeBuddy 的最佳用法不是只让它回答零散问题，而是让它围绕真实项目、源码、文档和验证命令协助完成一个清晰任务。把 TqSdk 源码、策略项目、运行环境和 :ref:`TqSdk Skills 压缩包与使用说明 <tqsdk_skills>` 准备好，通常比单独打磨提示词更稳定。
