#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'mayanqiong'


from abc import abstractmethod


class TqRiskRule(object):

    def __init__(self, api, account=None):
        # 记录必要参数， 每个风控规则都需要继承这个基类
        self._api = api
        account = self._api._account._check_valid(account)
        if account is None:
            raise Exception(f"多账户模式下, 需要指定账户实例 account")
        self._account = account
        self._account_key = self._account._account_key

    @abstractmethod
    def _could_insert_order(self, pack) -> (bool, str):  # 是否可以下单
        pass

    @abstractmethod
    def _on_insert_order(self, pack):
        pass


class TqRuleOpenCountsLimit(TqRiskRule):
    """
    风控规则类 - 交易日内开仓次数限制。

    此功能为 TqSdk 专业版提供，如需使用此功能，可以点击 `天勤量化专业版 <https://www.shinnytech.com/tqsdk_professional/>`_ 申请试用或购买
    """

    def __init__(self, api, open_counts_limit, symbol, account=None):
        """
        Args:
            api (TqApi): TqApi 实例

            open_volumes_limit (int): 交易日内开仓手数上限

            symbol (str/list of str): 负责限制的合约代码或合约代码列表.
                * str: 一个合约代码
                * list of str: 合约代码列表

            account  (TqAccount/TqKq/TqSim): [可选] 指定发送下单指令的账户实例, 多账户模式下，该参数必须指定

        Example1::

            from tqsdk import TqApi
            from tqsdk.risk_rule import TqRuleOpenCountsLimit

            api = TqApi(auth=TqAuth("信易账户", "账户密码"))

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

    def _could_insert_order(self, pack) -> {bool, str}:
        if pack['account_key'] == self._account_key:
            symbol = pack["exchange_id"] + "." + pack["instrument_id"]
            if pack["offset"] == "OPEN" and symbol in self.symbol_list:
                if self.data[symbol] + 1 > self.open_counts_limit:
                    return False, f"触发风控规则，合约 {symbol} 开仓到达交易日内开仓次数限制 {self.open_counts_limit}, " \
                                  f"已下单次数 {self.data[symbol]}"
        return True, ""

    def _on_insert_order(self, pack):
        if pack['account_key'] == self._account_key:
            symbol = pack["exchange_id"] + "." + pack["instrument_id"]
            if pack["offset"] == "OPEN" and symbol in self.symbol_list:
                self.data[symbol] += 1


class TqRuleOpenVolumesLimit(TqRiskRule):
    """
    风控规则类 - 交易日内开仓手数限制

    此功能为 TqSdk 专业版提供，如需使用此功能，可以点击 `天勤量化专业版 <https://www.shinnytech.com/tqsdk_professional/>`_ 申请试用或购买
    """

    def __init__(self, api, open_volumes_limit, symbol, account=None):
        """
        Args:
            api (TqApi): TqApi 实例

            open_volumes_limit (int): 交易日内开仓手数上限

            symbol (str/list of str): 负责限制的合约代码或合约代码列表.
                * str: 一个合约代码
                * list of str: 合约代码列表

            account  (TqAccount/TqKq/TqSim): [可选] 指定发送下单指令的账户实例, 多账户模式下，该参数必须指定

        Example1::

            from tqsdk import TqApi
            from tqsdk.risk_rule import TqRuleOpenVolumesLimit

            api = TqApi(auth=TqAuth("信易账户", "账户密码"))

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
            api = TqApi(account=account, auth=TqAuth("信易账户", "账户密码"))

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

    def _could_insert_order(self, pack) -> {bool, str}:
        if pack['account_key'] == self._account_key:
            symbol = pack["exchange_id"] + "." + pack["instrument_id"]
            if pack["offset"] == "OPEN" and symbol in self.symbol_list:
                if self.data[symbol] + pack["volume"] > self.open_volumes_limit:
                    return False, f"触发风控规则，合约 {symbol} 开仓到达交易日内开仓手数限制 {self.open_volumes_limit}, " \
                                  f"已下单手数 {self.data[symbol]}, 即将下单手数 {pack['volume']}"
        return True, ""

    def _on_insert_order(self, pack):
        if pack['account_key'] == self._account_key:
            symbol = pack["exchange_id"] + "." + pack["instrument_id"]
            if pack["offset"] == "OPEN" and symbol in self.symbol_list:
                self.data[symbol] += pack["volume"]


class TqRuleAccOpenVolumesLimit(TqRiskRule):
    """
    风控规则类 - 累计开仓手数限制。

    限制合约开仓手数之和。

    此功能为 TqSdk 专业版提供，如需使用此功能，可以点击 `天勤量化专业版 <https://www.shinnytech.com/tqsdk_professional/>`_ 申请试用或购买

    """

    def __init__(self, api, open_volumes_limit, symbol, account=None):
        """
        Args:
            api (TqApi): TqApi 实例


            open_volumes_limit (int): 交易日内开仓手数之和上限

            symbol (str/list of str): 负责限制的合约代码或合约代码列表.
                * str: 一个合约代码
                * list of str: 合约代码列表

            account  (TqAccount/TqKq/TqSim): [可选] 指定发送下单指令的账户实例, 多账户模式下，该参数必须指定

        Example::

            from tqsdk import TqApi, TqKq, TqRiskRuleError
            from tqsdk.risk_rule import TqRuleAccOpenVolumesLimit

            account = TqKq()
            api = TqApi(account=account, auth=TqAuth("信易账户", "账户密码"))

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

    def _could_insert_order(self, pack) -> {bool, str}:
        symbol = pack["exchange_id"] + "." + pack["instrument_id"]
        if pack['account_key'] == self._account_key and symbol in self.symbol_list:  # 当前账户下单
            if pack["offset"] == "OPEN" and self.open_volumes + pack['volume'] > self.open_volumes_limit:
                return False, f"触发风控规则，所有合约日内合约开仓不超过 {self.open_volumes_limit} 手, 已下单手数 {self.open_volumes}"
        return True, ""

    def _on_insert_order(self, pack):
        symbol = pack["exchange_id"] + "." + pack["instrument_id"]
        if pack['account_key'] == self._account_key and symbol in self.symbol_list:  # 当前账户下单
            if pack["offset"] == "OPEN":  # 开仓单把手数累加
                self.open_volumes += pack['volume']
