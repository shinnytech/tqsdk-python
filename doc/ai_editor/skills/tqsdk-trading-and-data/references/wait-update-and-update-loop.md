# wait_update And The Update Loop

## Use This Reference For

- `wait_update()` and `is_changing()` explanations
- Why data or orders look stale
- `deadline` usage
- Async update notifications
- Jupyter and backtest caveats

## Table Of Contents

- Mental model
- Practical rules
- Typical patterns
- `deadline` guidance
- Backtest-specific notes
- Async pattern
- Jupyter caveats
- Common explanations to reuse

## Mental Model

`wait_update()` is the center of TqSdk's runtime model.

Each call can do all of the following:

- send pending subscription or trading packets
- let background tasks run
- receive one business-data update and merge it into in-memory objects
- block until there is an update, unless `deadline` expires

This is why `get_quote`, `get_kline_serial`, `get_account`, `get_position`, `get_order`, `get_trade`, `insert_order`, `cancel_order`, `TargetPosTask`, and `TargetPosScheduler` all depend on later `wait_update()` calls.

## Practical Rules

1. Call `get_*` once, keep the returned reference, then loop on `api.wait_update()`.
2. Use `api.is_changing(obj)` or `api.is_changing(obj, field)` to gate work.
3. Do not recreate quotes, K-line serials, or account objects inside the loop.
4. Do not call `sleep()` to "wait for TqSdk". If you need progress, keep the update loop running.
5. If you need a timeout, use `wait_update(deadline=...)`.

## Typical Patterns

Streaming quote:

```python
from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))
quote = api.get_quote("SHFE.au2504")

while True:
    if not api.wait_update():
        continue
    if api.is_changing(quote, ["last_price", "ask_price1", "bid_price1"]):
        print(quote.datetime, quote.last_price, quote.ask_price1, quote.bid_price1)
```

New K-line only:

```python
klines = api.get_kline_serial("DCE.i2505", 60, data_length=200)

while True:
    api.wait_update()
    if api.is_changing(klines.iloc[-1], "datetime"):
        print("new bar", klines.iloc[-1].datetime, klines.iloc[-1].close)
```

Order state tracking:

```python
order = api.insert_order("DCE.m2505", "BUY", offset="OPEN", volume=1)

while order.status != "FINISHED":
    api.wait_update()
    if api.is_changing(order, ["status", "volume_left", "last_msg"]):
        print(order.status, order.volume_left, order.last_msg)
```

## `deadline` Guidance

Use `deadline` when the user wants to avoid indefinite blocking, especially in notebooks or interactive tools.

```python
import time

deadline = time.time() + 5
updated = api.wait_update(deadline=deadline)
```

- `True`: some business data changed
- `False`: the deadline arrived before a new update

Do not recommend tiny deadlines in busy loops unless the user really needs polling behavior.

## Backtest-Specific Notes

In backtest mode, `wait_update()` does not behave exactly like live mode.

- One call may update order state without advancing quote time.
- The next call may advance market time.
- Multiple subscribed series advance in time order, not "all at once".

Use this reference together with [simulation-and-backtest.md](simulation-and-backtest.md) when the user is confused by backtest timing.

## Async Pattern

If the user is already writing async TqSdk code, prefer `register_update_notify()` instead of inventing callbacks.

```python
async with api.register_update_notify(quote) as update_chan:
    async for _ in update_chan:
        print(quote.last_price)
```

This still depends on the outer program continuing to drive the API.

## Jupyter Caveats

- Do not recommend trading workflows in Jupyter unless the user accepts the limitations.
- Prefer synchronous examples there.
- Recommend `deadline` to avoid long blocking calls.

## Common Explanations To Reuse

- "The object is a live reference, not a one-time copy."
- "`insert_order()` and `cancel_order()` queue the request. The actual packet is sent on the next `wait_update()`."
- "`TargetPosTask` only works while the update loop keeps running."
- "If you never call `wait_update()` again, data stops moving and background tasks stop acting."

## Repository Sources

- `doc/usage/framework.rst`
- `doc/usage/backtest.rst`
- `doc/usage/jupyter.rst`
- `doc/advanced/for_vnpy_user.rst`
- `tqsdk/api.py`
