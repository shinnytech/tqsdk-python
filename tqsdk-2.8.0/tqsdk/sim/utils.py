#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'


from pandas import DataFrame

from tqsdk.objs import Trade, Account
from tqsdk.tafunc import get_sharp, get_sortino

TRADING_DAYS_OF_YEAR = 250


def _get_price_range(quote):
    """ 返回合约对应的买一卖一盘口价格"""
    ask_price = quote["ask_price1"]
    bid_price = quote["bid_price1"]
    if quote["ins_class"].endswith("INDEX"):
        # 在指数交易时，使用 tick 进行回测时，backtest 发的 quote 没有买一卖一价；或者在实时行情中，指数的 quote 也没有买一卖一价
        if ask_price != ask_price:
            ask_price = quote["last_price"] + quote["price_tick"]
        if bid_price != bid_price:
            bid_price = quote["last_price"] - quote["price_tick"]
    return ask_price, bid_price


def _get_option_margin(quote, last_price, underlying_last_price):
    """返回每张期权占用保证金，只有空头持仓占用保证金"""
    # 期权保证金计算公式参考深交所文档 http://docs.static.szse.cn/www/disclosure/notice/general/W020191207433397366259.pdf
    if quote["option_class"] == "CALL":
        # 认购期权义务仓开仓保证金＝[合约最新价 + Max（12% × 合约标的最新价 - 认购期权虚值， 7% × 合约标的最新价）] × 合约单位
        # 认购期权虚值＝Max（行权价 - 合约标的最新价，0）
        out_value = max(quote["strike_price"] - underlying_last_price, 0)
        return (last_price + max(0.12 * underlying_last_price - out_value,
                                 0.07 * underlying_last_price)) * quote["volume_multiple"]
    else:
        # 认沽期权义务仓开仓保证金＝Min[合约最新价+ Max（12% × 合约标的最新价 - 认沽期权虚值，7% × 行权价），行权价] × 合约单位
        # 认沽期权虚值＝Max（合约标的最新价 - 行权价，0）
        out_value = max(underlying_last_price - quote["strike_price"], 0)
        return min(quote["last_price"] + max(0.12 * underlying_last_price - out_value,
                                             0.07 * quote["strike_price"]),
                   quote["strike_price"]) * quote["volume_multiple"]


def _get_premium(trade, quote):
    """返回成交导致的权利金变化"""
    if quote["ins_class"].endswith("OPTION"):
        premium = trade["price"] * trade["volume"] * quote["volume_multiple"]
        return -premium if trade["direction"] == "BUY" else premium
    else:
        return 0


def _get_close_profit(trade, quote, position):
    """返回成交导致的平仓盈亏变化"""
    if quote["ins_class"].endswith("OPTION"):
        # 期权没有持仓盈亏没有持仓价，其平仓的盈亏体现在市价变化中
        return 0
    # 期货及其他使用持仓价计算
    elif trade["direction"] == "SELL":
        return (trade["price"] - position["position_price_long"]) * trade["volume"] * quote["volume_multiple"]
    else:
        return (position["position_price_short"] - trade["price"]) * trade["volume"] * quote["volume_multiple"]


def _get_commission(quote={}):
    """返回每手手续费"""
    if quote.get("ins_class", "").endswith("OPTION"):
        return quote.get("user_commission", 10)  # 期权quote没有commission字段, 设为固定10元一张, 优先采用用户设置的参数
    return quote.get("user_commission", quote.get('commission', float('nan')))


def _get_future_margin(quote={}):
    """返回期货每手保证金"""
    if quote.get("ins_class", "").endswith("OPTION"):
        return float('nan')
    return quote.get("user_margin", quote.get("margin", float('nan')))


def _get_sub_df(origin_df, symbol, dir, offset):
    df = origin_df.where(
        (origin_df['symbol'] == symbol) & (origin_df['offset'] == offset) & (origin_df['direction'] == dir))
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def _get_account_df(trade_log={}):
    date_keys = sorted(trade_log.keys())
    data = [{'date': dt} for dt in date_keys]
    for item in data:
        item.update(trade_log[item['date']]['account'])
    return DataFrame(data=data, columns=list(Account(None).keys()) + ['date'])


def _get_trade_df(trade_log={}):
    date_keys = sorted(trade_log.keys())
    trade_array = []
    for date in date_keys:
        trade_array.extend(trade_log[date]['trades'])
    return DataFrame(data=trade_array, columns=list(Trade(None).keys()))


