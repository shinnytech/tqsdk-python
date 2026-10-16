.. _tqsdk_skills:

========================================
TqSdk Skills 压缩包与使用说明
========================================

把完整技能包交给 AI，再用自然语言描述需求。推荐先复制下面的提示词，它会引导 AI 读取技能、检查环境，再编写和验证代码。

.. include:: ../_includes/tqsdk_ai_agent_intro.rst
   :end-before: .. tqsdk_skills_ref_marker

概述
=====

Skills 是给 AI 使用的任务说明和参考资料，帮助它选择正确的接口、理解账户模式和更新循环。它本身不是 TqSdk 软件，也不会在下载后自动运行或登录账户。

压缩包保留 ``SKILL.md``、``agents/openai.yaml``、``scripts/`` 和 ``references/`` 目录。AI 读取入口后只加载当前任务需要的参考文件；不要求你先理解全部 API。

下载压缩包
===========

`下载 tqsdk-trading-and-data.zip <skills/tqsdk-trading-and-data.zip>`_

给 OpenClaw 或本地 Agent 直接使用
=================================

使用页面顶部的“复制给 AI”，在最后补充需求，例如：“检查我的 Python 环境，获取螺纹钢主连最近 200 根 1 分钟 K 线，保存为 CSV。”

需要运行代码时，技能会引导 AI：

1. 确认当前项目使用的 Python 解释器、虚拟环境和依赖约束。
2. 检查是否能导入 TqSdk。**未安装时，先安装到同一个项目环境，再验证版本和导入路径。** 已有可用版本时继续使用，不自动升级；项目有锁定版本时遵守该版本。
3. 使用相应账户模式生成代码，运行与任务匹配的检查，说明实际结果。

如果只是在解释接口，不需要为了回答问题安装软件。缺少 Python、网络或执行权限时，AI 会说明具体缺项；快期账户认证和实盘交易授权也与安装软件分开处理。

Skills 是什么
==============

Skills 可以理解为“专门给 AI 使用的能力包”或“任务说明包”。它不是单独的一篇使用文档，而是一组按固定结构组织好的文件，告诉 AI：

* 这个主题是什么。
* 什么时候应该使用这组能力。
* 应该优先遵循什么工作流。
* 需要时再去读取哪些补充参考文件。

对于支持 skills 的 AI 产品来说，AI 可以先读取 ``SKILL.md`` 判断这组能力是否适合当前任务，再按需加载 ``references/`` 等文件，而不是每次都把整套说明一次性塞进上下文。

Skills 有什么用
================

对于 TqSdk 这类 API 较多、账户类型较多、数据与交易边界也比较多的项目，skill 的主要价值是：

* 让 AI 更快判断当前需求属于“行情、历史数据、账户查询、下单、模拟还是回测”。
* 让 AI 对照本地已安装版本的接口、官方文档和相关示例编写代码。
* 在运行前检查环境，区分“没有安装”“装到了另一个 Python”和“依赖损坏”。
* 把长说明拆成多文件，减少上下文噪声，只在需要时读取具体参考文件。
* 把容易出错的边界条件写清楚，例如 :py:class:`TqApi(auth=...) <tqsdk.TqApi>` 的默认账户、:py:meth:`insert_order <tqsdk.TqApi.insert_order>` 需要配合 :py:meth:`wait_update() <tqsdk.TqApi.wait_update>` 发出、:py:class:`TargetPosTask <tqsdk.TargetPosTask>` 不应和手工下单混用等。
* 方便直接分发给其他 AI，而不需要再手动整理成另一套提示词。

配好 Skills 后更容易解决的 TqSdk 用例
=====================================

当目标 AI 已经正确读取这组 skill 后，下面这些 TqSdk 任务通常会更容易做对，也更容易一次给出可执行结果：

* **获取实时行情**

  例如：
  “请用 TqSdk 获取当前黄金主力或指定合约的最新价、买一、卖一，并给出一个可直接运行的 Python 示例。”

* **获取 K 线或 Tick 历史数据**

  例如：
  “请用 TqSdk 获取 ``DCE.i`` 当前主力合约最近 500 根 1 分钟 K 线，并返回 pandas DataFrame 的处理示例。”

* **导出长时间区间的历史数据**

  例如：
  “请用 TqSdk 的 :py:class:`DataDownloader <tqsdk.tools.DataDownloader>` 下载 ``KQ.m@SHFE.rb`` 在 2025-01-01 到 2025-03-01 的 1 分钟数据到 CSV。”

* **选择正确的账户类型**

  例如：
  “我想做快期模拟交易，请给我 :py:class:`TqKq <tqsdk.TqKq>` 的初始化示例，并解释它和 :py:class:`TqSim <tqsdk.TqSim>` 的区别。”

