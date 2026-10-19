from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from tejtm.models import TypeGuess
from tejtm.typing.detectors import detect_semantic_type, type_compatibility

_WS = re.compile(r"\s")


@dataclass(frozen=True, slots=True)
class ValueSignature:
    semantic_type: str
    type_confidence: float
    avg_length: float
    digit_ratio: float
    space_ratio: float
    distinct_ratio: float
    uppercase_ratio: float
    token_prefix: str = ""


def value_signature(samples: Sequence[str]) -> ValueSignature | None:
    values = [str(s).strip() for s in samples if s is not None and str(s).strip()]
    if not values:
        return None
    guess = detect_semantic_type(values)
    total_chars = sum(len(v) for v in values)
    digits = sum(sum(c.isdigit() for c in v) for v in values)
    spaces = sum(len(_WS.findall(v)) for v in values)
    distinct = len(set(values)) / len(values)
    upper = sum(1 for v in values if v.isupper()) / len(values)
    return ValueSignature(
        semantic_type=guess.label,
        type_confidence=guess.confidence,
        avg_length=total_chars / len(values),
        digit_ratio=digits / total_chars if total_chars else 0.0,
        space_ratio=spaces / total_chars if total_chars else 0.0,
        distinct_ratio=distinct,
        uppercase_ratio=upper,
        token_prefix=_dominant_prefix(values),
    )


def signature_similarity(a: ValueSignature, b: ValueSignature) -> float:
    type_score = type_compatibility(
        TypeGuess(a.semantic_type, a.type_confidence),
        b.semantic_type,
    )
    if type_score <= 0 and a.semantic_type != b.semantic_type:
        type_part = 0.15 if _types_loosely_compatible(a.semantic_type, b.semantic_type) else 0.0
    else:
        type_part = type_score

    prefix_part = 1.0 if a.token_prefix and a.token_prefix == b.token_prefix else 0.0
    shape = 1.0 - min(
        1.0,
        (
            abs(a.digit_ratio - b.digit_ratio)
            + abs(a.space_ratio - b.space_ratio)
            + abs(a.distinct_ratio - b.distinct_ratio) * 0.5
            + abs(a.uppercase_ratio - b.uppercase_ratio) * 0.5
            + min(1.0, abs(a.avg_length - b.avg_length) / max(a.avg_length, b.avg_length, 1.0))
        )
        / 3.0,
    )
    blended = 0.45 * type_part + 0.35 * shape + 0.20 * prefix_part
    return max(0.0, min(1.0, blended))


def expectation_from_type(expected_semantic_type: str) -> ValueSignature:
    profiles: dict[str, ValueSignature] = {
        "email": ValueSignature("email", 1.0, 22.0, 0.0, 0.0, 0.9, 0.0),
        "phone": ValueSignature("phone", 1.0, 12.0, 0.5, 0.05, 0.9, 0.0),
        "uuid": ValueSignature("uuid", 1.0, 36.0, 0.0, 0.0, 1.0, 0.0),
        "url": ValueSignature("url", 1.0, 30.0, 0.05, 0.0, 0.9, 0.0),
        "date": ValueSignature("date", 1.0, 10.0, 0.3, 0.0, 0.8, 0.0),
        "datetime": ValueSignature("datetime", 1.0, 19.0, 0.35, 0.05, 0.8, 0.0),
        "integer": ValueSignature("integer", 1.0, 4.0, 0.9, 0.0, 0.7, 0.0),
        "number": ValueSignature("number", 1.0, 6.0, 0.4, 0.0, 0.7, 0.0),
        "currency": ValueSignature("currency", 1.0, 8.0, 0.5, 0.0, 0.6, 0.0),
        "boolean": ValueSignature("boolean", 1.0, 4.0, 0.0, 0.0, 0.3, 0.0),
        "freetext": ValueSignature("freetext", 0.5, 16.0, 0.1, 0.12, 0.85, 0.1),
    }
    return profiles.get(expected_semantic_type, profiles["freetext"])


def _dominant_prefix(values: Sequence[str]) -> str:
    buckets: dict[str, int] = {}
    for v in values:
        token = v.strip()
        if "-" in token:
            key = token.split("-", 1)[0].casefold()
        elif len(token) >= 3:
            key = token[:3].casefold()
        else:
            key = token.casefold()
        buckets[key] = buckets.get(key, 0) + 1
    if not buckets:
        return ""
    return max(buckets, key=buckets.get)


def _types_loosely_compatible(a: str, b: str) -> bool:
    pairs = {("integer", "number"), ("date", "datetime"), ("freetext", "uuid")}
    return (a, b) in pairs or (b, a) in pairs
