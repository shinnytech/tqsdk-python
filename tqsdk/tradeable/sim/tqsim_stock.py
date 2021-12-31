#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'mayanqiong'

from tqsdk.tradeable.mixin import StockMixin
from tqsdk.datetime import _format_from_timestamp_nano
from tqsdk.report import TqReport
from tqsdk.tradeable.sim.basesim import BaseSim
from tqsdk.tradeable.sim.trade_stock import SimTradeStock


class TqSimStock(BaseSim, StockMixin):
    """
    天勤股票模拟交易类

    该类实现了一个本地的股票模拟交易账户，并且在内部完成撮合交易，在回测模式下，只能使用 TqSimStock 账户来交易股票合约。

    股票模拟交易只支持 ins_class 字段为 'STOCK' 的合约，且不支持 T+0 交易。

    限价单要求报单价格达到或超过对手盘价格才能成交, 成交价为报单价格, 如果没有对手盘(涨跌停)则无法成交

    市价单使用对手盘价格成交, 如果没有对手盘(涨跌停)则自动撤单

    模拟交易不会有部分成交的情况, 要成交就是全部成交

    TqSimStock 暂不支持设置手续费
    """

    def __init__(self, init_balance: float = 10000000.0, account_id: str = None) -> None:
        """
        Args:
            init_balance (float): [可选]初始资金, 默认为一千万

            account_id (str): [可选]帐号, 默认为 TQSIM_STOCK

        Example1::

            # 修改TqSim模拟帐号的初始资金为100000
            from tqsdk import TqApi, TqSimStock, TqAuth
            api = TqApi(TqSimStock(init_balance=100000), auth=TqAuth("信易账户", "账户密码"))

        Example2::

            # 同时使用 TqSim 交易期货，TqSimStock 交易股票
            from tqsdk import TqApi, TqAuth, TqMultiAccount, TqSim, TqSimStock

            tqsim_future = TqSim()
            tqsim_stock = TqSimStock()

            api = TqApi(account=TqMultiAccount([tqsim_future, tqsim_stock]), auth=TqAuth("信易账户", "账户密码"))

            # 多账户下单，需要指定下单账户
            order1 = api.insert_order(symbol="SHFE.cu2112", direction="BUY", offset="OPEN", volume=10, limit_price=72250.0, account=tqsim_future)
            order2 = api.insert_order(symbol="SSE.603666", direction="BUY", volume=300, account=tqsim_stock)
            while order1.status != 'FINISHED' or order2.status != 'FINISHED':
                api.wait_update()

            # 打印账户可用资金
            future_account = tqsim_future.get_account()
            stock_account = tqsim_stock.get_account()
            print(future_account.available, stock_account.available)
            api.close()

        Example3::

            # 在回测模式下，同时使用 TqSim 交易期货，TqSimStock 交易股票
            api = TqApi(account=TqMultiAccount([tqsim_future, tqsim_stock]),
                        backtest=TqBacktest(start_dt=datetime(2021, 7, 12), end_dt=datetime(2021, 7, 14)),
                        auth=TqAuth("信易账户", "账户密码"))

            future_account = api.get_account(tqsim_future)
            stock_account = api.get_account(tqsim_stock)

            future_quote = api.get_quote("SHFE.cu2112")
            future_stock = api.get_quote("SSE.603666")

            while datetime.strptime(future_stock.datetime, "%Y-%m-%d %H:%M:%S.%f") < datetime(2021, 7, 12, 9, 50):
                api.wait_update()

            # 开仓，多账户下单，需要指定下单账户
            order1 = api.insert_order(symbol="SHFE.cu2112", direction="BUY", offset="OPEN", volume=10, limit_price=future_quote.ask_price1, account=tqsim_future)
            order2 = api.insert_order(symbol="SSE.603666", direction="BUY", volume=300, account=tqsim_stock)
            while order1.status != 'FINISHED' or order2.status != 'FINISHED':
                api.wait_update()

            # 等待行情回测到第二天
            while datetime.strptime(future_stock.datetime, "%Y-%m-%d %H:%M:%S.%f") < datetime(2021, 7, 13, 10, 30):
                api.wait_update()
            # 平仓，股票只能 T+1 交易
            order3 = api.insert_order(symbol="SHFE.cu2112", direction="SELL", offset="CLOSE", volume=8, limit_price=future_quote.bid_price1, account=tqsim_future)
            order4 = api.insert_order(symbol="SSE.603666", direction="SELL", volume=200, account=tqsim_stock)
            while order3.status != 'FINISHED' or order4.status != 'FINISHED':
                api.wait_update()

            try:  # 等到回测结束
                while True:
                    api.wait_update()
            except BacktestFinished:
                api.close()

        """
        if float(init_balance) <= 0:
            raise Exception("初始资金(init_balance) %s 错误, 请检查 init_balance 是否填写正确" % (init_balance))
        super(TqSimStock, self).__init__(account_id="TQSIM_STOCK" if account_id is None else account_id,
                                         init_balance=float(init_balance),
                                         trade_class=SimTradeStock)

    @property
    def _account_info(self):
        info = super(TqSimStock, self)._account_info
        info.update({
            "account_type": self._account_type
        })
        return info

    def _handle_on_alive(self, msg, order):
        """
        在 order 状态变为 ALIVE 调用，屏幕输出信息，打印日志
        """
        symbol = f"{order['exchange_id']}.{order['instrument_id']}"
        self._api._print(
            f"模拟交易下单 {self._account_name}, {order['order_id']}: 时间: {_format_from_timestamp_nano(order['insert_date_time'])}, "
            f"合约: {symbol}, 方向: {order['direction']}, 手数: {order['volume_left']}, "
            f"价格: {order.get('limit_price', '市价')}")
        self._logger.debug(msg, order_id=order["order_id"], datetime=order["insert_date_time"],
                           symbol=symbol, direction=order["direction"],
                           volume_left=order["volume_left"], limit_price=order.get("limit_price", "市价"))

    def _handle_on_finished(self, msg, order):
        """
        在 order 状态变为 FINISHED 调用，屏幕输出信息，打印日志
        """
        self._api._print(f"模拟交易委托单 {self._account_name}, {order['order_id']}: {order['last_msg']}")
        self._logger.debug(msg, order_id=order["order_id"], last_msg=order["last_msg"], status=order["status"],
                           volume_orign=order["volume_orign"], volume_left=order["volume_left"])

    def _report(self):
        if not self.trade_log:
            return
        date_keys = sorted(self.trade_log.keys())
        self._api._print(f"模拟交易成交记录, 账户: {self._account_name}")
        for d in date_keys:
            for t in self.trade_log[d]["trades"]:
                symbol = t["exchange_id"] + "." + t["instrument_id"]
                self._api._print(f"时间: {_format_from_timestamp_nano(t['trade_date_time'])}, 合约: {symbol}, "
                                 f"方向: {t['direction']}, 手数: {t['volume']}, 价格: {t['price']:.3f}, 手续费: {t['fee']:.2f}")

        self._api._print(f"模拟交易账户资金, 账户: {self._account_name}")
        for d in date_keys:
            account = self.trade_log[d]["account"]
            self._api._print(
                f"日期: {d}, 账户资产: {account['asset']:.2f}, 分红: {account['dividend_balance_today']:.2f}, "
                f"买入成本: {account['cost']:.2f}, 盈亏: {account['profit_today']:.2f}, 盈亏比: {account['profit_rate_today']:.2f}, "
                f"手续费: {account['buy_fee_today'] + account['sell_fee_today']:.2f}")
        report = TqReport(report_id=self._account_id, trade_log=self.trade_log, quotes=self._data['quotes'], account_type="SPOT")
        self.tqsdk_stat = report.default_metrics
        self._api._print(
            f"收益率: {self.tqsdk_stat['ror'] * 100:.2f}%, 年化收益率: {self.tqsdk_stat['annual_yield'] * 100:.2f}%, "
            f"最大回撤: {self.tqsdk_stat['max_drawdown'] * 100:.2f}%, 年化夏普率: {self.tqsdk_stat['sharpe_ratio']:.4f},"
            f"年化索提诺比率: {self.tqsdk_stat['sortino_ratio']:.4f}")
