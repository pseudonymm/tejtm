from __future__ import annotations

import re
from datetime import datetime
from typing import Callable, Sequence

from tejtm.models import TypeGuess

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", re.IGNORECASE)
_URL = re.compile(r"^https?://\S+$", re.IGNORECASE)
_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_PHONE = re.compile(r"^\+?[\d\s().-]{7,}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
_TIME = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")
_CURRENCY = re.compile(
    r"^[\$€£]\s*-?\d{1,3}(?:,\d{3})*(?:\.\d+)?$|"
    r"^-?\d{1,3}(?:,\d{3})+(?:\.\d+)?$"
)
_BOOL = {"true", "false", "yes", "no", "0", "1", "y", "n"}


def _match_rate(samples: Sequence[str], predicate: Callable[[str], bool]) -> tuple[float, str]:
    values = [s.strip() for s in samples if s and str(s).strip()]
    if not values:
        return 0.0, "no samples"
    hits = sum(1 for v in values if predicate(v))
    rate = hits / len(values)
    return rate, f"{hits}/{len(values)} matched"


def detect_semantic_type(samples: Sequence[str]) -> TypeGuess:
    checks: list[tuple[str, Callable[[str], bool]]] = [
        ("email", lambda v: bool(_EMAIL.match(v))),
        ("url", lambda v: bool(_URL.match(v))),
        ("uuid", lambda v: bool(_UUID.match(v))),
        ("phone", _is_phone),
        ("datetime", lambda v: bool(_DATETIME.match(v))),
        ("date", lambda v: bool(_DATE.match(v)) and _parse_date(v)),
        ("time", lambda v: bool(_TIME.match(v))),
        ("boolean", lambda v: v.casefold() in _BOOL),
        ("currency", lambda v: bool(_CURRENCY.match(v.replace(" ", "")))),
        ("integer", _is_int),
        ("number", _is_number),
    ]
    best_label = "freetext"
    best_rate = 0.0
    best_evidence = ""
    for label, pred in checks:
        rate, evidence = _match_rate(samples, pred)
        if rate > best_rate:
            best_rate = rate
            best_label = label
            best_evidence = evidence
    if best_rate < 0.5:
        return TypeGuess(label="freetext", confidence=best_rate, evidence=best_evidence or "weak signal")
    return TypeGuess(label=best_label, confidence=best_rate, evidence=best_evidence)


def _is_phone(value: str) -> bool:
    if _DATE.match(value) or _DATETIME.match(value) or _TIME.match(value):
        return False
    if not _PHONE.match(value):
        return False
    digits = sum(c.isdigit() for c in value)
    if digits < 7:
        return False
    return not value.isdigit()


def _is_int(value: str) -> bool:
    try:
        int(value.replace(",", ""))
        return "." not in value
    except ValueError:
        return False


def _is_number(value: str) -> bool:
    try:
        float(value.replace(",", "").replace("$", "").replace("€", "").replace("£", ""))
        return True
    except ValueError:
        return False


def _parse_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def type_compatibility(source: TypeGuess, expected: str | None) -> float:
    if expected is None:
        return 0.0
    if source.label == expected:
        return min(1.0, 0.5 + 0.5 * source.confidence)
    compatible = {
        ("integer", "number"),
        ("number", "integer"),
        ("datetime", "date"),
        ("date", "datetime"),
        ("number", "currency"),
        ("currency", "number"),
    }
    if (source.label, expected) in compatible:
        return 0.6 * source.confidence
    return 0.0
