#!/usr/bin/env python
# coding=utf-8
__author__ = "Chaos"

from tqsdk import TqApi, TqAuth, TqKq
import math

# === 用户参数 ===
SYMBOL = "SHFE.ag2506"      # 交易合约
DIRECTION = "BUY"          # "BUY"为买入，"SELL"为卖出
OFFSET = "OPEN"       # "OPEN"为开仓，"CLOSE"为平仓,"CLOSETODAY"为平今仓
TOTAL_VOLUME = 20          # 目标总手数
ORDERBOOK_RATIO = 0.2       # 盘口量比比例（如0.2表示20%）
ORDER_TYPE = "对价"         # "对价"为对价报单，"挂价"为挂价报单
ORDERBOOK_TYPE = "对手盘口"  # "对手盘口"或"挂单盘口"

# === 初始化API ===
acc = TqKq()
api = TqApi(account=acc, auth=TqAuth("快期账号", "快期密码"))
quote = api.get_quote(SYMBOL)

# === 初始化变量 ===
traded_volume = 0           # 已成交手数
last_printed_volume = 0     # 上次打印的成交手数
current_order = None        # 当前订单

print(f"盘口算法启动，合约: {SYMBOL}，目标: {TOTAL_VOLUME}手，方向: {DIRECTION}，量比比例: {ORDERBOOK_RATIO*100}%")

def get_orderbook_volume():
    """获取盘口数量"""
    if ORDERBOOK_TYPE == "对手盘口":
        # 对手盘口：买入时看卖一量，卖出时看买一量
        return quote.ask_volume1 if DIRECTION == "BUY" else quote.bid_volume1
    else:
        # 挂单盘口：买入时看买一量，卖出时看卖一量
        return quote.bid_volume1 if DIRECTION == "BUY" else quote.ask_volume1

def get_order_price():
    """获取下单价格"""
    if ORDER_TYPE == "对价":
        # 对价报单
        return quote.ask_price1 if DIRECTION == "BUY" else quote.bid_price1
    else:
        # 挂价报单
        return quote.bid_price1 if DIRECTION == "BUY" else quote.ask_price1

try:
    while traded_volume < TOTAL_VOLUME:
        api.wait_update()
        
        # 获取当前盘口数量
        orderbook_volume = get_orderbook_volume()
        # 计算本轮应下单手数
        order_volume = int(math.floor(orderbook_volume * ORDERBOOK_RATIO))
        # 不能超过剩余目标
        order_volume = min(order_volume, TOTAL_VOLUME - traded_volume)
        
        if order_volume > 0:
            print(f"\n当前盘口数量: {orderbook_volume}手")
            print(f"计算下单手数: {orderbook_volume} * {ORDERBOOK_RATIO} = {order_volume}手")
            
            # 下新单
            price = get_order_price()
            current_order = api.insert_order(
                symbol=SYMBOL,
                direction=DIRECTION,
                offset=OFFSET,
                volume=order_volume,
                limit_price=price
            )
            print(f"下单: {order_volume}手，价格: {price}，报单类型: {ORDER_TYPE}")
            
            # 记录上一次的状态和剩余量
            last_status = current_order.status
            last_volume_left = current_order.volume_left
            
            # 等待订单状态更新
            while current_order.status == "ALIVE":
                api.wait_update()
                # 只在状态或剩余量发生变化时打印
                if current_order.status != last_status or current_order.volume_left != last_volume_left:
                    print(f"订单状态更新: {current_order.status}, 剩余量: {current_order.volume_left}")
                    last_status = current_order.status
                    last_volume_left = current_order.volume_left
                
                # 检查价格是否变化
                new_price = get_order_price()
                if new_price != price:
                    print(f"价格发生变化: {price} -> {new_price}")
                    # 如果还有未成交部分，先撤单
                    if current_order.volume_left > 0:
                        print(f"撤单: {current_order.volume_left}手")
                        api.cancel_order(current_order.order_id)
                        # 等待撤单完成
                        while current_order.status == "ALIVE":
                            api.wait_update()
                        # 重新下单
                        current_order = api.insert_order(
                            symbol=SYMBOL,
                            direction=DIRECTION,
                            offset=OFFSET,
                            volume=current_order.volume_left,
                            limit_price=new_price
                        )
                        print(f"重新下单: {current_order.volume_left}手，价格: {new_price}")
                        price = new_price
                        last_status = current_order.status
                        last_volume_left = current_order.volume_left
                    else:
                        # 如果订单已经完成，跳出循环
                        break
            
            # 检查订单是否出错
            if current_order.is_error:
                print(f"下单失败: {current_order.last_msg}")
                break
            
            # 计算实际成交量
            actual_trade = current_order.volume_orign - current_order.volume_left
            if actual_trade > 0:
                print(f"本轮成交: {actual_trade}手")
                traded_volume += actual_trade
                
                # 只在成交手数变化时打印进度
                if traded_volume > last_printed_volume:
                    print(f"当前进度: {traded_volume} / {TOTAL_VOLUME}")
                    last_printed_volume = traded_volume
            else:
                print(f"订单未成交: {current_order.last_msg}")
                
    print("盘口算法执行完毕")
except Exception as e:
    print(f"算法执行异常: {e}")
finally:
    api.close()
