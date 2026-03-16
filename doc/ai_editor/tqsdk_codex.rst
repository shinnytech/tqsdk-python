.. _tqsdk_codex:

========================================
使用 Codex 协作开发 TqSdk 项目
========================================

概述
=====

`Codex <https://openai.com/codex/>`_ 更接近“面向真实仓库执行任务的代码代理”，而不是传统意义上的 AI 编辑器。它的典型用法不是在一个编辑器侧栏里边写边问，而是让 Codex 围绕一个代码仓库完成完整任务，例如阅读代码、修改文件、运行命令、做验证、总结结果，或者直接对 GitHub 拉取请求进行审查。

对 TqSdk 用户来说，这种工作方式很适合以下场景：

* 让 Codex 阅读现有策略，补全一段回测、下单或风控逻辑。
* 让 Codex 对照 TqSdk 源码解释 API 的实际行为，而不是只做泛化问答。
* 让 Codex 修改文档、示例或脚本，并执行验证命令确认结果。
* 让 Codex 在 GitHub 上帮助审查 PR，检查策略逻辑、回归风险和文档一致性。

官方入口与参考资料
====================

如果您是第一次使用 Codex，建议先看 OpenAI 官方材料：

* `Codex 官方页面 <https://openai.com/codex/>`_
* `Get started with Codex <https://openai.com/codex/get-started/>`_
* `Using Codex on ChatGPT <https://help.openai.com/en/articles/11096431-codex-on-chatgpt>`_
* `Codex Best practices <https://developers.openai.com/codex/best-practices>`_
* `Workflows <https://developers.openai.com/codex/common-workflows>`_
* `AGENTS.md <https://developers.openai.com/codex/agents-md>`_
* `Cloud environments <https://developers.openai.com/codex/cloud/environments>`_

Codex 与传统 AI 编辑器的差别
==============================

如果您已经熟悉常见的 AI 编辑器，可以把差异简单理解为：

* 传统 AI 编辑器更偏“在编辑器里即时协助写代码”。
* Codex 更偏“围绕仓库接任务，执行一整段工程流程”。

因此，使用 Codex 时，最重要的不是快捷键，而是下面几件事：

* 仓库是否完整，能否让 Codex 看懂上下文。
* 任务描述是否明确，是否给出了完成标准。
* 是否告诉 Codex 该运行哪些验证命令。
* 是否用 ``AGENTS.md`` 把项目约束写清楚。

对于 TqSdk 项目，这种差异很关键。很多问题并不是“某个 API 怎么用”，而是“当前策略为什么没成交”“这次改动会不会破坏回测”“这个 PR 是否引入行为回归”。这类问题更适合交给 Codex 处理。

开始前先准备好仓库
====================

Codex 最适合处理已经具备基本工程结构的项目。建议先准备好：

1. 您自己的 TqSdk 策略项目，或者一个专门的示例仓库。
2. 明确的 Python 环境与依赖安装方式。
3. 可执行的验证命令，例如测试、示例运行命令或文档构建命令。
4. 如果需要深度解释实现细节，再把 TqSdk 源码放进同一工作区。

如果您要研究 TqSdk 源码，可使用以下仓库地址：

* GitHub: `https://github.com/shinnytech/tqsdk-python <https://github.com/shinnytech/tqsdk-python>`_
* Gitee: `https://gitee.com/tianqin_quantification_tqsdk/tqsdk-python <https://gitee.com/tianqin_quantification_tqsdk/tqsdk-python>`_

准备 Python 环境
----------------

在让 Codex 动手之前，建议先确保本地或云端环境具备稳定的安装与验证路径。

如果您是在克隆下来的 TqSdk 源码仓库里工作，常见准备步骤如下： ::

    python -m pip install -r requirements.txt

    python -m pip install -e .

其中 ``requirements.txt`` 用于安装项目依赖，``python -m pip install -e .`` 用于把当前仓库作为可编辑包安装到环境中。

如果您只是准备一个独立的最小使用环境，而不是直接修改 TqSdk 源码仓库，也可以直接安装 TqSdk： ::

    python -m pip install tqsdk

安装完成后，可以准备一个最简单的验证命令，例如： ::

    python -c "import tqsdk; print(tqsdk.__version__)"

如果您的项目还依赖 pandas、numpy、TA 计算库或回测脚本，也建议把这些安装步骤写进仓库文档或 ``AGENTS.md``，不要让 Codex 靠猜。

按官方推荐方式写 AGENTS.md
===========================

OpenAI 官方当前非常强调 ``AGENTS.md``。它的作用类似“给 Codex 的项目内说明书”，用来描述仓库结构、开发约束、验证方式和注意事项。Codex 会优先参考这些说明。

对于 TqSdk 项目，建议把下面几类信息写进 ``AGENTS.md``：

* 项目的主要目录做什么。
* 哪些文件是策略入口，哪些文件是公共工具。
* 使用哪个 Python 版本、哪个虚拟环境或依赖管理方式。
* 修改后至少要运行哪些检查命令。
* 哪些文件不要动，或者哪些改动需要特别谨慎。
* 不要提交真实账号、密码、私钥、交易口令。

一个适合 TqSdk 项目的精简示例如下： ::

    # AGENTS.md
    - Use Python 3.11 for this repo.
    - Install dependencies with: python -m pip install -r requirements.txt
    - Install the current package with: python -m pip install -e .
    - Main strategy files live in strategies/
    - Shared helpers live in utils/
    - Do not commit real trading credentials
    - After changing Python code, run:
      - python -m pytest
      - python -c "import tqsdk"
    - After changing docs, run:
      - python -m sphinx -q -b dummy doc build/sphinx_dummy

如果您的仓库里已经有文档规范、回测规范或提交规范，也建议合并到 ``AGENTS.md`` 中。这样 Codex 在执行任务时更稳定，不容易偏离项目实际要求。

