.. _tqsdk_codex:

========================================
使用 Codex 协作开发 TqSdk 项目
========================================

概述
=====

`Codex <https://openai.com/codex/>`_ 更适合作为“围绕真实仓库执行任务的代码代理”，而不只是一个在编辑器里答问题的助手。它的典型用法是围绕仓库完成整段工程流程，例如阅读代码、修改文件、运行命令、执行验证、总结结果，或者直接参与 GitHub 拉取请求审查。

对 TqSdk 用户来说，这种工作方式很适合以下场景：

* 阅读现有策略，并补全回测、下单或风控逻辑。
* 对照 TqSdk 源码解释 API 的实际行为，而不是只做泛化问答。
* 修改文档、示例或脚本，并执行验证命令确认结果。
* 审查 PR，检查策略逻辑、回归风险和文档一致性。

Codex 与传统 AI 编辑器的差别
==============================

如果做一个最简单的区分：

* 传统 AI 编辑器更偏向“在编辑器里即时补代码、答问题”。
* Codex 更偏向“围绕仓库接一个完整任务并交付结果”。

因此，使用 Codex 时最重要的不是快捷键，而是四件事：

* 仓库是否完整。
* 任务是否清晰。
* 验证是否明确。
* 上下文资料是否齐全。

开始前准备
==========

准备完整仓库
----------------

第一次在 TqSdk 项目里使用 Codex，建议按下面顺序准备，而不是一开始就直接提问：

#. 准备 ``tqsdk-python`` 源码，或者您自己的策略仓库。
#. 在 Codex 中打开仓库根目录，而不是只打开 ``tqsdk`` 或 ``doc`` 子目录。
#. 准备 Python 环境、依赖安装命令和最小验证命令。
#. 准备 :ref:`TqSdk Skills 压缩包与使用说明 <tqsdk_skills>`。
#. 给 Codex 一个边界清楚、带完成标准和验证要求的任务。

对 TqSdk 这类项目，这个顺序很重要。很多问题并不是“某个 API 名字是什么”，而是“当前策略为什么没成交”“这次改动会不会破坏回测”“这个示例是否仍然符合当前实现”。这些问题都依赖完整仓库、实际源码和可执行验证。

准备 TqSdk 源码
----------------

如果您需要解释 API 实现、排查行为差异或核对文档与代码是否一致，建议把 TqSdk 源码放到本地。这样 Codex 可以直接读取真实实现，而不是只根据零散文档猜测接口行为。

如果您要研究 TqSdk 源码，可使用以下仓库地址：

* GitHub: `https://github.com/shinnytech/tqsdk-python <https://github.com/shinnytech/tqsdk-python>`_
* Gitee: `https://gitee.com/tianqin_quantification_tqsdk/tqsdk-python <https://gitee.com/tianqin_quantification_tqsdk/tqsdk-python>`_

从 GitHub 或 Gitee 获取源码到本地
----------------------------------

如果您还没有把 TqSdk 源码下载到本地，可以先用 ``git clone`` 获取仓库。

#. 先准备一个本地目录，用来存放源码仓库。
#. 打开终端，进入这个目录。
#. 选择 GitHub 或 Gitee 其中一个地址执行 ``git clone``。

例如，在 Windows PowerShell 中可以这样做：

.. code-block:: powershell

    cd C:\Users\您的用户名\Desktop
    git clone https://github.com/shinnytech/tqsdk-python.git

如果您使用 Gitee，也可以执行：

.. code-block:: powershell

    cd C:\Users\您的用户名\Desktop
    git clone https://gitee.com/tianqin_quantification_tqsdk/tqsdk-python.git

克隆完成后，本地会得到一个 ``tqsdk-python`` 目录，里面就是完整的 TqSdk 源码、文档和示例。

如果提示 ``git`` 命令不存在，说明本机还没有安装 Git。此时建议先安装 Git，再重新执行上面的命令。

在 Codex 中打开本地项目
------------------------

当源码已经下载到本地后，下一步就是让 Codex 直接看到这个仓库：

#. 打开 Codex。
#. 选择“打开文件夹”或等效入口。
#. 选择刚刚克隆下来的 ``tqsdk-python`` 目录。
#. 确认当前工作区就是仓库根目录，而不是某个子目录。

