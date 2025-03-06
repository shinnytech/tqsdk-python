from datetime import date
from tqsdk import TqApi, TqSim, TqAccount, TqBacktest, TqAuth

def run_backtest():
    api = TqApi(backtest=TqBacktest(start_dt=date(2021, 1, 1), end_dt=date(2021, 12, 31)), web_gui=True, auth=TqAuth("13760685574", "xdy19870920"))

def run_simulation():
    api = TqApi(TqSim(init_balance=100000), web_gui=True, auth=TqAuth("13760685574", "xdy19870920"))

def run_real_trading():
    api = TqApi(TqAccount("期货公司", "账户", "密码"), web_gui=True, auth=TqAuth("13760685574", "xdy19870920"))

def main():
    print("请选择运行模式: 1. 回测 2. 模拟 3. 实盘")
    choice = input("输入选择(1/2/3): ")
    if choice == '1':
        run_backtest()
    elif choice == '2':
        run_simulation()
    elif choice == '3':
        run_real_trading()
    else:
        print("无效选择，请输入1, 2或3")

if __name__ == "__main__":
    main()
