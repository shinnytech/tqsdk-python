#!usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = 'yanqiong'

import functools
import os
import random
import secrets
from bisect import bisect_right
from typing import Callable

from sgqlc.operation import Operation
from pandas.core.internals import BlockManager

from tqsdk.diff import _get_obj
from tqsdk.ins_schema import ins_schema, _add_all_frags
from tqsdk.tafunc import get_dividend_df

RD = random.Random(secrets.randbits(128))  # 初始化随机数引擎，使用随机数作为seed，防止用户同时拉起多个策略，产生同样的 seed


def _reinit_rd():
    global RD
    RD = random.Random(secrets.randbits(128))


try:
    # fork 构造多进程策略时，需要在子进程中重新初始化 RD，否则会不同进程会生成相同的 uuid，产生重复报单或者相同 chart_id
    os.register_at_fork(after_in_child=_reinit_rd)  # 仅支持 Unix，且 pyversion >= 3.7
except AttributeError:
    pass


def _generate_uuid(prefix=''):
    return f"{prefix + '_' if prefix else ''}{RD.getrandbits(128):032x}"


def _query_for_quote(symbol):
    """
    返回请求某个合约的合约信息的 query_pack
    调用次函数应该全部都是sdk的代码主动请求合约信息
    用户请求合约信息一定是 PYSDK_api 开头的请求，因为用户请求的合约信息在回测时带有 timestamp 参数，是不应该调用此函数的
    """
    symbol_list = symbol if isinstance(symbol, list) else [symbol]
    op = Operation(ins_schema.rootQuery)
    query = op.multi_symbol_info(instrument_id=symbol_list)
    _add_all_frags(query)
    return {
        "aid": "ins_query",
        "query_id": _generate_uuid(prefix='PYSDK_quote_'),
        "query": op.__to_graphql__()
    }


def _query_for_init():
    """
    返回某些类型合约的 query
    todo: 为了兼容旧版提供给用户的 api._data["quote"].items() 类似用法，应该限制交易所 ["SHFE", "DCE", "CZCE", "INE", "CFFEX", "KQ"]
    """
    op = Operation(ins_schema.rootQuery)
    query = op.multi_symbol_info(class_=["FUTURE", "INDEX", "OPTION", "COMBINE", "CONT"],
                                 exchange_id=["SHFE", "DCE", "CZCE", "INE", "CFFEX", "KQ", "GFEX"])
    _add_all_frags(query)
    return op.__to_graphql__()


night_trading_table = {
    "DCE.a": ["21:00:00", "23:00:00"],
    "DCE.b": ["21:00:00", "23:00:00"],
    "DCE.c": ["21:00:00", "23:00:00"],
    "DCE.cs": ["21:00:00", "23:00:00"],
    "DCE.m": ["21:00:00", "23:00:00"],
    "DCE.y": ["21:00:00", "23:00:00"],
    "DCE.p": ["21:00:00", "23:00:00"],
    "DCE.l": ["21:00:00", "23:00:00"],
    "DCE.v": ["21:00:00", "23:00:00"],
    "DCE.pp": ["21:00:00", "23:00:00"],
    "DCE.j": ["21:00:00", "23:00:00"],
    "DCE.jm": ["21:00:00", "23:00:00"],
    "DCE.i": ["21:00:00", "23:00:00"],
    "DCE.eg": ["21:00:00", "23:00:00"],
    "DCE.eb": ["21:00:00", "23:00:00"],
    "DCE.rr": ["21:00:00", "23:00:00"],
    "DCE.pg": ["21:00:00", "23:00:00"],
    "CZCE.CF": ["21:00:00", "23:00:00"],
    "CZCE.CY": ["21:00:00", "23:00:00"],
    "CZCE.SA": ["21:00:00", "23:00:00"],
    "CZCE.SR": ["21:00:00", "23:00:00"],
    "CZCE.TA": ["21:00:00", "23:00:00"],
    "CZCE.OI": ["21:00:00", "23:00:00"],
    "CZCE.MA": ["21:00:00", "23:00:00"],
    "CZCE.FG": ["21:00:00", "23:00:00"],
    "CZCE.RM": ["21:00:00", "23:00:00"],
    "CZCE.ZC": ["21:00:00", "23:00:00"],
    "CZCE.TC": ["21:00:00", "23:00:00"],
    "SHFE.rb": ["21:00:00", "23:00:00"],
    "SHFE.hc": ["21:00:00", "23:00:00"],
    "SHFE.fu": ["21:00:00", "23:00:00"],
    "SHFE.bu": ["21:00:00", "23:00:00"],
    "SHFE.ru": ["21:00:00", "23:00:00"],
    "SHFE.sp": ["21:00:00", "23:00:00"],
    "INE.nr": ["21:00:00", "23:00:00"],
    "SHFE.cu": ["21:00:00", "25:00:00"],
    "SHFE.al": ["21:00:00", "25:00:00"],
    "SHFE.zn": ["21:00:00", "25:00:00"],
    "SHFE.pb": ["21:00:00", "25:00:00"],
    "SHFE.ni": ["21:00:00", "25:00:00"],
    "SHFE.sn": ["21:00:00", "25:00:00"],
    "SHFE.ss": ["21:00:00", "25:00:00"],
    "SHFE.au": ["21:00:00", "26:30:00"],
    "SHFE.ag": ["21:00:00", "26:30:00"],
    "INE.sc": ["21:00:00", "26:30:00"],
}


