#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'mayanqiong'

import time
import sys

from typing import Tuple, Union, List, Dict, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from tqsdk.api import TqApi
    from tqsdk.api import UnionTradeable


class TqRiskRule(object):

    def __init__(self, api: 'TqApi', account: Optional['UnionTradeable'] = None) -> None:
        # 记录必要参数， 每个风控规则都需要继承这个基类
        self._api = api
        account = self._api._account._check_valid(account)
        if account is None:
            raise Exception(f"多账户模式下, 需要指定账户实例 account")
        self._account = account
        self._account_key = self._account._account_key

    def _could_insert_order(self, pack: Dict[str, Any]) -> Tuple[bool, str]:  # 是否可以下单
        """
        检查是否可以下单的默认实现，子类可以覆盖此方法来实现自定义逻辑
        默认情况下不限制下单操作
        """
        return True, ""

    def _on_insert_order(self, pack: Dict[str, Any]) -> None:
        """
        下单后的处理默认实现，子类可以覆盖此方法来实现自定义逻辑
        默认情况下不做任何处理
        """
        pass

    def _could_cancel_order(self, pack: Dict[str, Any]) -> Tuple[bool, str]:  # 是否可以撤单
        """
        检查是否可以撤单的默认实现，子类可以覆盖此方法来实现自定义逻辑
        默认情况下不限制撤单操作
        """
        return True, ""

    def _on_cancel_order(self, pack: Dict[str, Any]) -> None:
        """
        撤单后的处理默认实现，子类可以覆盖此方法来实现自定义逻辑
        默认情况下不做任何处理
        """
        pass

    def _on_settle(self) -> None:
        """
        结算后的处理默认实现，子类可以覆盖此方法来实现自定义逻辑
        默认情况下不做任何处理
        """
        pass


class TqRuleOpenCountsLimit(TqRiskRule):
    """
    风控规则类 - 交易日内开仓次数限制。

    """

    def __init__(self, api: 'TqApi', open_counts_limit: int, symbol: Union[str, List[str]], account: Optional['UnionTradeable'] = None) -> None:
        """
        Args:
            api (TqApi): TqApi 实例

            open_counts_limit (int): 交易日内开仓次数上限

            symbol (str/list of str): 负责限制的合约代码或合约代码列表.
                * str: 一个合约代码
                * list of str: 合约代码列表

            account (TqAccount/TqKq/TqZq/TqKqStock/TqSim/TqSimStock/TqCtp/TqRohon/TqJees/TqYida/TqTradingUnit): [可选] 指定发送下单指令的账户实例, 多账户模式下，该参数必须指定

        Example1::

            from tqsdk import TqApi
            from tqsdk.risk_rule import TqRuleOpenCountsLimit

            api = TqApi(auth=TqAuth("快期账户", "账户密码"))

            rule = TqRuleOpenCountsLimit(api, open_counts_limit=10, symbol="DCE.m2112")  # 创建风控规则实例
            api.add_risk_rule(rule)  # 添加风控规则

            quote = api.get_quote("DCE.m2112")
            try:
                # 每次最新价变动，下一笔订单，直到超过开仓次数风控限制
                while True:
                    api.wait_update()
                    if api.is_changing(quote, ['last_price']):
                        order = api.insert_order(symbol="DCE.m2112", direction="BUY", offset="OPEN", volume=1)
                        while order.status != "FINISHED":
                            api.wait_update()
            except TqRiskRuleError as e:
                print('!!!', e)
            api.close()

        """
        super(TqRuleOpenCountsLimit, self).__init__(api=api, account=account)
        if open_counts_limit < 0:
            raise Exception("参数 open_volumes_limit 必须大于 0 的数字")
        self.open_counts_limit = open_counts_limit
        self.symbol_list = [symbol] if isinstance(symbol, str) else symbol
        self.data = {s: 0 for s in self.symbol_list}
        for order_id, order in self._api._data.get('trade', {}).get(self._account_key, {}).get('orders', {}).items():
            symbol = order["exchange_id"] + "." + order["instrument_id"]
            if order["offset"] == "OPEN" and symbol in self.data:
                self.data[symbol] += 1

    def _could_insert_order(self, pack: Dict[str, Any]) -> Tuple[bool, str]:
        if pack['account_key'] == self._account_key:
            symbol = pack["exchange_id"] + "." + pack["instrument_id"]
            if pack["offset"] == "OPEN" and symbol in self.symbol_list:
                if self.data[symbol] + 1 > self.open_counts_limit:
                    return False, f"触发风控规则，合约 {symbol} 开仓到达交易日内开仓次数限制 {self.open_counts_limit}, " \
                                  f"已下单次数 {self.data[symbol]}"
        return True, ""

    def _on_insert_order(self, pack: Dict[str, Any]) -> None:
        if pack['account_key'] == self._account_key:
            symbol = pack["exchange_id"] + "." + pack["instrument_id"]
            if pack["offset"] == "OPEN" and symbol in self.symbol_list:
                self.data[symbol] += 1

    def _on_settle(self) -> None:
        for k in self.data.keys():
            self.data[k] = 0