如果您在本地克隆后的路径是 ``C:\Users\您的用户名\Desktop\tqsdk-python``，那么在 Codex 中应该打开这个目录本身，而不是只打开 ``tqsdk`` 或 ``doc`` 子目录。这样 Codex 才能同时看到源码、示例、文档和依赖文件。

如果您有自己的策略项目，也可以把策略项目和 ``tqsdk-python`` 一起放进同一个工作区。这样 Codex 就能同时读取您的业务代码和 TqSdk 源码，在解释 API 行为、定位问题或修改策略时通常更准确。

准备 Python 环境
----------------

在让 Codex 动手之前，建议先把依赖安装和验证路径准备清楚，不要让它靠猜。

如果您是在克隆下来的 TqSdk 源码仓库里工作，常见准备步骤如下：

.. code-block:: bash

    python -m pip install -r requirements.txt
    python -m pip install -e .

其中 ``requirements.txt`` 用于安装项目依赖，``python -m pip install -e .`` 用于把当前仓库作为可编辑包安装到环境中。

如果您只是准备一个独立的最小使用环境，而不是直接修改 TqSdk 源码仓库，也可以直接安装 TqSdk：

.. code-block:: bash

    python -m pip install tqsdk

安装完成后，建议至少准备一个最简单的验证命令，例如：

.. code-block:: bash

    python -c "import tqsdk; print(tqsdk.__version__)"

如果您的项目还依赖 pandas、numpy、TA 计算库或回测脚本，也建议把这些安装步骤写进仓库文档、README 或 skills 说明中，不要让 Codex 靠猜。

准备 TqSdk Skills
-----------------

对于 TqSdk 项目，更推荐直接使用 :ref:`TqSdk Skills 压缩包与使用说明 <tqsdk_skills>`，把技能包、参考资料和使用说明一起提供给 Codex 或其他 AI。

这样比单独维护一段只面向 Codex 的项目说明更直接，尤其适合下面这些场景：

* 让 AI 在行情、历史数据、账户、下单、模拟和回测之间选对接口。
* 让 AI 优先参考已经整理好的多文件说明，而不是凭印象猜测 TqSdk 用法。
* 让 AI 在处理任务时按需读取 ``SKILL.md`` 和 ``references/``，减少上下文噪声。
* 让 AI 在回答前先建立“账户类型、数据来源、调用顺序、验证方式”这些基础约束。

如果您准备把 TqSdk 能力分发给其他 AI 工具，也建议直接分发完整的 skills 压缩包，而不是只复制单篇说明文档。

使用 Codex 的推荐工作流
========================

下面这套工作流比较适合 TqSdk 项目。

1. 先把仓库接入 Codex
---------------------

建议优先使用官方支持的仓库接入方式，例如在 Codex 中连接 GitHub 仓库，或直接在本地打开已经准备好的项目目录，再为任务选择运行环境。通常需要先说明这些内容：

* 选择目标仓库或分支。
* 配置环境准备方式，例如依赖安装、启动脚本或 Dockerfile。
* 根据需要决定是否允许联网。
* 决定任务执行范围，是只读分析、代码修改，还是连验证一起执行。

对于 TqSdk 项目，如果策略依赖某些外部服务、特定环境变量或私有数据源，建议在任务里明确说明“哪些能力可用，哪些不可用”。

2. 一次只给 Codex 一个清晰任务
-------------------------------

对 TqSdk 来说，下面这种表达通常更好：

* “请检查当前回测脚本为什么没有成交，只修改 `backtest_demo.py`，并在修改后运行最小验证。”
* “请为 `TargetPosTask` 示例补一段止损说明，同时构建文档确认无语法错误。”
* “请阅读 `tqsdk/api.py` 和当前策略文件，解释 `wait_update()` 为什么会导致这段逻辑重复触发。”

不太推荐这种过宽的任务：

* “帮我把整个项目优化一下。”
* “把这个策略改到最好。”

对于 Codex，任务越像一个可以验收的 issue，结果通常越稳定。

3. 明确写出完成标准
-------------------

对 TqSdk 项目，推荐把完成标准写得具体一点，例如：

* 修复后脚本能正常导入运行。
* 回测脚本至少能跑到首个下单分支。
* 文档修改后通过 Sphinx dummy 构建。
* 只修改指定文件，不调整对外 API。
* 给出简要说明，包括原因、改动点和未覆盖风险。

如果没有完成标准，Codex 往往容易停在“给出建议”而不是“交付结果”。

4. 要求它自己执行验证
---------------------

