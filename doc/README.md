# 文档构建与引用检查

在仓库根目录安装 `requirements.txt` 中的文档依赖，并准备 Pandoc，然后执行：

```console
python -m sphinx -b html -W --keep-going -E doc build/doc
python doc/check_links.py build/doc
```

严格构建会检查 Python 对象和章节引用；HTML 检查会遍历站内链接，验证目标文件和锚点真实存在。
首次构建需要联网读取 Python、pandas 的官方文档索引；HTML 检查不需要联网。

函数签名和章节标题后的链接图标支持点击或聚焦后按 Enter 复制完整链接，并显示“链接已复制”。
复制时去掉搜索结果的 `highlight` 参数，保留页面路径、其他参数和对应锚点。
浏览器不支持 Clipboard API 或拒绝写入时，明确提示右键复制链接地址，不显示复制成功。
原始锚点链接仍然保留，支持右键菜单、Ctrl/Cmd 点击以及禁用 JavaScript 后的跳转。
修改相关交互后，需在构建产物中验证鼠标和键盘复制、失败提示、锚点定位及代码块复制。

正文介绍接口、类或字段时，使用明确的 Sphinx 交叉引用。例如：

```rst
:py:meth:`get_quote() <tqsdk.TqApi.get_quote>`
:py:class:`quote <tqsdk.objs.Quote>`
:py:attr:`quote.last_price <tqsdk.objs.Quote.last_price>`
:py:func:`~tqsdk.tafunc.ma`
```

`quote` 是示例变量名，链接目标是它的对象类型 `tqsdk.objs.Quote`。
普通的双反引号只表示代码样式，不会生成链接。代码块、参数值、文件名及没有对应 API 的局部变量可以继续使用普通代码样式。

以 API 参考页登记的名称作为链接目标，例如 `tqsdk.TqApi.wait_update`。
新增返回类型时，应同时补上相应参考条目。历史接口已经下线时保留历史说明，并指出当前入口。
不要通过忽略引用警告掩盖缺失的文档目标；`_ext/tqsdk_xrefs.py` 仅处理类型注解中的已知别名。
