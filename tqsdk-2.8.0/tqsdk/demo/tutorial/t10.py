#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from tqsdk import TqApi, TqAuth

# 创建API实例,传入自己的信易账户
api = TqApi(auth=TqAuth("信易账户", "账户密码"))
# 获得上期所 ni2011 的行情引用，当行情有变化时 quote 中的字段会对应更新
quote = api.get_quote("SHFE.ni2011")

# 输出 ni2011 的最新行情时间和最新价
print(quote.datetime, quote.last_price)

# 关闭api,释放资源
api.close()
