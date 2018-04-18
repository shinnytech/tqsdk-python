# encoding: UTF-8

from tqsdk.api import TqApi
from tqsdk.task import TaskManager


class DemoMa:
    def __init__(self):
        self.api = TqApi()
        self.tm = TaskManager(self.api)

    def task_main(self):
        print("start")
        symbol = "SHFE.cu1805"
        kline_serial_5s = self.api.get_kline_serial(symbol, 5)
        kline_serial_1m = self.api.get_kline_serial(symbol, 60)
        while True:
            yield {
                "KLINE_DATA_UPDATED": lambda: self.api.is_changing(kline_serial_1m) or self.api.is_changing(kline_serial_5s),
            }
            # 计算最近3根5秒线均价
            average_price_15s = (kline_serial_5s[-1]["close"] + kline_serial_5s[-2]["close"] + kline_serial_5s[-3]["close"]) / 3
            # 计算最近30根1分钟线均价
            average_price_30m = sum(kline_serial_1m.close[-30:]) / 30
            # 如果条件符合
            print("average_price_15s", average_price_15s, "average_price_30m", average_price_30m)
            if average_price_15s > average_price_30m:
                self.api.insert_order(symbol=symbol, direction="BUY", offset="OPEN", volume=1, limit_price=5000)
        print("finish")

    def run(self):
        self.tm.start_task(self.task_main())
        self.api.run()


if __name__ == "__main__":
    d = DemoMa()
    d.run()

