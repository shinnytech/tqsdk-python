.. _version:

版本变更
=============================
2.8.4 (2021/08/31)

* 修复：由于缺少初始合约文件，TqApi 初始化可能失败的问题


2.8.3 (2021/08/30)

* 增加：is_changing 接口增加对于委托单 :py:meth:`~tqsdk.objs.Order.is_dead`、:py:meth:`~tqsdk.objs.Order.is_online`、
  :py:meth:`~tqsdk.objs.Order.is_error`、:py:meth:`~tqsdk.objs.Order.trade_price` 字段支持判断是否更新
* 修复: TqApi 初始化可能失败的问题
* 优化: 将已知下市合约直接打包在代码中，缩短 TqApi 初始化时间
* docs: 完善主力切换规则说明，将阿里源替换为清华源


2.8.2 (2021/08/17)

* 增加：is_changing 接口增加对于合约 :py:meth:`~tqsdk.objs.Quote.expire_rest_days`，持仓 :py:meth:`~tqsdk.objs.Position.pos_long`、
  :py:meth:`~tqsdk.objs.Position.pos_short`、:py:meth:`~tqsdk.objs.Position.pos` 字段支持判断是否更新
* 修复：2.8.1 版本重构后，不支持多线程运行的问题
* docs: 更新合约字段示例说明


2.8.1 (2021/08/12)

* 增加：增强在协程中的支持，以下接口 :py:meth:`~tqsdk.api.TqApi.query_quotes`，:py:meth:`~tqsdk.api.TqApi.query_cont_quotes`，
  :py:meth:`~tqsdk.api.TqApi.query_options`，:py:meth:`~tqsdk.api.TqApi.query_atm_options`，
  :py:meth:`~tqsdk.api.TqApi.query_symbol_info`，:py:meth:`~tqsdk.api.TqApi.query_all_level_options`，
  :py:meth:`~tqsdk.api.TqApi.query_all_level_finance_options`，支持协程中
  ``in_options, at_options, out_options = await api.query_all_level_finance_options("SSE.510300", 4.60, "CALL", nearbys = 1)`` 写法，参考文档：:ref:`multi_async_task`
* 修复：target_pos_task 优化报错提示，已经结束的 TargetPosTask 实例再调用 set_target_volume 设置手数会报错。参考文档：:py:meth:`~tqsdk.lib.target_pos_task.TargetPosTask.cancel`
* 修复：下载历史数据时，某些数据未按照最小价格变动单位保留相应小数位数的问题
* 重构：优化 wait_update、is_changing 接口的实现，增强对协程的支持
* docs：完善回测字段规则文档说明


2.8.0 (2021/08/05)

* 增加：**支持免费用户每日回测 3 次**


2.7.2 (2021/07/30)

* 增加：**支持在回测中使用 query 系列函数，查询结果为回测当天的合约信息**
* 增加：Quote 对象增加 underlying_quote 属性，值是一个 Quote 对象（为 underlying_symbol 属性对应的合约引用）或者是 None
* web_gui: 修复在 safari 和 firefox 无法正常显示的问题
* docs: 完善支持用户自助购买文档


2.7.1 (2021/07/21)

* 修复: query 系列查询看跌期权时，未返回指定的实值、平值、虚值序列的问题
* docs: 完善 position 文档说明
* docs: 补充期权示例


2.7.0 (2021/07/15)

* 增加：**去除 Cython 编译，本地代码全部开源**
* 增加：**支持 ARM 架构下 CPU 的安装使用**
* 增加：TqApi 增加 :py:meth:`~tqsdk.api.TqApi.query_all_level_finance_options` 接口，支持查询指定当月、下月、季月等到期月份的金融期权。
* 增加：支持上期能源下载 ticks 5 档行情
* 修复：某些参数可能造成 twap 无法执行的问题
* 修复：客户端发送的 variables 中变量值不支持空字符串、空列表或者列表中包括空字符串
* 删除：为期权持仓、成交、委托单对象添加部分期权合约信息的功能（2.6.5 增加功能）
* doc: 添加隔夜开盘抢单示例，不再建议用户自定义次席连接


2.6.6 (2021/07/05)

