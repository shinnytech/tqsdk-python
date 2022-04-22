from tqsdk import TqApi, TqAuth

'''
根据输入的ETF期权来查询该期权的交易所规则下的理论卖方保证金，实际情况请以期货公司收取的一手保证金为准
'''

def etf_margin_cal(symbol):
    quote_etf = api.get_quote(symbol)
    # 判断期权标的是不是ETF
    if quote_etf.underlying_symbol in ["SSE.510050", "SSE.510300", "SZSE.159919"]:
        if quote_etf.option_class == "CALL":
            # 认购期权虚值＝Max（行权价-合约标的前收盘价，0）
            call_out_value = max(quote_etf.strike_price - quote_etf.underlying_quote.pre_close, 0)
            # 认购期权义务仓开仓保证金＝[合约前结算价+Max（12%×合约标的前收盘价-认购期权虚值，7%×合约标的前收盘价）]×合约单位
            call_margin = (quote_etf.pre_settlement + max(0.12 * quote_etf.underlying_quote.pre_close - call_out_value,
                                                          0.07 * quote_etf.underlying_quote.pre_close)) * quote_etf.volume_multiple
            return round(call_margin, 2)
        elif quote_etf.option_class == "PUT":
            # 认沽期权虚值＝Max（合约标的前收盘价-行权价，0）
            put_out_value = max(quote_etf.underlying_quote.pre_close - quote_etf.strike_price, 0)
            # 认沽期权义务仓开仓保证金＝Min[合约前结算价+Max（12%×合约标的前收盘价-认沽期权虚值，7%×行权价），行权价]×合约单位。
            put_margin = min(quote_etf.pre_settlement + max(0.12 * quote_etf.underlying_quote.pre_close - put_out_value,
                                                            0.07 * quote_etf.strike_price),
                             quote_etf.strike_price) * quote_etf.volume_multiple
            return round(put_margin, 2)
    else:
        print("输入的不是ETF期权合约")
        return None


# 创建api
api = TqApi(auth=TqAuth("信易账户", "账户密码"))

# 深交所300etf期权
symbol = "SZSE.90000833"

print(etf_margin_cal(symbol))

api.close()
