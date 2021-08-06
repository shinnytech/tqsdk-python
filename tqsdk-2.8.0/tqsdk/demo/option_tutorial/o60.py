from tqsdk import TqApi, TqAuth
from tqsdk.ta import VOLATILITY_CURVE

api = TqApi(auth=TqAuth("信易账户", "账户密码"))

# 获取 m2112 的看跌期权
underlying = "DCE.m2101"
options = api.query_options(underlying_symbol=underlying, option_class="PUT", expired=False)

# 批量获取合约的行情信息, 存储结构必须为 dict, key 为合约, value 为行情数据
quote = {}
for symbol in options:
    quote[symbol] = api.get_quote(symbol)
options.append(underlying)

klines = api.get_kline_serial(options, 24 * 60 * 60, 20)

# 使用 VOLATILITY_CURVE 函数计算波动率曲面
vc = VOLATILITY_CURVE(klines, quote, underlying, r=0.025)

print(vc)

api.close()
