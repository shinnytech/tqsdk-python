#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'mayanqiong'

import asyncio
from typing import Optional, Union

from pandas import DataFrame

from tqsdk.api import TqApi, TqAccount, TqSim, TqKq
from tqsdk.channel import TqChan
from tqsdk.datetime import _get_trade_timestamp
from tqsdk.lib.target_pos_task import TargetPosTask
from tqsdk.lib.utils import _check_time_table, _get_deadline_from_interval
from tqsdk.objs import Trade


class TargetPosScheduler(object):
    """算法执行引擎，根据设定的目标持仓任务列表，调整指定合约到目标头寸"""

    def __init__(self, api: TqApi, symbol: str, time_table: DataFrame, offset_priority: str = "今昨,开",
                 min_volume: Optional[int] = None, max_volume: Optional[int] = None, trade_chan: Optional[TqChan] = None,
                 trade_objs_chan: Optional[TqChan] = None, account: Optional[Union[TqAccount, TqKq, TqSim]] = None) -> None:
        """
        创建算法执行引擎实例，根据设定的目标持仓任务列表，调用 TargetPosTask 来调整指定合约到目标头寸。

        **注意:**
            1. TargetPosScheduler 创建后不会立即不下单或撤单, 它的下单和撤单动作, 是在之后的每次 wait_update 时执行的. 因此, **需保证后续还会调用wait_update()** 。

            2. 请勿同时使用 TargetPosScheduler、TargetPosTask、insert_order() 函数, 否则将导致报错或错误下单。

            3. `symbol`，`offset_priority`，`min_volume`，`max_volume`，`trade_chan`，`trade_objs_chan`，`account` 这几个参数会直接传给 TargetPosTask，请按照 TargetPosTask 的说明设置参数。

        Args:
            api (TqApi): TqApi实例，该task依托于指定api下单/撤单

            symbol (str): 负责调整的合约代码

            time_table (DataFrame): 目标持仓任务列表，每一行表示一项目标持仓任务，其应该包含以下几列：
                + interval: 当前这项任务的持续时间长度，单位为秒，经过这么多秒之后，此项任务应该退出，剩余未调整到的目标持仓，会留到下一项任务中
                    * 注意1：对于最后一项任务，会按照当前项参数，调整到目标持仓后立即退出（时间参数不对最后一项任务起作用）
                    * 注意2：时间长度可以跨非交易时间段（可以跨小节等待），但是不可以跨交易日
                + target_pos: 当前这项任务的目标净持仓手数
                + price: 当前这项任务的下单价格模式，此列中非 None 的项，会作为创建 TargetPosTask 实例的 price 参数，支持以下几种参数：
                    * None: 不下单，表示暂停一段时间
                    * "PASSIVE" : 排队价下单
                    * "ACTIVE": 对价下单
                    * Callable (direction: str) -> Union[float, int]: 传入函数作为价格参数，函数参数为下单方向，函数返回值是下单价格。如果返回 nan，程序会抛错。

            offset_priority (str): [可选]开平仓顺序，昨=平昨仓，今=平今仓，开=开仓，逗号=等待之前操作完成

                                   对于下单指令区分平今/昨的交易所(如上期所)，按照今/昨仓的数量计算是否能平今/昨仓
                                   对于下单指令不区分平今/昨的交易所(如中金所)，按照“先平当日新开仓，再平历史仓”的规则计算是否能平今/昨仓，如果这些交易所设置为"昨开"在有当日新开仓和历史仓仓的情况下，会自动跳过平昨仓进入到下一步

                                   * "今昨,开" 表示先平今仓，再平昨仓，等待平仓完成后开仓，对于没有单向大边的品种避免了开仓保证金不足
                                   * "今昨开" 表示先平今仓，再平昨仓，并开仓，所有指令同时发出，适合有单向大边的品种
                                   * "昨开" 表示先平昨仓，再开仓，禁止平今仓，适合股指这样平今手续费较高的品种
                                   * "开" 表示只开仓，不平仓，适合需要进行锁仓操作的品种

            min_volume (int): [可选] **大单拆分模式下** 每笔最小下单的手数，默认不启用 **大单拆分模式**

            max_volume (int): [可选] **大单拆分模式下** 每笔最大下单的手数，默认不启用 **大单拆分模式**

            trade_chan (TqChan): [可选]成交通知channel, 当有成交发生时会将成交手数(多头为正数，空头为负数)发到该channel上

            trade_objs_chan (TqChan): [可选]成交对象通知channel, 当有成交发生时会将成交对象发送到该channel上

            account (TqAccount/TqKq/TqSim): [可选]指定发送下单指令的账户实例, 多账户模式下，该参数必须指定

        Example::

            from pandas import DataFrame
            from tqsdk import TqApi, TargetPosScheduler

            api = TqApi(auth=TqAuth("信易账户", "账户密码"))
            time_table = DataFrame([
                [25, 10, "PASSIVE"],
                [5, 10, "ACTIVE"],
                [25, 20, "PASSIVE"],
                [5, 20, "ACTIVE"],
            ], columns=['interval', 'target_pos', 'price'])

            scheduler = TargetPosScheduler(api, 'SHFE.cu2112', time_table=time_table)
            while True:
                api.wait_update()
                if scheduler.is_finished():
                    break

            print("打印出 scheduler 全部成交以及成交均价")
            print(scheduler.trades_df)
            average_trade_price = sum(scheduler.trades_df['price'] * scheduler.trades_df['volume']) / sum(scheduler.trades_df['volume'])
            print("成交均价:", average_trade_price)
            api.close()
        """
        self._api = api
        self._account = account

        # 这些参数直接传给 TargetPosTask，由 TargetPosTask 来检查其合法性
        self._symbol = symbol
        self._offset_priority = offset_priority
        self._min_volume = min_volume
        self._max_volume = max_volume
        self._trade_chan = trade_chan

        self._trade_objs_chan = trade_objs_chan if trade_objs_chan else TqChan(self._api)
        self._time_table = _check_time_table(time_table)
        self._task = self._api.create_task(self._run())

        self._trade_keys = list(Trade(None).keys())
        self.trades_df = DataFrame(columns=self._trade_keys)  # 所有的 trade 列表
        self._trade_recv_task = self._api.create_task(self._trade_recv())

    async def _run(self):
        """负责调整目标持仓的task"""
        quote = await self._api.get_quote(self._symbol)
        self._time_table['deadline'] = _get_deadline_from_interval(quote, self._time_table['interval'])
        target_pos_task = None
        try:
            _index = 0  # _index 表示下标
            for index, row in self._time_table.iterrows():
                if row['price'] is None:
                    target_pos_task = None
                else:
                    target_pos_task = TargetPosTask(api=self._api, symbol=self._symbol, price=row['price'],
                                                    offset_priority=self._offset_priority,
                                                    min_volume=self._min_volume, max_volume=self._max_volume,
                                                    trade_chan=self._trade_chan,
                                                    trade_objs_chan=self._trade_objs_chan,
                                                    account=self._account)
                    target_pos_task.set_target_volume(row['target_pos'])
                if _index < self._time_table.shape[0] - 1:  # 非最后一项
                    async for _ in self._api.register_update_notify(quote):
                        if _get_trade_timestamp(quote.datetime, float('nan')) > row['deadline']:
                            if target_pos_task:
                                target_pos_task._task.cancel()
                                await asyncio.gather(target_pos_task._task, return_exceptions=True)
                            break
                elif target_pos_task:  # 最后一项，如果有 target_pos_task 等待持仓调整完成，否则直接退出
                    position = self._api.get_position(self._symbol, self._account)
                    async for _ in self._api.register_update_notify(position):
                        if position.pos == row['target_pos']:
                            break
                _index = _index + 1
        finally:
            if target_pos_task:
                target_pos_task._task.cancel()
                await asyncio.gather(target_pos_task._task, return_exceptions=True)
            await self._trade_objs_chan.close()
            await self._trade_recv_task

    async def _trade_recv(self):
        async for trade in self._trade_objs_chan:
            self.trades_df.loc[self.trades_df.shape[0]] = [trade[k] for k in self._trade_keys]

    def cancel(self):
        """
        取消当前 TargetPosScheduler 实例，会将该实例已经发出但还是未成交的委托单撤单。

        Example::

            from pandas import DataFrame
            from tqsdk import TqApi, TargetPosScheduler

            api = TqApi(auth=TqAuth("信易账户", "账户密码"))
            time_table = DataFrame([
                [25, 10, "PASSIVE"],
                [5, 10, "ACTIVE"],
                [25, 20, "PASSIVE"],
                [5, 20, "ACTIVE"],
            ], columns=['interval', 'target_pos', 'price'])

            scheduler = TargetPosScheduler(api, 'SHFE.cu2112', time_table=time_table)

            api.wait_update()
            # 运行代码。。。
            scheduler.cancel()
            while True:
                api.wait_update()
                if scheduler.is_finished():
                    break
            api.close()
        """
        if not self._task.done():
            self._task.cancel()
        return

    def is_finished(self):
        """
        返回当前 TargetPosScheduler 实例是否已经结束。即此实例不会再发出下单或者撤单的任何动作。

        Returns:
            bool: 当前 TargetPosScheduler 实例是否已经结束
        """
        return self._task.done()
