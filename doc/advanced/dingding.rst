.. _dingding:

将程序信息推送到手机端
=================================================
TqSdk 并不提供专门的服务器来推送消息，但是你可以通过其他 SDK 来做到这个效果，在发生成交或者条件满足时，进行消息推送，以钉钉为例::

    from datetime import datetime, time, timedelta
    import requests
    from json import dumps
    from tqsdk import TqApi, TqAuth, TargetPosTask


    def send_msg(content):
        """钉钉消息提醒模块"""
        webhook = "设置自己的钉钉 webhook"

        # 钉钉安全规则将 天勤量化 设为关键字
        msg = {"msgtype": "text",
               "text": {"content": "{}\n{}\n".format("天勤量化\n" + content,
                                                     datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}, }
        headers = {"content-type": "application/json;charset=utf-8"}
        body = dumps(msg)
        requests.post(webhook, data=body, headers=headers)
        print(content)


    api = TqApi(auth=TqAuth("快期账户", "账户密码"))
    quote = api.get_quote("SHFE.rb2109")
    target_pos = TargetPosTask(api, "SHFE.rb2110")
    send_msg("策略开始运行")
    a = 0
    while True:
        api.wait_update()
        # 通过本地变量 a 来避免多次发送钉钉消息触发流控
        if quote.last_price > 5110 and a == 0:
            send_msg("行情满足条件，开多头5手")
            target_pos.set_target_volume(5)
            a = 1


具体说明，请参考 `钉钉操作手册 <https://developers.dingtalk.com/document/app/custom-robot-access>`_
