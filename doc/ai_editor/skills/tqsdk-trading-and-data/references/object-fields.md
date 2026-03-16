# Object Fields

## Table Of Contents

- How to use this reference
- Quote, K-line, and Tick
- Futures `Account`, `Position`, `Order`, `Trade`
- Stock `SecurityAccount`, `SecurityPosition`, `SecurityOrder`, `SecurityTrade`
- Practical answering rules

## How To Use This Reference

Use this file when the user asks what object fields mean.

Rules:

1. Identify whether the object is market data, futures trading, or stock trading.
2. Explain the smallest relevant field set first.
3. Mention whether the object is a live reference updated by `wait_update()`.
4. Mention when a field is only meaningful for futures or only for stock.

## Quote, K-line, And Tick

`Quote` common fields:

| Field | Meaning | Typical use |
| --- | --- | --- |
| `datetime` | exchange timestamp string | confirm freshness |
| `last_price` | latest traded price | current price display |
| `ask_price1`, `bid_price1` | best ask and best bid | spread, order pricing |
| `ask_volume1`, `bid_volume1` | top-of-book volume | liquidity checks |
| `volume` | cumulative traded volume | activity checks |
| `open_interest` | open interest | futures participation |
| `highest`, `lowest`, `open`, `close`, `average` | session statistics | intraday analysis |
| `price_tick` | minimum price increment | order price calculation |
| `volume_multiple` | contract multiplier | PnL and sizing |
| `instrument_name`, `instrument_id`, `exchange_id`, `ins_class` | contract identity | explain what the symbol is |
| `underlying_symbol` | underlying for main contracts and options | map derived contracts |
| `expired` | whether the contract is expired | avoid stale examples |

K-line row common fields:

- `datetime`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `open_oi`
- `close_oi`

Tick row common fields:

- `datetime`
- `last_price`
- `ask_price1`, `bid_price1`
- `highest`, `lowest`
- `volume`
- `amount`
- `open_interest`

## Futures `Account`

Most useful fields:

| Field | Meaning |
| --- | --- |
| `balance` | dynamic account equity |
| `available` | available funds |
| `margin` | margin in use |
| `float_profit` | floating PnL versus open price |
| `position_profit` | position PnL versus prior settlement |
| `close_profit` | realized close PnL today |
| `commission` | fees paid today |
| `deposit`, `withdraw` | today's cash movement |
| `risk_ratio` | margin divided by equity |
| `market_value` | option market value |

## Futures `Position`

Most useful fields:

| Field | Meaning |
| --- | --- |
| `pos` | net position |
| `pos_long`, `pos_short` | long and short total lots |
| `pos_long_today`, `pos_short_today` | today's long and short lots |
| `pos_long_his`, `pos_short_his` | yesterday's long and short lots |
| `float_profit` | floating PnL |
| `position_profit` | position PnL |
| `margin` | margin used by this position |
| `open_price_long`, `open_price_short` | average open price |
| `position_price_long`, `position_price_short` | average holding cost basis |

Less preferred compatibility fields from the broker side:

- `volume_long*`
- `volume_short*`

Prefer the `pos_*` fields in explanations unless the user explicitly needs the broker-returned compatibility values.

## Futures `Order`

| Field | Meaning |
| --- | --- |
| `order_id` | client order id |
| `exchange_order_id` | exchange order id |
| `direction` | `BUY` or `SELL` |
| `offset` | `OPEN`, `CLOSE`, `CLOSETODAY` |
| `volume_orign` | original order size |
| `volume_left` | unfilled size |
| `limit_price` | order limit price |
| `price_type` | `ANY`, `LIMIT`, `BEST`, or `FIVELEVEL` depending on exchange behavior |
| `volume_condition` | quantity condition |
| `time_condition` | time condition |
| `insert_date_time` | order timestamp in nanoseconds |
| `status` | `ALIVE` or `FINISHED` |
| `last_msg` | latest order-state message |
| `is_dead` | definitely cannot trade anymore |
| `is_online` | definitely accepted by exchange and waiting |
| `is_error` | definitely a bad order |
| `trade_price` | average traded price |

Useful related property:

- `order.trade_records`

## Futures `Trade`

| Field | Meaning |
| --- | --- |
| `trade_id` | trade id |
| `order_id` | parent order id |
| `price` | trade price |
| `volume` | filled lots |
| `direction` | `BUY` or `SELL` |
| `offset` | open or close action |
| `trade_date_time` | trade timestamp in nanoseconds |

## Stock `SecurityAccount`

| Field | Meaning |
| --- | --- |
| `asset` | total current assets |
| `available` | current available cash |
| `drawable` | cash that can be withdrawn |
| `market_value` | current stock market value |
| `cost` | current total buy cost |
| `hold_profit` | holding profit |
| `float_profit_today` | today's floating profit |
| `real_profit_today` | today's realized profit |
| `profit_today` | today's total profit |
| `profit_rate_today` | today's profit rate |
| `buy_frozen_balance`, `buy_frozen_fee` | cash and fee frozen by pending buy orders |

## Stock `SecurityPosition`

| Field | Meaning |
| --- | --- |
| `volume` | current shares |
| `volume_his` | prior-day shares |
| `last_price` | latest price |
| `market_value` | current market value |
| `cost` | current cost |
| `hold_profit` | holding profit |
| `profit_today` | today's total profit |
| `profit_rate_today` | today's profit rate |
| `real_profit_total` | accumulated realized profit |
| `profit_total` | total profit |

## Stock `SecurityOrder`

| Field | Meaning |
| --- | --- |
| `order_id` | client order id |
| `exchange_order_id` | exchange order id |
| `direction` | `BUY` or `SELL` |
| `volume_orign` | requested shares |
| `volume_left` | unfilled shares |
| `price_type` | price type |
| `limit_price` | limit price |
| `frozen_fee` | frozen fee |
| `status` | current order state |
| `last_msg` | latest order-state message |

## Stock `SecurityTrade`

| Field | Meaning |
| --- | --- |
| `trade_id` | trade id |
| `order_id` | parent order id |
| `direction` | `BUY`, `SELL`, `SHARED`, or `DEVIDEND` |
| `volume` | shares or granted shares |
| `price` | trade price |
| `balance` | cash amount or dividend amount |
| `fee` | fee |
| `trade_date_time` | trade timestamp in nanoseconds |

## Practical Answering Rules

- Futures timestamps and stock timestamps are generally nanoseconds since Unix epoch on order and trade objects.
- Market-data `datetime` is usually a human-readable string.
- When the user asks "what fields should I print", prefer 4 to 8 fields, not the full object.
- For "all orders" or "all trades", explain that the getter returns a dict-like collection keyed by id.
- For "what traded under this order", prefer `order.trade_records`.
- For "what orders belong to this position", mention `position.orders`.

## Repository Sources

- `tqsdk/objs.py`
- `tqsdk/api.py`
- `tqsdk/tradeable/mixin.py`
