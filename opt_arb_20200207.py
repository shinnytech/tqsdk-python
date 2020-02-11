from tqsdk import TqApi, TqSim, TqBacktest, TqReplay
from tqsdk.lib import TargetPosTask
from tqsdk.tafunc import time_to_datetime
from tqsdk.exceptions import BacktestFinished
from datetime import datetime, date
from contextlib import closing
from opt import TqOption, OptionTrade

#api = TqApi(TqSim())
api = TqApi(TqSim(init_balance=300000), backtest=TqBacktest(
    start_dt=datetime(2020, 1, 1, 9), end_dt=datetime(2020, 2, 7, 16)))
#api = TqApi(backtest=TqReplay(date(2020,2,5)), web_gui=True)
kq_m = api.get_quote("KQ.m@DCE.i")
opt_api = TqOption(api, future_product_id="SR", option_product_id="SR_o")
main_contract_id = kq_m.underlying_symbol
future = api.get_quote(main_contract_id)
future_id, opts = opt_api.get_future_opt_symbols(
    strike_year=future.delivery_year, strike_month=future.delivery_month)
trade = OptionTrade(api, opt_api, future_id, opts, save_data=True,
                    long_call_threshold=-5, long_put_threshold=-5)
# future_id, opts = opt_api.get_future_opt_symbols(opt_api.strike_dates[0])  # 选一个2020-3合约

print("期货代码：" + future_id)

# 期货行情订阅
future_quote = api.get_quote(future_id)
# 期权-期货套利任务准备
for opt in opts.values():
    trade.parity_quote_task(opt, future_quote)
api.wait_update()
# 主线程
if api._backtest is None:
    while True:
        api.wait_update()
        if trade.save_data and (datetime.now().minute == 0 or datetime.now().minute == 30) and datetime.now().second == 0:
            print('ts:{}'.format(datetime.now()))
            trade.quote_df.to_excel('quote_data_rt_{}.xlsx'.format(
                datetime.now().strftime('%Y%m%d%H')))
else:
    with closing(api):
        while True:
            try:
                api.wait_update()
                if trade.save_data and datetime.now().second == 0:
                    print('ts:{}'.format(time_to_datetime(
                        api._backtest._current_dt)))
            except BacktestFinished:
                trade.quote_df.to_excel('quote_data_bt_{}.xlsx'.format(
                    datetime.now().strftime('%Y%m%d%H%M')))
                exit()
