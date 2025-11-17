import numpy as np
import pandas as pd
from tqsdk import TqApi, TqAuth, TargetPosTask, TqBacktest, BacktestFinished
from datetime import date

# === 全局参数 ===
SYMBOL_Y = "SHFE.ss2209"
SYMBOL_X = "SHFE.ni2209"
OBS_VAR = 0.01
STATE_VAR = 0.0001
INIT_MEAN = 1.0
INIT_VAR = 1.0
WIN = 60
OPEN_H = 2.0
OPEN_L = -2.0
CLOSE_H = 0.5
CLOSE_L = -0.5
STOP_SPREAD = 3.0
MAX_HOLD = 10
POS_PCT = 0.05
INIT_CAP = 10000000

# === 全局变量 ===
state_mean = INIT_MEAN
state_var = INIT_VAR
prices_y, prices_x, hedge_ratios, spreads, zscores = [], [], [], [], []
position = 0
entry_z = 0
entry_time = None
trade_count = 0
win_count = 0
total_profit = 0
total_loss = 0
hold_days = 0
last_day = None

# === API初始化 ===
api = TqApi(backtest=TqBacktest(start_dt=date(2022, 7, 4), end_dt=date(2022, 8, 31)),
                auth=TqAuth("快期账号", "快期密码"))
quote_y = api.get_quote(SYMBOL_Y)
quote_x = api.get_quote(SYMBOL_X)
klines_y = api.get_kline_serial(SYMBOL_Y, 60*60)
klines_x = api.get_kline_serial(SYMBOL_X, 60*60)
target_y = TargetPosTask(api, SYMBOL_Y)
target_x = TargetPosTask(api, SYMBOL_X)

try:
    while True:
        api.wait_update()
        if api.is_changing(klines_y.iloc[-1], "datetime") or api.is_changing(klines_x.iloc[-1], "datetime"):
            price_y = klines_y.iloc[-1]["close"]
            price_x = klines_x.iloc[-1]["close"]
            now = pd.to_datetime(klines_y.iloc[-1]["datetime"], unit="ns")
            today = now.date()
            if last_day and today != last_day and position != 0:
                hold_days += 1
            last_day = today
            prices_y.append(price_y)
            prices_x.append(price_x)
            if len(prices_y) > 10:
                # 卡尔曼滤波
                pred_mean = state_mean
                pred_var = state_var + STATE_VAR
                k_gain = pred_var / (pred_var * price_x**2 + OBS_VAR)
                state_mean = pred_mean + k_gain * (price_y - pred_mean * price_x)
                state_var = (1 - k_gain * price_x) * pred_var
                hedge_ratios.append(state_mean)
                spread = price_y - state_mean * price_x
                spreads.append(spread)
                if len(spreads) >= WIN:
                    recent = spreads[-WIN:]
                    mean = np.mean(recent)
                    std = np.std(recent)
                    z = (spread - mean) / std if std > 0 else 0
                    zscores.append(z)
                    print(f"时间:{now}, Y:{price_y}, X:{price_x}, 对冲比:{state_mean:.4f}, Z:{z:.4f}")
                    # 开仓
                    if position == 0:
                        if z < OPEN_L:
                            lots = int(INIT_CAP * POS_PCT / quote_y.margin)
                            lots_x = int(lots * state_mean * price_y * quote_y.volume_multiple / (price_x * quote_x.volume_multiple))
                            if lots > 0 and lots_x > 0:
                                target_y.set_target_volume(lots)
                                target_x.set_target_volume(-lots_x)
                                position = 1
                                entry_z = z
                                entry_time = now
                                print(f"开多Y空X, Y:{lots}, X:{lots_x}, 入场Z:{z:.4f}")
                        elif z > OPEN_H:
                            lots = int(INIT_CAP * POS_PCT / quote_y.margin)
                            lots_x = int(lots * state_mean * price_y * quote_y.volume_multiple / (price_x * quote_x.volume_multiple))
                            if lots > 0 and lots_x > 0:
                                target_y.set_target_volume(-lots)
                                target_x.set_target_volume(lots_x)
                                position = -1
                                entry_z = z
                                entry_time = now
                                print(f"开空Y多X, Y:{lots}, X:{lots_x}, 入场Z:{z:.4f}")
                    # 平仓
                    else:
                        profit_cond = CLOSE_L < z < CLOSE_H
                        stop_cond = (position == 1 and z < entry_z - STOP_SPREAD) or (position == -1 and z > entry_z + STOP_SPREAD)
                        max_hold = hold_days >= MAX_HOLD
                        if profit_cond or stop_cond or max_hold:
                            target_y.set_target_volume(0)
                            target_x.set_target_volume(0)
                            trade_count += 1
                            pnl = (z - entry_z) * position
                            if pnl > 0:
                                win_count += 1
                                total_profit += pnl
                            else:
                                total_loss -= pnl
                            reason = "回归" if profit_cond else "止损" if stop_cond else "超期"
                            print(f"平仓:{reason}, 出场Z:{z:.4f}, 收益:{pnl:.4f}, 持有天:{hold_days}")
                            position = 0
                            entry_z = 0
                            entry_time = None
                            hold_days = 0

except BacktestFinished as e:
    print("回测结束")
    api.close()

