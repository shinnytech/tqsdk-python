#!/usr/bin/env python
#  -*- coding: utf-8 -*-

"""Parser for the text returned by :meth:`TqApi.get_settlement_info`.

The settlement statement is a human-readable, bilingual table.  This module
only removes whitespace used for table alignment; values otherwise remain in
their original textual representation.  In particular, dates, numbers,
percentages and Chinese enum values are not normalized.
"""

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple


class SettlementInfoParseError(ValueError):
    """Raised when a settlement statement does not have the expected format."""


_ACCOUNT_FIELDS: Sequence[Tuple[str, str]] = (
    ("balance_bf", "Balance B/F"),
    ("deposit_withdrawal", "Deposit/Withdrawal"),
    ("realized_profit", "Realized P/L"),
    ("mtm_profit", "MTM P/L"),
    ("exercise_profit", "Exercise P/L"),
    ("commission", "Commission"),
    ("exercise_fee", "Exercise Fee"),
    ("delivery_fee", "Delivery Fee"),
    ("new_fx_pledge", "New FX Pledge"),
    ("fx_redemption", "FX Redemption"),
    ("change_in_pledge_amount", "Chg in Pledge Amt"),
    ("premium_received", "Premium Received"),
    ("premium_paid", "Premium Paid"),
    ("delivery_profit", "Delivery P/L"),
    ("initial_margin", "Initial Margin"),
    ("balance_cf", "Balance C/F"),
    ("pledge_amount", "Pledge Amount"),
    ("client_equity", "Client Equity"),
    ("fx_pledge_occupied", "FX Pledge Occ."),
    ("margin_occupied", "Margin Occupied"),
    ("delivery_margin", "Delivery Margin"),
    ("market_value_long", "Market Value(long)"),
    ("market_value_short", "Market Value(short)"),
    ("market_value_equity", "Market Value(equity)"),
    ("fund_available", "Fund Avail."),
    ("risk_degree", "Risk Degree"),
    ("margin_call", "Margin Call"),
    ("change_in_fx_pledge", "Chg in FX Pledge"),
)

_TRADE_FIELDS: Sequence[str] = (
    "date",
    "invest_unit",
    "exchange",
    "trading_code",
    "product",
    "instrument_id",
    "direction",
    "hedge_type",
    "price",
    "volume",
    "turnover",
    "offset",
    "commission",
    "realized_profit",
    "premium",
    "trade_id",
    "account_id",
)

_POSITION_FIELDS: Sequence[str] = (
    "invest_unit",
    "trading_code",
    "product",
    "instrument_id",
    "long_position",
    "average_buy_price",
    "short_position",
    "average_sell_price",
    "previous_settlement_price",
    "settlement_price",
    "mtm_profit",
    "margin_occupied",
    "hedge_type",
    "market_value_long",
    "market_value_short",
    "account_id",
)

_CREATION_DATE_RE = re.compile(r"Creation Date\s*[：:]\s*([^\s|]+)", re.IGNORECASE)
_CLIENT_RE = re.compile(
    r"客户号\s*Client ID\s*[：:]\s*([^\s]+)\s+"
    r"客户名称\s*Client Name\s*[：:]\s*([^\r\n]*)",
    re.IGNORECASE,
)
_TRADING_DAY_RE = re.compile(r"日期\s*Date\s*[：:]\s*([^\s|]+)", re.IGNORECASE)
_ACCOUNT_RE = re.compile(
    r"资金账号\s*[：:]\s*([^\s]+).*?"
    r"AccountID\s*[：:]\s*([^\s]+)\s+Currency\s*[：:]\s*([^\s|]+)",
    re.IGNORECASE,
)


def _required_match(pattern: re.Pattern, raw: str, field_name: str) -> re.Match:
    match = pattern.search(raw)
    if match is None:
        raise SettlementInfoParseError("结算单缺少%s" % field_name)
    return match


def _company_name(lines: Sequence[str], creation_line: int) -> str:
    for line in reversed(lines[:creation_line]):
        value = line.strip().lstrip("\ufeff")
        if value and not set(value) <= {"-"}:
            return value
    raise SettlementInfoParseError("结算单缺少期货公司名称")