class TqRuleOpenVolumesLimit(TqRiskRule):
    """
    风控规则类 - 交易日内开仓手数限制

    """

    def __init__(self, api: 'TqApi', open_volumes_limit: int, symbol: Union[str, List[str]], account: Optional['UnionTradeable'] = None) -> None:
        """
        Args:
            api (TqApi): TqApi 实例

            open_volumes_limit (int): 交易日内开仓手数上限

            symbol (str/list of str): 负责限制的合约代码或合约代码列表.
                * str: 一个合约代码
                * list of str: 合约代码列表

            account (TqAccount/TqKq/TqZq/TqKqStock/TqSim/TqSimStock/TqCtp/TqRohon/TqJees/TqYida/TqTradingUnit): [可选] 指定发送下单指令的账户实例, 多账户模式下，该参数必须指定

        Example1::

            from tqsdk import TqApi
            from tqsdk.risk_rule import TqRuleOpenVolumesLimit

            api = TqApi(auth=TqAuth("快期账户", "账户密码"))

            rule = TqRuleOpenVolumesLimit(api, open_volumes_limit=10, symbol="DCE.m2112")  # 创建风控规则实例
            api.add_risk_rule(rule)  # 添加风控规则

            # 下单 5 手，不会触发风控规则
            order1 = api.insert_order(symbol="DCE.m2112", direction="BUY", offset="OPEN", volume=5)
            while order1.status != "FINISHED":
                api.wait_update()

            # 继续下单 8 手，会触发风控规则
            order2 = api.insert_order(symbol="DCE.m2112", direction="BUY", offset="OPEN", volume=8)
            while order2.status != "FINISHED":
                api.wait_update()
            api.close()


        Example2::


            from tqsdk import TqApi, TqKq, TqRiskRuleError
            from tqsdk.risk_rule import TqRuleOpenVolumesLimit

            account = TqKq()
            api = TqApi(account=account, auth=TqAuth("快期账户", "账户密码"))

            rule = TqRuleOpenVolumesLimit(api, open_volumes_limit=10, symbol="DCE.m2112", account=account)  # 创建风控规则实例
            api.add_risk_rule(rule)  # 添加风控规则

            try:
                # 下单 11 手，触发风控规则
                order1 = api.insert_order(symbol="DCE.m2112", direction="BUY", offset="OPEN", volume=11)
                while order1.status != "FINISHED":
                    api.wait_update()
            except TqRiskRuleError as e:
                print("!!!", e)

            api.close()
        """
        super(TqRuleOpenVolumesLimit, self).__init__(api=api, account=account)
        if open_volumes_limit < 0:
            raise Exception("参数 open_volumes_limit 必须大于 0 的数字")
        self.open_volumes_limit = open_volumes_limit
        self.symbol_list = [symbol] if isinstance(symbol, str) else symbol
        self.data = {s: 0 for s in self.symbol_list}
        for trade_id, trade in self._api._data.get('trade', {}).get(self._account_key, {}).get('trades', {}).items():
            symbol = trade["exchange_id"] + "." + trade["instrument_id"]
            if trade["offset"] == "OPEN" and symbol in self.data:
                self.data[symbol] += trade["volume"]

    def _could_insert_order(self, pack: Dict[str, Any]) -> Tuple[bool, str]:
        if pack['account_key'] == self._account_key:
            symbol = pack["exchange_id"] + "." + pack["instrument_id"]
            if pack["offset"] == "OPEN" and symbol in self.symbol_list:
                if self.data[symbol] + pack["volume"] > self.open_volumes_limit:
                    return False, f"触发风控规则，合约 {symbol} 开仓到达交易日内开仓手数限制 {self.open_volumes_limit}, " \
                                  f"已下单手数 {self.data[symbol]}, 即将下单手数 {pack['volume']}"
        return True, ""

    def _on_insert_order(self, pack: Dict[str, Any]) -> None:
        if pack['account_key'] == self._account_key:
            symbol = pack["exchange_id"] + "." + pack["instrument_id"]
            if pack["offset"] == "OPEN" and symbol in self.symbol_list:
                self.data[symbol] += pack["volume"]

    def _on_settle(self) -> None:
        for k in self.data.keys():
            self.data[k] = 0


