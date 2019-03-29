from tqsdk import TqApi

# 创建API实例
api = TqApi()

# 获得上期所 cu1812 的行情引用
quote = api.get_quote("SHFE.cu1812")

# 输出行情时间和最新价
print(quote["datetime"], quote["last_price"])
