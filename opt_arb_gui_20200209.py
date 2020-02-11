import asyncio
import sys
import PySimpleGUI as sg
from tqsdk import TqApi, TqSim, TqAccount, TqBacktest
from tqsdk.lib import TargetPosTask
from tqsdk.tafunc import time_to_datetime
from tqsdk.exceptions import BacktestFinished
from datetime import datetime, date
from contextlib import closing
from opt import TqOption, OptionTrade


window = sg.Window('请输入策略运行参数', layout = [[sg.Text('交易账户')],
          [sg.Text('期货公司'), sg.Input("快期模拟", key="broker_id")],
          [sg.Text('账号'), sg.Input("jincheng", key="user_id")],
          [sg.Text('密码'), sg.Input("123456", key="password", password_char='*')],
          [sg.Text('策略参数')],
          [sg.Text('期货主连代码'), sg.Input("KQ.m@CZCE.SR", key="future_kq_id")],
          [sg.Text('期货product_id'), sg.Input("SR", key="future_product_id")],
          [sg.Text('期权product_id'), sg.Input("SR", key="option_product_id")],
          [sg.Text('最大long call值'), sg.Input(-5, key="long_call_threshold")],
          [sg.Text('最大long put值'), sg.Input(-5, key="long_put_threshold")],
          [sg.Text('最小行权价'), sg.Input(5400, key="min_strike")],
          [sg.Text('最大行权价'), sg.Input(5800, key="max_strike")],
          [sg.OK()]])

# 读取用户输入值
event, input_values = window.Read()
print(event, input_values)
window.close()


loop = asyncio.get_event_loop()
api = TqApi(loop=loop, account=TqAccount(input_values["broker_id"], input_values["user_id"], input_values["password"]) if len(input_values["broker_id"])> 2 else TqSim())
opt_api = TqOption(api, future_product_id=input_values["future_product_id"], option_product_id=input_values["option_product_id"])
kq_m = api.get_quote(input_values["future_kq_id"])
main_contract_id = kq_m.underlying_symbol
future = api.get_quote(main_contract_id)
future_id, opts = opt_api.get_future_opt_symbols(
    strike_year=future.delivery_year, strike_month=future.delivery_month,
    min_strike=float(input_values["min_strike"]), max_strike=float(input_values["max_strike"]))

# 期货行情订阅
future_quote = api.get_quote(future_id)
#quote_layout = [[sg.Text("time=", size=(5,1)), sg.Text("%H:%m:%S", key="dt", size=(10,1))], [sg.Text("strike",size=(5,1)), sg.Text("call",size=(6,1)), sg.Text("put",size=(6,1))]]
#quote_layout.extend([[sg.Text(opt["K"],size=(5,1)), sg.Text("nan", key="{}-call_premium".format(opt["K"]),size=(6,1)), sg.Text("nan", key="{}-put_premium".format(opt["K"]),size=(6,1))] for opt in opts.values()])
#quote_window = sg.Window(future_id, quote_layout, size=(300,300))
#async def new_quote_window():
#    event, _ = quote_window.Read(timeout=0)
#    if event is None or event == 'Exit':
#        sys.exit(0)
#api.create_task(new_quote_window())

trade = OptionTrade(api, opt_api, future_id, opts, can_trade=True,
                    long_call_threshold=float(input_values["long_call_threshold"]), 
                    long_put_threshold=float(input_values["long_put_threshold"]))

for opt in opts.values():
    trade.parity_quote_task(opt, future_quote)

# 主线程
while True:
    api.wait_update()
