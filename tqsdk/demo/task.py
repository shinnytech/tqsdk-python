# encoding: UTF-8

from tqsdk.api import TqApi
from tqsdk.task import TaskManager


class DemoTask:
    def __init__(self):
        self.api = TqApi()
        self.tm = TaskManager(self.api)

    def task_main(self):
        print ("start")
        quote = self.api.get_quote("SHFE.cu1805")
        while True:
            wait_result = yield {
                "QUOTE_CHANGED": lambda: self.api.is_changing(quote),
                "TIMEOUT": 0.2,
            }
            if wait_result["QUOTE_CHANGED"]:
                print("Quote", quote)
            if wait_result["TIMEOUT"]:
                print("Timeout")

    def run(self):
        self.tm.start_task(self.task_main())
        self.api.run()


if __name__ == "__main__":
    d = DemoTask()
    d.run()

