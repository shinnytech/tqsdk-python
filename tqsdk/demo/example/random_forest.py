#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'limin'

import pandas as pd
import datetime
from contextlib import closing
from tqsdk import TqApi, TqSim, TqBacktest, BacktestFinished, TargetPosTask
from tqsdk.tafunc import sma, ema2, trma
from sklearn.ensemble import RandomForestClassifier

pd.set_option('display.max_rows', None)  # 设置Pandas显示的行数
pd.set_option('display.width', None)  # 设置Pandas显示的宽度

'''
应用随机森林对某交易日涨跌情况的预测(使用sklearn包)
参考:https://www.joinquant.com/post/1571
'''

symbol = "SHFE.ru1811"  # 交易合约代码
close_hour, close_minute = 14, 50  # 预定收盘时间(因为真实收盘后无法进行交易, 所以提前设定收盘时间)


def get_prediction_data(klines, n):
    """获取用于随机森林的n个输入数据(n为数据长度): n天中每天的特征参数及其涨跌情况"""
    close_prices = klines.close[- 30 - n:]  # 获取本交易日及以前的收盘价(此时在预定的收盘时间: 认为本交易日已收盘)
    # 计算所需指标
    sma_data = sma(close_prices, 30, 0.02)[-n:]  # SMA指标, 函数默认时间周期参数:30
    wma_data = ema2(close_prices, 30)[-n:]  # WMA指标
    mom_data = trma(close_prices, 30)[-n:]  # MOM指标
    x_all = list(zip(sma_data, wma_data, mom_data))  # 样本特征组
    y_all = list(klines.close.iloc[i] >= klines.close.iloc[i - 1] for i in list(reversed(range(-1, -n - 1, -1))))  # 样本标签组
    # x_all:            大前天指标 前天指标 昨天指标 (今天指标)
    # y_all:   (大前天)    前天     昨天    今天      -明天-
    # 准备算法需要用到的数据
    x_train = x_all[: -1]  # 训练数据: 特征
    x_predict = x_all[-1]  # 预测数据(用本交易日的指标预测下一交易日的涨跌)
    y_train = y_all[1:]  # 训练数据: 标签 (去掉第一个数据后让其与指标隔一位对齐(例如: 昨天的特征 -> 对应预测今天的涨跌标签))

    return x_train, y_train, x_predict


predictions = []  # 用于记录每次的预测结果(在每个交易日收盘时用收盘数据预测下一交易日的涨跌,并记录在此列表里)
api = TqApi(TqSim(), backtest=TqBacktest(start_dt=datetime.date(2018, 7, 2), end_dt=datetime.date(2018, 9, 26)))
quote = api.get_quote(symbol)
klines = api.get_kline_serial(symbol, duration_seconds=24 * 60 * 60)  # 日线
target_pos = TargetPosTask(api, symbol)
with closing(api):
    try:
        while True:
            while not api.is_changing(klines.iloc[-1], "datetime"):  # 等到达下一个交易日
                api.wait_update()
            while True:
                api.wait_update()
                # 在收盘后预测下一交易日的涨跌情况
                if api.is_changing(quote, "datetime"):
                    now = datetime.datetime.strptime(quote["datetime"], "%Y-%m-%d %H:%M:%S.%f")  # 当前quote的时间
                    # 判断是否到达预定收盘时间: 如果到达 则认为本交易日收盘, 此时预测下一交易日的涨跌情况, 并调整为对应仓位
                    if now.hour == close_hour and now.minute >= close_minute:
                        # 1- 获取数据
                        x_train, y_train, x_predict = get_prediction_data(klines, 75)  # 参数1: K线, 参数2:需要的数据长度

                        # 2- 利用机器学习算法预测下一个交易日的涨跌情况
                        # n_estimators 参数: 选择森林里（决策）树的数目; bootstrap 参数: 选择建立决策树时，是否使用有放回抽样
                        clf = RandomForestClassifier(n_estimators=30, bootstrap=True)
                        clf.fit(x_train, y_train)  # 传入训练数据, 进行参数训练
                        predictions.append(bool(clf.predict([x_predict])))  # 传入测试数据进行预测, 得到预测的结果

                        # 3- 进行交易
                        if predictions[-1] == True:  # 如果预测结果为涨: 买入
                            print(quote["datetime"], "预测下一交易日为 涨")
                            target_pos.set_target_volume(10)
                        else:  # 如果预测结果为跌: 卖出
                            print(quote["datetime"], "预测下一交易日为 跌")
                            target_pos.set_target_volume(-10)
                        break

    except BacktestFinished:  # 回测结束, 获取预测结果，统计正确率
        klines["pre_close"] = klines["close"].shift(1)  # 增加 pre_close(上一交易日的收盘价) 字段
        klines = klines[-len(predictions) + 1:]  # 取出在回测日期内的K线数据
        klines["prediction"] = predictions[:-1]  # 增加预测的本交易日涨跌情况字段(向后移一个数据目的: 将 本交易日对应下一交易日的涨跌 调整为 本交易日对应本交易日的涨跌)
        results = (klines["close"] - klines["pre_close"] >= 0) == klines["prediction"]

        print(klines)
        print("----回测结束----")
        print("预测结果正误:\n", results)
        print("预测结果数目统计: 总计", len(results),"个预测结果")
        print(pd.value_counts(results))
        print("预测的准确率:")
        print((pd.value_counts(results)[True]) / len(results))
