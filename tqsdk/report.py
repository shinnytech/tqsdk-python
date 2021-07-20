#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'

import numpy as np
from pandas import DataFrame, Series

from tqsdk.tafunc import get_sharp, get_sortino, get_calmar, _cum_counts

TRADING_DAYS_OF_YEAR = 250
TRADING_DAYS_OF_MONTH = 21

class TqReport(object):
    """
    天勤报告类，辅助 web_gui 显示回测统计信息和统计图表

    1. 目前只针对 TqSim 账户回测有意义
    2. 每份报告针对一组对应的账户截面记录和成交记录

    """

    def __init__(self, report_id: str, account_df: DataFrame, trade_df: DataFrame):
        """
        Args:
            report_id (str): 报告Id

            account_df (pandas.DataFrame): 每日账户截面记录
                应该包括的列有：
                + 'date': 日期
                + 'pre_balance': 昨日权益
                + 'balance': 今日权益
                + 'commission': 日内手续费
                + 'risk_ratio': 风险度

            trade_df (pandas.DataFrame): 成交记录
                应该包括的列有：
                + 'user_id'
                + 'order_id'
                + 'trade_id'
                + 'exchange_trade_id'
                + 'exchange_id'
                + 'instrument_id'
                + 'direction'
                + 'offset'
                + 'price'
                + 'volume'
                + 'trade_date_time'
                + 'commission'

        Example::

            TODO: 补充示例

        """
        self.report_id = report_id
        self.account_df = account_df.sort_values(by=['date'], ignore_index=True)
        # self.account_df.index = account_df['date']
        self.trade_df = trade_df.sort_values(by=['trade_date_time'], ignore_index=True)
        self.trade_df["offset1"] = trade_df["offset"].replace("CLOSETODAY", "CLOSE")

        # default metrics
        init_balance = self.account_df.iloc[0]['pre_balance']
        self.account_df['profit'] = self.account_df['balance'] - self.account_df['balance'].shift(fill_value=init_balance)  # 每日收益
        self.account_df['is_profit'] = np.where(self.account_df['profit'] > 0, 1, 0)  # 是否收益
        self.account_df['is_loss'] = np.where(self.account_df['profit'] < 0, 1, 0)  # 是否亏损
        self.account_df['daily_yield'] = self.account_df['balance'] / self.account_df['balance'].shift(fill_value=init_balance) - 1  # 每日收益率
        self.account_df['max_balance'] = self.account_df['balance'].cummax()  # 当前单日最大权益
        self.account_df['drawdown'] = (self.account_df['max_balance'] - self.account_df['balance']) / self.account_df['max_balance']  # 回撤
        self.default_metrics = self._get_default_metrics()

    def _get_default_metrics(self):
        if self.account_df.shape[0] > 0:
            _ror = self.account_df.iloc[-1]['balance'] / self.account_df.iloc[0]['pre_balance']
            return {
                "start_date": self.account_df.iloc[0]["date"],
                "end_date": self.account_df.iloc[-1]["date"],
                "start_balance": self.account_df.iloc[0]['pre_balance'],
                "end_balance": self.account_df.iloc[-1]['balance'],
                "ror": _ror - 1,  # 收益率
                "annual_yield": _ror ** (TRADING_DAYS_OF_YEAR / self.account_df.shape[0]) - 1,  # 年化收益率
                "trading_days": self.account_df.shape[0],  # 总交易天数
                "cum_profit_days": self.account_df['is_profit'].sum(),  # 累计盈利天数
                "cum_loss_days": self.account_df['is_loss'].sum(),  # 累计亏损天数
                "max_drawdown": self.account_df['drawdown'].max(),  # 最大回撤
                "commission":  self.account_df['commission'].sum(),  # 总手续费
                "open_times": self.trade_df.loc[self.trade_df["offset1"] == "OPEN"].shape[0],  # 开仓次数
                "close_times": self.trade_df.loc[self.trade_df["offset1"] == "CLOSE"].shape[0],  # 平仓次数
                "daily_risk_ratio": self.account_df['risk_ratio'].mean(),  # 提供日均风险度
                "max_cont_profit_days": _cum_counts(self.account_df['is_profit']).max(),  # 最大连续盈利天数
                "max_cont_loss_days": _cum_counts(self.account_df['is_loss']).max(),  # 最大连续亏损天数
                "sharpe_ratio": get_sharp(self.account_df['daily_yield']),  # 年化夏普率
                "calmar_ratio": get_calmar(self.account_df['daily_yield'], self.account_df['drawdown'].max()),  # 年化卡玛比率
                "sortino_ratio": get_sortino(self.account_df['daily_yield'])  # 年化索提诺比率
            }
        else:
            return {}

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