* 修复: 支持 pandas 1.3.0 版本
* 修复：回测中某些有夜盘的合约，报夜盘时间不在可交易时间段的问题
* web_gui: 成交列表中成交价格默认显示4位小数
* doc：完善钉钉推送文档


2.6.5 (2021/06/30)

* 增加：为期权持仓、成交、委托单对象添加部分期权合约信息，方便用户查看
* 增加：回测时，Quote 对象支持读取 expired 值
* 修复：TargetPosScheduler 最后一项等到目标持仓完成退出，最后一项设置的超时时间无效
* 修复：回测时如果先订阅日线，可能出现无法成交的问题
* doc：完善期权文档、增加 :ref:`enterprise` 文档说明


2.6.4 (2021/06/23)

* 增加：:py:class:`~tqsdk.objs.Quote` 增加 :py:class:`~tqsdk.objs.Quote.expire_rest_days` 属性，表示距离到期日天数
* 增加：TqApi 增加 :py:meth:`~tqsdk.api.TqApi.query_symbol_info` 接口，支持批量查询合约信息
* 增加：TqApi 增加 :py:meth:`~tqsdk.api.TqApi.query_all_level_options` 接口，返回标的对应的全部的实值、平值、虚值期权
* 增加：TqApi 中 :py:meth:`~tqsdk.api.TqApi.query_atm_options` 接口，扩大参数 price_level 支持范围
* 增加：sim.tqsdk_stat 增加总手续费字段
* 修复：回测中某些有夜盘的合约，报夜盘时间不在可交易时间段的问题
* 修复：回测报告中，在有期权交易时，每日收益值有错误
* 修复：回测中限制 :py:meth:`~tqsdk.api.TqApi.get_quote_list` 参数列表长度，最多支持 100 合约
* web_gui: 修复部分成交记录箭头标注位置不对的问题
* web_gui: 修复报告页面日期没有显示的问题
* web_gui: 支持代码运行中可以修改指标颜色
* web_gui: 成交列表中，部分成交价格没有按照最小变动价格保留小数位数的问题
* doc：完善期权文档
* doc：完善回测文档


2.6.3 (2021/06/11)

* 修复：twap 策略某些参数组合无法执行的问题，修改后生成随机手数可能最后一笔的下单手数小于设置的最小手数
* 修复：TqSim 模拟交易期权时，某些情况下标的行情不更新的问题
* 完善文档：增加指数、主连行情、期权使用文档说明
* web_gui: 增加回测报告图表页面（增加每日资金、每日盈亏、滚动夏普比率、滚动索提诺比率图表）
* web_gui: 指标线可以绘制虚线


2.6.2 (2021/06/03)

* 修复：在回测某些时间段时，指数无法交易的问题
* 重构：TqSim 回测统计函数重构，增加 sortino_ratio 索提诺比率指标
* 重构：算法模块中产生随机序列的方法
* 优化: target_pos_task 报错提示文字
* 优化: 网络链接建立、断连时的报错提示文字
* 优化：单线程创建多个异步任务文档完善，参考文档：:ref:`multi_async_task`
* web_gui: 修复成交量图在高分屏下高度错误的问题
* web_gui: k线文字标注为开高低收
* web_gui: 图表不显示 BoardId


2.6.1 (2021/05/27)

* 增加：增强在协程中的支持，以下接口 :py:meth:`~tqsdk.api.TqApi.get_quote`，:py:meth:`~tqsdk.api.TqApi.get_quote_list`，
  :py:meth:`~tqsdk.api.TqApi.get_kline_serial`，:py:meth:`~tqsdk.api.TqApi.get_tick_serial` 支持协程中
  ``quote = await api.get_quote('SHFE.cu2106')`` 写法，参考文档：:ref:`multi_async_task`
* 增加：:py:meth:`~tqsdk.algorithm.time_table_generater.vwap_table` 的示例代码，参考链接 :ref:`demo-algorithm-vwap`
* 优化：:py:meth:`~tqsdk.algorithm.time_table_generater.twap_table` 的示例代码，参考链接 :ref:`demo-algorithm-twap`
* 优化：在网络链接开始尝试重连时，增加通知和日志
* 修复：多次创建同合约 TargetPosTask 实例，可能抛错的问题
* 完善文档：补充期权示例文档