def _quotes_add_night(quotes):
    """为 quotes 中应该有夜盘但是市价合约文件中没有夜盘的品种，添加夜盘时间"""
    for symbol in quotes:
        product_id = quotes[symbol].get("product_id")
        if quotes[symbol].get("trading_time") and product_id:
            key = f"{quotes[symbol].get('exchange_id')}.{product_id}"
            if key in night_trading_table and (not quotes[symbol]["trading_time"].get("night")):
                quotes[symbol]["trading_time"]["night"] = [night_trading_table[key]]


def _bisect_value(a, x, priority="right"):
    """
    返回 bisect_right() 取得下标对应的值，当插入点距离前后元素距离相等，priority 表示优先返回右边的值还是左边的值
    a: 必须是已经排序好（升序排列）的 list
    bisect_right : Return the index where to insert item x in list a, assuming a is sorted.
    """
    assert priority in ['left', 'right']
    insert_index = bisect_right(a, x)
    if 0 < insert_index < len(a):
        left_dis = x - a[insert_index - 1]
        right_dis = a[insert_index] - x
        if left_dis == right_dis:
            mid_index = insert_index - 1 if priority == "left" else insert_index
        elif left_dis < right_dis:
            mid_index = insert_index - 1
        else:
            mid_index = insert_index
    else:
        assert insert_index == 0 or insert_index == len(a)
        mid_index = 0 if insert_index == 0 else (len(a) - 1)
    return a[mid_index]


class BlockManagerUnconsolidated(BlockManager):
    """mock BlockManager for unconsolidated, 不会因为自动合并同类型的 blocks 而导致 k 线数据不更新"""
    def __init__(self, *args, **kwargs):
        BlockManager.__init__(self, *args, **kwargs)
        self._is_consolidated = False
        self._known_consolidated = False

    def _consolidate_inplace(self): pass


async def _get_dividend_factor(api, quote, start_dt_nano, end_dt_nano, chart_id_prefix="PYSDK_dividend_factor"):
    # 对每个除权除息矩阵增加 factor 序列，为当日的复权因子
    df = get_dividend_df(quote.stock_dividend_ratio, quote.cash_dividend_ratio)
    df = df[df["datetime"].between(start_dt_nano, end_dt_nano, inclusive="right")]  # 只需要一段时间之间的复权因子, 左开右闭
    df["pre_close"] = float('nan')  # 初始化 pre_close 为 nan
    for i in range(len(df)):
        chart_info = {
            "aid": "set_chart",
            "chart_id": _generate_uuid(chart_id_prefix),
            "ins_list": quote.instrument_id,
            "duration": 86400 * 1000000000,
            "view_width": 2,
            "focus_datetime": int(df["datetime"].iloc[i]),
            "focus_position": 1
        }
        await api._send_chan.send(chart_info)
        chart = _get_obj(api._data, ["charts", chart_info["chart_id"]])
        serial = _get_obj(api._data, ["klines", quote.instrument_id, str(86400000000000)])
        try:
            async with api.register_update_notify() as update_chan:
                async for _ in update_chan:
                    if not (chart_info.items() <= _get_obj(chart, ["state"]).items()):
                        continue  # 当前请求还没收齐回应, 不应继续处理
                    if chart.get("ready", False) is False:
                        continue  # 合约的数据是否收到
                    left_id = chart.get("left_id", -1)
                    assert left_id != -1  # 需要下载除权除息日的前一天行情，即这一天一定是有行情的，left_id 一定不是 -1
                    last_item = serial["data"].get(str(left_id), {})
                    # 复权时间点的昨收盘
                    df.loc[i, 'pre_close'] = last_item['close'] if last_item.get('close') else float('nan')
                    break
        finally:
            await api._send_chan.send({
                "aid": "set_chart",
                "chart_id": chart_info["chart_id"],
                "ins_list": "",
                "duration": 86400000000000,
                "view_width": 2
            })
    df["factor"] = (df["pre_close"] - df["cash_dividend"]) / df["pre_close"] / (1 + df["stock_dividend"])
    df["factor"].fillna(1.0, inplace=True)
    return df


def deprecated_chart_id(*expect_args) -> Callable:
    """
    废弃 chart_id 参数后，希望支持用户不修改如下的代码

    api.get_kline_serial(symbol, 3600, 1000, "xxx", "F")
    api.get_tick_serial(symbol, 200, "xxx", "F")
    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            kwargs.pop("chart_id", None)
            if len(args) == len(expect_args) + 1:
                # 用户传入的 args 参数比 expect_args 多一个，说明用户主动在 position args 位置上传入了 chart_id 参数，需要去掉
                # 如果长度一样或者比 expect_args 少，就按照用户传入原本的参数处理
                # 倒数第二个是 chart_id 参数
                args = args[:-2] + args[-1:]
            return f(self, *args, **kwargs)
        return wrapper

    return decorator
