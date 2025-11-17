#!/usr/bin/env python
# coding=utf-8
__author__ = "Chaos"

from tqsdk import TqApi, TqAuth, TqKq, TargetPosTask

# === 用户参数 ===
SYMBOL = "SHFE.ag2506"      # 交易合约
TOTAL_VOLUME = 100          # 目标总手数
MIN_VOLUME = 1              # 每笔最小委托手数
MAX_VOLUME = 10             # 每笔最大委托手数
DIRECTION = "BUY"           # "BUY"为买入，"SELL"为卖出
ORDER_TYPE = "ACTIVE"       # 对价 "ACTIVE" / 挂价 "PASSIVE" / 指定价 lambda direction: 价格

# === 初始化 ===
api = TqApi(account=TqKq(), auth=TqAuth("快期账号", "快期密码"))
quote = api.get_quote(SYMBOL)

# 创建目标持仓任务
target_pos = TargetPosTask(
    api, SYMBOL,
    price=ORDER_TYPE,
    min_volume=MIN_VOLUME,
    max_volume=MAX_VOLUME
)

# 获取下单方式描述
order_type_str = (f"指定价 {ORDER_TYPE(DIRECTION)}" if callable(ORDER_TYPE) 
                 else str(ORDER_TYPE))

print(f"冰山算法启动，合约: {SYMBOL}，目标: {TOTAL_VOLUME}手，"
      f"每批: {MIN_VOLUME}-{MAX_VOLUME}手，方向: {DIRECTION}，下单方式: {order_type_str}")

try:
    # 获取初始持仓并设置目标
    pos = api.get_position(SYMBOL)
    start_net_pos = pos.pos_long - pos.pos_short
    target_volume = start_net_pos + (TOTAL_VOLUME if DIRECTION == "BUY" else -TOTAL_VOLUME)
    target_pos.set_target_volume(target_volume)
    
    last_progress = 0  # 记录上次进度

    while True:
        api.wait_update()
        pos = api.get_position(SYMBOL)
        net_pos = pos.pos_long - pos.pos_short
        progress = abs(net_pos - start_net_pos)
        
        # 当进度发生变化时打印
        if progress != last_progress:
            print(f"当前进度: {progress}/{TOTAL_VOLUME}")
            last_progress = progress
        
        # 检查是否完成
        if (DIRECTION == "BUY" and net_pos >= target_volume) or \
           (DIRECTION == "SELL" and net_pos <= target_volume):
            print(f"冰山算法完成")
            break

except Exception as e:
    print(f"算法执行异常: {e}")
finally:
    api.close()