对 TqSdk 这类工程项目，最有价值的不是“生成一段代码”，而是“生成后继续验证”。建议在任务里直接写明：

* 改完后请运行哪些命令。
* 如果命令失败，请附带失败原因。
* 如果环境不满足，请先说明卡点，不要假装已经验证成功。

例如：

.. code-block:: text

    请修改策略后运行：
    python -m pytest
    python -c "import tqsdk"

如果您在维护文档，也可以要求：

.. code-block:: text

    请在修改后运行：
    python -m sphinx -q -b dummy doc build/sphinx_dummy

5. 让 Codex 做审查而不只是写代码
---------------------------------

Codex 也很适合做 TqSdk 项目的代码审查或 PR 审查。常见场景包括：

* 检查策略条件改动是否改变了原有交易语义。
* 检查回测脚本与实盘脚本是否混用了不兼容参数。
* 检查文档示例是否与当前 API 一致。
* 检查 PR 是否缺少必要测试、验证步骤或风险提示。

如果您已经把仓库接到 GitHub，也可以把 Codex 用作 PR reviewer，而不仅仅是代码生成器。

TqSdk 项目里最值得交给 Codex 的任务
====================================

下面这些任务类型，通常最能发挥 Codex 的价值：

* 阅读和解释现有策略：例如“请阅读 `strategies/spread.py`，解释开仓、平仓和调仓条件”。
* 做小而完整的代码改动：例如“在现有双均线策略中增加止损参数，只修改 `demo.py`”。
* 排查运行错误和行为异常：例如“回测能跑通但永远不开仓，请检查条件、K 线更新和下单参数”。
* 维护文档和示例：例如“整理 README 的源码获取说明，并保留 GitHub 和 Gitee 两个入口”。

这几类任务共同特点是范围清楚、可以验证，而且通常能直接落到仓库中的具体文件。

适合直接复制的提示词模板
==========================

下面几类提示词，更适合直接复制后按需改写。

模板一：改策略
--------------

.. code-block:: text

    请阅读当前仓库，定位双均线策略入口文件。
    只修改策略文件，不要改公共库。
    为开仓逻辑增加固定止损参数，保持原有开平仓语义不变。
    修改后请运行最小验证命令，并总结改动与风险。

模板二：查问题
--------------

.. code-block:: text

    请检查这个 TqSdk 回测脚本为什么没有成交。
    先阅读相关文件，再查看报错或日志。
    只做必要修改。
    完成标准：
    1. 解释根因
    2. 提交最小修复
    3. 运行验证命令

模板三：改文档
--------------

.. code-block:: text

    请更新 TqSdk 的 Codex 使用文档。
    目标是让内容更贴近 Codex 的仓库协作工作流。
    保留现有文档风格，但不要写成通用 IDE 教程。
    修改后请运行 Sphinx dummy 构建并报告结果。

使用 Codex 时的注意事项
========================

对于 TqSdk 项目，下面几点尤其重要：

* **不要提供真实交易凭证**：账号、密码、CTP 凭证、私钥应使用占位符或环境变量。
* **把数据和联网前提说清楚**：如果某个脚本依赖外部行情服务、私有接口或内网数据库，要提前告诉 Codex。
* **优先让它做最小修改**：策略类项目对行为变化很敏感，尽量避免“大改一遍”的任务描述。
* **总是要求验证**：没有验证的“看起来合理”并不等于可用。
* **优先提供完整的 TqSdk Skills**：这比在每次任务里手工重复背景说明更稳定。

官方入口与参考资料
====================

如果您准备进一步了解 Codex 本身，可以继续参考这些官方资料：

* `Codex 官方页面 <https://openai.com/codex/>`_
* `Get started with Codex <https://openai.com/codex/get-started/>`_
* `Using Codex on ChatGPT <https://help.openai.com/en/articles/11096431-codex-on-chatgpt>`_
* `Codex Best practices <https://developers.openai.com/codex/best-practices>`_
* `Workflows <https://developers.openai.com/codex/common-workflows>`_
* `Cloud environments <https://developers.openai.com/codex/cloud/environments>`_

总结
=====

对于 TqSdk 用户，Codex 的最佳用法不是把它当成泛化问答助手，而是让它围绕真实仓库处理可验收任务。把仓库、环境、验证命令和 :ref:`TqSdk Skills 压缩包与使用说明 <tqsdk_skills>` 准备好，通常比反复打磨提示词更能稳定提升协作效果。
