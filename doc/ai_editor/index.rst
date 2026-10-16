.. _ai_editor:

通过 AI 工具使用 TqSdk
========================================

从官方 Skills 开始，让 AI 按 TqSdk 的实际接口和运行规则帮你完成需求。

.. include:: ../_includes/tqsdk_ai_agent_intro.rst

接下来可以直接提需求，例如：“获取螺纹钢主连最近 200 根 1 分钟 K 线，保存为 CSV。”需要本地运行时，AI 会先检查解释器和依赖，再生成、运行并核对结果。已有项目会沿用原来的环境和版本约束。

给 AI 说明 **想做什么、运行模式、合约和期望结果**；如果知道 SDK 版本和账户类型，也一起提供。排错时附上去除账号密码后的异常。初次尝试交易程序可先使用本地模拟；已有明确账户模式时按该模式处理，实盘下单与撤单需有对应授权。

AI 工具接入
----------------------------------------

.. toctree::
    :maxdepth: 1

    tqsdk_trae.rst
    tqsdk_codebuddy.rst
    tqsdk_codex.rst

TqSdk Skills
----------------------------------------

.. toctree::
    :maxdepth: 1

    tqsdk_skills.rst
