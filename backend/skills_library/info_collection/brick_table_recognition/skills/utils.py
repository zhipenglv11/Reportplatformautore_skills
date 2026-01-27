from __future__ import annotations

import re
from typing import Optional


_PLACEHOLDER_RE = re.compile(r"^\s*(—|-|/|\\)\s*$")


def normalize_test_date(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None
    # Accept YYYY-MM-DD only when complete and clear.
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return raw
    return raw


def normalize_strength(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    raw = value.strip()
    if not raw or _PLACEHOLDER_RE.fullmatch(raw):
        return None
    try:
        number = float(raw)
    except ValueError:
        return None
    return round(number, 1)


def normalize_location(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    # Collapse consecutive spaces.
    return re.sub(r"\s{2,}", " ", trimmed)
