# encoding: UTF-8

from tqsdk.api import TqApi
from tqsdk.task import TaskManager
from tqsdk.tools import make_order_until_all_matched


class DemoSpread:
    def __init__(self):
        self.api = TqApi()
        self.tm = TaskManager(self.api)

    def task_main(self):
        print ("start")
        symbol_a = "SHFE.cu1805"
        symbol_b = "SHFE.cu1806"
        quote_a = self.api.get_quote(symbol_a)
        quote_b = self.api.get_quote(symbol_b)
        buy_open_spread = 50000
        sell_close_spread = -70000
        max_volume = 5
        long_volume = 0
        while True:
            wait_result = yield {
                "BUY_OPEN": lambda: long_volume == 0 and quote_a["ask_price1"] - quote_b["bid_price1"] < buy_open_spread,
                "SELL_CLOSE": lambda: long_volume > 0 and quote_a["bid_price1"] - quote_b["ask_price1"] > sell_close_spread,
            }
            if wait_result["BUY_OPEN"]:
                task_a = self.tm.start_task(make_order_until_all_matched(self.api, symbol=symbol_a, direction="BUY", offset="OPEN", volume=max_volume))
                task_b = self.tm.start_task(make_order_until_all_matched(self.api, symbol=symbol_b, direction="SELL", offset="OPEN", volume=max_volume))
                long_volume = max_volume
            if wait_result["SELL_CLOSE"]:
                task_a = self.tm.start_task(make_order_until_all_matched(self.api, symbol=symbol_a, direction="SELL", offset="CLOSE", volume=max_volume))
                task_b = self.tm.start_task(make_order_until_all_matched(self.api, symbol=symbol_b, direction="BUY", offset="CLOSE", volume=max_volume))
                long_volume = 0
            wait_subtask_finish = yield {
                "ANY_TASK_ERROR": lambda: self.tm.get_error(task_a) or self.tm.get_error(task_b),
                "BOTH_TASK_FINSISH": lambda: self.tm.is_finish(task_a) and self.tm.is_finish(task_b),
            }
            if wait_subtask_finish["ANY_TASK_ERROR"]:
                break
        print ("finish")

    def run(self):
        self.tm.start_task(self.task_main())
        self.api.run()


if __name__ == "__main__":
    d = DemoSpread()
    d.run()

