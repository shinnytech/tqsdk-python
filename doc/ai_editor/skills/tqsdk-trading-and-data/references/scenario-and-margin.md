# Scenario And Margin

## Use This Reference For

- `TqScenario`
- Real-account margin-rate lookup
- Margin occupancy and risk-ratio what-if analysis
- Questions such as "how many lots can I still open?" or "how much margin will I release?"

## Table Of Contents

- When to choose `TqScenario`
- Core APIs
- Snapshot inputs
- Margin-rate sources
- Limited margin discount behavior
- Common patterns
- Boundaries
- Repository sources

## When To Choose `TqScenario`

Use `TqScenario` when the user wants synchronous "what if" analysis against a snapshot of current futures positions and funds.

Typical requests:

- max lots under a margin budget
- how many lots to close to free a target amount of margin
- margin or risk ratio after opening or reducing multiple futures symbols
- risk ratio after changing a futures margin rate
- risk ratio after keeping positions unchanged but changing starting equity

Prefer live-order helpers such as `insert_order()` or `TargetPosTask` only when the user wants execution, not trial calculation.

## Core APIs

- `TqScenario(api, account=None, positions=None, init_balance=10000000.0)`
- `scenario_insert_order(symbol, direction, offset, volume, limit_price)`
- `scenario_set_margin_rate(symbol, margin_rate)`
- `scenario_get_account()`

Important behavior:

- `TqScenario` creates an internal futures trading snapshot and updates it immediately after each `scenario_*` call.
- `scenario_insert_order()` matches immediately at the passed `limit_price`.
- `scenario_insert_order()` does not model partial fills. Read `status`, `volume_left`, and `last_msg`.
- `scenario_get_account()` returns only `margin` and `risk_ratio`.
- `scenario_set_margin_rate()` updates one futures symbol inside the scenario and recalculates account margin from `pre_settlement`.

## Snapshot Inputs

- Pass `positions=api.get_position()` to start from the current futures position snapshot.
- Pass one `Position` object if the user only wants to trial one symbol.
- Omit `positions` to start from an empty futures account.
- Use `init_balance` to choose the starting equity for the scenario snapshot.
- When the user wants "current positions plus extra capital", read `balance = api.get_account().balance` first, then pass `init_balance=balance + extra`.

Keep all related trial actions inside one `TqScenario` object so the margin and risk calculations stay cumulative.

## Margin-Rate Sources

- `account=None` creates an internal `TqSim()` and uses `Quote.margin` together with `pre_settlement`.
- `account=TqAccount(...)` or `account=TqKq()` triggers account-specific margin-rate lookup through the internal pre-insert-order path.
- The first uncached real-account lookup is synchronous and may spend time inside `wait_update()` before returning.
- If account-specific lookup fails, TqSdk falls back to `Quote.margin`.
- CTP margin-rate lookup is flow-controlled at roughly one new symbol per second.
- `scenario_set_margin_rate()` is the right API when the user explicitly wants to shock one futures symbol to a hypothetical new margin rate.

## Limited Margin Discount Behavior

- Reuse one `TqScenario` object and apply actions step by step when the margin result depends on net exposure after each trade.
- The reported margin change can reflect the limited built-in margin discount rules already modeled by TqSdk's simulator, including supported futures hedge and cross-period cases.
- Do not promise exact broker settlement logic for every custom preferential rule. If the user asks about a broker-specific rule that TqSdk does not model, say the result is only the built-in approximation.

## Common Patterns

### "How many lots can I still open under a 200000 margin budget?"

```python
from tqsdk import TqApi, TqAuth, TqAccount, TqScenario

account = TqAccount("broker", "acct", "pwd")
api = TqApi(account=account, auth=TqAuth("quick_user", "quick_pass"))
symbol = "SHFE.rb2611"
quote = api.get_quote(symbol)
positions = api.get_position()

with TqScenario(api, account=account, positions=positions) as s:
    base_margin = s.scenario_get_account().margin
    lots = 0
    while True:
        order = s.scenario_insert_order(symbol, "BUY", "OPEN", 1, quote.last_price)
        if order.status == "FINISHED" and order.volume_left > 0:
            break
        lots += 1
        if s.scenario_get_account().margin - base_margin > 200000:
            s.scenario_insert_order(symbol, "SELL", "CLOSETODAY", 1, quote.last_price)
            lots -= 1
            break
```

### "What happens if the futures margin rate becomes 15%?"

```python
account = TqAccount("broker", "acct", "pwd")
api = TqApi(account=account, auth=TqAuth("quick_user", "quick_pass"))
positions = api.get_position()

with TqScenario(api, account=account, positions=positions) as s:
    before = s.scenario_get_account()
    s.scenario_set_margin_rate("SHFE.rb2611", 0.15)
    after = s.scenario_get_account()
```

### "What happens if I add 100000 equity and keep positions unchanged?"

```python
account = TqAccount("broker", "acct", "pwd")
api = TqApi(account=account, auth=TqAuth("quick_user", "quick_pass"))
positions = api.get_position()
balance = api.get_account().balance

with TqScenario(api, account=account, positions=positions, init_balance=balance + 100000) as s:
    after = s.scenario_get_account()
```

## Boundaries

- `TqScenario` currently supports futures only.
- `TqScenario` currently supports one account snapshot at a time.
- `TqScenario` is synchronous. Run it outside the hot `wait_update()` loop when possible.
- `scenario_insert_order()` always fills immediately at the passed price inside the trial snapshot.
- `scenario_insert_order()` and `scenario_get_account()` return reduced objects, not the full live `Order` or `Account`.
- Preserve `CLOSE` versus `CLOSETODAY` when closing SHFE or INE positions imported from a live snapshot.
- Do not recommend `TqScenario` for stock trading, option pricing shocks, or arbitrary custom broker discount tables that the simulator does not model.

## Repository Sources

- `tqsdk/scenario/tqscenario.py`
- `design/scenario.md`
- `doc/reference/tqsdk.scenario.rst`
- `tqsdk/test/scenario/test_scenario.py`
- `tqsdk/test/scenario/test_pre_insert_order.py`
- `tqsdk/api.py`
