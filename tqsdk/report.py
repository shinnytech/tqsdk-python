#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'

from typing import Dict, Optional

import numpy as np
from pandas import DataFrame, Series

from tqsdk.objs import Account, Trade, SecurityAccount, SecurityTrade
from tqsdk.tafunc import get_sharp, get_sortino, get_calmar, _cum_counts

TRADING_DAYS_OF_YEAR = 250
TRADING_DAYS_OF_MONTH = 21

class TqReport(object):
    """
    天勤报告类，辅助 web_gui 显示回测统计信息和统计图表

    1. 目前只针对 TqSim 账户回测有意义
    2. 每份报告针对一组对应的账户截面记录和成交记录

    """

    def __init__(self, report_id: str, trade_log: Optional[Dict] = None, quotes: Optional[Dict] = None, account_type: str = "FUTURE"):
        """
        本模块为给 TqSim 提供交易成交统计
        Args:
            report_id (str): 报告Id

            trade_log (dict): TqSim 交易结束之后生产的每日账户截面和交易记录
                {
                    '2020-09-01': {
                        "trades": [],
                        "account": {},
                        "positions": {},
                    '2020-09-02': {....},
                }

            quotes (dict): 合约信息

        Example::

            TODO: 补充示例

        """
        self.report_id = report_id
        self.trade_log = trade_log
        self.quotes = quotes
        self.account_type = account_type
        self.date_keys = sorted(trade_log.keys())
        self.account_df, self.trade_df = self._get_df()
        # default metrics
        self.default_metrics = self._get_default_metrics() if self.account_type == "FUTURE" else self._get_stock_metrics()

    def _get_df(self):
        type_account = Account if self.account_type == "FUTURE" else SecurityAccount
        type_trade = Trade if self.account_type == "FUTURE" else SecurityTrade
        account_data = [{'date': dt} for dt in self.date_keys]
        for item in account_data:
            item.update(self.trade_log[item['date']]['account'])
        account_df = DataFrame(data=account_data, columns=['date'] + list(type_account(None).keys()))
        trade_array = []
        for date in self.date_keys:
            trade_array.extend(self.trade_log[date]['trades'])
        trade_df = DataFrame(data=trade_array, columns=list(type_trade(None).keys()))
        if type_trade == Trade:
            trade_df["offset1"] = trade_df["offset"].replace("CLOSETODAY", "CLOSE")
        return account_df, trade_df

    def _get_default_metrics(self):
        if self.account_df.shape[0] > 0:
            result = self._get_account_stat_metrics()
            result.update(self._get_trades_stat_metrics())
            return result
        else:
            return {
                "winning_rate": float('nan'),  # 胜率
                "profit_loss_ratio": float('nan'),  # 盈亏额比例
                "ror": float('nan'),  # 收益率
                "annual_yield": float('nan'),  # 年化收益率
                "max_drawdown": float('nan'),  # 最大回撤
                "sharpe_ratio": float('nan'),  # 年化夏普率
                "sortino_ratio": float('nan'),  # 年化索提诺比率
                "commission": 0,  # 总手续费
                "tqsdk_punchline": ""
            }

    def _get_stock_metrics(self):
        if self.account_df.shape[0] > 0:
            init_asset = self.account_df.iloc[0]['asset_his']
            asset = self.account_df.iloc[-1]['asset']
            self.account_df['profit'] = self.account_df['asset'] - self.account_df['asset'].shift(fill_value=init_asset)  # 每日收益
            self.account_df['is_profit'] = np.where(self.account_df['profit'] > 0, 1, 0)  # 是否收益
            self.account_df['is_loss'] = np.where(self.account_df['profit'] < 0, 1, 0)  # 是否亏损
            self.account_df['daily_yield'] = self.account_df['asset'] / self.account_df['asset'].shift(fill_value=init_asset) - 1  # 每日收益率
            self.account_df['max_asset'] = self.account_df['asset'].cummax()  # 当前单日最大权益
            self.account_df['drawdown'] = (self.account_df['max_asset'] - self.account_df['asset']) / self.account_df['max_asset']  # 回撤
            _ror = asset / init_asset
            return {
                "start_date": self.account_df.iloc[0]["date"],
                "end_date": self.account_df.iloc[-1]["date"],
                "init_asset": init_asset,
                "asset": init_asset,
                "start_asset": init_asset,
                "end_asset": asset,
                "ror": _ror - 1,  # 收益率
                "annual_yield": _ror ** (TRADING_DAYS_OF_YEAR / self.account_df.shape[0]) - 1,  # 年化收益率
                "trading_days": self.account_df.shape[0],  # 总交易天数
                "cum_profit_days": self.account_df['is_profit'].sum(),  # 累计盈利天数
                "cum_loss_days": self.account_df['is_loss'].sum(),  # 累计亏损天数
                "max_drawdown": self.account_df['drawdown'].max(),  # 最大回撤
                "fee": self.account_df['buy_fee_today'].sum() + self.account_df['sell_fee_today'].sum(),  # 总手续费
                "buy_times": self.trade_df.loc[self.trade_df["direction"] == "BUY"].shape[0],  # 买次数
                "sell_times": self.trade_df.loc[self.trade_df["direction"] == "SELL"].shape[0],  # 卖次数
                "max_cont_profit_days": _cum_counts(self.account_df['is_profit']).max(),  # 最大连续盈利天数
                "max_cont_loss_days": _cum_counts(self.account_df['is_loss']).max(),  # 最大连续亏损天数
                "sharpe_ratio": get_sharp(self.account_df['daily_yield']),  # 年化夏普率
                "calmar_ratio": get_calmar(self.account_df['daily_yield'], self.account_df['drawdown'].max()),  # 年化卡玛比率
                "sortino_ratio": get_sortino(self.account_df['daily_yield']),  # 年化索提诺比率
                "tqsdk_punchline": self._get_tqsdk_punchlines(_ror - 1)
            }
        else:
            return {
                "profit_loss_ratio": float('nan'),  # 盈亏额比例
                "ror": float('nan'),  # 收益率
                "annual_yield": float('nan'),  # 年化收益率
                "max_drawdown": float('nan'),  # 最大回撤
                "sharpe_ratio": float('nan'),  # 年化夏普率
                "sortino_ratio": float('nan'),  # 年化索提诺比率
                "fee": 0,  # 总手续费
                "tqsdk_punchline": ""
            }

    def _get_account_stat_metrics(self):
        init_balance = self.account_df.iloc[0]['pre_balance']
        balance = self.account_df.iloc[-1]['balance']
        self.account_df['profit'] = self.account_df['balance'] - self.account_df['balance'].shift(fill_value=init_balance)  # 每日收益
        self.account_df['is_profit'] = np.where(self.account_df['profit'] > 0, 1, 0)  # 是否收益
        self.account_df['is_loss'] = np.where(self.account_df['profit'] < 0, 1, 0)  # 是否亏损
        self.account_df['daily_yield'] = self.account_df['balance'] / self.account_df['balance'].shift(fill_value=init_balance) - 1  # 每日收益率
        self.account_df['max_balance'] = self.account_df['balance'].cummax()  # 当前单日最大权益
        self.account_df['drawdown'] = (self.account_df['max_balance'] - self.account_df['balance']) / self.account_df['max_balance']  # 回撤
        _ror = self.account_df.iloc[-1]['balance'] / self.account_df.iloc[0]['pre_balance']
        return {
            "start_date": self.account_df.iloc[0]["date"],
            "end_date": self.account_df.iloc[-1]["date"],
            "init_balance": init_balance,
            "balance": balance,
            "start_balance": init_balance,
            "end_balance": balance,
            "ror": _ror - 1,  # 收益率
            "annual_yield": _ror ** (TRADING_DAYS_OF_YEAR / self.account_df.shape[0]) - 1,  # 年化收益率
            "trading_days": self.account_df.shape[0],  # 总交易天数
            "cum_profit_days": self.account_df['is_profit'].sum(),  # 累计盈利天数
            "cum_loss_days": self.account_df['is_loss'].sum(),  # 累计亏损天数
            "max_drawdown": self.account_df['drawdown'].max(),  # 最大回撤
            "commission": self.account_df['commission'].sum(),  # 总手续费
            "open_times": self.trade_df.loc[self.trade_df["offset1"] == "OPEN"].shape[0],  # 开仓次数
            "close_times": self.trade_df.loc[self.trade_df["offset1"] == "CLOSE"].shape[0],  # 平仓次数
            "daily_risk_ratio": self.account_df['risk_ratio'].mean(),  # 提供日均风险度
            "max_cont_profit_days": _cum_counts(self.account_df['is_profit']).max(),  # 最大连续盈利天数
            "max_cont_loss_days": _cum_counts(self.account_df['is_loss']).max(),  # 最大连续亏损天数
            "sharpe_ratio": get_sharp(self.account_df['daily_yield']),  # 年化夏普率
            "calmar_ratio": get_calmar(self.account_df['daily_yield'], self.account_df['drawdown'].max()),  # 年化卡玛比率
            "sortino_ratio": get_sortino(self.account_df['daily_yield']),  # 年化索提诺比率
            "tqsdk_punchline": self._get_tqsdk_punchlines(_ror - 1)
        }

    def _get_trades_stat_metrics(self):
        """
        根据成交手数计算 胜率，盈亏额比例
        self.quotes 主要需要合约乘数，用于计算盈亏额
        """
        trade_array = []
        for date in self.date_keys:
            for trade in self.trade_log[date]['trades']:
                # 每一行都是 1 手的成交记录
                trade_array.extend([{
                    "symbol": f"{trade['exchange_id']}.{trade['instrument_id']}",
                    "direction": trade["direction"],
                    "offset": "CLOSE" if trade["offset"] == "CLOSETODAY" else trade["offset"],
                    "price": trade["price"]
                } for i in range(trade['volume'])])
        trade_df = DataFrame(data=trade_array, columns=['symbol', 'direction', 'offset', 'price'])
        profit_volumes = 0  # 盈利手数
        loss_volumes = 0  # 亏损手数
        profit_value = 0  # 盈利额
        loss_value = 0  # 亏损额
        all_symbols = trade_df['symbol'].drop_duplicates()
        for symbol in all_symbols:
            for direction in ["BUY", "SELL"]:
                open_df = self._get_sub_df(trade_df, symbol, dir=direction, offset='OPEN')
                close_df = self._get_sub_df(trade_df, symbol, dir=("SELL" if direction == "BUY" else "BUY"), offset='CLOSE')
                close_df['profit'] = (close_df['price'] - open_df['price']) * (1 if direction == "BUY" else -1)
                profit_volumes += close_df.loc[close_df['profit'] >= 0].shape[0]  # 盈利手数
                loss_volumes += close_df.loc[close_df['profit'] < 0].shape[0]  # 亏损手数
                profit_value += close_df.loc[close_df['profit'] >= 0, 'profit'].sum() * self.quotes[symbol]['volume_multiple']
                loss_value += close_df.loc[close_df['profit'] < 0, 'profit'].sum() * self.quotes[symbol]['volume_multiple']
        winning_rate = profit_volumes / (profit_volumes + loss_volumes) if profit_volumes + loss_volumes else 0
        profit_pre_volume = profit_value / profit_volumes if profit_volumes else 0
        loss_pre_volume = loss_value / loss_volumes if loss_volumes else 0
        profit_loss_ratio = abs(profit_pre_volume / loss_pre_volume) if loss_pre_volume else float("inf")
        return {
            "profit_volumes": profit_volumes,
            "loss_volumes": loss_volumes,
            "profit_value": profit_value,
            "loss_value": loss_value,
            "winning_rate": winning_rate,
            "profit_loss_ratio": profit_loss_ratio
        }

    def _get_tqsdk_punchlines(self, ror):
        tqsdk_punchlines = [
            '幸好是模拟账户，不然你就亏完啦',
            '触底反弹,与其执迷修改参数，不如改变策略思路去天勤官网策略库进修',
            '越挫越勇，不如去天勤量化官网策略库进修',
            '不要灰心，少侠重新来过',
            '策略看来小有所成',
            '策略看来的得心应手',
            '策略看来春风得意，堪比当代索罗斯',
            '策略看来独孤求败，小心过拟合噢'
        ]
        ror_level = [i for i, k in enumerate([-1, -0.5, -0.2, 0, 0.2, 0.5, 1]) if ror < k]
        if len(ror_level) > 0:
            return tqsdk_punchlines[ror_level[0]]
        else:
            return tqsdk_punchlines[-1]

    def _get_sub_df(self, origin_df, symbol, dir, offset):
        df = origin_df.where(
            (origin_df['symbol'] == symbol) & (origin_df['offset'] == offset) & (origin_df['direction'] == dir))
        df.dropna(inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def metrics(self, **kwargs):
        self.default_metrics.update(kwargs)
        return [{
            self.report_id: {"metrics": self.default_metrics.copy()}
        }]

    def full(self):
        data = self.metrics()
        data += self.daily_balance()
        data += self.daily_profit()
        data += self.drawdown()
        data += self.sharp_rolling()
        data += self.sortino_rolling()
        # data += self.calmar_rolling()
        return data

    def daily_balance(self):
        """每日资金曲线"""
        return [{
            self.report_id: {
                "charts": {
                    "daily_balance": {
                        "title": {
                            "left": 'center',
                            "text": "每日账户资金"
                        },
                        "xAxis": {
                            "type": 'category',
                            "data": self.account_df['date'].to_dict()
                        },
                        "yAxis": {
                            "type": 'value',
                            "min": 'dataMin',
                            "max": 'dataMax',
                        },
                        "series": {
                            "0": {
                                "data": self.account_df['balance'].map(lambda x: '%.2f' % x).to_dict(),
                                "type": 'line'
                            }
                        }
                    }
                }
            }
        }]

    def daily_profit(self):
        """每日盈亏"""
        profit = Series(np.where(self.account_df['profit'] >= 0, self.account_df['profit'], float('nan')))  # 收益
        loss = Series(np.where(self.account_df['profit'] < 0, self.account_df['profit'], float('nan')))  # 亏损
        return [{
            self.report_id: {
                "charts": {
                    "daily_profit": {
                        "title": {
                            "left": 'center',
                            "text": "每日盈亏"
                        },
                        "xAxis": {
                            "type": 'category',
                            "data": self.account_df['date'].to_dict()
                        },
                        "yAxis": {
                            "type": 'value'
                        },
                        "series": {
                            "0": {
                                "data": profit.to_dict(),
                                "type": 'bar',
                                "itemStyle": {
                                    "color": "#ee6666"
                                },
                                "stack": 'one',
                            },
                            "1": {
                                "data": loss.to_dict(),
                                "type": 'bar',
                                "itemStyle": {
                                    "color": "#91cc75"
                                },
                                "stack": 'one',
                            }
                        }
                    }
                }
            }
        }]

    def drawdown(self):
        """回撤"""
        return [{
            self.report_id: {
                "charts": {
                    "drawdown": {
                        "title": {
                            "left": 'center',
                            "text": "回撤"
                        },
                        "xAxis": {
                            "type": 'category',
                            "data": self.account_df['date'].to_dict()
                        },
                        "yAxis": {
                            "type": 'value'
                        },
                        "series": {
                            "0": {
                                "data": self.account_df['drawdown'].to_dict(),
                                "type": 'line'
                            }
                        }
                    }
                }
            }
        }]

    def sharp_rolling(self):
        """滚动夏普比率图表"""
        rolling_sharp = self.account_df['daily_yield'].rolling(TRADING_DAYS_OF_MONTH).apply(get_sharp)
        return [{
            self.report_id: {
                "charts": {
                    "sharp_rolling": {
                        "title": {
                            "left": 'center',
                            "text": "滚动夏普比率图表"
                        },
                        "xAxis": {
                            "type": 'category',
                            "data": self.account_df['date'].to_dict()
                        },
                        "yAxis": {
                            "type": 'value'
                        },
                        "series": {
                            "0": {
                                "data": rolling_sharp.to_dict(),
                                "type": 'line'
                            }
                        }
                    }
                }
            }
        }]

    def sortino_rolling(self):
        """滚动索提诺比率图表"""
        rolling_sortino = self.account_df['daily_yield'].rolling(TRADING_DAYS_OF_MONTH).apply(get_sortino)
        return [{
            self.report_id: {
                "charts": {
                    "sortino_rolling": {
                        "title": {
                            "left": 'center',
                            "text": "滚动索提诺比率图表"
                        },
                        "xAxis": {
                            "type": 'category',
                            "data": self.account_df['date'].to_dict()
                        },
                        "yAxis": {
                            "type": 'value'
                        },
                        "series": {
                            "0": {
                                "name": "滚动索提诺比率图表",
                                "data": rolling_sortino.to_dict(),
                                "type": 'line'
                            }
                        }
                    }
                }
            }
        }]

    def calmar_rolling(self):
        """滚动卡玛比率图表"""
        rolling_calmar = self.account_df['daily_yield'].rolling(TRADING_DAYS_OF_MONTH).apply(
            lambda x: get_calmar(x, self.account_df.loc[x.index]['drawdown'].max()))
        return [{
            self.report_id: {
                "charts": {
                    "calmar_rolling": {
                        "title": {
                            "left": 'center',
                            "text": "滚动卡玛比率图表"
                        },
                        "xAxis": {
                            "type": 'category',
                            "data": self.account_df['date'].to_dict()
                        },
                        "yAxis": {
                            "type": 'value'
                        },
                        "series": {
                            "0": {
                                "data": rolling_calmar.to_dict(),
                                "type": 'line'
                            },
                        }
                    }
                }
            }
        }]