2.6.0 (2021/05/20)

* 增加：``tqsdk.algorithm`` 模块提供 :py:meth:`~tqsdk.algorithm.time_table_generater.vwap_table` 帮助用户完成 vwap 算法下单。
* 增加：:py:class:`~tqsdk.exceptions.TqTimeoutError` 错误类型，方便用于捕获此错误
* 增加：:py:class:`~tqsdk.lib.target_pos_task.TargetPosTask` 实例提供 :py:meth:`~tqsdk.lib.target_pos_task.TargetPosTask.cancel`、:py:meth:`~tqsdk.lib.target_pos_task.TargetPosTask.is_finished` 方法
* 修复：在异步代码中调用 get_quote 函数时，可能遇到 Task 未被引用而引发的错误
* 修复：Windows 中下载数据时，文件已经被占用而无法继续下载时，TqSdk 没有正常退出的错误
* 优化：针对初始化时的可能出现超时退出的问题，增加错误收集和提示


2.5.1 (2021/05/13)

* 增加：负责策略执行工具 :py:class:`~tqsdk.lib.target_pos_scheduler.TargetPosScheduler`，帮助用户完成复杂的下单策略，同时提供给用户极大的调整空间。文档参考 :ref:`target_pos_scheduler`
* 增加：TqSim 支持用户设置期权手续费
* 修复: 协程中调用 get_quote 可能超时的问题
* 修复: 首次登录期货账户可能会抛错的问题
* 优化：修改文档，增加测试脚本日志输出


2.5.0 (2021/04/27)

+ 增加：:py:meth:`~tqsdk.api.TqApi.get_quote_list` 接口，支持批量订阅合约。注意其参数和返回值都是 list 类型。
+ 增加：版本通知功能，后续版本升级将在 TqSdk 版本大于等于 2.5.0 以上版本做通知
+ 优化：TqApi 初始化逻辑，减少了一大半 TqApi 初始化时间


2.4.1 (2021/04/16)

* 增加：TqSim 支持 BEST / FIVELEVEL 市价单
* 修复：回测情况下可能遇到单个合约行情回退的问题
* 修复：get_position 获取持仓添加默认的 exchange_id, instrument_id
* 修复：回测时用到多合约 Kline 且其中某个合约在回测区间内下市，可能导致程序崩溃
* 重构：合约服务模块独立为一个模块，增加了查询合约服务等待时间，减少了api初始化创建失败的概率
* 完善文档


2.4.0 (2021/03/30)

* 增加：:py:class:`~tqsdk.algorithm.twap` 增加 trades，average_trade_price 属性，用于获取成交记录和成交均价
* 增加: query_cont_quotes 接口增加 has_night 参数，详情参考 :py:meth:`~tqsdk.api.TqApi.query_cont_quotes`
* 增加：**支持用户回测中设置 TqSim 的保证金和手续费**，详情参考 :py:meth:`~tqsdk.sim.TqSim.set_margin`、:py:meth:`~tqsdk.sim.TqSim.set_commission`、:py:meth:`~tqsdk.sim.TqSim.get_margin`、:py:meth:`~tqsdk.sim.TqSim.get_commission`
* 增加：**支持用户回测中使用 quote.underlying_symbol 获取主连对应的主力合约**，详情参考 :ref:`backtest_underlying_symbol`
* 修复: 回测时大于日线周期的 K 线的收盘时间错误


2.3.5 (2021/03/19)

* 增加：:py:class:`~tqsdk.algorithm.twap` 支持在多账户下使用
* 重构： TqSim 模拟交易模块，修复了 TqSim 模拟交易期权时部分字段计算错误的问题，增加测试用例覆盖，提高 TqSim 模块准确性
* 修复：:py:class:`~tqsdk.lib.TargetPosTask` 能支持多账户下使用
* 修复：之前版本下载无任何成交的合约会显示在 0% 卡住或退出程序，修改为超时（30s）之后跳过该无成交合约下载后续合约
* 完善文档：增加 TargetPosTask 大单拆分模式用法示例，修改完善期权文档等
* 依赖库升级：pandas 版本要求为 >= 1.1.0