class TqRuleAccOpenVolumesLimit(TqRiskRule):
    """
    风控规则类 - 累计开仓手数限制。

    限制合约开仓手数之和。

    """

    def __init__(self, api: 'TqApi', open_volumes_limit: int, symbol: Union[str, List[str]], account: Optional['UnionTradeable'] = None) -> None:
        """
        Args:
            api (TqApi): TqApi 实例


            open_volumes_limit (int): 交易日内开仓手数之和上限

            symbol (str/list of str): 负责限制的合约代码或合约代码列表.
                * str: 一个合约代码
                * list of str: 合约代码列表

            account (TqAccount/TqKq/TqZq/TqKqStock/TqSim/TqSimStock/TqCtp/TqRohon/TqJees/TqYida/TqTradingUnit): [可选] 指定发送下单指令的账户实例, 多账户模式下，该参数必须指定

        Example::

            from tqsdk import TqApi, TqKq, TqRiskRuleError
            from tqsdk.risk_rule import TqRuleAccOpenVolumesLimit

            account = TqKq()
            api = TqApi(account=account, auth=TqAuth("快期账户", "账户密码"))

            quote = api.get_quote("SSE.000300")
            call_in, call_at, call_out = api.query_all_level_finance_options("SSE.000300", quote.last_price, "CALL", nearbys=0)
            put_in, put_at, put_out = api.query_all_level_finance_options("SSE.000300", quote.last_price, "PUT", nearbys=0)
            near_symbols = call_in + call_at + call_out + put_in + put_at + put_out  # 找到所有当月期权合约

            symbols = api.query_options("SSE.000300", expired=False)  # 找到所有中金所期权合约

            # 规则1: 中金所当月期权合约日内开仓不超过 100 手
            # 规则2: 中金所所有期权合约日内合约开仓不超过 200 手
            rule1 = TqRuleAccOpenVolumesLimit(api, open_volumes_limit=100, symbol=near_symbols, account=account)  # 创建风控规则实例
            rule2 = TqRuleAccOpenVolumesLimit(api, open_volumes_limit=200, symbol=symbols, account=account)  # 创建风控规则实例
            api.add_risk_rule(rule1)  # 添加风控规则
            api.add_risk_rule(rule2)  # 添加风控规则

            try:
                # 下单 101 手，触发风控规则
                order1 = api.insert_order(symbol="CFFEX.IO2111-C-4900", direction="BUY", offset="OPEN", volume=101, limit_price=35.6)
                while order1.status != "FINISHED":
                    api.wait_update()
            except TqRiskRuleError as e:
                print("!!!", e)  # 报错，当月期权合约日内合约开仓不超过 100 手, 已下单次数 0

            api.close()
        """
        super(TqRuleAccOpenVolumesLimit, self).__init__(api=api, account=account)
        if open_volumes_limit < 0:
            raise Exception("参数 open_volumes_limit 必须大于 0 的数字")
        self.open_volumes_limit = open_volumes_limit
        self.open_volumes = 0  # 所有合约日内合约开仓手数
        self.symbol_list = [symbol] if isinstance(symbol, str) else symbol
        for trade_id, trade in self._api._data.get('trade', {}).get(self._account_key, {}).get('trades', {}).items():
            if trade["offset"] == "OPEN" and f'{trade["exchange_id"]}.{trade["instrument_id"]}' in self.symbol_list:
                self.open_volumes += trade['volume']

    def _could_insert_order(self, pack: Dict[str, Any]) -> Tuple[bool, str]:
        symbol = pack["exchange_id"] + "." + pack["instrument_id"]
        if pack['account_key'] == self._account_key and symbol in self.symbol_list:  # 当前账户下单
            if pack["offset"] == "OPEN" and self.open_volumes + pack['volume'] > self.open_volumes_limit:
                return False, f"触发风控规则，所有合约日内合约开仓不超过 {self.open_volumes_limit} 手, 已下单手数 {self.open_volumes}"
        return True, ""

    def _on_insert_order(self, pack: Dict[str, Any]) -> None:
        symbol = pack["exchange_id"] + "." + pack["instrument_id"]
        if pack['account_key'] == self._account_key and symbol in self.symbol_list:  # 当前账户下单
            if pack["offset"] == "OPEN":  # 开仓单把手数累加
                self.open_volumes += pack['volume']

    def _on_settle(self) -> None:
        self.open_volumes = 0


