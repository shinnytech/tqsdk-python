#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = "mayanqiong"

from tqsdk.tradeable.sim.trade_base import SimTradeBase
from tqsdk.tradeable.sim.utils import _get_stock_fee, _get_order_price, _get_dividend_ratio


class SimTradeStock(SimTradeBase):
    """
    天勤模拟交易账户，期货及商品期权
    """

    def _generate_account(self, init_balance):
        return {
            "user_id": self._account_id,  # 客户号, 与 order / trade 对象中的 user_id 值保持一致
            "currency": "CNY",
            "market_value_his": 0.0,  # 期初市值
            "asset_his": init_balance,  # 期初资产
            "cost_his": 0.0,  # 期初买入成本
            "deposit": 0.0,
            "withdraw": 0.0,
            "dividend_balance_today": 0.0,  # 当日分红金额

            "available_his": init_balance,

            "market_value": 0.0,  # 当前市值
            "asset": init_balance,  # 当前资产 = 当前市值 + 可用余额 + 冻结
            "available": init_balance,  # 可用余额 = 期初余额 + 当日分红金额 - 买入费用 - 卖出费用 + 当日入金 - 当日出金 - 当日买入占用资金 + 当日卖出释放资金 - 委托冻结金额 - 委托冻结费用
            "drawable": init_balance,  # 可取余额 = 可用余额 - 当日卖出释放资金
            "buy_frozen_balance": 0.0,  # 当前交易冻结金额（不含费用）= sum(order.volume_orign * order.limit_price)
            "buy_frozen_fee": 0.0,  # 当前交易冻结费用 = sum(order.frozen_fee)
            "buy_balance_today": 0.0,  # 当日买入占用资金（不含费用）
            "buy_fee_today": 0.0,  # 当日买入累计费用
            "sell_balance_today": 0.0,  # 当日卖出释放资金
            "sell_fee_today": 0.0,  # 当日卖出累计费用
            "cost": 0.0,  # 当前买入成本 = SUM（买入成本）
            "hold_profit": 0.0,  # 当日持仓盈亏 = 当前市值 - 当前买入成本
            "float_profit_today": 0.0,  # 当日浮动盈亏 = SUM(持仓当日浮动盈亏)
            "real_profit_today": 0.0,  # 当日实现盈亏 = SUM(持仓当日实现盈亏)
            "profit_today": 0.0,  # 当日盈亏 = 当日浮动盈亏 + 当日实现盈亏
            "profit_rate_today": 0.0  # 当日盈亏比 = 当日盈亏 / (当前买入成本 if 当前买入成本 > 0 else 期初资产)
        }

    def _generate_position(self, symbol, quote, underlying_quote) -> dict:
        return {
            "user_id": self._account_id,
            "exchange_id": symbol.split(".", maxsplit=1)[0],
            "instrument_id": symbol.split(".", maxsplit=1)[1],
            "create_date": "",  # 建仓日期
            "volume_his": 0,  # 昨持仓数量
            "cost_his": 0.0,  # 期初买入成本
            "market_value_his": 0.0,  # 期初市值
            "real_profit_his": 0.0,  # 期初实现盈亏
            "shared_volume_today": 0,  # 今送股数量
            "devidend_balance_today": 0.0,  # 今分红金额

            "buy_volume_his": 0,  # 期初累计买入持仓
            "buy_balance_his": 0.0,  # 期初累计买入金额
            "buy_fee_his": 0.0,  # 期初累计买入费用
            "sell_volume_his": 0,  # 期初累计卖出持仓
            "sell_balance_his": 0.0,  # 期初累计卖出金额
            "sell_fee_his": 0.0,  # 期初累计卖出费用

            "buy_volume_today": 0,  # 当日累计买入持仓
            "buy_balance_today": 0.0,  # 当日累计买入金额 (不包括费用)
            "buy_fee_today": 0.0,  # 当日累计买入费用
            "sell_volume_today": 0,  # 当日累计卖出持仓
            "sell_balance_today": 0.0,  # 当日累计卖出金额 (不包括费用)
            "sell_fee_today": 0.0,  # 当日累计卖出费用

            "last_price": quote["last_price"],
            "sell_volume_frozen": 0,  # 今日卖出冻结手数
            "sell_float_profit_today": 0.0,  # 昨仓浮动盈亏 = (昨持仓数量 - 今卖数量) * (最新价 - 昨收盘价)
            "buy_float_profit_today": 0.0,  # 今仓浮动盈亏 = (今持仓数量 - (昨持仓数量 - 今卖数量)) * (最新价 - 买入均价)
            # 买入均价 = (buy_balance_today + buy_fee_today) / buy_volume_today

            "cost": 0.0,  # 当前成本 = 期初成本 + 今买金额 + 今买费用 - 今卖数量 × (期初买入成本 / 期初持仓数量)
            "volume": 0,  # 今持仓数量 = 昨持仓数量 + 今买数量 - 今卖数量 + 送股数量
            "market_value": 0.0,  # 当前市值 = 持仓数量 × 行情最新价
            "float_profit_today": 0.0,  # 当日浮动盈亏 = sell_float_profit_today + buy_float_profit_today
            "real_profit_today": 0.0,  # 当日实现盈亏 = 今卖数量 * (最新价 - 昨收盘价) - 今卖费用 + 今派息金额
            "profit_today": 0.0,  # 当日盈亏 = 当日浮动盈亏 + 当日实现盈亏
            "profit_rate_today": 0.0,  # 当日收益率 = 当日盈亏 / ( 当前成本 if 当前成本 > 0 else 期初市值)
            "hold_profit": 0.0,  # 当日持仓盈亏 = 当前市值 – 当前买入成本
            "real_profit_total": 0.0,  # 累计实现盈亏 += 当日实现盈亏（成本）
            "profit_total": 0.0,  # 总盈亏 = 累计实现盈亏 + 持仓盈亏
            "profit_rate_total": 0.0,  # 累计收益率 = 总盈亏 / (当前成本 if 当前成本 > 0 else 期初成本)
        }

    def _generate_order(self, pack: dict) -> dict:
        """order 对象预处理"""
        order = pack.copy()
        order["exchange_order_id"] = order["order_id"]
        order["volume_orign"] = order["volume"]
        order["volume_left"] = order["volume"]
        order["frozen_balance"] = 0.0
        order["frozen_fee"] = 0.0
        order["last_msg"] = "报单成功"
        order["status"] = "ALIVE"
        order["insert_date_time"] = self._get_trade_timestamp()
        del order["aid"]
        del order["volume"]
        self._append_to_diffs(["orders", order["order_id"]], order)
        return order

    def _generate_trade(self, order, quote, price) -> dict:
        fee = _get_stock_fee(order["direction"], order["volume_left"], price)
        return {
            "user_id": order["user_id"],
            "order_id": order["order_id"],
            "trade_id": order["order_id"] + "|" + str(order["volume_left"]),
            "exchange_trade_id": order["order_id"] + "|" + str(order["volume_left"]),
            "exchange_id": order["exchange_id"],
            "instrument_id": order["instrument_id"],
            "direction": order["direction"],  # 下单方向, BUY=买, SELL=卖，SHARED=送股，DEVIDEND=分红 (送股|分红没有计算费用)
            "price": price,
            "volume": order["volume_left"],
            "trade_date_time": self._get_trade_timestamp(),  # todo: 可能导致测试结果不确定
            "fee": fee
        }

    def _on_settle(self):
        for symbol in self._orders:
            for order in self._orders[symbol].values():
                order["frozen_balance"] = 0.0
                order["frozen_fee"] = 0.0
                order["last_msg"] = "交易日结束，自动撤销当日有效的委托单（GFD）"
                order["status"] = "FINISHED"
                self._append_to_diffs(["orders", order["order_id"]], order)

        dividend_balance_today = 0.0  # 今日分红总的分红数据
        for position in self._positions.values():
            symbol = f"{position['exchange_id']}.{position['instrument_id']}"
            quote, _ = self._get_quotes_by_symbol(symbol)
            stock_dividend, cash_dividend = _get_dividend_ratio(quote)
            # position 原始字段
            position["volume_his"] = position["volume"]  # 期初持仓数量
            position["cost_his"] = position["cost"]  # 期初买入成本
            position["market_value_his"] = position["market_value"]  # 期初市值
            position["real_profit_his"] = position["real_profit_today"]  # 期初实现盈亏

            # 处理分红送股
            position["shared_volume_today"] = stock_dividend * position["volume"]  # 今送股数量
            position["devidend_balance_today"] = cash_dividend * position["volume"]  # 今分红金额
            if position["shared_volume_today"] > 0.0 or position["devidend_balance_today"] > 0.0:
                position["volume"] += position["shared_volume_today"]
                position["market_value"] -= position["devidend_balance_today"]  # 分红后的市值
                position["last_price"] = position["market_value"] / position["volume"]  # 分红送股后的最新价, todo: 可能会于第二天收到的第一笔行情有误差？
                dividend_balance_today += position["devidend_balance_today"]  # 记录累积分红金额，account 需要

            position["buy_volume_his"] = position["buy_volume_today"]
            position["buy_balance_his"] = position["buy_balance_today"]
            position["buy_fee_his"] = position["buy_fee_today"]
            position["sell_volume_his"] = position["sell_volume_today"]
            position["sell_balance_his"] = position["sell_balance_today"]
            position["sell_fee_his"] = position["sell_fee_today"]
            position["buy_volume_today"] = 0
            position["buy_balance_today"] = 0.0
            position["buy_fee_today"] = 0.0
            position["sell_volume_today"] = 0
            position["sell_balance_today"] = 0.0
            position["sell_fee_today"] = 0.0

            position["sell_volume_frozen"] = 0
            position["buy_avg_price"] = 0.0
            position["sell_float_profit_today"] = 0.0
            position["buy_float_profit_today"] = 0.0

            position["float_profit_today"] = 0.0  # 当日浮动盈亏 = position["sell_float_profit_today"] + position["buy_float_profit_today"]
            position["real_profit_today"] = 0.0  # 当日实现盈亏 = 今卖数量 * (最新价 - 昨收盘价) - 今卖费用 + 今派息金额
            position["profit_today"] = 0.0  # 当日盈亏 = 当日浮动盈亏 + 当日实现盈亏
            position["profit_rate_today"] = 0.0 # 当日收益率 = 当日盈亏 / ( 当前成本 if 当前成本 > 0 else 期初市值)
            position["hold_profit"] = 0.0  # 当日持仓盈亏 = 当前市值 – 当前买入成本
            self._append_to_diffs(["positions", symbol], position)

        # account 原始字段
        self._account["dividend_balance_today"] = dividend_balance_today
        self._account["market_value_his"] = self._account["market_value"]
        self._account["asset_his"] = self._account["asset"]
        self._account["cost_his"] = self._account["cost"]
        self._account["available_his"] = self._account["available"] + self._account["buy_frozen_balance"] + self._account["buy_frozen_fee"]
        self._account["buy_frozen_balance"] = 0.0
        self._account["buy_frozen_fee"] = 0.0
        self._account["buy_balance_today"] = 0.0
        self._account["buy_fee_today"] = 0.0
        self._account["sell_balance_today"] = 0.0
        self._account["sell_fee_today"] = 0.0
        self._account["asset"] += self._account["dividend_balance_today"]
        self._account["market_value"] -= self._account["dividend_balance_today"]
        # account 计算字段
        self._account["available"] = self._account["asset"] - self._account["market_value"]  # 当前可用余额 = 当前资产 - 当前市值
        self._account["drawable"] = self._account["available"]
        self._account["hold_profit"] = 0.0  # 当日持仓盈亏 = 当前市值 - 当前买入成本
        self._account["float_profit_today"] = 0.0  # 当日浮动盈亏 = SUM(持仓当日浮动盈亏)
        self._account["real_profit_today"] = 0.0  # 当日实现盈亏 = SUM(持仓当日实现盈亏)
        self._account["profit_today"] = 0.0  # 当日盈亏 = 当日浮动盈亏 + 当日实现盈亏
        self._account["profit_rate_today"] = 0.0  # 当日盈亏比 = 当日盈亏 / (当前买入成本 if 当前买入成本 > 0 else 期初资产)
        # 根据公式 账户权益 不需要计算 self._account["balance"] = static_balance + market_value
        self._append_to_diffs(["accounts", "CNY"], self._account)

    def _check_insert_order(self, order, symbol, position, quote, underlying_quote=None):
        # 无法计入 orderbook
        if quote["ins_class"] != "STOCK":
            order["last_msg"] = "不支持的合约类型，TqSimStock 只支持股票模拟交易"
            order["status"] = "FINISHED"

        if order["status"] == "ALIVE" and not self._is_in_trading_time(quote):
            order["last_msg"] = "下单失败, 不在可交易时间段内"
            order["status"] = "FINISHED"

        if order["status"] == "ALIVE" and order["direction"] == "BUY":
            price = _get_order_price(quote, order)
            order["frozen_balance"] = price * order["volume_orign"]
            order["frozen_fee"] = _get_stock_fee(order["direction"], order["volume_orign"], price)
            if order["frozen_balance"] + order["frozen_fee"] > self._account["available"]:
                order["frozen_balance"] = 0.0
                order["frozen_fee"] = 0.0
                order["last_msg"] = "开仓资金不足"
                order["status"] = "FINISHED"

        if order["status"] == "ALIVE" and order["direction"] == "SELL":
            if position["volume_his"] + position["shared_volume_today"] - position["sell_volume_today"] - position["sell_volume_frozen"] < order["volume_orign"]:
                order["last_msg"] = "平仓手数不足"
                order["status"] = "FINISHED"

        if order["status"] == "FINISHED":
            self._append_to_diffs(["orders", order["order_id"]], order)

    def _on_insert_order(self, order, symbol, position, quote, underlying_quote=None):
        """记录在 orderbook"""
        if order["direction"] == "BUY":
            self._adjust_account_by_order(buy_frozen_balance=order["frozen_balance"], buy_frozen_fee=order["frozen_fee"])
            self._append_to_diffs(["accounts", "CNY"], self._account)
        else:
            position["sell_volume_frozen"] += order["volume_orign"]
            self._append_to_diffs(["positions", symbol], position)

    def _on_order_failed(self, symbol, order):
        origin_frozen_balance = order["frozen_balance"]
        origin_frozen_fee = order["frozen_fee"]
        order["frozen_balance"] = 0.0
        order["frozen_fee"] = 0.0
        self._append_to_diffs(["orders", order["order_id"]], order)
        # 调整账户和持仓
        if order["direction"] == "BUY":
            self._adjust_account_by_order(buy_frozen_balance=-origin_frozen_balance, buy_frozen_fee=-origin_frozen_fee)
            self._append_to_diffs(["accounts", "CNY"], self._account)
        else:
            position = self._positions[symbol]
            position["sell_volume_frozen"] -= order["volume_orign"]
            self._append_to_diffs(["positions", symbol], position)

    def _on_order_traded(self, order, trade, symbol, position, quote, underlying_quote):
        origin_frozen_balance = order["frozen_balance"]
        origin_frozen_fee = order["frozen_fee"]
        order["frozen_balance"] = 0.0
        order["frozen_fee"] = 0.0
        order["volume_left"] = 0
        self._append_to_diffs(["trades", trade["trade_id"]], trade)
        self._append_to_diffs(["orders", order["order_id"]], order)

        # 调整账户和持仓
        if order["direction"] == "BUY":
            if position["volume"] == 0:
                position["create_date"] = quote['datetime'][:10]
            self._adjust_account_by_order(buy_frozen_balance=-origin_frozen_balance, buy_frozen_fee=-origin_frozen_fee)
            # 修改 position 原始字段
            buy_balance = trade["volume"] * trade["price"]
            position["buy_volume_today"] += trade["volume"]
            position["buy_balance_today"] += buy_balance
            position["buy_fee_today"] += trade["fee"]
            # 修改 account 原始字段
            self._adjust_account_by_trade(buy_fee=trade["fee"], buy_balance=buy_balance)
            self._adjust_position_account(position, pre_last_price=trade["price"], last_price=position["last_price"],
                                          buy_volume=trade["volume"], buy_balance=buy_balance, buy_fee=trade["fee"])
        else:
            position["sell_volume_frozen"] -= order["volume_orign"]
            # 修改 position 原始字段
            sell_balance = trade["volume"] * trade["price"]
            position["sell_volume_today"] += trade["volume"]
            position["sell_balance_today"] += sell_balance
            position["sell_fee_today"] += trade["fee"]
            self._adjust_account_by_trade(sell_fee=trade["fee"], sell_balance=sell_balance)
            self._adjust_position_account(position, last_price=quote["last_price"], sell_volume=trade["volume"],
                                          sell_balance=sell_balance, sell_fee=trade["fee"])

        self._append_to_diffs(["positions", symbol], position)
        self._append_to_diffs(["accounts", "CNY"], self._account)

    def _on_update_quotes(self, symbol, position, quote, underlying_quote):
        # 调整持仓保证金和盈亏
        if position["volume"] > 0:
            if position["last_price"] != quote["last_price"]:
                self._adjust_position_account(position, pre_last_price=position["last_price"], last_price=quote["last_price"])
                position["last_price"] = quote["last_price"]
        # 修改辅助变量
        position["last_price"] = quote["last_price"]
        self._append_to_diffs(["positions", symbol], position)  # 一定要返回 position，下游会用到 future_margin 字段判断修改保证金是否成功
        self._append_to_diffs(["accounts", "CNY"], self._account)

    def _adjust_position_account(self, position, pre_last_price=float("nan"), last_price=float("nan"), buy_volume=0, buy_balance=0, buy_fee=0, sell_volume=0, sell_balance=0, sell_fee=0):
        """
        价格变化，使得 position 中的以下计算字段需要修改，这个函数计算出需要修改的差值部分，计算出差值部分修改 position、account
        有两种情况下调用
        1. 委托单 FINISHED，且全部成交，分为4种：buy_open, buy_close, sell_open, sell_close
        2. 行情跳动
        """
        assert [buy_volume, sell_volume].count(0) >= 1  # 只有一个大于0, 或者都是0，表示价格变化导致的字段修改
        if buy_volume > 0:
            position["volume"] += buy_volume
            cost = buy_balance + buy_fee
            market_value = buy_volume * position["last_price"]
            position["buy_avg_price"] = (position["buy_balance_today"] + position["buy_fee_today"]) / position["buy_volume_today"]
            buy_float_profit_today = (position["volume"] - (position["volume_his"] - position["sell_volume_today"])) * (last_price - position["buy_avg_price"])  # 今仓浮动盈亏 = (今持仓数量 - (昨持仓数量 - 今卖数量)) * (最新价 - 买入均价)
            self._adjust_position(position, cost=cost, market_value=market_value,
                                  sell_float_profit_today=0,
                                  buy_float_profit_today=buy_float_profit_today, real_profit_today=0)
            self._adjust_account_by_position(market_value=market_value, cost=cost,
                                             float_profit_today=buy_float_profit_today,
                                             real_profit_today=0)
        elif sell_volume > 0:
            position["volume"] -= sell_volume
            cost = -sell_volume * (position["cost_his"] / position["volume_his"])
            market_value = -sell_volume * position["last_price"]
            real_profit_today = (sell_volume / position["volume_his"]) * position["sell_float_profit_today"]
            sell_float_profit_today = position["sell_float_profit_today"] - real_profit_today
            self._adjust_position(position, cost=cost, market_value=market_value,
                                  sell_float_profit_today=sell_float_profit_today,
                                  buy_float_profit_today=0, real_profit_today=real_profit_today)
            self._adjust_account_by_position(market_value=market_value, cost=cost,
                                             float_profit_today=sell_float_profit_today,
                                             real_profit_today=real_profit_today)
        else:
            market_value = position["volume"] * last_price - position["market_value"]
            sell_float_profit_today = (position["volume_his"] - position["sell_volume_today"]) * (last_price - pre_last_price)  # 昨仓浮动盈亏 = (昨持仓数量 - 今卖数量) * (最新价 - 昨收盘价)
            buy_float_profit_today = (position["volume"] - (position["volume_his"] - position["sell_volume_today"])) * (last_price - position["buy_avg_price"])  # 今仓浮动盈亏 = (今持仓数量 - (昨持仓数量 - 今卖数量)) * (最新价 - 买入均价)
            self._adjust_position(position, cost=0, market_value=market_value, sell_float_profit_today=sell_float_profit_today, buy_float_profit_today=buy_float_profit_today, real_profit_today=0)
            self._adjust_account_by_position(market_value=market_value, cost=0, float_profit_today=sell_float_profit_today+buy_float_profit_today, real_profit_today=0)

    # -------- 对于 position 的计算字段修改分为两类：
    # 1. 针对手数相关的修改，在下单、成交时会修改
    # 2. 针对盈亏、保证金、市值的修改，由于参考合约最新价，在成交、行情跳动时会修改
    def _adjust_position(self, position, cost=0, market_value=0, sell_float_profit_today=0, buy_float_profit_today=0, real_profit_today=0):
        # 更新 position 计算字段，根据差值更新的字段
        position["sell_float_profit_today"] += sell_float_profit_today
        position["buy_float_profit_today"] += buy_float_profit_today

        position["cost"] += cost  # 当前成本 = 期初成本 + 今买金额 + 今买费用 - 今卖数量 × (期初买入成本 / 期初持仓数量)
        position["market_value"] += market_value  # 当前市值 = 持仓数量 × 行情最新价
        position["float_profit_today"] += sell_float_profit_today + buy_float_profit_today  # 当日浮动盈亏 = (昨持仓数量 - 今卖数量) * (最新价 - 昨收盘价) + (今持仓数量 - (昨持仓数量 - 今卖数量)) * (最新价 - 买入均价)
        position["real_profit_today"] += real_profit_today  # 当日实现盈亏 = 今卖数量 * (最新价 - 昨收盘价) - 今卖费用 + 今派息金额
        position["profit_today"] += sell_float_profit_today + buy_float_profit_today + real_profit_today
        position["hold_profit"] += (market_value - cost)
        position["real_profit_total"] += real_profit_today  # 累计实现盈亏 += 当日实现盈亏（成本）
        position["profit_total"] += real_profit_today + (market_value - cost)  # 总盈亏 = 累计实现盈亏 + 持仓盈亏
        # 当日收益率 = 当日盈亏 / ( 当前成本 if 当前成本 > 0 else 期初市值)
        if position["cost"] > 0:
            position["profit_rate_today"] = position["profit_today"] / position["cost"]
        else:
            position["profit_rate_today"] = position["profit_today"] / position["market_value_his"] if position["market_value_his"] > 0 else 0.0
        # 累计收益率 = 总盈亏 / (当前成本 if 当前成本 > 0 else 期初成本)
        if position["cost"] > 0:
            position["profit_rate_total"] = position["profit_total"] / position["cost"]
        else:
            position["profit_rate_total"] = position["profit_total"] / position["cost_his"] if position["cost_his"] > 0 else 0.0


    # -------- 对于 account 的修改分为以下三类
    def _adjust_account_by_trade(self, buy_fee=0, buy_balance=0, sell_fee=0, sell_balance=0):
        """由成交引起的 account 原始字段变化，account 需要更新的计算字段"""
        # account 原始字段
        self._account["buy_balance_today"] += buy_balance  # 当日买入占用资金（不含费用）
        self._account["buy_fee_today"] += buy_fee  # 当日买入累计费用
        self._account["sell_balance_today"] += sell_balance  # 当日卖出释放资金
        self._account["sell_fee_today"] += sell_fee  # 当日卖出累计费用
        # account 计算字段
        self._account["available"] += (sell_balance - buy_fee - sell_fee - buy_balance)
        self._account["asset"] += (sell_balance - buy_fee - sell_fee - buy_balance)
        self._account["drawable"] = max(self._account["available_his"] + min(0, self._account["sell_balance_today"] - self._account["buy_balance_today"] - self._account["buy_fee_today"] - self._account["buy_frozen_balance"] - self._account["buy_frozen_fee"]), 0)

    def _adjust_account_by_position(self, market_value=0, cost=0, float_profit_today=0, real_profit_today=0):
        """由 position 变化，account 需要更新的计算字段"""
        # account 计算字段，持仓字段求和的字段
        self._account["market_value"] += market_value
        self._account["cost"] += cost
        self._account["float_profit_today"] += float_profit_today
        self._account["real_profit_today"] += real_profit_today
        # account 计算字段
        self._account["asset"] += market_value  # 当前资产 = 当前市值 + 当前可用余额 + 委托冻结金额 + 委托冻结费用
        # 当前可取余额 = MAX( 期初余额 + MIN(0，当日卖出释放资金 - 当日买入占用资金 - 委托冻结金额) , 0)
        self._account["drawable"] = max(self._account["available_his"] + min(0, self._account["sell_balance_today"] - self._account["buy_balance_today"] - self._account["buy_fee_today"] - self._account["buy_frozen_balance"] - self._account["buy_frozen_fee"]), 0)
        self._account["hold_profit"] = self._account["market_value"] - self._account["cost"]  # 当日持仓盈亏 = 当前市值 - 当前买入成本
        self._account["profit_today"] = self._account["float_profit_today"] + self._account["real_profit_today"]  # 当日盈亏 = 当日浮动盈亏 + 当日实现盈亏
        # 当日盈亏比 = 当日盈亏 / (当前买入成本 if 当前买入成本 > 0 else 期初资产)
        if self._account["cost"] > 0:
            self._account["profit_rate_today"] = self._account["profit_today"] / self._account["cost"]
        else:
            self._account["profit_rate_today"] = self._account["profit_today"] / self._account["asset_his"] if self._account["asset_his"] > 0 else 0.0

    def _adjust_account_by_order(self, buy_frozen_balance=0, buy_frozen_fee=0):
        """由 order 变化，account 需要更新的计算字段"""
        self._account["buy_frozen_balance"] += buy_frozen_balance
        self._account["buy_frozen_fee"] += buy_frozen_fee
        self._account["available"] -= (buy_frozen_balance + buy_frozen_fee)
        self._account["drawable"] = max(self._account["available_his"] + min(0, self._account["sell_balance_today"] - self._account["buy_balance_today"] - self._account["buy_fee_today"] - self._account["buy_frozen_balance"] - self._account["buy_frozen_fee"]), 0)