def _account_value(raw: str, label: str) -> Optional[str]:
    pattern = re.compile(
        re.escape(label) + r"\s*[：:]\s*([^\s|]+)",
        re.IGNORECASE,
    )
    match = pattern.search(raw)
    return match.group(1).strip() if match else None


def _split_row(line: str) -> List[str]:
    value = line.strip()
    return [column.strip() for column in value.strip("|").split("|")]


def _is_table_heading(columns: Sequence[str]) -> bool:
    if not columns:
        return True
    first = columns[0].strip()
    return (
        first in {"成交日期", "投资单元"}
        or first.lower() in {"date", "investunit"}
        or first.startswith("共")
    )


def _parse_table_row(
        columns: Sequence[str], fields: Sequence[str], section_name: str, line_number: int
) -> Dict[str, str]:
    if len(columns) != len(fields):
        raise SettlementInfoParseError(
            "结算单%s第%d行列数错误: 预期%d列，实际%d列"
            % (section_name, line_number, len(fields), len(columns))
        )
    return dict(zip(fields, columns))


def parse_settlement_info(settlement_info: str) -> Dict[str, Any]:
    """Parse a textual settlement statement returned by ``get_settlement_info``.

    Args:
        settlement_info: The original settlement statement string.

    Returns:
        A dictionary containing statement metadata, one account summary, a
        list of trades and a list of summarized positions.  Every value read
        from the statement is a stripped string.  A missing account field is
        ``None`` and an absent business table is represented by an empty list.
        An empty or whitespace-only statement returns an empty dictionary.

    Raises:
        TypeError: If ``settlement_info`` is not a string.
        SettlementInfoParseError: If required metadata is missing or a row in
            a supported table is malformed.
    """
    if not isinstance(settlement_info, str):
        raise TypeError("settlement_info 参数必须是 str")
    if not settlement_info.strip():
        return {}

    lines = settlement_info.splitlines()
    creation_match = _required_match(_CREATION_DATE_RE, settlement_info, "制表日期")
    creation_line = len(re.split(r"\r\n|\r|\n", settlement_info[:creation_match.start()])) - 1
    company_name = _company_name(lines, creation_line)

    client_match = _required_match(_CLIENT_RE, settlement_info, "客户信息")
    trading_day_match = _required_match(_TRADING_DAY_RE, settlement_info, "交易日")
    account_match = _required_match(_ACCOUNT_RE, settlement_info, "资金账户信息")

    chinese_account_id = account_match.group(1).strip()
    account_id = account_match.group(2).strip()
    if chinese_account_id != account_id:
        raise SettlementInfoParseError("结算单中的资金账号不一致")

    account: Dict[str, Optional[str]] = {
        "account_id": account_id,
        "currency": account_match.group(3).strip(),
    }
    account.update({key: _account_value(settlement_info, label) for key, label in _ACCOUNT_FIELDS})

    trades: List[Dict[str, str]] = []
    positions: List[Dict[str, str]] = []
    section: Optional[str] = None
    for line_number, line in enumerate(lines, start=1):
        if "成交记录 Transaction Record" in line:
            section = "trade"
            continue
        if "持仓汇总 Positions" in line:
            section = "position"
            continue
        if "平仓明细 Position Closed" in line or "持仓明细 Positions Detail" in line:
            section = None
            continue
        if section is None or not line.strip().startswith("|"):
            continue

        columns = _split_row(line)
        if _is_table_heading(columns):
            continue
        if section == "trade":
            trades.append(_parse_table_row(columns, _TRADE_FIELDS, "成交记录", line_number))
        else:
            positions.append(_parse_table_row(columns, _POSITION_FIELDS, "持仓汇总", line_number))

    return {
        "futures_company_name": company_name,
        "creation_date": creation_match.group(1).strip(),
        "client_id": client_match.group(1).strip(),
        "client_name": client_match.group(2).strip(),
        "trading_day": trading_day_match.group(1).strip(),
        "account": account,
        "trades": trades,
        "positions": positions,
    }


__all__ = ["SettlementInfoParseError", "parse_settlement_info"]
