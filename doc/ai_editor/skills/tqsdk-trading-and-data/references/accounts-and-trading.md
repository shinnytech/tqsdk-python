# Accounts And Trading

## Use This Reference For

- Reading funds, positions, orders, and trades
- Futures versus stock account objects
- Multi-account getter patterns

## Table Of Contents

- Core getters
- Futures and stock objects
- Funds, positions, orders, trades
- Common field subsets
- Multi-account patterns

Read [account-type-matrix.md](account-type-matrix.md) first if the user is still choosing an account class.
Read [object-fields.md](object-fields.md) when the user asks what a field means.
Read [order-functions-and-position-tools.md](order-functions-and-position-tools.md) for `insert_order`, `cancel_order`, and `TargetPosTask`.

## Core Getters

- `api.get_account(account=None)`
- `api.get_position(symbol=None, account=None)`
- `api.get_order(order_id=None, account=None)`
- `api.get_trade(trade_id=None, account=None)`

These all return live references that refresh during `wait_update()`.

## Futures And Stock Objects

Futures-like accounts return:

- `Account`
- `Position`
- `Order`
- `Trade`

Stock-like accounts return:

- `SecurityAccount`
- `SecurityPosition`
- `SecurityOrder`
- `SecurityTrade`

Do not explain futures-only fields such as `offset`, `margin`, or `pos_long_today` on stock objects.

## Funds, Positions, Orders, Trades

Basic pattern:

```python
from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))
account = api.get_account()
position = api.get_position("DCE.m2505")
orders = api.get_order()
trades = api.get_trade()

while True:
    api.wait_update()
    if api.is_changing(account, "available"):
        print("available", account.available)
    if api.is_changing(position, ["pos_long", "pos_short", "float_profit"]):
        print(position.pos_long, position.pos_short, position.float_profit)
```

For generic examples, `TqApi(auth=...)` is enough and defaults to a local `TqSim()` account.
Switch to `TqKq()`, `TqAccount(...)`, or another explicit account class only when the user needs that exact account mode.

Important collection behavior:

- `get_order()` without `order_id` returns a dict-like collection keyed by order id
- `get_trade()` without `trade_id` returns a dict-like collection keyed by trade id
- `order.trade_records` is usually a better answer than dumping every trade in the account
- `position.orders` returns related ALIVE orders for that position

## Common Field Subsets

Use the smallest relevant subset when answering users.

Account:

- futures: `balance`, `available`, `margin`, `float_profit`, `position_profit`, `risk_ratio`
- stock: `asset`, `available`, `drawable`, `market_value`, `hold_profit`, `profit_today`

Position:

- futures: `pos`, `pos_long`, `pos_short`, `pos_long_today`, `pos_short_today`, `float_profit`, `position_profit`
- stock: `volume`, `volume_his`, `last_price`, `market_value`, `hold_profit`, `profit_today`

Order:

- futures: `order_id`, `status`, `direction`, `offset`, `volume_orign`, `volume_left`, `limit_price`, `last_msg`
- stock: `order_id`, `status`, `direction`, `volume_orign`, `volume_left`, `limit_price`, `last_msg`

Trade:

- futures: `trade_id`, `order_id`, `price`, `volume`, `direction`, `offset`, `trade_date_time`
- stock: `trade_id`, `order_id`, `price`, `volume`, `balance`, `fee`, `direction`, `trade_date_time`

## Multi-Account Patterns

API-based pattern:

```python
from tqsdk import TqApi, TqAuth, TqAccount, TqKq, TqMultiAccount

real_acc = TqAccount("H海通期货", "123456", "123456")
sim_acc = TqKq()

api = TqApi(TqMultiAccount([real_acc, sim_acc]), auth=TqAuth("快期账户", "账户密码"))
account_info = api.get_account(account=sim_acc)
position = api.get_position("DCE.m2505", account=sim_acc)
orders = api.get_order(account=sim_acc)
trades = api.get_trade(account=sim_acc)
```

Account-object pattern:

```python
account_info = sim_acc.get_account()
position = sim_acc.get_position("DCE.m2505")
orders = sim_acc.get_order()
trades = sim_acc.get_trade()
```

## Repository Sources

- `tqsdk/api.py`
- `tqsdk/tradeable/mixin.py`
- `tqsdk/demo/tutorial/t40.py`
- `tqsdk/demo/download_orders.py`
- `tqsdk/demo/multiaccount.py`