* **查询资金、持仓、委托和成交**

  例如：
  “请用 TqSdk 登录后获取账户权益、可用资金、某个合约的持仓，以及当日全部委托和成交记录。”

* **试算保证金和风险度**

  例如：
  “请用 TqSdk 判断当前持仓下还能再开多少手螺纹钢，或者把某个品种保证金率调到 15% 后，账户风险度会变成多少。”

* **定位为什么策略没成交**

  例如：
  “请检查这段 TqSdk 策略为什么一直没有成交，是合约过期、``offset`` 填错、没调用 :py:meth:`wait_update() <tqsdk.TqApi.wait_update>`，还是账户模式不对？”

* **补全回测脚本**

  例如：
  “请把这个实时策略改成 :py:class:`TqBacktest <tqsdk.TqBacktest>` 可回测版本，并保持原有交易逻辑不变。”

这些场景的共同点是：它们都不仅仅是在问“API 名字是什么”，而是在问“应该选哪种模式、用哪套调用顺序、怎样避免典型错误”。这类问题正是 skill 比单次普通问答更有价值的地方。

压缩包内容
===========

压缩包根目录为 ``tqsdk-trading-and-data/``，其中包含：

* ``SKILL.md``: skill 的触发说明、工作流和使用规则。
* ``agents/openai.yaml``: 面向支持 skill UI 的元信息。
* ``scripts/check_environment.py``: 只读检查当前解释器、TqSdk 版本和导入路径，不联网、不安装、不连接账户。
* ``references/environment-setup.md``: 缺少 TqSdk 时的安装流程，以及虚拟环境、版本约束和导入错误排查。
* ``references/market-data.md``: 行情、K 线、Tick、合约发现和历史下载。
* ``references/accounts-and-trading.md``: 登录、资金、持仓、委托、成交、下单和撤单。
* ``references/scenario-and-margin.md``: :py:class:`TqScenario <tqsdk.TqScenario>`、实盘保证金率、保证金试算和风险度试算。
* ``references/simulation-and-backtest.md``: :py:class:`TqSim <tqsdk.TqSim>`、:py:class:`TqKq <tqsdk.TqKq>` 和回测。
* ``references/example-map.md``: 仓库内示例文件索引。
* 其他专题参考：更新循环、账户类型、字段含义、下单与目标持仓、常见错误。``SKILL.md`` 中提供完整索引。

如何给其他 AI 使用
===================

方式一：目标 AI 原生支持 skills 目录
----------------------------------------

1. 下载并解压 ``tqsdk-trading-and-data.zip``。
2. 保持 ``tqsdk-trading-and-data/`` 目录结构不变，不要只拷贝单个 ``SKILL.md``。
3. 将整个目录复制到目标 AI 的 skills 目录或导入入口中。
4. 让目标 AI 先读取 ``SKILL.md``，再按需读取 ``references/`` 中的参考文件。

方式二：目标 AI 不支持直接导入 skill
----------------------------------------

1. 下载并解压压缩包。
2. 将整个 ``tqsdk-trading-and-data/`` 文件夹作为附件、工作区目录或额外上下文提供给目标 AI。
3. 在提示词中明确要求：

   * 先阅读 ``SKILL.md``。
   * 涉及行情与历史数据时读取 ``references/market-data.md``。
   * 涉及账户、持仓、委托、成交和交易时读取 ``references/accounts-and-trading.md``。
   * 涉及 :py:class:`TqScenario <tqsdk.TqScenario>`、保证金率、保证金占用或风险度试算时读取 ``references/scenario-and-margin.md``。
   * 涉及回测或模拟环境时读取 ``references/simulation-and-backtest.md``。

方式三：在 ChatGPT 的 Codex 中使用
----------------------------------------

1. 打开 ChatGPT 桌面应用，从 ChatGPT 下拉菜单选择 Codex，并打开策略项目文件夹。
2. 将解压后的 ``tqsdk-trading-and-data/`` 目录放入项目可见位置，保留 ``agents/openai.yaml``、``scripts/`` 和 ``references/``。
3. 告诉 Codex 技能包路径，让它先阅读 ``SKILL.md``，再按任务读取参考文件。若技能已安装并被 Codex 识别，也可使用 ``$tqsdk-trading-and-data`` 调用。

从打开应用到生成第一个行情程序的完整步骤见 :ref:`tqsdk_codex`。

使用建议
=========

* 如果目标 AI 需要多文件技能包，请始终分发压缩包或完整目录，不要把多文件 skill 再手工压平为一篇长文。
* 如果只是做一次性问答，也建议至少同时提供 ``SKILL.md`` 和相关 ``references/`` 文件，避免模型只拿到不完整上下文。
