#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'mayanqiong'

from datetime import datetime

import requests

from tqsdk.calendar import TqContCalendar


class TqBacktestContinuous(object):

    def __init__(self, start_dt: int, end_dt: int, headers=None) -> None:
        """
        为回测时提供某个交易日的主连表
        start_dt 开始的交易日
        end_dt 结束的交易日
        """
        self._cont_calendar = TqContCalendar(start_dt=datetime.fromtimestamp(start_dt / 1e9),
                                             end_dt=datetime.fromtimestamp(end_dt / 1e9),
                                             headers=headers)

    def _get_history_cont_quotes(self, trading_day):
        df = self._cont_calendar._get_cont_underlying_on_date(dt=datetime.fromtimestamp(trading_day / 1e9))
        quotes = {k: {"underlying_symbol": df.iloc[0][k]} for k in df.columns if k.startswith("KQ.m")}
        return quotes


class TqBacktestDividend(object):

    def __init__(self, start_dt: int, end_dt: int, headers=None) -> None:
        """
        为回测时提供分红送股信息
        start_dt 开始的交易日
        end_dt 结束的交易日
        """
        self._headers = headers
        self._start_dt = start_dt
        self._end_dt = end_dt
        self._start_date = datetime.fromtimestamp(self._start_dt / 1000000000).strftime('%Y%m%d')
        self._end_date = datetime.fromtimestamp(self._end_dt / 1000000000).strftime('%Y%m%d')
        self._stocks = {}  # 记录全部股票合约及从 stock-dividend 服务获取的原始数据

    def _get_dividend(self, quotes, trading_day):
        dt = datetime.fromtimestamp(trading_day / 1000000000).strftime('%Y%m%d')
        self._request_stock_dividend(quotes)
        rsp_quotes = {}
        # self._stocks 中应该已经记录了 quotes 中全部股票合约
        for symbol, stock in self._stocks.items():
            if stock['request_successed'] is True:  # 从 stock-dividend 服务获取的原始数据
                rsp_quotes[symbol] = {
                    'cash_dividend_ratio': [f"{item['drdate']},{item['cash']}" for item in stock['dividend_list']
                                            if item['recorddate'] <= dt and item['cash'] > 0],  # 除权除息日,每股分红（税后）
                    'stock_dividend_ratio': [f"{item['drdate']},{item['share']}" for item in stock['dividend_list']
                                             if item['recorddate'] <= dt and item['share'] > 0]  # 除权除息日,每股送转股数量
                }
            else:
                # todo: stock['request_successed'] == False 表示请求不成功, 退回到原始合约服务中的分红送股数据, 用户会收到未来数据,
                #  但是 tqsim 能保证取到结算时下一个交易日的分红信息
                #  此时，quotes 为 tqbacktest._data['quotes'] 应该保存了全部的合约信息
                rsp_quotes[symbol] = {
                    'cash_dividend_ratio': quotes[symbol].get('cash_dividend_ratio', []),
                    'stock_dividend_ratio': quotes[symbol].get('stock_dividend_ratio', [])
                }
        return rsp_quotes

    def _request_stock_dividend(self, quotes):
        # 对于股票合约，从 stock-dividend 服务请求回测时间段的分红方案
        stock_list = [s for s in quotes if quotes[s]['ins_class'] == 'STOCK' and s not in self._stocks]
        if len(stock_list) == 0:
            return
        # 每个合约只会请求一次，请求失败就退回到原始合约服务中的分红送股数据
        for s in stock_list:
            self._stocks[s] = {
                'request_successed': False,
                'dividend_list': []
            }
        # https://github.com/shinnytech/stock-dividend
        rsp = requests.get(url="https://stock-dividend.shinnytech.com/query",
                           headers=self._headers, timeout=30,
                           params={
                               "stock_list": ','.join(stock_list),
                               "start_date": self._start_date,
                               "end_date": self._end_date
                           })
        if rsp.status_code != 200:
            return
        result = rsp.json().get('result')
        for s in stock_list:
            self._stocks[s]['request_successed'] = True
        for item in result:
            """
            stockcode: 证券代码
            marketcode: 市场代码
            share: 每股送转股数量
            cash: 每股分红（税后）
            recorddate: 股权登记日
            drdate: 除权除息日
            """
            self._stocks[f"{item['marketcode']}.{item['stockcode']}"]["dividend_list"].append(item)
