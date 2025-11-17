from tqsdk import TqApi, TargetPosTask
from tqsdk.tafunc import ma
import numpy as np

api = TqApi()

SYMBOL_rb = "SHFE.rb2001"
SYMBOL_i = "DCE.i2001"
SYMBOL_j = "DCE.j2001"

klines_rb = api.get_kline_serial(SYMBOL_rb, 86400)
klines_i = api.get_kline_serial(SYMBOL_i, 86400)
klines_j = api.get_kline_serial(SYMBOL_j, 86400)

target_pos_rb = TargetPosTask(api, SYMBOL_rb)
target_pos_i = TargetPosTask(api, SYMBOL_i)
target_pos_j = TargetPosTask(api, SYMBOL_j)


# 计算钢厂利润线，并将利润线画到副图
def cal_spread(klines_rb, klines_i, klines_j):
    index_spread = klines_rb.close - 1.6 * klines_i.close - 0.5 * klines_j.close
    # 使用15日均值，与注释保持一致
    ma_spread = ma(index_spread, 15)
    # 计算标准差
    spread_std = np.std(index_spread)
    klines_rb["index_spread"] = index_spread
    klines_rb["index_spread.board"] = "index_spread"

    return index_spread, ma_spread, spread_std


# 初始计算利润线
index_spread, ma_spread, spread_std = cal_spread(klines_rb, klines_i, klines_j)

print("ma_spread是%.2f,index_spread是%.2f,spread_std是%.2f" % (ma_spread.iloc[-1], index_spread.iloc[-1], spread_std))

# 记录当前持仓状态，避免重复发出信号
current_position = 0  # 0表示空仓，1表示多螺纹空焦炭焦煤，-1表示空螺纹多焦炭焦煤

while True:
    api.wait_update()

    # 每次有新日线生成时重新计算利润线
    if api.is_changing(klines_j.iloc[-1], "datetime"):
        index_spread, ma_spread, spread_std = cal_spread(klines_rb, klines_i, klines_j)

        # 计算上下轨
        upper_band = ma_spread.iloc[-1] + 0.5 * spread_std
        lower_band = ma_spread.iloc[-1] - 0.5 * spread_std

        print("ma_spread是%.2f,index_spread是%.2f,spread_std是%.2f" % (
            ma_spread.iloc[-1], index_spread.iloc[-1], spread_std))
        print("上轨是%.2f,下轨是%.2f" % (upper_band, lower_band))

        # 确保有足够的历史数据
        if len(index_spread) >= 2:
            # 1. 检测下穿上轨：前一个K线在上轨之上，当前K线在上轨之下或等于上轨
            if index_spread.iloc[-2] > upper_band and index_spread.iloc[-1] <= upper_band:
                if current_position != -1:  # 避免重复开仓
                    # 价差序列下穿上轨，利润冲高回落进行回复，策略空螺纹钢、多焦煤焦炭
                    target_pos_rb.set_target_volume(-100)
                    target_pos_i.set_target_volume(100)
                    target_pos_j.set_target_volume(100)
                    current_position = -1
                    print("下穿上轨：空螺纹钢、多焦煤焦炭")

            # 2. 检测上穿下轨：前一个K线在下轨之下，当前K线在下轨之上或等于下轨
            elif index_spread.iloc[-2] < lower_band and index_spread.iloc[-1] >= lower_band:
                if current_position != 1:  # 避免重复开仓
                    # 价差序列上穿下轨，利润过低回复上升，策略多螺纹钢、空焦煤焦炭
                    target_pos_rb.set_target_volume(100)
                    target_pos_i.set_target_volume(-100)
                    target_pos_j.set_target_volume(-100)
                    current_position = 1
                    print("上穿下轨：多螺纹钢、空焦煤焦炭")

    # 实时监控价差变化情况
    if api.is_changing(klines_rb.iloc[-1], "close") or api.is_changing(klines_i.iloc[-1], "close") or api.is_changing(
            klines_j.iloc[-1], "close"):
        # 实时更新价差
        current_spread = klines_rb.close.iloc[-1] - 1.6 * klines_i.close.iloc[-1] - 0.5 * klines_j.close.iloc[-1]
        # 可以添加实时监控输出
        # print("当前价差: %.2f" % current_spread)
