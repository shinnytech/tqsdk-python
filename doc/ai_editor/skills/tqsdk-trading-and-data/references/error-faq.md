# Error FAQ

## Use This Reference For

- Common TqSdk error messages
- "Why is nothing updating?"
- "Why is my order or `TargetPosTask` not moving?"
- Multi-account mistakes
- Stock versus futures mistakes

## Table Of Contents

- No data, `NaN`, or empty fields
- `insert_order()` or `cancel_order()` does nothing
- `TargetPosTask` does not act
- Multi-account errors
- `offset` errors
- Stock and futures mixed up
- `wait_update()` blocks too long
- Backtest behavior looks wrong
- `DataDownloader` errors
- "未初始化 TqApi"
- Named exception classes
- Error triage order

## No Data, `NaN`, Or Empty Fields

Typical cause:

- the user created the object but did not keep calling `wait_update()`
- the first data packet has not arrived yet
- the symbol is expired or not the one they meant

Check:

1. Is the code still calling `api.wait_update()`?
2. Is `quote.datetime` still empty?
3. Did the user hardcode an expired contract?

## `insert_order()` Or `cancel_order()` "Does Nothing"

Typical cause:

- the user called the API but never called `wait_update()` afterward

Reuse this explanation:

- "`insert_order()` and `cancel_order()` queue the request. The actual packet is sent on the next `wait_update()`."

## `TargetPosTask` Does Not Act

Typical causes:

- no `wait_update()` after `set_target_volume()`
- the user mixed `TargetPosTask` with manual `insert_order()` on the same symbol
- the user created another `TargetPosTask` for the same account and symbol with different parameters
- the task was canceled or already finished

Relevant messages:

- "已经结束的 TargetPosTask 实例不可以再设置手数。"
- "您试图用不同的 ... 参数创建两个 ... 调仓任务"

## Multi-Account Error: "需要指定账户实例 account"

Typical cause:

- the API was created with `TqMultiAccount`, but `account=` was omitted

Fix:

- pass `account=` to account-sensitive APIs
- or switch to `account_obj.get_account()`, `account_obj.get_position()`, `account_obj.get_order()`, `account_obj.get_trade()`

## `offset` Errors

Typical causes:

- futures code used an invalid `offset`
- stock code wrongly set `offset`

Fix:

- futures: use `OPEN`, `CLOSE`, or `CLOSETODAY`
- stock: do not pass `offset`

## Stock And Futures Mixed Up

Typical symptoms:

- using futures fields on stock objects
- expecting `TargetPosTask` to work for stock trading
- expecting stock orders to accept futures-style `offset`

Fix:

- determine whether the account is futures-like or stock-like first
- use `SecurityAccount`, `SecurityPosition`, `SecurityOrder`, `SecurityTrade` semantics for stock

## `wait_update()` Blocks Too Long

Typical cause:

- the user expects polling behavior from a blocking update loop
- the code is running in Jupyter and hangs waiting for updates

Fix:

- use `deadline=...` when the user truly needs a timeout
- in Jupyter, prefer simple synchronous examples and explicitly mention the limitation

## Backtest Behavior Looks Wrong

Typical confusion:

- one `wait_update()` updates only order state
- the next `wait_update()` advances time
- multiple series advance in timestamp order

Fix:

- explain that backtest progression differs from live mode
- point to subscribed series and `is_changing(...)` checks

## `DataDownloader` Errors

Common cases:

- account does not have permission for historical download
- tick download attempted with multiple symbols
- unsupported `adj_type`
- unsupported output argument types

If the user asks about a download error, check `symbol_list`, `dur_sec`, `adj_type`, and whether the account has download permission.

## "未初始化 TqApi"

Typical cause:

- the user called account-object getters before wiring the account into `TqApi`

Fix:

- create `api = TqApi(...)` first
- only then call `account.get_account()` or similar account-object getters

## Named Exception Classes

These exception names are worth recognizing explicitly:

- Top-level exports from `tqsdk.__init__`: `BacktestFinished`, `TqTimeoutError`, `TqBacktestPermissionError`, `TqRiskRuleError`
- `TqContextManagerError`: context-manager misuse; import it from `tqsdk.exceptions` if the user is already using that name directly

If the user reports one of these names directly, prefer explaining the meaning of the exception before proposing code changes.

## Error Triage Order

When debugging, check in this order:

1. wrong account type
2. missing `wait_update()`
3. futures versus stock mismatch
4. missing `account=` in multi-account mode
5. wrong symbol or expired symbol
6. wrong `offset`, `advanced`, or order-price mode
7. unsupported target-position workflow

## Repository Sources

- `tqsdk/api.py`
- `tqsdk/lib/utils.py`
- `tqsdk/lib/target_pos_task.py`
- `tqsdk/lib/target_pos_scheduler.py`
- `tqsdk/tools/downloader.py`
- `tqsdk/tradeable/mixin.py`
- `tqsdk/exceptions.py`
- `doc/usage/framework.rst`
- `doc/usage/backtest.rst`
- `doc/usage/jupyter.rst`
