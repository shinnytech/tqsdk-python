---
name: tqsdk-trading-and-data
description: "使用 TqSdk Python SDK 获取行情与历史数据、编写或排查交易与回测程序，并在需要本地运行时检查环境、安装缺失的 TqSdk。适用于明确使用 TqSdk、TqApi、TargetPosTask 等接口的开发、数据和账户问题；通用金融问答或其他数据产品不必使用本技能。"
---

# TqSdk Trading and Data

用实际接口完成用户的 TqSdk 任务。先确定任务和运行环境，按需读取专题参考，再生成最小可运行方案并验证结果。技能包是使用说明，不是已安装的 SDK，也不代表已经连接任何账户。

## 开始处理

1. **确认任务范围。** 区分接口解释、代码编写、本地执行和实盘操作。尊重用户指定的账户、合约、时间范围和项目约束；只有缺少会影响结果的必要信息时才询问。
2. **需要本地运行时，先检查环境。** 用项目实际运行脚本的解释器执行 [scripts/check_environment.py](scripts/check_environment.py)。只解释接口时不必安装软件。若状态为 `not_installed`，按 [environment-setup.md](references/environment-setup.md) 在当前项目环境中安装 TqSdk，验证导入后继续任务。已有版本可用时不自动升级；导入损坏不能当成未安装处理。
3. **以用户版本为准。** 优先检查已安装 SDK 的签名、docstring 和相关源码；有仓库时参考对应版本的源码。发布文档和技能示例可能比用户版本新，不要虚构接口或为了一个示例擅自升级。技能内的仓库路径不保证存在于用户电脑上，替代入口见 [example-map.md](references/example-map.md)。
4. **选择运行模式。** 仅取数或无账户要求的入门程序可显式用 `TqSim()`；用户要求快期模拟、实盘或股票账户时保留该选择。`TqAuth` 是快期服务认证，`TqAccount` 是期货资金账户。实盘登录失败时报告错误，不能悄悄换成模拟账户。
5. **验证并交付。** 先做语法和导入检查，再按任务验证实际数据、输出文件或回测结果。缺少认证时继续完成可离线验证的部分，明确未运行的步骤。报告使用的解释器、SDK 版本和实际验证结果；不能把语法通过说成行情或交易成功。

## 按任务读取

| 当前任务 | 参考文件 |
| --- | --- |
| 安装、解释器、依赖或导入错误 | [environment-setup.md](references/environment-setup.md) |
| `wait_update`、`is_changing`、超时与异步通知 | [wait-update-and-update-loop.md](references/wait-update-and-update-loop.md) |
| 行情、K 线、Tick、合约发现和历史下载 | [market-data.md](references/market-data.md) |
| 选择本地模拟、快期模拟、实盘、股票或多账户 | [account-type-matrix.md](references/account-type-matrix.md) |
| 读取资金、持仓、委托、成交 | [accounts-and-trading.md](references/accounts-and-trading.md) |
| 手工下单、撤单、目标持仓、调度执行和最小开仓手数 | [order-functions-and-position-tools.md](references/order-functions-and-position-tools.md) |
| 数据与账户对象的字段含义 | [object-fields.md](references/object-fields.md) |
| 模拟与历史回测 | [simulation-and-backtest.md](references/simulation-and-backtest.md) |
| 保证金、风险度和 `TqScenario` 试算 | [scenario-and-margin.md](references/scenario-and-margin.md) |
| 运行错误与排查顺序 | [error-faq.md](references/error-faq.md) |
| 官方示例、文档和源码定位 | [example-map.md](references/example-map.md) |

## 编写代码时保持的规则

- `get_*` 通常返回持续更新的引用。订阅一次并保存对象，用 `wait_update()` 推进，再用 `is_changing()` 或明确的就绪条件处理相关更新。需要历史快照时显式复制；不要通过反复订阅或 `sleep()` 等待数据。
- K 线 `iloc[-1]` 是正在形成的柱。按收盘信号交易时，在新柱出现后使用 `iloc[-2]` 和已完成的窗口；检查长度、`NaN` 和数据时间。回测保持用户原有信号、撮合和估值时点，不用未来数据。
- 当前行情示例优先使用 `KQ.m@...` 主连；主连不能直接下单。交易用用户指定或已核实的真实合约，必要时读取主连的 `underlying_symbol`；不能把合约列表第一项当成主力。历史回测按目标日期核实合约覆盖，不用今天的 `expired=False` 排除历史合约。
- `insert_order()` 返回不代表成交，`FINISHED` 也可能是撤单或拒单。结合 `volume_left`、`last_msg` 和成交记录判断；有时限时报告实际状态，不能将超时当作已撤单。
- 同一账户、同一合约选择一种持仓控制方式。不要把 `TargetPosTask` 与手工下单混用；股票账户不使用期货 `offset` 或 `TargetPosTask`。多账户操作明确传入 `account=`。
- 用环境变量、交互式隐藏输入或项目已有安全配置提供凭据，不把真实密码写进示例、日志或聊天。安装、导入和只读取数不包含实盘下单授权；执行实盘下单或撤单前，确认操作参数在用户已有授权范围内。
- API 会话用上下文管理器或 `finally: api.close()` 释放。回测处理 `BacktestFinished`，交互式取数在需要时设置合理超时并报告是否收到有效数据。
- `TqScenario` 只做期货快照试算。计算当前账户风险时显式传入该账户权益；说明保证金数据来自行情还是账户查询及可能的回退。试算结果不保证真实可成交手数，详细限制按需读取专题参考。
