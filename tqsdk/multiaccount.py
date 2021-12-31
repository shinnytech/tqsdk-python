#!/usr/bin/env python
# -*- coding: utf-8 -*-
__time__ = '2020/8/5 22:45'
__author__ = 'Hong Yan'

from typing import List, Union, Optional

from shinny_structlog import ShinnyLoggerAdapter

from tqsdk.connect import TqConnect, TdReconnectHandler
from tqsdk.channel import TqChan
from tqsdk.tradeable import TqAccount, TqKq, TqKqStock, TqSim, TqSimStock, BaseSim, BaseOtg
from tqsdk.tradeable.mixin import StockMixin


class TqMultiAccount(object):
    """
    天勤多账户 - TqMultiAccount

    天勤多账户模块提供了单 `api` 同时操作不同账户及其组合的功能支持，目前已支持实盘账户、模拟账户和快期模拟账户的任意组合。
    使用天勤多账户进行跨市场或跨账户交易时，可以在不引入多进程和多线程的前提下, 比较方便的传递账户信息进行策略编写,
    同时, 也更方便对不同账户的交易数据进行统计分析。

    **注意**

    - 多账户模式下, 对于 get_position，account，insert_order，set_target_volume 等函数必须指定 account 参数
    - 多账户模式下, 实盘账户的数量受限于信易账户支持实盘账户数, 详见:`更多的实盘交易账户数 <https://doc.shinnytech.com/tqsdk/latest/profession.html#id2>`_

    """

    def __init__(self, accounts: Optional[List[Union[TqAccount, TqKq, TqKqStock, TqSim, TqSimStock]]] = None):
        """
        创建 TqMultiAccount 实例

        Args:
            accounts (List[Union[TqAccount, TqKq, TqKqStock, TqSim, TqSimStock]]): [可选] 多账户列表, 若未指定任何账户, 则为 [TqSim()]

        Example1::

            from tqsdk import TqApi, TqMultiAccount

            account1 = TqAccount("H海通期货", "123456", "123456")
            account2 = TqAccount("H宏源期货", "654321", "123456")
            api = TqApi(TqMultiAccount([account1, account2]), auth=TqAuth("信易账户", "账户密码"))
            # 分别获取账户资金信息
            order1 = api.insert_order(symbol="DCE.m2101", direction="BUY", offset="OPEN", volume=3, account=account1)
            order2 = api.insert_order(symbol="SHFE.au2012C308", direction="BUY", offset="OPEN", volume=3, limit_price=78.0, account=account2)
            while order1.status != "FINISHED" or order2.status != "FINISHED":
                 api.wait_update()
            # 分别获取账户资金信息
            account_info1 = account1.get_account()
            account_info2 = account1.get_account()
            api.close()

        Example2::

            # 多账户模式下使用 TargetPosTask
            from tqsdk import TqApi, TqMultiAccount, TqAuth, TargetPosTask

            account1 = TqAccount("H海通期货", "123456", "123456")
            account2 = TqAccount("H宏源期货", "654321", "123456")
            api = TqApi(TqMultiAccount([account1, account2]), auth=TqAuth("信易账户", "账户密码"))
            symbol1 = "DCE.m2105"
            symbol2 = "DCE.i2101"
            position1 = account1.get_position(symbol1)
            position2 = account2.get_position(symbol2)
            # 多账户模式下, 调仓工具需要指定账户实例
            target_pos1 = TargetPosTask(api, symbol1, account=account1)
            target_pos2 = TargetPosTask(api, symbol2, account=account2)
            target_pos1.set_target_volume(30)
            target_pos2.set_target_volume(80)
            while position1.volume_long != 30 or position2.volume_long != 80:
                api.wait_update()

            api.close()

        """
        self._account_list = accounts if accounts else [TqSim()]
        self._has_tq_account = any([True for a in self._account_list if isinstance(a, BaseOtg)])  # 是否存在实盘账户(TqAccount/TqKq/TqKqStock)
        self._map_conn_id = {}  # 每次建立连接时，记录每个 conn_id 对应的账户
        if self._has_duplicate_account():
            raise Exception("多账户列表中不允许使用重复的账户实例.")

    def _has_duplicate_account(self):
        # 存在相同的账户实例
        account_set = set([a._account_key for a in self._account_list])
        return len(account_set) != len(self._account_list)

    def _check_valid(self, account: Union[str, TqAccount, TqKq, TqKqStock, TqSim, TqSimStock, None]):
        """
        查询委托、成交、资产、委托时, 需要指定账户实例
        account: 类型 str 表示 account_key，其他为账户类型或者 None
        """
        if isinstance(account, str):
            selected_list = [a for a in self._account_list if a._account_key == account]
            return selected_list[0] if selected_list else None
        elif account is None:
            return self._account_list[0] if len(self._account_list) == 1 else None
        else:
            return account if account in self._account_list else None

    def _get_account_id(self, account):
        """ 获取指定账户实例的账户属性 """
        acc = self._check_valid(account)
        return acc._account_id if acc else None

    def _get_account_key(self, account):
        """ 获取指定账户实例的账户属性 """
        acc = self._check_valid(account)
        return acc._account_key if acc else None

    def _is_stock_type(self, account_or_account_key):
        """ 判断账户类型是否为股票账户 """
        acc = self._check_valid(account_or_account_key)
        return isinstance(acc, StockMixin)

    def _get_trade_more_data_and_order_id(self, data):
        """ 获取业务信息截面 trade_more_data 标识，当且仅当所有账户的标识置为 false 时，业务信息截面就绪 """
        trade_more_datas = []
        for account in self._account_list:
            trade_node = data.get("trade", {}).get(account._account_key, {})
            trade_more_data = trade_node.get("trade_more_data", True)
            trade_more_datas.append(trade_more_data)
        return any(trade_more_datas)

    def _run(self, api, api_send_chan, api_recv_chan, ws_md_send_chan, ws_md_recv_chan):
        self._api = api
        log = ShinnyLoggerAdapter(self._api._logger.getChild("TqMultiAccount"))
        for index, account in enumerate(self._account_list):
            _send_chan = api_send_chan if index == len(self._account_list) - 1 else TqChan(self._api, logger=log)
            _recv_chan = api_recv_chan if index == len(self._account_list) - 1 else TqChan(self._api, logger=log)
            _send_chan._logger_bind(chan_name=f"send to account_{index}")
            _recv_chan._logger_bind(chan_name=f"recv from account_{index}")
            ws_md_send_chan._logger_bind(chan_from=f"account_{index}")
            ws_md_recv_chan._logger_bind(chan_to=f"account_{index}")
            if isinstance(account, BaseSim):
                # 启动模拟账户实例
                self._api.create_task(
                    account._run(self._api, _send_chan, _recv_chan, ws_md_send_chan, ws_md_recv_chan))
            else:
                # 连接交易服务器
                ws_td_send_chan, ws_td_recv_chan = self._connect_td(account, index)
                ws_td_send_chan._logger_bind(chan_from=f"account_{index}")
                ws_td_recv_chan._logger_bind(chan_to=f"account_{index}")
                # 账户处理消息
                self._api.create_task(
                    account._run(self._api, _send_chan, _recv_chan, ws_md_send_chan, ws_md_recv_chan, ws_td_send_chan,
                                 ws_td_recv_chan)
                )
            ws_md_send_chan, ws_md_recv_chan = _send_chan, _recv_chan

    def _connect_td(self, account: Union[TqAccount, TqKq, TqKqStock] = None, index: int = 0):
        # 连接交易服务器
        td_logger = self._format_logger("TqConnect", account)
        conn_id = f"td_{index}"
        ws_td_send_chan = TqChan(self._api, chan_name=f"send to {conn_id}", logger=td_logger)
        ws_td_recv_chan = TqChan(self._api, chan_name=f"recv from {conn_id}", logger=td_logger)
        conn = TqConnect(td_logger, conn_id=conn_id)
        self._api.create_task(conn._run(self._api, account._td_url, ws_td_send_chan, ws_td_recv_chan))
        ws_td_send_chan._logger_bind(chan_from=f"td_reconn_{index}")
        ws_td_recv_chan._logger_bind(chan_to=f"td_reconn_{index}")

        td_handler_logger = self._format_logger("TdReconnect", account)
        td_reconnect = TdReconnectHandler(td_handler_logger)
        send_to_recon = TqChan(self._api, chan_name=f"send to td_reconn_{index}", logger=td_handler_logger)
        recv_from_recon = TqChan(self._api, chan_name=f"recv from td_reconn_{index}", logger=td_handler_logger)
        self._api.create_task(
            td_reconnect._run(self._api, send_to_recon, recv_from_recon, ws_td_send_chan, ws_td_recv_chan)
        )
        self._map_conn_id[conn_id] = account
        return send_to_recon, recv_from_recon

    def _format_logger(self, log_name: str, account: Union[TqAccount, TqKq, TqKqStock, TqSim]):
        return ShinnyLoggerAdapter(self._api._logger.getChild(log_name),
                                   url=account._td_url,
                                   broker_id=account._broker_id,
                                   account_id=account._account_id)
