# Example Map

Use this file when you need a concrete repository example or doc page before writing or revising an answer.

## If The User Asks About `wait_update`

- `doc/usage/framework.rst`
  - core update-loop explanation
- `doc/advanced/for_vnpy_user.rst`
  - practical `wait_update` and `is_changing` framing for strategy users
- `doc/usage/jupyter.rst`
  - notebook caveats and `deadline`

## If The User Asks About Market Data

- `tqsdk/demo/tutorial/t10.py`
  - minimal quote read
- `tqsdk/demo/tutorial/t30.py`
  - quote, tick, and K-line updates with `is_changing`
- `tqsdk/demo/tutorial/underlying_symbol.py`
  - main-contract `underlying_symbol`
- `doc/usage/mddatas.rst`
  - broader market-data usage patterns

## If The User Asks About Funds, Positions, Orders, Or Trades

- `tqsdk/demo/tutorial/t40.py`
  - account, position, and order state in the update loop
- `tqsdk/demo/download_orders.py`
  - export orders and trades
- `tqsdk/tradeable/mixin.py`
  - account-object getter patterns

## If The User Asks About Manual Orders

- `tqsdk/demo/tutorial/t41.py`
  - open then close with manual orders
- `tqsdk/demo/tutorial/t60.py`
  - strategy using `insert_order`
- `tqsdk/api.py`
  - exact `insert_order` and `cancel_order` semantics

## If The User Asks About `TargetPosTask` Or Scheduled Execution

- `tqsdk/demo/tutorial/t70.py`
  - basic `TargetPosTask` strategy
- `doc/usage/targetpostask.rst`
  - `TargetPosTask` rules and caveats
- `doc/advanced/targetpostask2.rst`
  - `cancel()` and `is_finished()`
- `doc/advanced/scheduler.rst`
  - `TargetPosScheduler`

## If The User Asks About Account Types Or Multi-Account

- `doc/usage/shinny_account.rst`
  - Quick account versus real account login
- `tqsdk/demo/multiaccount.py`
  - one API with multiple accounts
- `doc/reference/tqsdk.multiaccount.rst`
  - `TqMultiAccount`
- `doc/reference/tqsdk.tqkq.rst`
  - `TqKq` and `TqKqStock`
- `doc/reference/tqsdk.sim.rst`
  - `TqSim` and `TqSimStock`

## If The User Asks About Backtest

- `tqsdk/demo/tutorial/backtest.py`
  - futures backtest setup
- `doc/usage/backtest.rst`
  - backtest behavior, wait-update progression, stock backtest notes

## If The User Asks About Common Errors

- `tqsdk/lib/utils.py`
  - parameter validation errors
- `tqsdk/lib/target_pos_task.py`
  - `TargetPosTask` misuse and lifecycle errors
- `tqsdk/tools/downloader.py`
  - download permissions and parameter errors
- `tqsdk/tradeable/mixin.py`
  - "未初始化 TqApi" style errors
