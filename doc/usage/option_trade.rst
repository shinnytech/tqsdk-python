.. _option_trade:

期权交易 & 交易所官方组合
====================================================
TqSdk 中期权交易(商品期权、金融期权和 ETF 期权)和交易所官方组合交易，均是 TqSdk 专业版中的功能

用户如果想在 TqSdk 中进行上述操作，可以点击 `天勤量化专业版 <https://www.shinnytech.com/tqsdk-buy/>`_ 申请使用或购买

TqSdk 中期权合和交易所官方组合的约代码格式参考如下::

	DCE.m1807-C-2450 - 大商所豆粕期权
	CZCE.CF003C11000 - 郑商所棉花期权
	SHFE.au2004C308 - 上期所黄金期权
	CFFEX.IO2002-C-3550 - 中金所沪深300股指期权
	SSE.10002513 - 上交所上证50etf期权
	SSE.10002504 - 上交所沪深300etf期权
	SZSE.90000097 - 深交所沪深300etf期权
	CZCE.SPD SR901&SR903 - 郑商所 SR901&SR903 跨期合约
	DCE.SP a1709&a1801 - 大商所 a1709&a1801 跨期合约



对于交易所官方组合，目前 TqSdk 中只支持交易所官方组合进行实盘交易


期权指标计算&序列计算函数
----------------------------------------------------
TqSdk 内提供了丰富的期权指标计算&序列计算函数，参考如下：

* :py:meth:`~tqsdk.ta.OPTION_GREEKS` - 计算期权希腊指标
* :py:meth:`~tqsdk.ta.OPTION_IMPV` - 计算期权隐含波动率
* :py:meth:`~tqsdk.ta.BS_VALUE` - 计算期权 BS 模型理论价格
* :py:meth:`~tqsdk.ta.OPTION_VALUE` - 计算期权内在价值，期权时间价值
* :py:meth:`~tqsdk.tafunc.get_bs_price` - 计算期权 BS 模型理论价格
* :py:meth:`~tqsdk.tafunc.get_delta` - 计算期权希腊指标 delta 值
* :py:meth:`~tqsdk.tafunc.get_gamma` - 计算期权希腊指标 gamma 值
* :py:meth:`~tqsdk.tafunc.get_rho` - 计算期权希腊指标 rho 值
* :py:meth:`~tqsdk.tafunc.get_theta` - 计算期权希腊指标 theta 值
* :py:meth:`~tqsdk.tafunc.get_vega` - 计算期权希腊指标 vega 值
* :py:meth:`~tqsdk.tafunc.get_his_volatility` - 计算某个合约的历史波动率
* :py:meth:`~tqsdk.tafunc.get_t` - 计算 K 线序列对应的年化到期时间，主要用于计算期权相关希腊指标时，需要得到计算出序列对应的年化到期时间

期权查询函数
----------------------------------------------------
TqSdk 内提供了完善的期权查询函数 :py:meth:`~tqsdk.TqApi.query_options` 和对应平值虚值期权查询函数  :py:meth:`~tqsdk.TqApi.query_atm_options` ，供用户搜索符合自己需求的期权::



    from tqsdk import TqApi, TqAuth
    api = TqApi(auth=TqAuth("快期账户", "账户密码"))

    ls = api.query_options("SHFE.au2012")
    print(ls)  # 标的为 "SHFE.au2012" 的所有期权

    ls = api.query_options("SHFE.au2012", option_class="PUT")
    print(ls)  # 标的为 "SHFE.au2012" 的看跌期权

    ls = api.query_options("SHFE.au2012", option_class="PUT", expired=False)
    print(ls)  # 标的为 "SHFE.au2012" 的看跌期权, 未下市的

    ls = api.query_options("SHFE.au2012", strike_price=340)
    print(ls)  # 标的为 "SHFE.au2012" 、行权价为 340 的期权

    ls = api.query_options("SSE.510300")
    print(ls)  # 中金所沪深300股指期权

    ls = api.query_options("SSE.510300")
    print(ls)  # 上交所沪深300etf期权

    ls = api.query_options("SSE.510300", exercise_year=2020, exercise_month=12)
    print(ls)  # 上交所沪深300etf期权, 限制条件 2020 年 12 月份行权




