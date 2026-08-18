# -*- coding: utf-8 -*-
__author__ = "chenli"

import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Match, Pattern, Union


Replacement = Union[str, Callable[[Match[str]], str]]


@dataclass(frozen=True)
class Converter:
    """一条字符串正则替换规则。"""

    pattern: Pattern[str]
    replacement: Replacement


def translate(text: str, rules: Iterable[Converter]) -> str:
    """按顺序应用字符串替换规则。"""
    for rule in rules:
        text = rule.pattern.sub(rule.replacement, text)
    return text


_MD_DATED_COMBO_PATTERN = re.compile(
    r"(?P<prefix>[^a-zA-Z0-9_-])"
    r"(?P<left_product>[a-z]{2})(?P<left_month>[0-9]{4})"
    r"-"
    r"(?P<right_product>[a-z]{2})(?P<right_month>[0-9]{4})"
    r"(?P<suffix>[^a-zA-Z0-9_-])"
)


def _md_dated_combo_to_ctp(match: Match[str]) -> str:
    left_product = match.group("left_product")
    right_product = match.group("right_product")
    combo_type = "SP" if left_product == right_product else "SPC"
    left = left_product + match.group("left_month")
    right = right_product + match.group("right_month")
    return (
        f"{match.group('prefix')}{combo_type} "
        f"{left}&{right}{match.group('suffix')}"
    )


_MD_PLAIN_COMBO_PATTERN = re.compile(
    r'"(?P<left_product>[a-z]{2})-(?P<right_product>[a-z]{2})"'
)


def _md_plain_combo_to_ctp(match: Match[str]) -> str:
    left_product = match.group("left_product")
    right_product = match.group("right_product")
    combo_type = "SP" if left_product == right_product else "SPC"
    return f'"{combo_type} {left_product}&{right_product}"'


MD_TO_CTP = (
    Converter(
        pattern=_MD_DATED_COMBO_PATTERN,
        replacement=_md_dated_combo_to_ctp,
    ),
    Converter(
        pattern=_MD_PLAIN_COMBO_PATTERN,
        replacement=_md_plain_combo_to_ctp,
    ),
)


_CTP_COMBO_PATTERN = re.compile(
    r"(?P<exchange>SHFE|INE)\.SPC? "
    r"(?P<left>[a-z]{2}[0-9]{4})&"
    r"(?P<right>[a-z]{2}[0-9]{4})"
)


CTP_TO_MD = (
    Converter(
        pattern=_CTP_COMBO_PATTERN,
        replacement=r"\g<exchange>.\g<left>-\g<right>",
    ),
)


def loads(
        s: Union[str, bytes, bytearray],
        *args: Any,
        rules: Iterable[Converter] = (),
        **kwargs: Any,
) -> Any:
    """转换 JSON 字符串后反序列化。"""
    if isinstance(s, str):
        s = translate(s, rules)
    return json.loads(s, *args, **kwargs)


def dumps(
        obj: Any,
        *args: Any,
        rules: Iterable[Converter] = (),
        **kwargs: Any,
) -> str:
    """序列化对象后转换 JSON 字符串。"""
    return translate(json.dumps(obj, *args, **kwargs), rules)
