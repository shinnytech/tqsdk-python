# encoding: UTF-8

from tqsdk.api import TqApi


class DemoCallback:
    def __init__(self):
        self.api = TqApi()
        self.quote = self.api.get_quote("SHFE.cu1805")

    def on_data_update(self):
        if self.quote.get("last_price", 0) > 1000:
            self.api.insert_order(symbol="SHFE.cu1805", direction="BUY", offset="OPEN", volume=1, limit_price=30000)

    def run(self):
        self.api.run(self.on_data_update)


if __name__ == "__main__":
    d = DemoCallback()
    d.run()