2.3.4 (2021/03/11)

* 增加：**TargetPosTask 增加 min_volume, max_volume 参数，支持大单拆分模式**，详情参考 :py:class:`~tqsdk.lib.TargetPosTask`
* 重构 TqSim 模拟交易模块，修复了 TqSim 模拟交易时账户、持仓部分资金字段计算错误的 bug
* 修复：:py:meth:`~tqsdk.api.TqApi.query_options`, :py:meth:`~tqsdk.api.TqApi.query_atm_options` 接口中 `has_A` 参数不生效的 bug
* 修复：在使用 TargetPosTask 时，主动调用 api.close() 程序不能正常退出的错误的 bug
* 修复：回测时使用多合约 Kline 可能引起的 bug
* 修复：在节假日时回测，由于节假日当日无夜盘而导致部分夜盘品种的交易时间段错误
* 修复：web_gui 在切换合约/周期时未更新用户绘图数据的 bug
* 修复：web_gui 幅图数据默认保留两位小数显示


2.3.3 (2021/02/19)

* 修复获取交易日历接口在低版本 pandas 下结果可能出错的问题


2.3.2 (2021/02/08)

* 增加 :py:meth:`~tqsdk.api.TqApi.get_trading_calendar` 接口，支持用户获取交易日历
* 增加 :py:meth:`~tqsdk.api.TqApi.query_atm_options` 接口，支持用户获取指定档位期权
* 修复在回测时订阅当天上市的合约可能出现报错的情况
* 修复 web_gui 回测时某些情况下定位不准确的问题
* 优化 :py:meth:`~tqsdk.api.TqApi.query_quotes` , 支持用户查询交易所的全部主连或指数
* 优化 TqSim 交易失败的提示
* 优化客户端发送的数据包量，降低流量占用


2.3.1 (2021/02/01)

* 增加 t96.py macd 绘图示例，详情参考 :ref:`tutorial-t96`
* 修复获取大量合约的多合约Kline，有可能等待超时的问题
* web 优化图表，回测时图表跳转到回测时间段
* 优化测试用例、文档


2.3.0 (2021/01/20)

* 股票实盘交易即将上线
* 回测增加支持获取多合约 Kline，现在可以在回测中使用期权相关函数
* TqSim 增加属性 tqsdk_stat，提供给用户查看回测交易统计信息，详情参考 :ref:`backtest`
* 修复 twap 可能少下单的问题，增加针对 twap 的测试用例


2.2.6 (2021/01/13)

* 增加接口 :py:meth:`~tqsdk.api.TqApi.get_kline_data_series`、:py:meth:`~tqsdk.api.TqApi.get_tick_data_series`，支持 **专业版用户** 获取一段时间 K 线或 Tick 的用法
* 修复 web 需要拖拽才能更新 K 线的问题，支持自动更新 K 线
* 修复下载多合约 K 线，列名顺序错误的问题
* 修复 web 盘口总手数可能显示错误的问题
* 修复 draw_text 设置颜色无效的问题


2.2.5 (2020/12/29)

* 复权统一命名规范 "F" 表示前复权，"B" 表示后复权，请检查您的代码是否符合规范
* 修复下载复权数据时，由于下载时间段无复权信息，可能导致失败的问题
* 修复复盘时，下单可能会报错的问题
* 修复在 get_kline_serial / get_tick_serial 在 pandas=1.2.0 版本下用法不兼容的问题
* 完善期权相关文档

2.2.4 (2020/12/23)

* 修复新用户第一次安装 TqSdk 可能遇到依赖库 pyJWT 版本不兼容的错误
* 修复 web_gui 拖拽不能缩小图表的问题


2.2.3 (2020/12/22)

* 修复 twap 在退出时由于未等待撤单完成，可能造成重复下单的问题
* 修复 twap 未按时间随机，成交后立即退出的问题
* 修复在复盘模式下 TqSim 设置初始资金无效
* 修复 web 绘制线型无法设置颜色的问题
* 修复回测模式下连接老版行情服务器无法运行问题


2.2.2 (2020/12/17)

