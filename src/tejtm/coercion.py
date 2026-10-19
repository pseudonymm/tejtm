from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping

from tejtm.typing.detectors import detect_semantic_type


def coerce_value(value: Any, semantic_type: str) -> Any:
    if value is None or value == "":
        return None
    text = str(value).strip()
    if semantic_type == "boolean":
        low = text.casefold()
        if low in ("true", "yes", "y", "1"):
            return True
        if low in ("false", "no", "n", "0"):
            return False
        return text
    if semantic_type == "integer":
        return int(text.replace(",", ""))
    if semantic_type == "number" or semantic_type == "currency":
        return float(text.replace(",", "").replace("$", "").replace("€", "").replace("£", ""))
    if semantic_type == "date":
        return date.fromisoformat(text[:10])
    if semantic_type == "datetime":
        return datetime.fromisoformat(text.replace("Z", "+00:00")[:19])
    return text


def coerce_record(record: Mapping[str, Any], field_types: Mapping[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in record.items():
        stype = field_types.get(key)
        if stype is None:
            out[key] = value
            continue
        try:
            out[key] = coerce_value(value, stype)
        except (ValueError, TypeError):
            out[key] = value
    return out


def infer_field_types_from_samples(
    records: list[Mapping[str, Any]],
    column: str,
) -> str:
    samples = [str(r.get(column, "")) for r in records if r.get(column) is not None]
    return detect_semantic_type(samples).label
