from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class SourceColumn:
    name: str
    samples: Sequence[str] = ()


@dataclass(frozen=True, slots=True)
class SourceProfile:
    columns: Sequence[SourceColumn]


@dataclass(frozen=True, slots=True)
class TargetField:
    id: str
    labels: Sequence[str] = ()
    aliases: Sequence[str] = ()
    expected_semantic_type: str | None = None
    description: str | None = None
    exemplar_samples: Sequence[str] = ()


@dataclass(frozen=True, slots=True)
class TargetSchema:
    fields: Sequence[TargetField]


@dataclass(frozen=True, slots=True)
class TypeGuess:
    label: str
    confidence: float
    evidence: str = ""


@dataclass(frozen=True, slots=True)
class ScorerResult:
    scorer: str
    score: float
    weight: float
    reason: str = ""


@dataclass(frozen=True, slots=True)
class FieldMapping:
    source_column: str
    target_field: str
    confidence: float
    breakdown: tuple[ScorerResult, ...] = ()


@dataclass(frozen=True, slots=True)
class MappingResult:
    mappings: tuple[FieldMapping, ...]
    unmapped_columns: tuple[str, ...]
    unmatched_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mappings": [
                {
                    "source_column": m.source_column,
                    "target_field": m.target_field,
                    "confidence": m.confidence,
                    "breakdown": [
                        {
                            "scorer": b.scorer,
                            "score": b.score,
                            "weight": b.weight,
                            "reason": b.reason,
                        }
                        for b in m.breakdown
                    ],
                }
                for m in self.mappings
            ],
            "unmapped_columns": list(self.unmapped_columns),
            "unmatched_fields": list(self.unmatched_fields),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MappingResult:
        mappings = tuple(
            FieldMapping(
                source_column=m["source_column"],
                target_field=m["target_field"],
                confidence=float(m["confidence"]),
                breakdown=tuple(
                    ScorerResult(
                        scorer=b["scorer"],
                        score=float(b["score"]),
                        weight=float(b["weight"]),
                        reason=b.get("reason", ""),
                    )
                    for b in m.get("breakdown", [])
                ),
            )
            for m in data.get("mappings", [])
        )
        return cls(
            mappings=mappings,
            unmapped_columns=tuple(data.get("unmapped_columns", [])),
            unmatched_fields=tuple(data.get("unmatched_fields", [])),
        )


@dataclass(frozen=True, slots=True)
class MappingConfig:
    weights: Mapping[str, float] = field(default_factory=dict)
    min_confidence: float = 0.55
    intent_margin: float = 0.08
    overrides: Mapping[str, str] = field(default_factory=dict)

    def weight(self, scorer: str, default: float) -> float:
        return self.weights.get(scorer, default)


DEFAULT_WEIGHTS: dict[str, float] = {
    "exact_name": 1.0,
    "fuzzy_name": 0.45,
    "semantic_type": 0.25,
    "header_embedding": 0.20,
    "value_intent": 0.30,
}