def _get_tqsim_stat(trade_log={}, quotes={}):
    """
    返回账户统计信息 tqsdk_stat
    quotes 主要需要合约乘数，用于计算盈亏额
    """
    date_keys = sorted(trade_log.keys())
    tqsdk_stat = {
        "winning_rate": float('nan'),  # 胜率
        "profit_loss_ratio": float('nan'),  # 盈亏额比例
        "ror": float('nan'),  # 收益率
        "annual_yield": float('nan'),  # 年化收益率
        "max_drawdown": float('nan'),  # 最大回撤
        "sharpe_ratio": float('nan'),  # 年化夏普率
        "sortino_ratio": float('nan'),  # 年化索提诺比率
        "commission":  0,  # 总手续费
        "tqsdk_punchline": ""
    }
    if len(date_keys) == 0:
        return tqsdk_stat
    tqsdk_stat["init_balance"] = trade_log[date_keys[0]]["account"]["pre_balance"]  # 起始资金
    tqsdk_stat["balance"] = trade_log[date_keys[-1]]["account"]["balance"]  # 结束资金
    tqsdk_stat["max_drawdown"] = 0  # 最大回撤

    ##### 根据成交手数计算 胜率，盈亏额比例
    trade_array = []
    for date in date_keys:
        for trade in trade_log[date]['trades']:
            # 每一行都是 1 手的成交记录
            trade_array.extend([{
                "symbol": f"{trade['exchange_id']}.{trade['instrument_id']}",
                "direction": trade["direction"],
                "offset": "CLOSE" if trade["offset"] == "CLOSETODAY" else trade["offset"],
                "price": trade["price"]
            } for i in range(trade['volume'])])
    trade_df = DataFrame(data=trade_array, columns=['symbol', 'direction', 'offset', 'price'])
    profit_volumes = 0  # 盈利手数
    loss_volumes = 0  # 亏损手数
    profit_value = 0  # 盈利额
    loss_value = 0  # 亏损额
    all_symbols = trade_df['symbol'].drop_duplicates()
    for symbol in all_symbols:
        for direction in ["BUY", "SELL"]:
            open_df = _get_sub_df(trade_df, symbol, dir=direction, offset='OPEN')
            close_df = _get_sub_df(trade_df, symbol, dir=("SELL" if direction == "BUY" else "BUY"), offset='CLOSE')
            close_df['profit'] = (close_df['price'] - open_df['price']) * (1 if direction == "BUY" else -1)
            profit_volumes += close_df.loc[close_df['profit'] >= 0].shape[0]  # 盈利手数
            loss_volumes += close_df.loc[close_df['profit'] < 0].shape[0]  # 亏损手数
            profit_value += close_df.loc[close_df['profit'] >= 0, 'profit'].sum() * quotes[symbol]['volume_multiple']
            loss_value += close_df.loc[close_df['profit'] < 0, 'profit'].sum() * quotes[symbol]['volume_multiple']
    tqsdk_stat["winning_rate"] = profit_volumes / (profit_volumes + loss_volumes) if profit_volumes + loss_volumes else 0
    profit_pre_volume = profit_value / profit_volumes if profit_volumes else 0
    loss_pre_volume = loss_value / loss_volumes if loss_volumes else 0
    tqsdk_stat["profit_loss_ratio"] = abs(profit_pre_volume / loss_pre_volume) if loss_pre_volume else float("inf")

    ##### 根据账户数据计算 收益率，年化收益率，最大回撤，年化夏普率
    _ror = tqsdk_stat["balance"] / tqsdk_stat["init_balance"]
    tqsdk_stat["ror"] = _ror - 1  # 收益率
    tqsdk_stat["annual_yield"] = _ror ** (TRADING_DAYS_OF_YEAR / len(date_keys)) - 1  # 年化收益率
    account_df = DataFrame(data=[trade_log[dt]['account'] for dt in date_keys], index=date_keys)
    account_df['max_balance'] = account_df['balance'].cummax()  # 当前单日最大权益
    account_df['drawdown'] = (account_df['max_balance'] - account_df['balance']) / account_df['max_balance']  # 回撤
    tqsdk_stat["max_drawdown"] = account_df['drawdown'].max()  # 最大回撤
    account_df['daily_yield'] = account_df['balance'] / account_df['balance'].shift(fill_value=tqsdk_stat["init_balance"]) - 1  # 每日收益
    tqsdk_stat["sharpe_ratio"] = get_sharp(account_df['daily_yield'])  # 年化夏普率
    tqsdk_stat["sortino_ratio"] = get_sortino(account_df['daily_yield'])  # 年化索提诺比率
    tqsdk_stat["commission"] = account_df["commission"].sum()  # 总手续费
    tqsdk_punchlines = [
        '幸好是模拟账户，不然你就亏完啦',
        '触底反弹,与其执迷修改参数，不如改变策略思路去天勤官网策略库进修',
        '越挫越勇，不如去天勤量化官网策略库进修',
        '不要灰心，少侠重新来过',
        '策略看来小有所成',
        '策略看来的得心应手',
        '策略看来春风得意，堪比当代索罗斯',
        '策略看来独孤求败，小心过拟合噢'
    ]
    ror_level = [i for i, k in enumerate([-1, -0.5, -0.2, 0, 0.2, 0.5, 1]) if tqsdk_stat["ror"] < k]
    if len(ror_level) > 0:
        tqsdk_stat["tqsdk_punchline"] = tqsdk_punchlines[ror_level[0]]
    else:
        tqsdk_stat["tqsdk_punchline"] = tqsdk_punchlines[-1]
    return tqsdk_stat
