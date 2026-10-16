.. _tqsdk_codex:

====================================================
使用 ChatGPT 中的 Codex 开发 TqSdk 项目
====================================================

现在可以在 **ChatGPT 桌面应用中选择 Codex**，让它读取项目、编写策略、修改文件并运行验证。本页从打开本地策略目录开始，带你完成第一个 TqSdk 行情任务。

1. 打开 ChatGPT，选择 Codex
====================================================

#. 从 `ChatGPT 下载页面 <https://chatgpt.com/download/>`_ 安装适合自己系统的桌面应用。
#. 打开应用，使用 ChatGPT 账户登录。
#. 从 **ChatGPT 下拉菜单中选择 Codex**。
#. 打开自己的策略项目文件夹，或为第一个示例准备一个新文件夹。
#. 在这个项目中开始新对话，描述希望完成的任务。

选择文件夹后，Codex 才能在对应项目中读取和修改本地文件。如果已有策略项目，直接打开项目根目录，让它同时看到策略、依赖文件和说明文档。入口与操作说明见 `ChatGPT 桌面应用指南 <https://learn.chatgpt.com/docs/app>`_ 和 `官方快速入门 <https://developers.openai.com/codex/quickstart>`_。

2. 先把 TqSdk Skills 交给 Codex
====================================================

在新对话中先发送下面这段提示词，让 Codex 按 TqSdk 的接口和运行规则工作：

.. code-block:: text

    请先下载并解压 TqSdk 官方技能包：
    https://doc.shinnytech.com/tqsdk/latest/ai_editor/skills/tqsdk-trading-and-data.zip
    先阅读其中的 SKILL.md，再按任务读取 references/ 中的说明。
    如果需要在本地运行代码，请先检查项目的 Python 环境和 TqSdk；
    未安装时按项目依赖要求安装到该环境，验证能导入后再继续，
    不要自动升级已有版本。

如果当前环境无法下载，可以手动下载并解压到项目目录，再告诉 Codex 所在路径。保留完整的 ``SKILL.md``、``references/`` 和脚本目录，详细说明见 :ref:`tqsdk_skills`。

3. 从打印一次行情开始
====================================================

接着发送一个简单、可以直接检查结果的任务：

.. code-block:: text

    请在当前项目中创建 hello_tqsdk.py。
    使用 TqSdk 获取 SHFE.rb2701 的行情，用 print(quote) 打印一次后关闭 API。
    先不要加入循环；快期账户和密码使用占位符，不要写入真实凭证。
    只获取行情，不发送交易委托。
    请检查代码语法，并告诉我如何用当前项目的 Python 运行它。

``SHFE.rb2701`` 是固定月份的示例合约；运行时请使用仍在交易的合约。生成后先查看文件和运行说明，再在本地填写登录信息运行。没有可用登录信息时，语法和导入检查可以完成，真实行情验证需要登录后进行。

第一个程序跑通后，在同一个对话中继续：

.. code-block:: text

    请把 hello_tqsdk.py 改成持续打印行情时间和最新价。
    在循环外调用一次 get_quote()，在 while True 循环里调用 wait_update()，
    等待更新后读取 quote.datetime 和 quote.last_price。
    请解释这两行循环代码如何配合，以及怎样停止程序。

对应的完整示例见 :ref:`quickstart`。随后可以继续要求读取 K 线、运行本地模拟策略或编写历史回测。

4. 让 Codex 检查环境并验证结果
====================================================

已有项目应沿用原来的 Python 环境和依赖约束。可以让 Codex 先报告解释器路径、TqSdk 版本，再执行与本次任务有关的检查。

一个最小的导入检查是：

.. code-block:: console

    python -c "import tqsdk; print(tqsdk.__version__)"

新建的独立策略环境需要安装 TqSdk 时，可使用：

.. code-block:: console

    python -m pip install tqsdk

编写策略时，可以把完成标准直接附在任务后面：

.. code-block:: text

    请先说明准备修改哪些文件，保留其他未提交改动。
    修改后执行与任务相关的语法、导入或测试检查。
    报告实际运行的命令、结果，以及哪些部分还没有验证。
    如果检查需要行情服务或登录信息，请说明具体前提。

语法通过、成功导入和实际收到行情是不同的验证结果。回测还应检查成交记录、手续费和保证金；模拟下单还应检查委托状态和最终持仓。让 Codex 根据任务报告这些结果，便于判断程序是否完成。

需要排查 SDK 实现时，补充源码
====================================================

编写自己的策略时，使用策略项目和 TqSdk Skills 即可开始。需要解释 API 实现、排查行为差异或修改 SDK 时，再把 TqSdk 源码提供给 Codex。

在终端中选择 GitHub 或 Gitee 的一个地址下载：

.. code-block:: console

    git clone https://github.com/shinnytech/tqsdk-python.git

或：

.. code-block:: console

    git clone https://gitee.com/tianqin_quantification_tqsdk/tqsdk-python.git

下载后，在 ChatGPT 的 Codex 中打开 ``tqsdk-python`` 根目录。若准备修改 SDK，可在专用 Python 环境中安装源码和项目依赖：

.. code-block:: console

    python -m pip install -r requirements.txt
    python -m pip install -e .

然后给出具体任务，例如：

.. code-block:: text

    请阅读 tqsdk/api.py 和我的策略文件，
    解释 wait_update() 返回后哪些数据可能发生变化。
    结合当前实现和相关示例说明，只做分析。

继续开发时怎么提需求
====================================================

* **排查问题：** 提供相关文件、去除账号密码后的异常，以及期望与实际行为，例如“回测结束但没有成交，请定位原因并做最小修复”。
* **修改策略：** 写明允许修改的文件、开平仓规则和验证方式，例如“在现有策略中增加止损参数，并核对模拟委托和最终持仓”。
* **修改文档：** 明确目标读者和示例要求，并要求运行文档构建。
* **审查改动：** 让 Codex 检查代码差异、API 用法、测试结果和未覆盖的情况，再决定是否提交或发起 PR。

账户密码、私钥等信息应在本地配置，不要放进提示词、日志或代码提交中。行情和回测任务需要的网络、数据与账户权限也应提前说明。

官方入口与参考资料
====================================================

* `ChatGPT 下载页面 <https://chatgpt.com/download/>`_
* `ChatGPT 桌面应用指南 <https://learn.chatgpt.com/docs/app>`_
* `官方快速入门：选择 Codex 并打开项目 <https://developers.openai.com/codex/quickstart>`_
* `Codex CLI：在终端使用 <https://learn.chatgpt.com/docs/codex/cli>`_
* `Codex IDE 扩展：在代码编辑器中使用 <https://learn.chatgpt.com/docs/codex/ide>`_
