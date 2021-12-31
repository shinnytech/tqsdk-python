#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'mayanqiong'

from tqsdk.tradeable.mixin import FutureMixin
from tqsdk.datetime import _format_from_timestamp_nano
from tqsdk.diff import _get_obj
from tqsdk.objs import Quote
from tqsdk.report import TqReport
from tqsdk.tradeable.sim.basesim import BaseSim
from tqsdk.tradeable.sim.trade_future import SimTrade
from tqsdk.tradeable.sim.utils import _get_future_margin, _get_commission


class TqSim(BaseSim, FutureMixin):
    """
    天勤模拟交易类

    该类实现了一个本地的模拟账户，并且在内部完成撮合交易，在回测和复盘模式下，只能使用 TqSim 账户来交易。

    限价单要求报单价格达到或超过对手盘价格才能成交, 成交价为报单价格, 如果没有对手盘(涨跌停)则无法成交

    市价单使用对手盘价格成交, 如果没有对手盘(涨跌停)则自动撤单

    模拟交易不会有部分成交的情况, 要成交就是全部成交
    """

    def __init__(self, init_balance: float = 10000000.0, account_id: str = None) -> None:
        """
        Args:
            init_balance (float): [可选]初始资金, 默认为一千万

            account_id (str): [可选]帐号, 默认为 TQSIM

        Example::

            # 修改TqSim模拟帐号的初始资金为100000
            from tqsdk import TqApi, TqSim, TqAuth
            api = TqApi(TqSim(init_balance=100000), auth=TqAuth("信易账户", "账户密码"))

        """
        if float(init_balance) <= 0:
            raise Exception("初始资金(init_balance) %s 错误, 请检查 init_balance 是否填写正确" % (init_balance))
        super(TqSim, self).__init__(account_id="TQSIM" if account_id is None else account_id,
                                    init_balance=float(init_balance),
                                    trade_class=SimTrade)

    @property
    def _account_info(self):
        info = super(TqSim, self)._account_info
        info.update({
            "account_type": self._account_type
        })
        return info

    def set_commission(self, symbol: str, commission: float=float('nan')):
        """
        设置指定合约模拟交易的每手手续费。

        Args:
            symbol (str): 合约代码

            commission (float): 每手手续费

        Returns:
            float: 设置的每手手续费

        Example::

            from tqsdk import TqSim, TqApi, TqAuth

            sim = TqSim()
            api = TqApi(sim, auth=TqAuth("信易账户", "账户密码"))

            sim.set_commission("SHFE.cu2112", 50)

            print(sim.get_commission("SHFE.cu2112"))
        """
        if commission != commission:
            raise Exception("合约手续费不可以设置为 float('nan')")
        quote = _get_obj(self._data, ["quotes", symbol], Quote(self._api if hasattr(self, "_api") else None))
        quote["user_commission"] = commission
        if self._quote_tasks.get(symbol):
            self._quote_tasks[symbol]["quote_chan"].send_nowait({
                "quotes": {symbol: {"user_commission": commission}}
            })
        return commission

    def set_margin(self, symbol: str, margin: float=float('nan')):
        """
        设置指定合约模拟交易的每手保证金。

        Args:
            symbol (str): 合约代码 (只支持期货合约)

            margin (float): 每手保证金

        Returns:
            float: 设置的每手保证金

        Example::

            from tqsdk import TqSim, TqApi, TqAuth

            sim = TqSim()
            api = TqApi(sim, auth=TqAuth("信易账户", "账户密码"))

            sim.set_margin("SHFE.cu2112", 26000)

            print(sim.get_margin("SHFE.cu2112"))
        """
        if margin != margin:
            raise Exception("合约手续费不可以设置为 float('nan')")
        quote = _get_obj(self._data, ["quotes", symbol], Quote(self._api if hasattr(self, "_api") else None))
        quote["user_margin"] = margin
        if self._quote_tasks.get(symbol):
            self._quote_tasks[symbol]["quote_chan"].send_nowait({
                "quotes": {symbol: {"user_margin": margin}}
            })
            # 当用户设置保证金时，用户应该得到的效果是：
            # 在调用 sim.set_margin() 之后，立即调用 api.get_position(symbol)，得到的 margin 字段应该按照新设置的保证金调整过，而且中间没有收到过行情更新包
            # 以下代码可以保证这个效果，说明：
            # 1. 持仓已经调整过:
            #   sim_trade 中持仓的 future_margin 字段更新，margin 会同时调整，那么 api 中持仓的 future_margin 更新时，margin 一定也已经更新
            # 2. 中间没有收到过行情更新包:
            #   前提1：根据 diff 协议，sim 收到 peek_message 时，会将缓存的 diffs 发给用户，当缓存的 diffs 为空，会转发 peek_message；
            #   前提2：api.wait_update() 会等到所有 task 都执行到 pending 状态，然后发送 peek_message 给 sim
            #   当用户代码执行到 sim.set_margin()，立即向 quote_chan 中发送一个数据包，quote_task 就会到 ready 状态，此时调用 wait_update()，
            #   到所有 task 执行到 pending 状态时，sim 的 diffs 中有数据了，此时收到 api 发来 peek_message 不会转发给上游，用户会先收到 sim 本身的账户数据，
            #   在下一次 wait_update，sim 的 diffs 为空，才会收到行情数据
            # 在回测时，以下代码应该只经历一次 wait_update
            while margin != self._api.get_position(symbol).get("future_margin"):
                self._api.wait_update()
        return margin

    def get_margin(self, symbol: str):
        """
        获取指定合约模拟交易的每手保证金。

        Args:
            symbol (str): 合约代码

        Returns:
            float: 返回合约模拟交易的每手保证金

        Example::

            from tqsdk import TqSim, TqApi, TqAuth

            sim = TqSim()
            api = TqApi(sim, auth=TqAuth("信易账户", "账户密码"))

            quote = api.get_quote("SHFE.cu2112")
            print(sim.get_margin("SHFE.cu2112"))
        """
        return _get_future_margin(self._data.get("quotes", {}).get(symbol, {}))

    def get_commission(self, symbol: str):
        """
        获取指定合约模拟交易的每手手续费

        Args:
            symbol (str): 合约代码

        Returns:
            float: 返回合约模拟交易的每手手续费

        Example::

            from tqsdk import TqSim, TqApi, TqAuth

            sim = TqSim()
            api = TqApi(sim, auth=TqAuth("信易账户", "账户密码"))

            quote = api.get_quote("SHFE.cu2112")
            print(sim.get_commission("SHFE.cu2112"))
        """
        return _get_commission(self._data.get("quotes", {}).get(symbol, {}))

    def _handle_on_alive(self, msg, order):
        """
        在 order 状态变为 ALIVE 调用，屏幕输出信息，打印日志
        """
        symbol = f"{order['exchange_id']}.{order['instrument_id']}"
        self._api._print(
            f"模拟交易下单 {self._account_name}, {order['order_id']}: 时间: {_format_from_timestamp_nano(order['insert_date_time'])}, "
            f"合约: {symbol}, 开平: {order['offset']}, 方向: {order['direction']}, 手数: {order['volume_left']}, "
            f"价格: {order.get('limit_price', '市价')}")
        self._logger.debug(msg, order_id=order["order_id"], datetime=order["insert_date_time"],
                           symbol=symbol, offset=order["offset"], direction=order["direction"],
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
                                 f"开平: {t['offset']}, 方向: {t['direction']}, 手数: {t['volume']}, 价格: {t['price']:.3f},"
                                 f"手续费: {t['commission']:.2f}")

        self._api._print(f"模拟交易账户资金, 账户: {self._account_name}")
        for d in date_keys:
            account = self.trade_log[d]["account"]
            self._api._print(
                f"日期: {d}, 账户权益: {account['balance']:.2f}, 可用资金: {account['available']:.2f}, "
                f"浮动盈亏: {account['float_profit']:.2f}, 持仓盈亏: {account['position_profit']:.2f}, "
                f"平仓盈亏: {account['close_profit']:.2f}, 市值: {account['market_value']:.2f}, "
                f"保证金: {account['margin']:.2f}, 手续费: {account['commission']:.2f}, "
                f"风险度: {account['risk_ratio'] * 100:.2f}%")

        # TqReport 模块计算交易统计信息
        report = TqReport(report_id=self._account_id, trade_log=self.trade_log, quotes=self._data['quotes'])
        self.tqsdk_stat = report.default_metrics
        self._api._print(
            f"胜率: {self.tqsdk_stat['winning_rate'] * 100:.2f}%, 盈亏额比例: {self.tqsdk_stat['profit_loss_ratio']:.2f}, "
            f"收益率: {self.tqsdk_stat['ror'] * 100:.2f}%, 年化收益率: {self.tqsdk_stat['annual_yield'] * 100:.2f}%, "
            f"最大回撤: {self.tqsdk_stat['max_drawdown'] * 100:.2f}%, 年化夏普率: {self.tqsdk_stat['sharpe_ratio']:.4f},"
            f"年化索提诺比率: {self.tqsdk_stat['sortino_ratio']:.4f}")

        # 回测情况下，在计算报告之后，还会发送绘制图表请求，
        # 这样处理，用户不要修改代码，就能够看到报告图表
        if self._tqsdk_backtest:
            self._api.draw_report(report.full())
