from tqsdk import TqApi, TqAuth

'''
如果买入看涨期权构建多头期货的价格小于卖出期货价格
存在套利机会则发出双边挂单
'''
api = TqApi(auth=TqAuth("信易账户", "账号密码"))

# 获取行权价为2950的MA109看涨期权的quote数据
quote_option = api.get_quote('CZCE.MA109C2950')

# 获取期权对应标的期货，即MA109的quote数据
quote = api.get_quote(quote_option.underlying_symbol)

# 套利机会尝试次数
times = 0

while True:
    api.wait_update()
    # 以对手价来计算买入看涨期权然后行权后的期货成本价格
    option_buy = quote_option.strike_price + quote_option.ask_price1
    # 判断当期货的买入1档，即卖出期货价格大于买入看涨期权的期货成本价格，形成套利空间时进行限价下单
    if quote.bid_price1 < option_buy and times == 0:
        times += 1
        # 以现在卖1档价格买入看涨期权
        order_opiton = api.insert_order('CZCE.MA109C2950', "BUY", "OPEN", 1, quote_option.ask_price1)
        # 以现在买1档的价格卖出期货
        order_future = api.insert_order(quote.underlying_symbol, "SELL", "OPEN", 1, quote.bid_price1)
        print("存在期货，期权套利空间尝试买入")