class TqRuleOrderRateLimit(TqRiskRule):
    """
    风控规则类 - 一个 API 实例每秒最大订单操作次数限制。
    
    针对特定的交易所和交易账户，设置每秒订单操作次数阈值（包括报单和撤单）。
    当操作次数达到阈值时触发风控。如果指定多个交易所，则每个交易所分别限制。
    """

    def __init__(self, api: 'TqApi', limit_per_second: int, exchange_id: Union[str, List[str]], account: Optional['UnionTradeable'] = None) -> None:
        """
        Args:
            api (TqApi): TqApi 实例

            limit_per_second (int): 每秒订单操作次数上限（当操作次数超过此值时触发风控）

            exchange_id (str/list of str): 指定交易所代码
                * str: 指定交易所代码，如 "SHFE", "DCE", "CZCE", "CFFEX" 等
                * list of str: 交易所代码列表，如 ["DCE", "SHFE"]，每个交易所分别限制

            account (TqAccount/TqKq/TqZq/TqKqStock/TqSim/TqSimStock/TqCtp/TqRohon/TqJees/TqYida/TqTradingUnit): [可选] 指定发送下单指令的账户实例, 多账户模式下，该参数必须指定

        Example1::

            from tqsdk import TqApi
            from tqsdk.risk_rule import TqRuleOrderRateLimit

            api = TqApi(auth=TqAuth("快期账户", "账户密码"))

            # 设置大连商品交易所每秒订单操作次数上限为 5（第6次操作时触发风控）
            rule = TqRuleOrderRateLimit(api, limit_per_second=5, exchange_id="DCE")
            api.add_risk_rule(rule)

            try:
                # 快速订单操作，第6次操作时触发风控
                for i in range(10):
                    order = api.insert_order(symbol="DCE.m2512", direction="BUY", offset="OPEN", volume=1)
                    api.wait_update()
            except TqRiskRuleError as e:
                print('!!!', e)
            api.close()

        Example2::

            from tqsdk import TqApi, TqKq
            from tqsdk.risk_rule import TqRuleOrderRateLimit

            account = TqKq()
            api = TqApi(account=account, auth=TqAuth("快期账户", "账户密码"))

            # 设置大连商品交易所每秒订单操作次数上限为 3（第4次操作时触发风控）
            rule = TqRuleOrderRateLimit(api, limit_per_second=3, exchange_id="DCE", account=account)
            api.add_risk_rule(rule)

            try:
                for i in range(4):
                    order = api.insert_order(symbol="DCE.m2512", direction="BUY", offset="OPEN", volume=1)
                    api.wait_update()
            except TqRiskRuleError as e:
                print("!!!", e)

            api.close()

        Example3::

            from tqsdk import TqApi, TqKq
            from tqsdk.risk_rule import TqRuleOrderRateLimit

            account = TqKq()
            api = TqApi(account=account, auth=TqAuth("快期账户", "账户密码"))

            # 设置大连商品交易所和上海期货交易所，每个交易所每秒订单操作次数上限为 5（第6次操作时触发风控）
            rule = TqRuleOrderRateLimit(api, limit_per_second=5, exchange_id=["DCE", "SHFE"], account=account)
            api.add_risk_rule(rule)
             
            try:
                for i in range(6):
                    order = api.insert_order(symbol="DCE.m2512", direction="BUY", offset="OPEN", volume=1)
                    api.wait_update()
                    if order.status == "ALIVE":
                        api.cancel_order(order)
                    api.wait_update()
            except TqRiskRuleError as e:
                print("!!!", e)

            api.close()
        """
        super(TqRuleOrderRateLimit, self).__init__(api=api, account=account)
        if limit_per_second <= 0:
            raise Exception("参数 limit_per_second 必须大于 0 的数字")
        self.limit_per_second = limit_per_second
        self.exchange_list = [exchange_id] if isinstance(exchange_id, str) else exchange_id
        # 为每个交易所单独记录订单操作时间戳
        self.operation_timestamps: Dict[str, List[float]] = {exchange: [] for exchange in self.exchange_list}

    def _could_insert_order(self, pack: Dict[str, Any]) -> Tuple[bool, str]:
        if pack['account_key'] == self._account_key:
            exchange_id = pack["exchange_id"]
            # 只对指定交易所的订单进行限制
            if exchange_id not in self.exchange_list:
                return True, ""
            
            return self._check_rate_limit(exchange_id, "报单操作")
        return True, ""

    def _on_insert_order(self, pack: Dict[str, Any]) -> None:
        if pack['account_key'] == self._account_key:
            exchange_id = pack["exchange_id"]
            # 只对指定交易所的订单进行记录
            if exchange_id not in self.exchange_list:
                return
                
            self._record_operation(exchange_id)

    def _could_cancel_order(self, pack: Dict[str, Any]) -> Tuple[bool, str]:
        if pack['account_key'] == self._account_key:
            # 从撤单包中获取交易所信息，需要通过order_id查找原始订单
            # 这里我们需要从API的订单数据中获取交易所信息
            exchange_id = self._get_exchange_from_cancel_pack(pack)
            if exchange_id and exchange_id in self.exchange_list:
                return self._check_rate_limit(exchange_id, "撤单操作")
        return True, ""

    def _on_cancel_order(self, pack: Dict[str, Any]) -> None:
        if pack['account_key'] == self._account_key:
            exchange_id = self._get_exchange_from_cancel_pack(pack)
            if exchange_id and exchange_id in self.exchange_list:
                self._record_operation(exchange_id)

    def _get_exchange_from_cancel_pack(self, pack: Dict[str, Any]) -> Optional[str]:
        """从撤单包中获取交易所信息"""
        # 撤单包中包含order_id，需要查找对应的订单来获取exchange_id
        order_id = pack.get("order_id")
        if order_id:
            # 从API的订单数据中查找
            orders = self._api._data.get('trade', {}).get(pack['account_key'], {}).get('orders', {})
            order = orders.get(order_id)
            if order:
                return order.get("exchange_id")
        return None

    def _check_rate_limit(self, exchange_id: str, operation_type: str) -> Tuple[bool, str]:
        """检查频率限制"""
        # 本规则的参考时间是交易所时间，而非本地时间，本地时间会受人为调整而发生跳变
        # 所以这里使用 _get_boot_time() 而非 time.time()，因为 _get_boot_time() 是暂停感知的单调时钟，不会因为休眠而停止
        current_time = self._get_boot_time()
        
        # 清理该交易所 1 秒前的记录
        self.operation_timestamps[exchange_id] = [ts for ts in self.operation_timestamps[exchange_id] 
                                                  if current_time - ts < 1.0]
        
        # 检查该交易所当前 1 秒内的操作数量是否超过阈值（当操作数量超过阈值时报错）
        current_count = len(self.operation_timestamps[exchange_id])
        # 当即将进行的操作次数超过阈值时，该操作被拒绝
        if current_count + 1 > self.limit_per_second:
            return False, f"触发风控规则，交易所 {exchange_id}, 每秒订单操作次数超过阈值 {self.limit_per_second}, " \
                          f"当前秒内已操作次数 {current_count}, 拒绝第 {current_count + 1} 次{operation_type}"
        return True, ""

    def _record_operation(self, exchange_id: str) -> None:
        """记录操作时间戳"""
        current_time = self._get_boot_time()
        self.operation_timestamps[exchange_id].append(current_time)

    def _on_settle(self) -> None:
        # 每个交易日结算时清空所有交易所的记录
        for exchange in self.exchange_list:
            self.operation_timestamps[exchange] = []

    def _get_boot_time(self):
        """系统自启动以来持续运行的时间，包括休眠，单位为秒"""
        if sys.platform.startswith("win"):
            # todo:
            # python 3.13 开始，time.monotonic() 函数在 Windows 上调用 QueryPerformanceCounter 实现，之前的版本是使用 GetTickCount64 实现: https://github.com/python/cpython/issues/88494
            # 这是一个 breaking change，GetTickCount64 在系统休眠时依然计时，QueryPerformanceCounter 提供更高精度的计时，但如果需要计算休眠时间，Windows 官方还是建议使用 GetTickCount64: https://learn.microsoft.com/en-us/windows/win32/sysinfo/interrupt-time
            # 权衡一下，只有最新 python 3.13 的用户，在进程运行过程中遇到系统休眠时，才有可能遇到无法获取准确时间的问题，为了避免引入 Windows 相关的依赖，还是使用 time.monotonic() 实现
            return time.monotonic()
        else:
            return time.clock_gettime(time.CLOCK_MONOTONIC)
