.. _tqsdk2ctptest:

在 TqSdk 中调用 TqSdk2 查询保证金
=================================================
TqSdk 没有直接提供查询保证金的接口，但是你可以通过使用 TqSdk2 的直连功能来做到这个效果。tqsdk和tqsdk2可以在一个py文件中同时运行。

该方法仅支持 TqSdk2 中直连CTP 柜台时使用。受限制于 CTP 柜台的流控机制(每秒 1 笔), 短时间发送大量查询指令后, 后续查询指令将会排队等待。
为了避免盘中的查询等待时间, 建议盘前启动程序, 对标的合约提前进行查询::

    from tqsdk import TqApi, TqAuth, TqAccount
    import tqsdk2

    account = tqsdk2.TqCtp(front_url, front_broker, app_id, auth_code, account_id, password)
    api_margin = tqsdk2.TqApi(account = account, auth=tqsdk2.TqAuth("快期账户", "账户密码"))
    rate = api_margin.get_margin_rates("SHFE.cu2201")
    print(rate)
    api = TqApi(TqAccount("期货公司","账号","密码"),auth=TqAuth("快期账户", "账户密码"))
    quote = api.get_quote("SHFE.cu2201")
    while True:
        api.wait_update()
        print(quote.datetime)
        # 正常和tqsdk一样执行策略


TqSdk2 的直连功能需要企业版权限，有关企业版的具体费用和功能，请参考 `天勤官方网站 <https://www.shinnytech.com/tqsdk-buy/>`_
如果想了解更多关于 TqSdk2 的直连功能TqCtp，请参考 `tqsdk2官方文档 <https://doc.shinnytech.com/tqsdk2/latest/reference/tqsdk2.ctp.html?highlight=tqctp#tqsdk2.TqCtp/>`_
