from tqsdk import TqApi

api = TqApi()

klines = api.get_kline_serial("DCE.m1901", 10)

# 判断开仓条件, 如果当前价格大于10秒K线的MA15则开多仓
while True:
    api.wait_update()
    if api.is_changing(klines):
        ma = sum(klines.close[-15:])/15
        print("最新价", klines.close[-1], "MA", ma)
        if klines.close[-1] > ma:
            print("最新价大于MA: 市价开仓")
            api.insert_order(symbol="DCE.m1901", direction="BUY", offset="OPEN", volume=5)
            break

# 判断平仓条件, 如果当前价格小于10秒K线的MA15则平仓
while True:
    api.wait_update()
    if api.is_changing(klines):
        ma = sum(klines.close[-15:])/15
        print("最新价", klines.close[-1], "MA", ma)
        if klines.close[-1] < ma:
            print("最新价小于MA: 市价平仓")
            api.insert_order(symbol="DCE.m1901", direction="SELL", offset="CLOSE", volume=5)
            break

# 关闭api,释放相应资源
api.close()
