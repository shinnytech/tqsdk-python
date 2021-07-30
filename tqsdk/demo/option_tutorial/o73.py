from tqsdk import TqApi, TqAuth
from datetime import datetime
from tqsdk.tafunc import time_to_datetime

'''
查询标的对应期权按虚值平值实值分类
'''
from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("信易账户", "账户密码"))

quote = api.get_quote("SSE.510300")

# 获取下月的上交所看涨300etf期权
in_money_options, at_money_options, out_of_money_options = api.query_all_level_finance_options("SSE.510300", quote.last_price, "CALL", nearbys = 1)

print(in_money_options)  # 实值期权列表
print(at_money_options)  # 平值期权列表
print(out_of_money_options)  # 虚值期权列表

api.close()
