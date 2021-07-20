from tqsdk import TqApi, TqAuth

'''
获取标的对应看涨期权的期权和行权价对应列表
'''
api = TqApi(auth=TqAuth("信易账户", "账号密码"))

# 获取沪深300股指期权的认购在市合约
ls = api.query_options("SSE.000300", "CALL", expired=False)

# 批量获取这些合约的quote合约信息
quote_ls = api.get_quote_list(ls)

option_ls = {}

# 遍历quote合约信息，将合约和其对应行权价组装成字典
for i in quote_ls:
    option_ls[i.instrument_id] = i.strike_price

print(option_ls)

api.close()