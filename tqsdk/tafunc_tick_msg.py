__author__ = 'y.m.wong'
import pandas as pd
"""
由https://github.com/shinnytech/shinny-futures-web/blob/master/src/components/TicksList.vue改写而来
"""

def cal_pc(tick:dict) -> int:
    """
    计算tick前后的pc值（可能是判断多空方向）
    :param tick: 当前tick
    :return: pc值
    """
    
    pc = 0
    if tick['trade_ask_spread'] >= 0:
        pc = 1
    elif tick['trade_bid_spread'] >= 0:
        pc = -1
    else:
        if tick['price_diff'] > 0:
            pc = 1
        elif tick['price_diff'] < 0:
            pc = -1
        else:
            pc = 0
    return pc

def cal_msg(tick:dict) -> str:
    """
    根据tick信息计算成交性质
    :param tick: 当前tick
    :return: string 成交性质
    """
    msg = ''
    if tick['oi_diff'] > 0 and tick['oi_diff'] == tick['vol_diff']:
        msg = '双开'
    elif tick['oi_diff'] < 0 and tick['oi_diff'] + tick['vol_diff'] == 0:
        msg = '双平'
    else:
        if tick['pc'] == 0:
            msg = '换手'
        else:
            msg = ('多' if tick['pc'] > 0 else '空') + ('开' if tick['oi_diff'] > 0 else '平' if tick['oi_diff'] < 0 else '换')
    return msg

def cal_ticks_msg(ticks: pd.Series) -> pd.DataFrame:
    """
        主函数：计算仓单“开平”字段
    """
    ticks_ex = pd.DataFrame()
    ticks_ex['datetime'] = ticks["datetime"]
    ticks_ex['vol_diff'] = ticks["volume"].diff()
    ticks_ex['oi_diff'] = ticks["open_interest"].diff()
    ticks_ex['price_diff'] = ticks["last_price"].diff()
    ticks_ex['trade_ask_spread'] = ticks["last_price"] - ticks["ask_price1"].shift(1)
    ticks_ex['trade_bid_spread'] = ticks["last_price"] - ticks["bid_price1"].shift(1)
    ticks_ex['pc'] = ticks_ex.apply(lambda tick: cal_pc(dict(tick)), axis=1)
    ticks_ex['msg'] = ticks_ex.apply(lambda tick: cal_msg(dict(tick)), axis=1)
    return ticks_ex

"""
demo:
from tqsdk import TqApi, TqBacktest, BacktestFinished
from datetime import datetime
from tqsdk.tafunc import time_to_datetime

api = TqApi(backtest=TqBacktest(datetime(2020,2,11,14,59,55),datetime(2020,2,11,15,00)))
ticks = api.get_tick_serial('DCE.j2005')
test = pd.DataFrame()
while True:
    api.wait_update()
    test = cal_ticks_ex(ticks)
    print(test)
"""