# Example Map

Use this file when you need a concrete repository example or doc page before writing or revising an answer.

## When The Repository Is Not Available

The ZIP contains this skill, not a full SDK checkout. Paths below are source pointers, not files guaranteed to exist in the user's project. Do not request a private repository or repeatedly search missing directories.

- Inspect the installed package using `tqsdk.__file__`, relevant docstrings and `inspect.signature(...)` with the selected project interpreter.
- For documentation use [TqSdk API reference](https://doc.shinnytech.com/tqsdk/latest/reference/index.html), [quickstart](https://doc.shinnytech.com/tqsdk/latest/quickstart.html), and [usage guide](https://doc.shinnytech.com/tqsdk/latest/usage/index.html).
- Public source is at [shinnytech/tqsdk-python](https://github.com/shinnytech/tqsdk-python). Match the user's SDK version before relying on a new parameter or behavior. Internal design/test pointers may not exist in the public release; public APIs and installed source remain the authority for that environment.
- Adapt historical example symbols and dates to the task; do not copy an expired contract into a current-market program.

## If TqSdk Is Missing

Read [environment-setup.md](environment-setup.md), then run the bundled `scripts/check_environment.py` from the user's project directory using its interpreter. Install a missing SDK according to project constraints and recheck before running code.

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
  - `TargetPosTask` rules and caveats, including `support_open_min_volume`
- `doc/advanced/targetpostask2.rst`
  - `cancel()` and `is_finished()`
- `doc/advanced/scheduler.rst`
  - `TargetPosScheduler`
- `tqsdk/algorithm/twap.py`
  - direct `Twap` behavior, including `support_open_min_volume`
- `design/target_pos_task_support_open_min_limit.md`
  - design notes for contracts with minimum opening volume rules
- `tqsdk/test/target_pos_task/test_open_min_volume.py`
  - regression cases for `support_open_min_volume`

## If The User Asks About Margin Trials Or `TqScenario`

- `tqsdk/scenario/tqscenario.py`
  - public `TqScenario` docstrings and method semantics
- `design/scenario.md`
  - scenario design, margin-rate source rules, and discount-model notes
- `tqsdk/test/scenario/test_scenario.py`
  - runnable what-if patterns for margin and risk changes
- `tqsdk/test/scenario/test_pre_insert_order.py`
  - real-account margin-rate lookup examples and expected values
- `doc/reference/tqsdk.scenario.rst`
  - public API reference entry

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