* **支持获取复权后 klines/ticks**，详情请参考文档 :py:meth:`~tqsdk.api.TqApi.get_kline_serial`、:py:meth:`~tqsdk.api.TqApi.get_tick_serial`
* **支持下载复权后 klines/ticks**，详情请参考文档 :py:class:`~tqsdk.tools.downloader.DataDownloader`
* Quote 对象增加除权表(stock_dividend_ratio)，除息表(cash_dividend_ratio) 两个字段，详情请参考文档 :py:class:`~tqsdk.objs.Quote`
* 修复 twap 算法在手数已经成交时状态没有变为已结束的 bug
* 修复文档中 reference/tqsdk.ta 页面内不能跳转连接


2.2.1 (2020/12/14)

* 修复用户使用 pyinstaller 打包文件，不会自动添加穿管认证文件和 web 资源文件的问题


2.2.0 (2020/12/08)

* **更换 web_gui 绘图引擎，极大改善 web_gui 交互性能**
* **由于后续行情服务器升级等原因，建议用户 2020/12/31 号前将 tqsdk 升级至 2.0 以上版本**
* 修复发布包中缺失 demo 文件夹的问题
* 修改 lib 示例文档


2.1.4 (2020/11/26)

* 增加计算波动率曲面函数，详情参考 :py:meth:`~tqsdk.ta.VOLATILITY_CURVE`
* **TargetPosTask 支持 price 参数为函数类型**，详情参考 :py:class:`~tqsdk.lib.TargetPosTask`
* 优化下载数据体验，已下市无数据合约提前退出
* 修复在复盘情况下会持续重复发送订阅合约请求的问题，可以改善复盘连接成功率
* 修改优化文档


2.1.3 (2020/11/20)

* 修复 twap 在某些边界条件下无法下单的 bug
* 修复 linux 平台下 web_gui 可能因为端口占用无法启动网页
* DataDownloader.get_data_series() 函数使用可能导致内存泄漏，暂时下线修复


2.1.2 (2020/11/19)

* 下载数据工具支持默认下载 ticks 五档行情
* 下载数据工具增加 get_data_series 接口，可以获取 dataframe 格式数据，详情请参考 :py:meth:`~tqsdk.tools.downloader.DataDownloader.get_data_series`
* 优化下载数据体验，无数据合约提前退出
* 修复 twap 算法可能无法持续下单的 bug
* web_gui 替换新版 logo
* web_gui 支持 K 线图放大显示


2.1.1 (2020/11/18)

* 增加 psutil 依赖包


2.1.0 (2020/11/17)

* **增加多账户功能**，详情请参考 :py:class:`~tqsdk.multiaccount`
* 优化日志模块，明确区分屏幕输出、日志文件中的日志格式，并在 TqApi 中提供参数 `disable_print`，可以禁止 TqApi 在屏幕输出内容，详情请参考 :py:class:`~tqsdk.api.TqApi`
* 修复复盘时 web_gui 时间显示错误
* 优化测试用例执行流程，支持并行运行测试
* 修改、优化优化文档
* Python >=3.6.4, 3.7, 3.8, 3.9 才能支持 TqSdk 2.1.0 及以上版本


2.0.5 (2020/11/03)

* 优化：Quote 对象增加若干字段：instrument_name、 exercise_year、exercise_month、last_exercise_datetime、exercise_type、public_float_share_quantity，详情请参考文档 :py:class:`~tqsdk.objs.Quote`
* 修改：query_options 接口参数名调整，兼容之前的用法
* 修复：CFFEX.IO 指数回测可能报错的bug
* 修复：快期模拟在 web_gui 中优化用户名显示
* 修复：未设置过 ETF 期权风控规则的账户首次设置风控规则时可能报错
* 优化文档：增加 query 系列函数返回数据类型的注释


2.0.4 (2020/10/13)

* 增加 Python 支持版本说明(3.6/3.7/3.8)
* 修复指数不能正常回测问题
* 修复 2020/08/03-2020/09/15 时间内下市合约查询失败的问题


2.0.3 (2020/09/23)

* 修复 api 对不存在合约名称的错误处理
* 增加下载委托单和成交记录的示例 :ref:`tutorial-downloader-orders`
* 增加 algorithm 算法模块，增加 :py:class:`~tqsdk.algorithm.twap` 算法以及对应的 demo 示例 :ref:`demo-algorithm-twap`