使用 Codex 的推荐工作流
========================

结合 OpenAI 官方当前的工作流建议，比较适合 TqSdk 的用法如下。

1. 先把仓库接入 Codex
---------------------

建议优先使用官方支持的仓库接入方式，例如在 Codex 中连接 GitHub 仓库，再为任务选择运行环境。根据 OpenAI 官方材料，您通常需要处理这些内容：

* 选择目标仓库或分支。
* 配置环境准备方式，例如依赖安装、启动脚本或 Dockerfile。
* 根据需要决定是否允许联网。
* 决定任务执行范围，是只读分析、代码修改，还是连验证一起执行。

对于 TqSdk 项目，如果策略依赖某些外部服务、特定环境变量或私有数据源，建议在任务里明确说明“哪些能力可用，哪些不可用”。

2. 一次只给 Codex 一个清晰任务
-------------------------------

OpenAI 官方建议任务尽量聚焦。对 TqSdk 来说，下面这种表达通常更好：

* “请检查当前回测脚本为什么没有成交，只修改 `backtest_demo.py`，并在修改后运行最小验证。”
* “请为 `TargetPosTask` 示例补一段止损说明，同时构建文档确认无语法错误。”
* “请阅读 `tqsdk/api.py` 和当前策略文件，解释 `wait_update()` 为什么会导致这段逻辑重复触发。”

不太推荐这种过宽的任务：

* “帮我把整个项目优化一下。”
* “把这个策略改到最好。”

对于 Codex，任务越像一个可以验收的 issue，结果通常越稳定。

3. 明确写出完成标准
-------------------

OpenAI 官方材料反复强调要告诉 Codex 什么叫“完成”。对 TqSdk 项目，推荐把完成标准写得具体一点，例如：

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

例如： ::

    请修改策略后运行：
    python -m pytest
    python -c "import tqsdk"

如果您在维护文档，也可以要求： ::

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

阅读和解释现有策略
------------------

例如：

* “请阅读 `strategies/spread.py`，解释开仓、平仓和调仓条件。”
* “请结合 `tqsdk/api.py` 说明这段循环对 `wait_update()` 的依赖关系。”

这类任务适合先建立共识，避免直接修改时方向跑偏。

做小而完整的代码改动
--------------------

例如：

* “在现有双均线策略中增加止损参数，只修改 `demo.py`。”
* “把账户初始化移到配置文件，避免把账号直接写在脚本里。”
* “为回测示例增加资金曲线输出，但不要改现有交易逻辑。”

这种任务范围明确，适合 Codex 一次交付。

排查运行错误和行为异常
----------------------

例如：

* “脚本报 `AttributeError`，请定位问题并修复。”
* “回测能跑通但永远不开仓，请检查条件、K 线更新和下单参数。”
* “文档示例运行失败，请对照当前 API 调整示例。”

这类问题通常要求 Codex 同时读代码、看堆栈和做验证，非常符合它的长处。

维护文档和示例
--------------

例如：

* “给 AI 编辑器专题补一篇 Codex 教程，并更新索引页。”
* “整理 README 的源码获取说明，保留 GitHub 和 Gitee 两个入口。”
* “更新示例命令，确保与当前安装方式一致。”

对于文档仓库，这类任务往往比“生成新功能代码”更稳定。

适合直接复制的提示词模板
==========================

下面几类提示词，更符合 OpenAI 官方推荐的 Codex 使用方式。

模板一：改策略
--------------

::

    请阅读当前仓库，定位双均线策略入口文件。
    只修改策略文件，不要改公共库。
    为开仓逻辑增加固定止损参数，保持原有开平仓语义不变。
    修改后请运行最小验证命令，并总结改动与风险。

模板二：查问题
--------------

::

    请检查这个 TqSdk 回测脚本为什么没有成交。
    先阅读相关文件，再查看报错或日志。
    只做必要修改。
    完成标准：
    1. 解释根因
    2. 提交最小修复
    3. 运行验证命令

模板三：改文档
--------------

::

    请更新 TqSdk 的 Codex 使用文档。
    目标是让内容更贴近 OpenAI 官方当前推荐的 Codex 工作流。
    保留现有文档风格，但不要写成通用 IDE 教程。
    修改后请运行 Sphinx dummy 构建并报告结果。

使用 Codex 时的注意事项
========================

对于 TqSdk 项目，下面几点尤其重要：

* **不要提供真实交易凭证**：账号、密码、CTP 凭证、私钥应使用占位符或环境变量。
* **把数据和联网前提说清楚**：如果某个脚本依赖外部行情服务、私有接口或内网数据库，要提前告诉 Codex。
* **优先让它做最小修改**：策略类项目对行为变化很敏感，尽量避免“大改一遍”的任务描述。
* **总是要求验证**：没有验证的“看起来合理”并不等于可用。
* **把限制写进 AGENTS.md**：这比在每次任务里重复说明更稳定。

总结
=====

对于 TqSdk 用户，Codex 的价值不在于“像编辑器助手一样回答问题”，而在于它可以围绕一个真实仓库接收任务、执行修改、运行验证并输出结果。只要您把仓库、环境、约束和完成标准准备好，Codex 非常适合承担以下工作：

* 策略与回测脚本的小步迭代。
* TqSdk 源码与现有业务代码的联合分析。
* 文档、示例和 PR 的持续维护。
* 以“读代码 -> 修改 -> 验证 -> 总结”为链路的完整工程任务。

如果您准备在 TqSdk 项目里长期使用 Codex，最值得先投入的工作不是写更多提示词，而是把 ``AGENTS.md``、验证命令和仓库结构整理好。这样 Codex 才能真正稳定地成为一个工程协作助手。
