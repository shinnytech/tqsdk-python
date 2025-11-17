#!/usr/bin/env python
# coding=utf-8
__author__ = "Chaos"

from tqsdk import TqApi, TqAuth, TqKq
import math

# === 用户参数 ===
SYMBOL = "SHFE.ag2506"      # 交易合约
DIRECTION = "BUY"           # "BUY"为买入，"SELL"为卖出
OFFSET = "OPEN"             # "OPEN"为开仓，"CLOSE"为平仓,"CLOSETODAY"为平今仓
TOTAL_VOLUME = 30          # 目标总手数
POV_RATIO = 0.1             # 跟量比例（如0.1表示10%）
ORDER_TYPE = "对价"         # "对价"为对价报单，"报价"为挂价报单

# === 初始化API ===
acc = TqKq()
api = TqApi(account=acc, auth=TqAuth("快期账号", "快期密码"))
quote = api.get_quote(SYMBOL)

# === 初始化变量 ===
base_volume = quote.volume  # 启动时的市场累计成交量
traded_volume = 0           # 已成交手数
last_printed_volume = 0     # 上次打印的成交手数

print(f"POV算法启动，合约: {SYMBOL}，目标: {TOTAL_VOLUME}手，方向: {DIRECTION}，量比比例: {POV_RATIO*100}%")

try:
    while traded_volume < TOTAL_VOLUME:
        api.wait_update()
        new_volume = quote.volume
        delta = new_volume - base_volume
        # 计算本轮应下单手数
        order_volume = int(math.floor(delta * POV_RATIO))
        # 不能超过剩余目标
        order_volume = min(order_volume, TOTAL_VOLUME - traded_volume)

        if order_volume > 0:
            print(f"\n市场成交量: {base_volume} -> {new_volume}手")
            print(f"变化量: {delta}手")
            print(f"计算下单手数: {delta} * {POV_RATIO} = {order_volume}手")

            # 根据报单类型选择价格
            if ORDER_TYPE == "对价":
                # 对价报单
                price = quote.ask_price1 if DIRECTION == "BUY" else quote.bid_price1
            else:
                # 挂价报单
                price = quote.bid_price1 if DIRECTION == "BUY" else quote.ask_price1

            order = api.insert_order(
                symbol=SYMBOL,
                direction=DIRECTION,
                offset=OFFSET,
                volume=order_volume,
                limit_price=price
            )
            print(f"下单: {order_volume}手，价格: {price}，报单类型: {ORDER_TYPE}")

            # 记录上一次的状态和剩余量
            last_status = order.status
            last_volume_left = order.volume_left

            # 等待订单状态更新
            while order.status == "ALIVE":
                api.wait_update()
                # 只在状态或剩余量发生变化时打印
                if order.status != last_status or order.volume_left != last_volume_left:
                    print(f"订单状态更新: {order.status}, 剩余量: {order.volume_left}")
                    last_status = order.status
                    last_volume_left = order.volume_left

            # 检查订单是否出错
            if order.is_error:
                print(f"下单失败: {order.last_msg}")
                break

            # 计算实际成交量
            actual_trade = order.volume_orign - order.volume_left
            if actual_trade > 0:
                print(f"本轮成交: {actual_trade}手")
                traded_volume += actual_trade
                base_volume = new_volume  # 更新基准成交量

                # 只在成交手数变化时打印进度
                if traded_volume > last_printed_volume:
                    print(f"当前进度: {traded_volume} / {TOTAL_VOLUME}")
                    last_printed_volume = traded_volume
            else:
                print(f"订单未成交: {order.last_msg}")

    print("POV算法执行完毕")
except Exception as e:
    print(f"捕获到异常: {e}")
finally:
    api.close()