2.0.2 (2020/09/18)

* 2020/10/01 以后，免费版用户不再支持回测，下载数据等功能，`点击了解专业版和免费版区别 <https://www.shinnytech.com/tqsdk_professional/>`_
* 修改中证 500 的合约名称为 SSE.000905
* 修改 TqAccount 检查参数类型并提示用户


2.0.1 (2020/09/17)

* 股票行情正式上线，点击查看详情 :ref:`mddatas`
* 发布 TqSdk 专业版，点击查看详情 :ref:`profession`
* 支持 ETF 期权交易，支持的期货公司名单参见 `点击查看详细说明 <https://www.shinnytech.com/blog/tq-support-broker/>`_
* 提供新版合约接口服务 :py:meth:`~tqsdk.api.TqApi.query_quotes`、:py:meth:`~tqsdk.api.TqApi.query_cont_quotes`、:py:meth:`~tqsdk.api.TqApi.query_options`，替代原有 _data 用法，建议尽早换用
* 增加设置、读取 ETF 期权风控规则的接口，:py:meth:`~tqsdk.api.TqApi.set_risk_management_rule`、:py:meth:`~tqsdk.api.TqApi.get_risk_management_rule`
* 增加 TqAuth 用户认证类，使用 TqApi 时 auth 为必填参数，:py:class:`~tqsdk.auth.TqAuth`，兼容原有 auth 用法。
* 增加权限校验，提示用户限制信息
* 修改为默认不开启 debug 记录日志
* 修复 TqKq 登录失败的问题
* 修改、优化文档及测试用例


1.8.3 (2020/07/29)

* 修复：pandas 的 consolidate 函数调用可能会造成 K 线数据不更新
* 修复：api.insert_order 没有检查大商所期权不支持市价单
* 优化用户 import pandas 遇到 ImportError 时问题提示
* 更新优化文档，增加股票相关示例，更新示例中的期货合约，标注文档中 objs 对象类型说明


1.8.2 (2020/07/07)

* 增加提供高级委托指令 FAK、FOK，并增加相关文档说明 :ref:`advanced_order`、示例代码
* 本地模拟交易 sim 支持 FAK、FOK 交易指令，快期模拟暂不支持
* 优化登录请求流程
* 优化测试用例代码，增加关于交易指令的测试用例
* 完善文档内容


1.8.1 (2020/06/19)

* 增加 :py:class:`~tqsdk.account.TqKq` 账户类型，可以使用统一的快期模拟账户登录，详情点击 :ref:`sim_trading`
* 增加支持指数回测
* 支持 `with TqApi() as api` 写法
* quote 对象增加 exchange_id 字段，表示交易所代码
* 重构 sim 模块代码，便于接入新版行情服务器
* 修复 settargetpos 回测时，在一个交易时段内最后一根 K 线下单无法成交的 bug
* 修复回测时某些品种夜盘无法交易的 bug
* 修复 ticksinfo 函数在 pandas 版本低于 1.0.0 无法正常使用的 bug
* 优化日志输出，实盘下默认启用日志
* 更新 logo，整理优化文档，增加股票行情、主连获取主力等文档说明，优化示例代码目录结构
* 修改、优化测试用例及 CI 流程


1.8.0 (2020/05/12)

* 股票行情测试版发布，**_stock 参数设置为 True 可以连接测试行情服务器，提供股票数据** `详细说明请点击查看 <https://www.shinnytech.com/blog/%e5%a4%a9%e5%8b%a4%e9%87%8f%e5%8c%961-8-0_beta%ef%bc%8c%e6%94%af%e6%8c%81%e8%82%a1%e7%a5%a8%e8%a1%8c%e6%83%85%e8%8e%b7%e5%8f%96%ef%bc%81/>`_
* 增加计算 ticks 开平方向函数(详见: :py:meth:`~tqsdk.tafunc.get_ticks_info` )
* 修复 sim 撤单未检查单号是否可撤
* 重构代码，优化模块划分
* 修改测试脚本和测试用例，提高持续集成效率


1.7.0 (2020/04/16)

