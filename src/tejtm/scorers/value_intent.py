from __future__ import annotations

import re

from tejtm.models import DEFAULT_WEIGHTS, ScorerResult, SourceColumn, TargetField
from tejtm.scorers.base import ScoringContext

_SKU = re.compile(r"^[A-Z]{2,}-\d+")
_ALL_CAPS = re.compile(r"^[A-Z0-9\s\-]+$")


class ValueIntentScorer:
    name = "value_intent"

    def score(self, column: SourceColumn, field: TargetField, context: ScoringContext) -> ScorerResult | None:
        if not field.description and not field.expected_semantic_type:
            return None
        sketch = _value_sketch(column.samples)
        score = _intent_score(sketch, field)
        if score <= 0:
            return None
        w = context.config.weight(self.name, DEFAULT_WEIGHTS[self.name])
        return ScorerResult(scorer=self.name, score=score, weight=w, reason=sketch)


def _value_sketch(samples: tuple[str, ...] | list[str]) -> str:
    values = [s for s in samples if s and str(s).strip()][:20]
    if not values:
        return "empty"
    avg_len = sum(len(v) for v in values) / len(values)
    digit_ratio = sum(sum(c.isdigit() for c in v) for v in values) / sum(len(v) for v in values)
    caps_ratio = sum(1 for v in values if _ALL_CAPS.match(v.strip())) / len(values)
    sku_ratio = sum(1 for v in values if _SKU.match(v.strip())) / len(values)
    return f"len={avg_len:.1f} digit={digit_ratio:.2f} caps={caps_ratio:.2f} sku={sku_ratio:.2f}"


def _intent_score(sketch: str, field: TargetField) -> float:
    desc = (field.description or "").casefold()
    expected = (field.expected_semantic_type or "").casefold()
    score = 0.0
    if "product" in desc or expected == "sku":
        if "sku=" in sketch and float(sketch.split("sku=")[1].split()[0]) > 0.3:
            score = max(score, 0.85)
        if "caps=" in sketch and float(sketch.split("caps=")[1].split()[0]) > 0.5:
            score = max(score, 0.7)
    if "person" in desc or "customer" in desc or expected == "person_name":
        if "caps=" in sketch and float(sketch.split("caps=")[1].split()[0]) < 0.3:
            score = max(score, 0.75)
    if field.expected_semantic_type == "email" and "digit=" in sketch:
        dr = float(sketch.split("digit=")[1].split()[0])
        if dr < 0.2:
            score = max(score, 0.6)
    return score
