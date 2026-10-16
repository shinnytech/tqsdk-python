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
- Use `init_balance` to choose the starting equity for the scenario snapshot. For current-account risk, pass the actual valid account equity explicitly; the default 10000000 is not the user's balance.
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
import math
import os
from tqsdk import TqApi, TqAuth, TqAccount, TqScenario

account = TqAccount(os.environ["TQ_BROKER_ID"], os.environ["TQ_ACCOUNT_ID"], os.environ["TQ_ACCOUNT_PASSWORD"])
with TqApi(account, auth=TqAuth(os.environ["TQ_AUTH_USER"], os.environ["TQ_AUTH_PASSWORD"])) as api:
    symbol = api.get_quote("KQ.m@SHFE.rb").underlying_symbol
    if not symbol:
        raise RuntimeError("尚未获取到主连标的合约")
    quote = api.get_quote(symbol)
    funds = api.get_account()
    if not all(math.isfinite(v) for v in (quote.last_price, funds.balance, funds.available)) or funds.balance <= 0:
        raise RuntimeError("行情或账户资金无效，不能进行当前账户试算")
    budget = min(200000.0, max(0.0, funds.available))
    max_trial_lots = 100  # Bounded example; use a task-appropriate limit.
    accepted = 0
    with TqScenario(api, account=account, positions=api.get_position(), init_balance=funds.balance) as trial:
        base_margin = trial.scenario_get_account().margin
        for candidate in range(1, max_trial_lots + 1):
            order = trial.scenario_insert_order(symbol, "BUY", "OPEN", 1, quote.last_price)
            if order.status != "FINISHED" or order.volume_left:
                break
            if trial.scenario_get_account().margin - base_margin > budget:
                break
            accepted = candidate
    print("本次试算边界内满足增量保证金预算的手数：", accepted)
    if accepted == max_trial_lots:
        print("已到试算上限，不能据此宣称是最大可开手数")

```

### "What happens if the futures margin rate becomes 15%?"

```python
# Fragment inside an existing API context with the selected account.
positions = api.get_position()
balance = api.get_account().balance
symbol = api.get_quote("KQ.m@SHFE.rb").underlying_symbol
if not symbol:
    raise RuntimeError("尚未获取到主连标的合约")
with TqScenario(api, account=account, positions=positions, init_balance=balance) as s:
    before = s.scenario_get_account()
    s.scenario_set_margin_rate(symbol, 0.15)
    after = s.scenario_get_account()
    print(before.margin, before.risk_ratio, after.margin, after.risk_ratio)

```

### "What happens if I add 100000 equity and keep positions unchanged?"

```python
# Fragment inside an existing API context with the selected account.
positions = api.get_position()
balance = api.get_account().balance
with TqScenario(api, account=account, positions=positions, init_balance=balance + 100000) as s:
    after = s.scenario_get_account()
    print(after.margin, after.risk_ratio)

```

The bounded loop reports only the explored scenario, not a guaranteed executable maximum. It does not model real liquidity, future price changes, all frozen funds or every broker margin preference. No `api.insert_order()` is sent by these trial calls. Validate funds and price before applying the remaining fragments.

## Boundaries

- `TqScenario` currently supports futures only.
- `TqScenario` currently supports one account snapshot at a time.
- `TqScenario` is synchronous. Run it outside the hot `wait_update()` loop when possible.
- Valid trial orders match at the passed price inside the snapshot; invalid or rejected orders do not prove a fill. Check returned `status`, `volume_left` and `last_msg`.
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
