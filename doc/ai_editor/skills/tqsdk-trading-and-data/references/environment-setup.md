# 环境检查与缺失依赖安装

在需要本地运行 TqSdk 程序时使用。解释概念、只审查代码或用户要求不执行时，不必安装。

## 选择正确的解释器

先检查项目已有的 `.venv`、Conda 环境、IDE/Notebook 内核和 `pyproject.toml`、requirements 或锁文件。沿用项目约定；多环境并存时以实际运行目标程序的解释器为准，不能只看终端的裸 `pip`。

在目标项目目录中，用选定解释器运行技能目录中的 `scripts/check_environment.py`，脚本路径相对技能根目录，不是用户项目根目录。检查时包含当前工作目录，便于发现本地同名模块遮蔽：

```console
python /path/to/tqsdk-trading-and-data/scripts/check_environment.py
```

将 `python` 替换成已经核实的解释器路径。Windows PowerShell 中，带空格的路径用 `& "C:\path\to\python.exe" ...` 调用。检查脚本不安装软件、不联网、不创建 API 会话；输出当前解释器、SDK 版本和导入路径，不读取账户凭据。

| 状态 / 退出码 | 接下来做什么 |
| --- | --- |
| `ready` / 0 | 沿用当前环境。确认 `module_path` 是预期安装或源码位置，然后继续任务。 |
| `not_installed` / 1 | 在这个项目环境中安装，再重新检查。 |
| `import_error` / 2 | 排查依赖损坏、版本冲突或本地同名模块；不要直接判定为缺少 TqSdk。 |
| `python_too_old` / 3 | 选择满足项目与 TqSdk 版本要求的 Python；当前文档最低为 3.9。 |

如果没有可用 Python，说明具体缺项，按用户系统和项目要求选择解释器；不要向无关系统环境安装。不同 SDK 版本的 `Requires-Python` 以所选包元数据为准。

## TqSdk 未安装时先安装

如果任务需要运行代码且允许执行工具，直接在任务范围内完成缺失依赖安装，再继续原任务，不要停在“你可以安装”的建议。遵守执行环境自身的权限要求；没有安装或联网权限时报告具体阻碍和可执行命令，不声称安装成功。

- **已有项目环境和依赖约束**：使用项目既有包管理方式安装缺失依赖，遵守指定版本及锁文件。不要覆盖锁文件、修改其他依赖或先卸载已有版本。
- **新项目、没有环境**：在项目目录创建 `.venv`，再用其中的解释器安装。不覆盖已存在的 `.venv`。

Windows PowerShell（仅用于新建环境）：

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install tqsdk
& .\.venv\Scripts\python.exe -c "import tqsdk; print(tqsdk.__version__); print(tqsdk.__file__)"
```

macOS / Linux（仅用于新建环境）：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install tqsdk
.venv/bin/python -c "import tqsdk; print(tqsdk.__version__); print(tqsdk.__file__)"
```

已有环境只需执行对应解释器的 `-m pip install tqsdk`；如果项目固定版本，用项目要求的版本替换包名，或执行项目规定的同步命令。不要默认加 `--upgrade`、`--user`、`sudo` 或关闭证书校验。安装成功后重新运行检查脚本，并用同一解释器运行用户程序。

包来源使用项目配置的可信索引或 [PyPI TqSdk](https://pypi.org/project/tqsdk/)。环境与安装原则参考 [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/installing-packages/)。

## 已安装但不可用

- `ModuleNotFoundError: tqsdk`：先核对实际解释器与安装解释器是否一致。
- 缺失 `numpy` 等其他模块、DLL 加载失败或包版本冲突：按完整异常定位具体依赖；`import_error` 不代表应该重新装 TqSdk。
- 导入到了项目中的 `tqsdk.py` 或同名目录：检查遮蔽问题。不要擅自删除用户文件；提出或实施任务所需的可审查改名修复。
- Notebook：用内核的 `sys.executable` 检查和安装，安装后必要时重启内核。
- SDK 源码开发项目：沿用项目开发安装流程，通常为对应环境的 `python -m pip install -e .`，不要用 PyPI 包替换工作区源码。

## 安装之后

导入成功只说明环境就绪。接下来根据需求读取行情、交易或回测参考；登录仍需要快期认证，实盘还需要正确的资金账户与授权。没有凭据时可完成语法/导入验证，说明实际取数或交易尚未执行；不要请求用户把密码粘贴到聊天中。
