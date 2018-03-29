# encoding: UTF-8

"""
tqsdk.tools 包括了一些常用的工具
"""

import uuid
import logging


def make_order_until_all_matched(api, symbol, direction, offset, volume):
    """
    对价跟踪追单

    按照指定合约的对手价(买单选卖一价, 卖单选买一价)跟踪下单, 下单后如果未全部成交, 且行情有变, 则撤单后重下, 反复循环直至完全成交

    注意: 这并非一个普通函数, 不能直接调用, 而需要使用 tqsdk.TaskManager().start_task 来运行

    Args:
       * api (TqApi): 一个TqApi实例, 负责发送指令和接收信息
       * symbol (str): 拟下单的合约symbol, 格式为 交易所代码.合约代码,  例如 "SHFE.cu1801"
       * direction (str): "BUY" 或 "SELL"
       * offset (str): "OPEN", "CLOSE" 或 "CLOSETODAY"
       * volume (int): 需要下单的手数

    Remark:
    """
    # 订阅指定合约的行情, 以便跟随市场价下单
    quote = api.get_quote(symbol)
    volume_left = volume
    while volume_left > 0:
        limit_price = quote["bid_price1"] if direction == "SELL" else quote["ask_price1"]
        # 发出报单
        order = api.insert_order(symbol=symbol, direction=direction, offset=offset, volume=volume_left, limit_price=limit_price)
        # 等待委托单完全成交, 或者行情有变
        wait_result = yield{
            "ORDER_FINISHED": lambda: order["status"] == "FINISHED",
            "PRICE_CHANGED": lambda: limit_price != (quote["bid_price1"] if direction == "SELL" else quote["ask_price1"])
        }
        # 如果委托单状态为已完成
        if wait_result["ORDER_FINISHED"]:
            if order["exchange_order_id"] == "":
                # 没有交易所单号, 判定为错单
                raise Exception("error order")
            else:
                return
        # 如果价格有变
        if wait_result["PRICE_CHANGED"]:
            # 发出撤单指令
            api.cancel_order(order)
        # 等待撤单指令生效, 或者委托单全部成交
        yield {
            "ORDER_CANCELED": lambda: order["status"] == 'FINISHED'
        }
        # 这时委托单已经FINISHED, 拿到未成交手数作为下轮追单使用
        volume_left = order["volume_left"]
