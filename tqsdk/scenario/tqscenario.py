#!usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'chenli'

from typing import Optional, Union

from tqsdk.api import TqApi
from tqsdk.diff import _simple_merge_diff
from tqsdk.entity import Entity
from tqsdk.objs import Account, Order, Position
from tqsdk.tradeable import TqSim, TqAccount, TqKq
from tqsdk.tradeable.sim.trade_future import SimTrade
from tqsdk.utils import _generate_uuid


class TqScenario(object):
    """
    天勤场景试算类

    该类通过创建内部 SimTrade 实例, 将用户当前账户的持仓/资金信息导入到一个独立的试算截面中,
    再通过同步接口对这个试算截面进行下单、调整保证金率、查询账户等操作, 用于评估不同交易动作对保证金占用和风险度的影响。

    常用于以下场景:

    1. 评估当前持仓下还能开多少手
    2. 评估减仓后可释放多少保证金
    3. 评估多合约组合开仓/减仓后的保证金与风险度
    4. 假设某个期货品种保证金率调整后重新测算账户风险度

    当前版本有如下约定：
    
    1. 仅支持期货合约
    2. 仅支持单账户试算
    3. 所有接口均为同步函数，不支持异步，建议在 wait_update 主循环外完成试算，不影响实盘业务数据更新
    4. 用户执行下单操作，以用户传入的价格立即撮合成交，不存在部分成交的情况
    5. 获取实盘保证金率时，如果失败，降级到使用 Quote 中的保证金信息
    6. ctp 保证金率查询有流控，大概 1 秒一次一个合约的查询请求
    7. 导入实盘的持仓区分今昨仓，对于上期所或者上期能源，平仓时注意区分平今/平昨
    """

    def __init__(self, api: TqApi, account: Optional[Union[TqSim, TqAccount, TqKq]] = None,
                 positions: Optional[Union[Position, Entity]] = None, init_balance: float = 10000000.0):
        """
        Args:
            api (TqApi): [必填] TqApi 实例

            account (Optional[Union[TqSim, TqAccount, TqKq]]): [可选] 保证金率来源账户。
                不传时默认创建 :py:class:`~tqsdk.tradeable.TqSim` 模拟账户, 使用 Quote 中的保证金信息;
                传入实盘账户时, 会按该账户对应的保证金率进行试算

            positions (Optional[Union[Position, Entity]]): [可选] 初始持仓截面。
                可以传入 :py:meth:`~tqsdk.api.TqApi.get_position` 返回的全部持仓对象,
                也可以传入某一个合约的持仓对象; 不传时表示从空仓开始试算

            init_balance (float): [可选] 初始账户资金, 默认为一千万。
                当传入 positions 时, 会以该资金和持仓共同构建试算账户截面;
                不传 positions 时, 可用于模拟空仓起步后的资金规模

        Example 1::

            from tqsdk import TqApi, TqAccount, TqAuth
            from tqsdk.scenario import TqScenario

            SYMBOL = "SHFE.rb2611"

            account = TqAccount("期货公司", "账号", "密码")
            api = TqApi(account=account, auth=TqAuth("快期账户", "账户密码"))

            quote = api.get_quote(SYMBOL)

            with TqScenario(api, account=account, init_balance=1000000) as s:
                s.scenario_insert_order(SYMBOL, "BUY", "OPEN", 1, quote.last_price)
                margin = s.scenario_get_account().margin

            print(f"场景1: {SYMBOL} 按 {quote.last_price} 价格开 1 手, 实盘保证金约为 {margin:.2f} 元")

        Example 2::

            from tqsdk import TqApi, TqAccount, TqAuth
            from tqsdk.scenario import TqScenario

            SYMBOL = "SHFE.rb2611"
            NEW_MARGIN_RATE = 0.15

            account = TqAccount("期货公司", "账号", "密码")
            api = TqApi(account=account, auth=TqAuth("快期账户", "账户密码"))

            positions = api.get_position()

            with TqScenario(api, account=account, positions=positions) as s:
                base_acc = s.scenario_get_account()
                s.scenario_set_margin_rate(SYMBOL, NEW_MARGIN_RATE)
                acc = s.scenario_get_account()

            print(f"场景2: 将 {SYMBOL} 保证金率调整为 {NEW_MARGIN_RATE:.0%}")
            print(f"  保证金: {base_acc.margin:.2f} -> {acc.margin:.2f}")
            print(f"  风险度: {base_acc.risk_ratio:.4f} -> {acc.risk_ratio:.4f}")

        Example 3::

            from tqsdk import TqApi, TqAccount, TqAuth
            from tqsdk.scenario import TqScenario

            SYMBOL = "SHFE.rb2611"
            BUDGET = 200000

            account = TqAccount("期货公司", "账号", "密码")
            api = TqApi(account=account, auth=TqAuth("快期账户", "账户密码"))

            quote = api.get_quote(SYMBOL)
            positions = api.get_position()

            with TqScenario(api, account=account, positions=positions) as s:
                base_margin = s.scenario_get_account().margin
                volume = 0
                while True:
                    order = s.scenario_insert_order(SYMBOL, "BUY", "OPEN", 1, quote.last_price)
                    if order.status == "FINISHED" and order.volume_left > 0:
                        print(f"开仓失败: {order.last_msg}")
                        break
                    volume += 1
                    added = s.scenario_get_account().margin - base_margin
                    if added > BUDGET:
                        order = s.scenario_insert_order(SYMBOL, "SELL", "CLOSETODAY", 1, quote.last_price)
                        if order.status == "FINISHED" and order.volume_left > 0:
                            print(f"平仓失败: {order.last_msg}")
                            break
                        volume -= 1
                        break
                acc = s.scenario_get_account()

            print(f"场景3: {BUDGET/10000:.0f} 万预算下 {SYMBOL} 最多可开 {volume} 手")
            print(f"  保证金 {base_margin:.2f} -> {acc.margin:.2f} (增加 {acc.margin - base_margin:.2f})")
            print(f"  风险度={acc.risk_ratio:.4f}")

        Example 4::

            from tqsdk import TqApi, TqAccount, TqAuth
            from tqsdk.scenario import TqScenario

            SYMBOL = "SHFE.rb2611"
            TARGET_SAVING = 200000

            account = TqAccount("期货公司", "账号", "密码")
            api = TqApi(account=account, auth=TqAuth("快期账户", "账户密码"))

            quote = api.get_quote(SYMBOL)
            positions = api.get_position()

            with TqScenario(api, account=account, positions=positions) as s:
                base_margin = s.scenario_get_account().margin
                volume = 0
                while True:
                    order = s.scenario_insert_order(SYMBOL, "SELL", "CLOSE", 1, quote.last_price)
                    if order.status == "FINISHED" and order.volume_left > 0:
                        print(f"平仓失败: {order.last_msg}")
                        break
                    volume += 1
                    saved = base_margin - s.scenario_get_account().margin
                    if saved >= TARGET_SAVING:
                        break
                acc = s.scenario_get_account()
                saved = base_margin - acc.margin

            print(f"场景4: 平仓 {volume} 手 {SYMBOL} 可节约 {saved:.2f} 元保证金")
            print(f"  保证金 {base_margin:.2f} -> {acc.margin:.2f}")
            print(f"  风险度={acc.risk_ratio:.4f}")

        Example 5::

            from tqsdk import TqApi, TqAccount, TqAuth
            from tqsdk.scenario import TqScenario

            SYMBOL_A = "SHFE.rb2611"
            SYMBOL_B = "DCE.b2606"
            VOL_A, VOL_B = 10, 20

            account = TqAccount("期货公司", "账号", "密码")
            api = TqApi(account=account, auth=TqAuth("快期账户", "账户密码"))

            quote_a = api.get_quote(SYMBOL_A)
            quote_b = api.get_quote(SYMBOL_B)
            positions = api.get_position()

            with TqScenario(api, account=account, positions=positions) as s:
                base_acc = s.scenario_get_account()
                order_a = s.scenario_insert_order(SYMBOL_A, "BUY", "OPEN", VOL_A, quote_a.last_price)
                order_b = s.scenario_insert_order(SYMBOL_B, "BUY", "OPEN", VOL_B, quote_b.last_price)
                if order_a.status == "FINISHED" and order_a.volume_left > 0:
                    print(f"A 开仓失败: {order_a.last_msg}")
                if order_b.status == "FINISHED" and order_b.volume_left > 0:
                    print(f"B 开仓失败: {order_b.last_msg}")
                acc = s.scenario_get_account()

            print(f"场景5: 开仓 {VOL_A}手{SYMBOL_A} + {VOL_B}手{SYMBOL_B}")
            print(f"  保证金: {base_acc.margin:.2f} -> {acc.margin:.2f} (增加 {acc.margin - base_acc.margin:.2f})")
            print(f"  风险度: {base_acc.risk_ratio:.4f} -> {acc.risk_ratio:.4f}")

        Example 6::

            from tqsdk import TqApi, TqAccount, TqAuth
            from tqsdk.scenario import TqScenario

            SYMBOL_A = "SHFE.rb2611"
            SYMBOL_B = "DCE.b2606"
            VOL_A, VOL_B = 10, 20
            INIT_BALANCE = 1000000

            account = TqAccount("期货公司", "账号", "密码")
            api = TqApi(account=account, auth=TqAuth("快期账户", "账户密码"))

            quote_a = api.get_quote(SYMBOL_A)
            quote_b = api.get_quote(SYMBOL_B)

            with TqScenario(api, account=account, init_balance=INIT_BALANCE) as s:
                s.scenario_insert_order(SYMBOL_A, "BUY", "OPEN", VOL_A, quote_a.last_price)
                s.scenario_insert_order(SYMBOL_B, "BUY", "OPEN", VOL_B, quote_b.last_price)
                acc = s.scenario_get_account()

            print(f"场景6: 空仓起步, 开仓 {VOL_A}手{SYMBOL_A} + {VOL_B}手{SYMBOL_B}")
            print(f"  初始资金: {INIT_BALANCE:.2f}")
            print(f"  保证金: {acc.margin:.2f}")
            print(f"  风险度: {acc.risk_ratio:.4f}")

        Example 7::

            from tqsdk import TqApi, TqAccount, TqAuth
            from tqsdk.scenario import TqScenario

            SYMBOL_A = "SHFE.rb2611"
            SYMBOL_B = "DCE.b2606"
            VOL_A, VOL_B = 10, 20

            account = TqAccount("期货公司", "账号", "密码")
            api = TqApi(account=account, auth=TqAuth("快期账户", "账户密码"))

            quote_a = api.get_quote(SYMBOL_A)
            quote_b = api.get_quote(SYMBOL_B)
            positions = api.get_position()

            with TqScenario(api, account=account, positions=positions) as s:
                base_acc = s.scenario_get_account()
                order_a = s.scenario_insert_order(SYMBOL_A, "SELL", "CLOSE", VOL_A, quote_a.last_price)
                order_b = s.scenario_insert_order(SYMBOL_B, "SELL", "CLOSE", VOL_B, quote_b.last_price)
                if order_a.status == "FINISHED" and order_a.volume_left > 0:
                    print(f"A 平仓失败: {order_a.last_msg}")
                if order_b.status == "FINISHED" and order_b.volume_left > 0:
                    print(f"B 平仓失败: {order_b.last_msg}")
                acc = s.scenario_get_account()

            print(f"场景7: 减仓 {VOL_A}手{SYMBOL_A} + {VOL_B}手{SYMBOL_B}")
            print(f"  保证金: {base_acc.margin:.2f} -> {acc.margin:.2f} (减少 {base_acc.margin - acc.margin:.2f})")
            print(f"  风险度: {base_acc.risk_ratio:.4f} -> {acc.risk_ratio:.4f}")

        Example 8::

            from tqsdk import TqApi, TqAccount, TqAuth
            from tqsdk.scenario import TqScenario

            EXTRA = 100000

            account = TqAccount("期货公司", "账号", "密码")
            api = TqApi(account=account, auth=TqAuth("快期账户", "账户密码"))

            positions = api.get_position()
            balance = api.get_account().balance
            risk_ratio = api.get_account().risk_ratio

            with TqScenario(api, account=account, positions=positions, init_balance=balance + EXTRA) as s:
                acc = s.scenario_get_account()

            print(f"场景8: 当前持仓不变，权益增加 {EXTRA/10000:.0f} 万")
            print(f"  风险度: {risk_ratio:.4f} -> {acc.risk_ratio:.4f}")
        """
        self._api = api
        self._account = account if account is not None else TqSim()
        self._account_key = str(id(self))
        self._account_id = "SCENARIO"
        self._quotes = {}

        self._sim_trade = SimTrade(
            account_key=self._account_key,
            account_id=self._account_id,
            init_balance=init_balance,
            get_trade_timestamp=lambda: 0,
            is_in_trading_time=lambda quote: True,
        )
        self._trade = self._sim_trade.init_snapshot()
        if positions is not None:
            self._import_positions(positions)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def _import_positions(self, positions):
        """从 api 获取的持仓对象中导入初始持仓到 SimTrade"""
        if isinstance(positions, Position):
            symbol = f"{positions.exchange_id}.{positions.instrument_id}"
            self._import_single_position(symbol, positions)
        elif isinstance(positions, Entity):
            for symbol, pos in positions.items():
                self._import_single_position(symbol, pos)

    def _import_single_position(self, symbol: str, pos):
        """将单个持仓合约导入 SimTrade"""
        pos_long_his = pos.get('pos_long_his', 0)
        pos_long_today = pos.get('pos_long_today', 0)
        pos_short_his = pos.get('pos_short_his', 0)
        pos_short_today = pos.get('pos_short_today', 0)
        pos_price_long = pos.get('position_price_long', float('nan'))
        pos_price_short = pos.get('position_price_short', float('nan'))
        if pos_long_his == 0 and pos_long_today == 0 and pos_short_his == 0 and pos_short_today == 0:
            return
        quote = self._ensure_quote(symbol)
        if quote.get("ins_class") != "FUTURE":
            return
        if pos_long_his > 0 and pos_price_long == pos_price_long:
            order_id_long_his = self._do_insert_order(symbol, "BUY", "OPEN", pos_long_his, pos_price_long)
            self._check_import_position(order_id_long_his, symbol, "多头", "老仓")
        if pos_short_his > 0 and pos_price_short == pos_price_short:
            order_id_short_his = self._do_insert_order(symbol, "SELL", "OPEN", pos_short_his, pos_price_short)
            self._check_import_position(order_id_short_his, symbol, "空头", "老仓")
        if (pos_long_his > 0 and pos_price_long == pos_price_long) or (pos_short_his > 0 and pos_price_short == pos_price_short):
            diffs, _, _ = self._sim_trade.settle()
            self._handle_diffs(diffs)
        if pos_long_today > 0 and pos_price_long == pos_price_long:
            order_id_long_today = self._do_insert_order(symbol, "BUY", "OPEN", pos_long_today, pos_price_long)
            self._check_import_position(order_id_long_today, symbol, "多头", "今仓")
        if pos_short_today > 0 and pos_price_short == pos_price_short:
            order_id_short_today = self._do_insert_order(symbol, "SELL", "OPEN", pos_short_today, pos_price_short)
            self._check_import_position(order_id_short_today, symbol, "空头", "今仓")

    def _check_import_position(self, order_id: str, symbol: str, direction: str, his_today: str):
        order = self._trade.get("trade", {}).get(self._account_key, {}).get("orders", {}).get(order_id, {})
        if order.get("status", "FINISHED") != "FINISHED" or order.get("volume_left", 0) > 0:
            self._api._print(f"导入 {symbol} {his_today}{direction}失败: {order.get('last_msg')}", "WARNING")

    def _ensure_quote(self, symbol: str) -> dict:
        """确保合约行情和保证金率已发送给 SimTrade, 返回 quote dict"""
        if symbol not in self._quotes:
            quote = self._api.get_quote(symbol)
            if quote.get("ins_class") != "FUTURE":
                return quote.copy()
            self._quotes[symbol] = quote.copy()
        diffs, _ = self._sim_trade.update_quotes(symbol, {"quotes": {symbol: self._quotes[symbol]}})
        self._handle_diffs(diffs)
        return self._quotes[symbol]

    def _do_insert_order(self, symbol: str, direction: str, offset: str, volume: int, price: float):
        """内部下单, 更新行情价格后调用 SimTrade.insert_order"""
        exchange_id, instrument_id = symbol.split(".", 1)
        order_id = _generate_uuid("PYSDK_scenario_insert")
        pack = {
            "aid": "insert_order",
            "user_id": self._account_id,
            "order_id": order_id,
            "exchange_id": exchange_id,
            "instrument_id": instrument_id,
            "direction": direction,
            "offset": offset,
            "volume": volume,
            "price_type": "LIMIT",
            "limit_price": price,
            "time_condition": "GFD",
            "volume_condition": "ANY",
        }

        if "margin_rate" not in self._quotes[symbol]:
            rate = self._api._get_margin_rate(quote=self._quotes[symbol], direction="BUY", account=self._account)
            self._quotes[symbol]["margin_rate"] = rate

        self._quotes[symbol]["margin"] = self._quotes[symbol].get("margin_rate") * price * self._quotes[symbol].get("volume_multiple")
        self._quotes[symbol]["last_price"] = price
        self._quotes[symbol]["ask_price1"] = price
        self._quotes[symbol]["bid_price1"] = price

        diffs, _ = self._sim_trade.update_quotes(symbol, {"quotes": {symbol: self._quotes[symbol]}})
        self._handle_diffs(diffs)
        diffs, _ = self._sim_trade.insert_order(symbol, pack)
        self._handle_diffs(diffs)
        return order_id

    def _handle_diffs(self, diffs):
        """将 SimTrade 返回的 diffs 合并到本地数据截面"""
        for diff in diffs:
            _simple_merge_diff(self._trade, diff)

    def scenario_set_margin_rate(self, symbol: str, margin_rate: float = float('nan')):
        """
        设置指定合约的保证金率。

        调用后会立即更新试算截面中的该合约保证金, 并同步刷新账户保证金占用与风险度。
        常用于模拟交易所或期货公司调整保证金率后的风险变化。

        Args:
            symbol (str): 合约代码, 格式为 交易所代码.合约代码, 例如 "SHFE.rb2611"

            margin_rate (float): 保证金率, 例如 0.12 表示 12%

        """
        if margin_rate != margin_rate:
            raise Exception("保证金率不可以设置为 nan")
        quote = self._ensure_quote(symbol)
        if quote.get("ins_class") != "FUTURE":
            raise Exception(f"场景试算目前只支持期货合约(FUTURE)，{symbol} 的合约类型是 {quote.get('ins_class')}")
        self._quotes[symbol]["margin_rate"] = margin_rate
        self._quotes[symbol]["margin"] = margin_rate * self._quotes[symbol].get("pre_settlement") * self._quotes[symbol].get("volume_multiple")
        diffs, _ = self._sim_trade.update_quotes(symbol, {"quotes": {symbol: self._quotes[symbol]}})
        self._handle_diffs(diffs)

    def scenario_insert_order(self, symbol: str, direction: str, offset: str, volume: int,
                              limit_price: float) -> Order:
        """
        场景试算下单。

        该接口会以传入的价格立即撮合成交, 并同步更新试算账户中的持仓、保证金占用和风险度。
        可以在同一个 TqScenario 对象中连续调用, 线性模拟一组交易动作的累计影响。

        Args:
            symbol (str): 合约代码, 格式为 交易所代码.合约代码, 例如 "SHFE.cu2501"

            direction (str): "BUY" 或 "SELL"

            offset (str): "OPEN", "CLOSE" 或 "CLOSETODAY" \
                (上期所和上期能源分平今/平昨, 平今用 "CLOSETODAY", 平昨用 "CLOSE"; 其他交易所直接用 "CLOSE")

            volume (int): 下单手数, 必须为正整数

            limit_price (float): 下单价格, 以该价格立即撮合成交

        Returns:
            :py:class:`~tqsdk.objs.Order`: 委托单对象, 仅包含以下字段:

                * status: "ALIVE" / "FINISHED"
                * volume_left: 剩余未成交手数, 0 表示全部成交
                * last_msg: 结果描述 (失败原因 / 成功提示)

        """
        if direction not in ("BUY", "SELL"):
            raise Exception("下单方向(direction) %s 错误, 请检查 direction 参数是否填写正确" % direction)
        if offset not in ("OPEN", "CLOSE", "CLOSETODAY"):
            raise Exception("开平方向(offset) %s 错误, 请检查 offset 参数是否填写正确" % offset)
        volume = int(volume)
        if volume <= 0:
            raise Exception("下单数量(volume) %s 错误, 请检查 volume 是否填写正确" % volume)
        limit_price = float(limit_price)
        if limit_price != limit_price:
            raise Exception(f"limit_price 参数不支持设置为 nan。")
        quote = self._ensure_quote(symbol)
        if quote.get("ins_class") != "FUTURE":
            raise Exception(f"场景试算目前只支持期货合约(FUTURE)，{symbol} 的合约类型是 {quote.get('ins_class')}")
        order_id = self._do_insert_order(symbol, direction, offset, volume, limit_price)
        order_data = self._trade.get("trade", {}).get(self._account_key, {}).get("orders", {}).get(order_id, {})
        result = Order(self._api)
        result.status = order_data.get("status", "FINISHED")
        result.volume_left = order_data.get("volume_left", 0)
        result.last_msg = order_data.get("last_msg", "")
        _keep = {"status", "volume_left", "last_msg"}
        for key in [k for k in result.__dict__ if not k.startswith("_") and k not in _keep]:
            del result.__dict__[key]
        return result

    def scenario_get_account(self) -> Account:
        """
        获取当前试算账户信息。

        返回值仅保证金和风险度两个与场景试算直接相关的字段, 适合在每次调用
        :py:meth:`~tqsdk.scenario.tqscenario.TqScenario.scenario_insert_order` 或
        :py:meth:`~tqsdk.scenario.tqscenario.TqScenario.scenario_set_margin_rate` 后立即读取结果。

        Returns:
            :py:class:`~tqsdk.objs.Account`: 账户对象, 仅包含以下字段:

                * margin: 保证金占用
                * risk_ratio: 风险度

        """
        account_data = self._trade.get("trade", {}).get(self._account_key, {}).get("accounts", {}).get("CNY", {})
        result = Account(self._api)
        result.margin = account_data.get("margin", 0.0)
        result.risk_ratio = account_data.get("risk_ratio", 0.0)
        _keep = {"margin", "risk_ratio"}
        for key in [k for k in result.__dict__ if not k.startswith("_") and k not in _keep]:
            del result.__dict__[key]
        return result