* **支持期权模拟交易，支持期权回测**
* 增加期权指标的计算公式 (希腊值、隐含波动率、理论价等)
* 增加TqSim模拟交易成交时间判断 (非交易时间段下的委托单将被判定为错单，以减小模拟帐号与实盘的差距)
* 增加账户、持仓中的市值字段 (如果交易了期权，则模拟帐号的账户、持仓字段的定义有一些改变(详见: :py:class:`tqsdk.objs.Account` ))
* 修复一个可能导致复盘连接失败的问题
* 优化示例代码
* 优化文档 (增加 :ref:`option_trade` 文档内容、增加在 :ref:`unanttended` 教程内容、优化文档其他细节）


1.6.3 (2020/03/16)

* 修复vscode 插件中不能登录交易的bug
* 增加免责声明
* 增加、完善测试用例
* 修改文档


1.6.2 (2020/02/18)

* 修改 web_gui 默认显示的 ip 地址为 127.0.0.1
* 修复 web_gui 不显示成交记录箭头的问题
* 策略结束后 api 将关闭所有 web 链接
* 优化对 vscode 的支持
* 增加 Quote 的 option_class (期权方向)和 product_id (品种代码)字段
* 优化文档


1.6.1 (2020/02/12)

* 修复 web_gui 不显示成交记录的问题
* 修复 python3.8 下设置 web_gui 参数无效的问题


1.6.0 (2020/02/11)

* 交易网关升级, **所有用户需升级至 1.6.0 版本以上**
* 修复参数搜索时由于 TargetPosTask 单实例造成的内存泄漏
* web_gui 参数格式改成 [ip]:port, 允许公网访问
* 改进 web 界面，增加分时图，优化盘口显示内容，修复相关问题
* 修改 barlast() 的返回值为 pandas.Series 类型序列
* 优化回测的成交时间准确性
* 完善文档内容


1.5.1 (2020/01/13)

* 优化 TqApi 参数 web_gui, 允许指定网页地址和端口(详见: :ref:`web_gui` )
* 更新优化 vscode 插件以及web 页面
* 简化画图函数color的参数
* 增加 barlast 功能函数(详见: :py:meth:`~tqsdk.tafunc.barlast` )
* 优化多合约k线报错提示及示例
* 修复 TargetPosTask 进行参数搜索时无法正确执行的bug
* 修复可能触发的回测结果计算报错的问题
* 增加测试用例
* 完善文档内容


1.5.0 (2020/01/06)

* 支持股票上线准备，增加天勤用户认证
* TqSim 的 trade_log 改为公开变量
* 完善文档内容


1.4.0 (2019/12/25)

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


1.3.2 (2019/12/19)

* 修复在填写了画图的 color 参数时引起的报错
* 修复在 vscode 插件和天勤终端中不能运行策略的bug
* 完善文档内容


1.3.1 (2019/12/18)

* 支持通过 :py:class:`tqsdk.api.TqApi` 内 **设置 web_gui=True 参数以实现实盘/回测的图像化支持** , (详见: :ref:`web_gui` )
* 增加支持 Python3.8
* 完善 TqSdk 各公开函数的参数类型标注及函数返回值类型标注
* 将 api 中除业务数据以外的所有变量私有化
* 完善测试用例
* 完善文档内容


1.2.1 (2019/12/04)

* 完善 insert_order() 函数返回的 order 的初始化字段：增加 limit_price、price_type、volume_condition、time_condition 字段
* 增加 quote 行情数据中的 trading_time、expire_datetime、delivery_month、delivery_year、ins_class 字段
* 删除 quote 行情数据中的 change、change_percent 字段
* 修复重复发送K线订阅指令给服务器的bug
* 修复未订阅行情时回测不能立即结束的bug
* 完善测试用例
* 完善文档内容


1.2.0 (2019/11/21)

* 支持同时获取对齐的多合约 K 线 (详见 :py:meth:`~tqsdk.api.TqApi.get_kline_serial` )
* 修复回测时未将非 TqSim 账号转换为 TqSim 的 bug
* 修复 wait_update() 填写 deadline 参数并等待超时后向服务器发送大量消息
* 完善测试用例
* 完善示例程序
* 完善文档内容


1.1.0 (2019/10/15)

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
