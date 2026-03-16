# Order Functions And Position Tools

## Use This Reference For

- `insert_order`
- `cancel_order`
- `TargetPosTask`
- `TargetPosScheduler`
- Choosing between manual order control and target-position control

## Table Of Contents

- Manual orders
- Cancel orders
- When to use manual orders
- `TargetPosTask`
- `TargetPosScheduler`
- Advanced helpers beyond the default answer
- Stock limitations

## Manual Orders: `insert_order`

`insert_order()` is the public API for direct order placement.

Key parameters:

- `symbol`
- `direction`: `BUY` or `SELL`
- `offset`: futures only, usually `OPEN`, `CLOSE`, `CLOSETODAY`
- `volume`
- `limit_price`
- `advanced`: `FAK`, `FOK`, or `None`
- `account`: required in multi-account mode

Important behavior:

- the order packet is actually sent on the next `wait_update()`
- stock trading does not use `offset`
- stock orders may omit `limit_price`; `limit_price=None` becomes `price_type="ANY"`

Basic futures example:

```python
from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))
quote = api.get_quote("SHFE.au2504")
order = api.insert_order(
    symbol="SHFE.au2504",
    direction="BUY",
    offset="OPEN",
    volume=1,
    limit_price=quote.ask_price1,
)

while order.status != "FINISHED":
    api.wait_update()
    print(order.status, order.volume_left, order.last_msg)
```

Advanced order modes:

- `advanced="FAK"`: remaining quantity is canceled immediately
- `advanced="FOK"`: all-or-kill
- `limit_price="BEST"` or `"FIVELEVEL"`: only supported on CFFEX

Do not recommend advanced combinations unless the exchange and contract class support them.

## Cancel Orders: `cancel_order`

```python
api.cancel_order(order)
api.wait_update()
```

Rules:

- `cancel_order()` accepts an order object or order id
- the cancel packet is also sent on the next `wait_update()`
- in multi-account mode, pass `account=...` if needed

## When To Use Manual Orders

Prefer manual orders when the user wants:

- explicit price control
- explicit cancellation logic
- partial-fill handling
- exchange-specific order semantics
- custom order chasing

## `TargetPosTask`

Use `TargetPosTask` when the user thinks in target net position, not individual orders.

```python
from tqsdk import TqApi, TqAuth, TargetPosTask

api = TqApi(auth=TqAuth("快期账户", "账户密码"))
target_pos = TargetPosTask(api, "DCE.m2505")
target_pos.set_target_volume(5)

while True:
    api.wait_update()
```

Rules:

- create one `TargetPosTask` per account and symbol
- keep calling `wait_update()` after `set_target_volume()`
- do not mix `TargetPosTask` and manual `insert_order()` on the same symbol
- if you need a different `price`, `offset_priority`, `min_volume`, or `max_volume`, cancel the old task before creating a new one

Useful parameters:

- `price`: `"ACTIVE"`, `"PASSIVE"`, or a custom price function
- `offset_priority`
- `min_volume` and `max_volume` for split execution
- `account` in multi-account mode

Useful lifecycle APIs:

- `target_pos.cancel()`
- `target_pos.is_finished()`

## `TargetPosScheduler`

Use `TargetPosScheduler` when the user wants scheduled target-position execution instead of one immediate target.

It is the public helper for time-table driven execution and works with:

- a custom `time_table`
- `twap_table(...)`
- `vwap_table(...)`

Common import:

```python
from tqsdk.algorithm import twap_table, vwap_table
```

It still depends on continuous `wait_update()` calls and must not be mixed with `TargetPosTask` or manual `insert_order()` for the same workflow.

## Advanced Helpers Beyond The Default Answer

These exist, but should not be the first answer unless the user is already using them:

- `InsertOrderTask`
- `InsertOrderUntilAllTradedTask`
- `tqsdk.algorithm.Twap`

Explain them as advanced or specialized execution helpers, not as the default recommendation.

## Stock Limitations

- Stock trading does not use `offset`
- `TargetPosTask` is not the right answer for stock trading
- Stock order objects are `SecurityOrder`, not `Order`

## Repository Sources

- `tqsdk/api.py`
- `doc/usage/targetpostask.rst`
- `doc/advanced/targetpostask2.rst`
- `doc/advanced/scheduler.rst`
- `tqsdk/lib/target_pos_task.py`
- `tqsdk/lib/target_pos_scheduler.py`
- `tqsdk/algorithm/time_table_generater.py`
- `tqsdk/algorithm/twap.py`
