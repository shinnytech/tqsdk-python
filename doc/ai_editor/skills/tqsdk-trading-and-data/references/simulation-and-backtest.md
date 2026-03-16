# Simulation And Backtest

## Use This Reference For

- Explaining the difference among `TqSim`, `TqKq`, `TqSimStock`, `TqKqStock`, and `TqBacktest`
- Writing backtest examples
- Knowing which tool to choose for local simulation, Quick simulation, stock simulation, or historical backtest

## Table Of Contents

- Simulation choices
- Backtest
- Choosing among them

## Simulation Choices

### `TqSim`

Use for:

- local futures simulation
- strategy development
- futures backtest account object
- disposable examples that should not depend on a persistent remote simulated account

Characteristics:

- local simulated matching
- in backtest mode, only `TqSim` or `TqSimStock` can trade
- good default when `TqApi` is created without an explicit account

### `TqKq`

Use for:

- Quick futures simulation
- simulated trading tied to the Quick ecosystem
- scenarios where the user expects account data to match the official Quick clients

Characteristics:

- remote simulated account behavior
- requires `auth=TqAuth(...)`

### `TqSimStock`

Use for:

- local stock simulation
- stock backtest
- mixed futures and stock backtest when paired with `TqMultiAccount`

Important boundary:

- stock trading rules differ from futures
- `TargetPosTask` is not supported for stock trading

### `TqKqStock`

Use for:

- Quick stock simulation
- stock account workflows that should stay in the Quick ecosystem

## Backtest

Backtest uses `TqBacktest(...)` together with `TqSim()` or `TqSimStock()`.

Futures backtest example:

```python
from datetime import date
from tqsdk import TqApi, TqAuth, TqBacktest, TqSim, TargetPosTask

api = TqApi(
    TqSim(),
    backtest=TqBacktest(start_dt=date(2025, 1, 1), end_dt=date(2025, 1, 31)),
    auth=TqAuth("快期账户", "账户密码"),
)

klines = api.get_kline_serial("DCE.m2505", 60, data_length=200)
target_pos = TargetPosTask(api, "DCE.m2505")

while True:
    api.wait_update()
    if api.is_changing(klines.iloc[-1], "datetime"):
        if klines.close.iloc[-1] > klines.close.iloc[-20:].mean():
            target_pos.set_target_volume(1)
        else:
            target_pos.set_target_volume(0)
```

Important boundaries:

- backtest is for historical strategy execution, not arbitrary long-range data export
- quote update behavior in backtest differs from live trading
- one `wait_update()` call may update only order state, and the next one may advance market time
- TqSdk can output account statistics at backtest end

Stock backtest boundaries:

- use `TqSimStock()` for stock backtest
- stock backtest does not use `TargetPosTask`
- if the user wants both futures and stock in one backtest, use `TqMultiAccount([TqSim(), TqSimStock()])`

## Choosing Among Them

- need an account for live-ish strategy development without persistence requirements: `TqSim`
- need a Quick futures simulated account: `TqKq`
- need a Quick stock simulated account: `TqKqStock`
- need a local stock simulated account: `TqSimStock`
- need historical futures strategy execution over a date range: `TqBacktest` with `TqSim`
- need historical stock strategy execution over a date range: `TqBacktest` with `TqSimStock`
- need long-range historical CSV export: `DataDownloader`, not backtest

## Repository Sources

- `tqsdk/demo/tutorial/backtest.py`
- `doc/usage/backtest.rst`
- `doc/reference/tqsdk.sim.rst`
- `doc/reference/tqsdk.tqkq.rst`
- `tqsdk/api.py`
