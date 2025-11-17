from tqsdk import TqApi, TqAuth, TargetPosTask, TqBacktest, BacktestFinished
import numpy as np
from datetime import date

CU = "SHFE.cu2407"
AL = "SHFE.al2407"
START_DATE = date(2023, 11, 1)
END_DATE = date(2024, 4, 30)
LOOKBACK_DAYS = 30
STD_THRESHOLD = 2.0
ORDER_VOLUME = 30
CLOSE_THRESHOLD = 0.5

api = TqApi(backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE), auth=TqAuth("快期账号", "快期密码"))

cu_quote = api.get_quote(CU)
al_quote = api.get_quote(AL)
cu_klines = api.get_kline_serial(CU, 60*60*24, LOOKBACK_DAYS)
al_klines = api.get_kline_serial(AL, 60*60*24, LOOKBACK_DAYS)
cu_pos = TargetPosTask(api, CU)
al_pos = TargetPosTask(api, AL)

try:
    # 计算历史铜铝比
    ratios = []
    for i in range(len(cu_klines) - 1):
        cu_price = cu_klines.close.iloc[i] * cu_quote.volume_multiple
        al_price = al_klines.close.iloc[i] * al_quote.volume_multiple
        ratios.append(cu_price / al_price)
    mean_ratio = np.mean(ratios)
    std_ratio = np.std(ratios)
    print(f"历史铜铝比均值: {mean_ratio:.4f}, 标准差: {std_ratio:.4f}")

    in_position = False
    while True:
        api.wait_update()
        if api.is_changing(cu_klines) or api.is_changing(al_klines):
            # 重新计算
            ratios = []
            for i in range(len(cu_klines) - 1):
                cu_price = cu_klines.close.iloc[i] * cu_quote.volume_multiple
                al_price = al_klines.close.iloc[i] * al_quote.volume_multiple
                ratios.append(cu_price / al_price)
            mean_ratio = np.mean(ratios)
            std_ratio = np.std(ratios)
            cu_price = cu_klines.close.iloc[-1] * cu_quote.volume_multiple
            al_price = al_klines.close.iloc[-1] * al_quote.volume_multiple
            current_ratio = cu_price / al_price
            z_score = (current_ratio - mean_ratio) / std_ratio
            print(f"当前铜铝比: {current_ratio:.4f}, Z-score: {z_score:.2f}")

            cu_position = api.get_position(CU)
            al_position = api.get_position(AL)
            current_cu_pos = cu_position.pos_long - cu_position.pos_short
            current_al_pos = al_position.pos_long - al_position.pos_short

            if not in_position:
                if z_score > STD_THRESHOLD:
                    # 做多铜铝比：买入铜，卖出铝
                    print(f"做多铜铝比：买入铜{ORDER_VOLUME}手，卖出铝{ORDER_VOLUME}手")
                    cu_pos.set_target_volume(ORDER_VOLUME)
                    al_pos.set_target_volume(-ORDER_VOLUME)
                    in_position = True
                elif z_score < -STD_THRESHOLD:
                    # 做空铜铝比：卖出铜，买入铝
                    print(f"做空铜铝比：卖出铜{ORDER_VOLUME}手，买入铝{ORDER_VOLUME}手")
                    cu_pos.set_target_volume(-ORDER_VOLUME)
                    al_pos.set_target_volume(ORDER_VOLUME)
                    in_position = True
            else:
                if abs(z_score) < CLOSE_THRESHOLD:
                    print("比率回归正常，平仓所有头寸")
                    cu_pos.set_target_volume(0)
                    al_pos.set_target_volume(0)
                    in_position = False
                # 止损逻辑
                if (z_score > STD_THRESHOLD * 1.5 and current_cu_pos < 0) or \
                   (z_score < -STD_THRESHOLD * 1.5 and current_cu_pos > 0):
                    print("止损：比率向不利方向进一步偏离")
                    cu_pos.set_target_volume(0)
                    al_pos.set_target_volume(0)
                    in_position = False

except BacktestFinished as e:
    print("回测结束")
    api.close()

