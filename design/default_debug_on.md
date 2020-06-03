# 目的：

优化问题排查流程 https://shinnytech.atlassian.net/browse/BE-218

# todo：

* 默认的日志文件夹位置 `os.path.join(os.path.expanduser('~'), ".tqsdk/logs")`

* 日志文件名
    + 用户 debug=False 指定关闭日志；debug=True 使用默认生成的日志文件；debug=“path_of_file” 指定日志文件
    + 默认 `datetime('%Y%m%d%H%M%S%f')-{os.getpid()}.log` example: `20200520101101217523-2.log`
    
* debug 默认值是 None；(在 setup_connection 添加 filehandler，不需要特别处理 tqwebhelper 了)

```
log_path = ""  # 日志存放文件
if debug is None:
    log_path = _defalut_log_file if isinstance(account, TqAccount) else ""
if debug is True or isinstance(debug, str):
    log_path = debug if isinstance(debug, str) else _defalut_log_file 
```

* 统一日志打印的 format
    + 实盘 `'%(asctime)s - %(levelname)6s - %(message)s'`
    + 回测 / 复盘 `'%(levelname)6s - %(message)s'`

* 第一条日志打印 tqsdk 版本号

* api.close()  时删除最后修改时间是 N 天前的日志, 提供环境变量 TQSDK_LOG_SAVED_DAYS 用户可以设置 N，默认 30

* 日志添加对外接口的调用，调用函数名+参数
    + 增加的原则是所有用户能调到并可能产生副作用的函数
    + api.xxx 中用户接口一定需要添加 ，lib 里的 set_target_volume
    + ta / tafunc 不添加，纯算法库

* 需要限制日志文件大小吗？
    + 不需要，理由：实盘没有 backtest/sim，日志不会一下子就几十上百M，实盘用户应该每天重启策略，策略重启是一定会创建新的日志文件

* 多进程同时写日志
    + 日志名称为当前时间+进程id，不同进程日志会记录在不同的文件里
    + 使用 api.copy() 方法，全部日志都是记录在 master_api._logger 下
 
* 实盘的日志记录中有用户账户信息

fix: #179 #177 
