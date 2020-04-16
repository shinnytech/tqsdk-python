.. _version:

版本变更
=============================
1.7.0(2020/04/16)

* **支持期权模拟交易，支持期权回测**
* 增加期权指标的计算公式 (希腊值、隐含波动率、理论价等)
* 增加TqSim模拟交易成交时间判断 (非交易时间段下的委托单将被判定为错单，以减小模拟帐号与实盘的差距)
* 增加账户、持仓中的市值字段 (如果交易了期权，则模拟帐号的账户、持仓字段的定义有一些改变(详见: :py:class:`tqsdk.objs.Account` ))
* 修复一个可能导致复盘连接失败的问题
* 优化示例代码
* 优化文档 (增加 :ref:`option_trade` 文档内容、增加在 :ref:`unanttended` 教程内容、优化文档其他细节）


1.6.3(2020/03/16)

* 修复vscode 插件中不能登录交易的bug
* 增加免责声明
* 增加、完善测试用例
* 修改文档


1.6.2(2020/02/18)

* 修改 web_gui 默认显示的 ip 地址为 127.0.0.1
* 修复 web_gui 不显示成交记录箭头的问题
* 策略结束后 api 将关闭所有 web 链接
* 优化对 vscode 的支持
* 增加 Quote 的 option_class (期权方向)和 product_id (品种代码)字段
* 优化文档


1.6.1(2020/02/12)

* 修复 web_gui 不显示成交记录的问题
* 修复 python3.8 下设置 web_gui 参数无效的问题


1.6.0(2020/02/11)

* 交易网关升级, **所有用户需升级至 1.6.0 版本以上**
* 修复参数搜索时由于 TargetPosTask 单实例造成的内存泄漏
* web_gui 参数格式改成 [ip]:port, 允许公网访问
* 改进 web 界面，增加分时图，优化盘口显示内容，修复相关问题
* 修改 barlast() 的返回值为 pandas.Series 类型序列
* 优化回测的成交时间准确性
* 完善文档内容


1.5.1(2020/01/13)

* 优化 TqApi 参数 web_gui, 允许指定网页地址和端口(详见: :ref:`web_gui` )
* 更新优化 vscode 插件以及web 页面
* 简化画图函数color的参数
* 增加 barlast 功能函数(详见: :py:meth:`~tqsdk.tafunc.barlast` )
* 优化多合约k线报错提示及示例
* 修复 TargetPosTask 进行参数搜索时无法正确执行的bug
* 修复可能触发的回测结果计算报错的问题
* 增加测试用例
* 完善文档内容


1.5.0(2020/01/06)

* 支持股票上线准备，增加天勤用户认证
* TqSim 的 trade_log 改为公开变量
* 完善文档内容


1.4.0(2019/12/25)

* 在 TqSdk 中直接支持复盘功能(详见: :ref:`replay` )
* 增加回测报告内容(胜率、每手盈亏额比例)
* 从当前版本开始，不再支持天勤终端合约代码图形显示
* 修复 web_gui 功能中的部分已知问题
* 修复在一些情况无法输出回测报告的问题
* 修复使用 slave/master 多线程模式时的报错问题
* 修复回测结束前最后一条行情未更新的bug
* 从 logger 中分离从服务器返回的通知信息(以便单独处理或屏蔽)
* 修复使用 TargetPoseTask 实例时可能引发的报错
* 完善文档内容


1.3.2(2019/12/19)

* 修复在填写了画图的 color 参数时引起的报错
* 修复在 vscode 插件和天勤终端中不能运行策略的bug
* 完善文档内容


1.3.1(2019/12/18)

* 支持通过 :py:class:`tqsdk.api.TqApi` 内 **设置 web_gui=True 参数以实现实盘/回测的图像化支持** , (详见: :ref:`web_gui` )
* 增加支持 Python3.8
* 完善 TqSdk 各公开函数的参数类型标注及函数返回值类型标注
* 将 api 中除业务数据以外的所有变量私有化
* 完善测试用例
* 完善文档内容


1.2.1(2019/12/04)

* 完善 insert_order() 函数返回的 order 的初始化字段：增加 limit_price、price_type、volume_condition、time_condition 字段
* 增加 quote 行情数据中的 trading_time、expire_datetime、delivery_month、delivery_year、ins_class 字段
* 删除 quote 行情数据中的 change、change_percent 字段
* 修复重复发送K线订阅指令给服务器的bug
* 修复未订阅行情时回测不能立即结束的bug
* 完善测试用例
* 完善文档内容


1.2.0(2019/11/21)

* 支持同时获取对齐的多合约 K 线 (详见 :py:meth:`~tqsdk.api.TqApi.get_kline_serial` )
* 修复回测时未将非 TqSim 账号转换为 TqSim 的 bug
* 修复 wait_update() 填写 deadline 参数并等待超时后向服务器发送大量消息
* 完善测试用例
* 完善示例程序
* 完善文档内容


1.1.0(2019/10/15)

* 增加时间类型转换的功能函数 (详见 :py:meth:`~tqsdk.tafunc` )
* 修复与天勤连接时的一些bug
* 完善测试用例及测试环境配置
* 修改回测log内容,去除回测时log中的当前本地时间
* 完善文档内容


1.0.0 (2019/09/19)

* 修复: 各id生成方式
* 修复: 重复输出日志
* 修复: 命令行运行策略文件时,复盘模式下的参数返回值
* 添加持续集成功能
* 完善文档内容


0.9.18 (2019/09/11)

* 修复: 断线重连时触发的一系列bug
* 修复: register_update_notify 以 klines 作为参数输入时报错的bug
* 修复: 因不能删除业务数据导致的内存泄漏bug
* 部分修复: diff中的数据不是dict类型导致的bug
* 增加gui相关示例程序及文档
* 增加单元测试用例
* 完善文档内容


0.9.17 (2019/08/27)

* 修复: TqApi.copy()创建slave实例时工作不正常的bug
* 改进行情订阅信息同步到天勤的机制
* 改进TqSdk运行错误传递给天勤的机制
* 将TqApi的私有成员名字前加前缀下划线
* 增加各公开函数的返回值类型标注
* 支持使用email地址作为模拟交易账号
* 增强TargetPosTask及指标函数等内容的说明文档


0.9.15 (2019/08/14)

* 调整tqsdk与天勤的连接机制
* 去除get_order()及get_position()等函数的返回值中与业务无关的"_path", "_listener" 数据, 使其只返回业务数据
* 添加对公开函数输入值类型及范围的检查


0.9.9 (2019/07/22)

* 持仓对象 :py:class:`~tqsdk.objs.Position` 增加了实时持仓手数属性 pos_long_his, pos_long_today, pos_short_his, pos_short_today ，这些属性在成交时与成交记录同步更新
* 修正 :py:class:`~tqsdk.lib.TargetPosTask` 因为持仓手数更新不同步导致下单手数错误的bug
* 取消交易单元机制


0.9.8 (2019/06/17):

* :py:class:`~tqsdk.api.TqApi` 增加 copy 函数，支持在一个进程中用master/slave模式创建多个TqApi实例


0.9.7 (2019/06/03):

* 修正持仓数据不能 copy() 的问题


0.9.6 (2019/05/30):

* :py:class:`~tqsdk.objs.Quote`, :py:class:`~tqsdk.objs.Account`, :py:class:`~tqsdk.objs.Position`, :py:class:`~tqsdk.objs.Order`, :py:class:`~tqsdk.objs.Trade` 的成员变量名在IDE中支持自动补全(Pycharm测试可用)
* :py:class:`~tqsdk.objs.Order` 增加了 :py:meth:`~tqsdk.objs.Order.is_dead` 属性 - 用于判定委托单是否确定已死亡（以后一定不会再产生成交）
* :py:class:`~tqsdk.objs.Order` 增加了 :py:meth:`~tqsdk.objs.Order.is_online` 属性 - 用于判定这个委托单是否确定已报入交易所（即下单成功，无论是否成交）
* :py:class:`~tqsdk.objs.Order` 增加了 :py:meth:`~tqsdk.objs.Order.is_error` 属性 - 用于判定这个委托单是否确定是错单（即下单失败，一定不会有成交）
* :py:class:`~tqsdk.objs.Order` 增加了 :py:meth:`~tqsdk.objs.Order.trade_price` 属性 - 委托单的平均成交价
* :py:class:`~tqsdk.objs.Order` 增加了 :py:meth:`~tqsdk.objs.Order.trade_records` 属性 - 委托单的成交记录
* 文档细节修正


0.9.5 (2019/05/24):

* 加入期货公司次席支持, 创建 TqAccount 时可以通过 front_broker 和 front_url 参数指定次席服务器


0.9.4 (2019/05/22):

* 修正穿透式监管采集信息编码问题


0.9.3 (2019/05/22):

* (BREAKING) 模拟交易默认资金调整为一千万
* 加入穿透式监管支持. 用户只需升级 TqSdk 到此版本, 无需向期货公司申请AppId, 即可满足穿透式监管信息采集规范要求.


0.9.2 (2019/05/07):

* 修正画图相关函数


0.9.1 (2019/04/15):

* (BREAKING) TqApi.get_quote, get_kline_serial, get_account 等函数, 现在调用时会等待初始数据到位后才返回
* (BREAKING) k线序列和tick序列格式改用pandas.DataFrame
* 支持上期所五档行情
* 增加 数十个技术指标 和 序列计算函数, 使用纯python实现. 加入ta和ta_func库
* 加入策略单元支持. 在一个账户下运行多个策略时, 可以实现仓位, 报单的相互隔离
* 加强与天勤终端的协作，支持策略程序在天勤中画图, 支持回测结果图形化显示与分析, 支持策略运行监控和手工下单干预
* 示例程序增加随机森林(random_forest)策略
* 示例程序增加菲阿里四价策略


0.8.9 (2019/01/21):

* 加入双均线策略
* 加入网格交易策略
* 数据下载器支持按交易日下载数据
* 修正模拟交易数据不正确的问题
* 修正回测时出现“平仓手数不足"的问题


2018/12/12:

* 加入直连行情交易服务器模式
* 模拟交易结束后输出交易报告
* 修正回测时账户资金计算错误的问题

2018/11/16:

* 加入策略回测功能

2018/10/25:

* 加入海龟策略

2018/10/17:

* 加入 dual thrust 策略
* 加入 r-breaker 策略


2018/08/30:

* 目标持仓模型(TargetPosTask)支持上期所的平今平昨和中金所禁止平今
* K线/Tick序列加入 to_dataframe 函数将数据转为 pandas.DataFrame
* 加入 close 函数用于退出时清理各种资源
* wait_update 由设定超时秒数改为设定截止时间, 并返回是否超时
* 加入调试模式，将调试信息写入指定的文件中
* 修正和某些开发环境不兼容的问题
* 规范了各业务数据的类型
* register_update_notify 支持监控特定的业务数据


2018/08/10:

* 目标持仓Task自动处理上期所平今/平昨
* 主力合约加入 underlying_symbol 字段用来获取标的合约
* 更新文档
