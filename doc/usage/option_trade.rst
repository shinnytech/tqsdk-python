.. _option_trade:

期权交易
====================================================

TqSdk 支持期权的模拟、实盘和回测功能，其中期权合约代码格式参考如下::

	DCE.m1807-C-2450 - 大商所豆粕期权
	CZCE.CF003C11000 - 郑商所棉花期权
	SHFE.au2004C308 - 上期所黄金期权
	CFFEX.IO2002-C-3550 - 中金所沪深300股指期权


为了更好的服务不同需求客户，TqSdk 目前对期权交易权限做了限制，在 TqSdk 中使用 TqAccount 指定账户进行期权交易的用户需要申请 `TqSdk 期权交易权限 <https://www.shinnytech.com/tqsdk-apply-permission/>`_，开通完成之后即可以 快期模拟账户或实盘账户进行期权交易，参考代码如下::

    from tqsdk import TqApi, TqAccount
    
    api = TqApi(TqAccount("快期模拟", "论坛邮箱账户", "论坛密码"), auth="论坛邮箱账户,论坛密码")
    order = api.insert_order("DCE.i2009-C-590", "BUY", "OPEN", 1, limit_price=70)  # 大商所只支持限价单
    while True:
        api.wait_update()
        if order.status == "FINISHED" and order.volume_left == 0:
            print("权限已开通，订单已完成")
            break

    api.close()

对于未使用 TqAccount 的策略程序，无需授权即可使用TqSim模拟交易期权或进行回测

需要注意由于期权指标有使用 :py:meth:`~tqsdk.api.TqApi.get_kline_serial` 获取多合约k线，而回测暂不支持获取多合约k线，所以目前回测时如果要获取期权计算指标则会报错


期权指标计算&序列计算函数
----------------------------------------------------
TqSdk 内提供了丰富的期权指标计算&序列计算函数，参考如下：

* :py:meth:`~tqsdk.ta.OPTION_GREEKS` - 期权希腊指标
* :py:meth:`~tqsdk.ta.OPTION_IMPV` - 计算期权隐含波动率
* :py:meth:`~tqsdk.ta.OPTION_VALUE` - 期权内在价值，期权时间价值
* :py:meth:`~tqsdk.tafunc.get_bs_price` - 计算期权 BS 模型理论价格
* :py:meth:`~tqsdk.tafunc.get_delta` - 计算期权希腊指标 delta 值
* :py:meth:`~tqsdk.tafunc.get_gamma` - 计算期权希腊指标 gamma 值
* :py:meth:`~tqsdk.tafunc.get_rho` - 计算期权希腊指标 rho 值
* :py:meth:`~tqsdk.tafunc.get_theta` - 计算期权希腊指标 theta 值
* :py:meth:`~tqsdk.tafunc.get_vega` - 计算期权希腊指标 vega 值
* :py:meth:`~tqsdk.tafunc.get_his_volatility` - 计算某个合约的历史波动率
* :py:meth:`~tqsdk.tafunc.get_t` - 计算 K 线序列对应的年化到期时间，主要用于计算期权相关希腊指标时，需要得到计算出序列对应的年化到期时间


