# 代码规范

  + 要求遵循 PEP-8 但不强制要求单行 80 个字符以内，原因见 https://lkml.org/lkml/2020/5/29/1038
  + 日志应输出到 stderr 或文件, 并允许通过配置/选项关闭或重定向
  + 所有输入输出都应该通过接口完成，不应 print 屏幕，不应产生文档中没有提到的副作用
  + 不应给用户惊喜，任何可能有副作用的操作都应由用户明确许可
  + 尽量保持兼容性，不应随意 break 他人的代码

# commit规范

一个提交说明应当包含3个部分：标题（必写，包含模块和主题），正文（可选）和尾注（可选），三个部分间分别用一个空行分隔，如下所示:
```
module: subject

body

footer
```

## 标题
标题的格式为 模块名称: 主题，末尾不加标点符号。其中，模块名称为py文件路径，主题应该是一句简要的话，说明本次提交做了什么。

## 正文
正文是可选部分。当提交涉及的内容比较复杂时，可以在正文部分详细描述本次提交“是什么”和“为什么”的问题。写正文时，请注意以下问题:
  + 读者未必准确解决的问题是什么。**即使问题在 issue tracker 中已经写明，也应把问题再描述一遍**，并可以在尾注部分引用对应问题编号
  + 如果你做了关键性的决策，比如选择了解决方案A而非B，请写下你做此选择的原因
  + 如果判定提交代码的正确性，需要依赖某些信息（例如根据交易所的某业务规则变更公告修改算法，则这个公告内容就是关键信息），这些信息又没有写入代码注释中，那么应该在这里写明
  + 如果本次提交会带来某些副作用（比如修正某BUG，但会使内存占用升高一倍），请务必明确写出

## 尾注
尾注是可选部分。在尾注部分，标记与此次 commit 相关的 issue id, 使用以下标志：
  + fixes: #XXX 解决了 XXX 所提及的问题
  + see also: #XXX 本次提交与 XXX 有关
  
## 提交说明示例

https://github.com/golang/go/commit/be64a19d99918c843f8555aad580221207ea35bc
```
cmd/compile, cmd/link, runtime: make defers low-cost through inline code and extra funcdata

Generate inline code at defer time to save the args of defer calls to unique
(autotmp) stack slots, and generate inline code at exit time to check which defer
calls were made and make the associated function/method/interface calls. We
remember that a particular defer statement was reached by storing in the deferBits
variable (always stored on the stack). At exit time, we check the bits of the
deferBits variable to determine which defer function calls to make (in reverse
order). These low-cost defers are only used for functions where no defers
appear in loops. In addition, we don't do these low-cost defers if there are too
many defer statements or too many exits in a function (to limit code increase).

When a function uses open-coded defers, we produce extra
FUNCDATA_OpenCodedDeferInfo information that specifies the number of defers, and
for each defer, the stack slots where the closure and associated args have been
stored. The funcdata also includes the location of the deferBits variable.
Therefore, for panics, we can use this funcdata to determine exactly which defers
are active, and call the appropriate functions/methods/closures with the correct
arguments for each active defer.

In order to unwind the stack correctly after a recover(), we need to add an extra
code segment to functions with open-coded defers that simply calls deferreturn()
and returns. This segment is not reachable by the normal function, but is returned
to by the runtime during recovery. We set the liveness information of this
deferreturn() to be the same as the liveness at the first function call during the
last defer exit code (so all return values and all stack slots needed by the defer
calls will be live).

I needed to increase the stackguard constant from 880 to 896, because of a small
amount of new code in deferreturn().

The -N flag disables open-coded defers. '-d defer' prints out the kind of defer
being used at each defer statement (heap-allocated, stack-allocated, or
open-coded).

Cost of defer statement  [ go test -run NONE -bench BenchmarkDefer$ runtime ]
  With normal (stack-allocated) defers only:         35.4  ns/op
  With open-coded defers:                             5.6  ns/op
  Cost of function call alone (remove defer keyword): 4.4  ns/op

Text size increase (including funcdata) for go binary without/with open-coded defers:  0.09%

The average size increase (including funcdata) for only the functions that use
open-coded defers is 1.1%.

The cost of a panic followed by a recover got noticeably slower, since panic
processing now requires a scan of the stack for open-coded defer frames. This scan
is required, even if no frames are using open-coded defers:

Cost of panic and recover [ go test -run NONE -bench BenchmarkPanicRecover runtime ]
  Without open-coded defers:        62.0 ns/op
  With open-coded defers:           255  ns/op

A CGO Go-to-C-to-Go benchmark got noticeably faster because of open-coded defers:

CGO Go-to-C-to-Go benchmark [cd misc/cgo/test; go test -run NONE -bench BenchmarkCGoCallback ]
  Without open-coded defers:        443 ns/op
  With open-coded defers:           347 ns/op

Updates #14939 (defer performance)
Updates #34481 (design doc)

Change-Id: I63b1a60d1ebf28126f55ee9fd7ecffe9cb23d1ff
Reviewed-on: https://go-review.googlesource.com/c/go/+/202340
Reviewed-by: Austin Clements <austin@google.com>
```
