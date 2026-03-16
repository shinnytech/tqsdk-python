# Market Data

## Use This Reference For

- `get_quote`
- `get_kline_serial`
- `get_tick_serial`
- `query_quotes`, `query_cont_quotes`, `query_symbol_info`, `get_trading_status`
- `DataDownloader`

## Table Of Contents

- Session setup
- Real-time quote
- K-line and tick series
- Contract discovery
- Long-range historical download

## Session Setup

For read-only examples, this is usually enough:

```python
from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))
```

Notes:

- `TqApi(auth=...)` defaults to a local `TqSim()` account.
- Market-data questions usually do not require a real trading account.
- Close the API explicitly or use a context manager.

## Real-Time Quote

```python
from tqsdk import TqApi, TqAuth

api = TqApi(auth=TqAuth("快期账户", "账户密码"))
quote = api.get_quote("SHFE.au2504")

while True:
    api.wait_update()
    if api.is_changing(quote, ["last_price", "ask_price1", "bid_price1"]):
        print(quote.datetime, quote.last_price, quote.ask_price1, quote.bid_price1)
```

Recommended quote fields:

- `datetime`
- `last_price`
- `ask_price1`, `bid_price1`
- `volume`, `open_interest`
- `price_tick`, `volume_multiple`
- `instrument_name`, `ins_class`, `expired`
- `underlying_symbol` for main contracts and options

If the user wants "current price", do not hardcode expired delivery months.

## K-Line And Tick Series

K-line:

```python
klines = api.get_kline_serial("DCE.i2505", 60, data_length=200)

while True:
    api.wait_update()
    if api.is_changing(klines.iloc[-1], "datetime"):
        print("new bar", klines.iloc[-1].datetime, klines.iloc[-1].close)
```

Tick:

```python
ticks = api.get_tick_serial("DCE.i2505", data_length=200)

while True:
    api.wait_update()
    if api.is_changing(ticks.iloc[-1], "datetime"):
        print(ticks.iloc[-1].datetime, ticks.iloc[-1].last_price)
```

Important semantics:

- Both APIs return pandas `DataFrame` objects that update in place.
- `get_kline_serial(..., data_length=...)` and `get_tick_serial(..., data_length=...)` support up to 10000 rows per request.
- For `get_kline_serial`, intraday durations can be arbitrary seconds; day-or-higher durations must be integer multiples of 86400, up to 28 days.
- When `symbol` is a list in `get_kline_serial`, all secondary symbols align to the first symbol's timeline.
- `adj_type` only matters for stock and fund contracts.

Typical columns:

- K-line: `datetime`, `open`, `high`, `low`, `close`, `volume`, `open_oi`, `close_oi`
- Tick: `datetime`, `last_price`, `ask_price1`, `bid_price1`, `highest`, `lowest`, `volume`, `amount`, `open_interest`

## Contract Discovery

Use discovery APIs before writing "current contract" examples.

- `api.query_quotes(...)`: broad filtering by contract class, exchange, product, expired flag, night session
- `api.query_cont_quotes(...)`: main-contract lookup
- `api.query_symbol_info(...)`: static metadata table, not a live object
- `api.get_trading_status(symbol)`: current trading state

Pattern:

```python
from tqsdk import TqApi, TqAuth

with TqApi(auth=TqAuth("快期账户", "账户密码")) as api:
    conts = api.query_cont_quotes(exchange_id="SHFE", product_id="au")
    info = api.query_symbol_info(list(conts))
    print(info[["instrument_id", "instrument_name", "ins_class", "price_tick", "volume_multiple"]])
```

## Long-Range Historical Download

Use `DataDownloader` when the user wants CSV export or long date ranges.

```python
from contextlib import closing
from datetime import date
from tqsdk import TqApi, TqAuth
from tqsdk.tools import DataDownloader

api = TqApi(auth=TqAuth("快期账户", "账户密码"))
task = DataDownloader(
    api,
    symbol_list="KQ.m@SHFE.rb",
    dur_sec=60,
    start_dt=date(2025, 1, 1),
    end_dt=date(2025, 2, 1),
    csv_file_name="rb_main_1m.csv",
)

with closing(api):
    while not task.is_finished():
        api.wait_update()
        print(f"{task.get_progress():.2f}%")
```

Notes:

- `dur_sec=0` means tick download.
- `DataDownloader` is a paid or permission-gated feature.
- Multi-symbol downloads align by the first symbol's trading calendar.

## Repository Sources

- `tqsdk/demo/tutorial/t10.py`
- `tqsdk/demo/tutorial/t30.py`
- `tqsdk/demo/tutorial/underlying_symbol.py`
- `doc/usage/mddatas.rst`
- `tqsdk/tools/downloader.py`
- `tqsdk/api.py`
