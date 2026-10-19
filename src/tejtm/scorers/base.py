from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from tejtm.models import MappingConfig, ScorerResult, SourceColumn, TargetField, TypeGuess


@dataclass
class ScoringContext:
    config: MappingConfig
    column_types: dict[str, TypeGuess] = field(default_factory=dict)
    field_embeddings: dict[str, tuple[float, ...]] | None = None


class Scorer(Protocol):
    name: str

    def score(
        self,
        column: SourceColumn,
        field: TargetField,
        context: ScoringContext,
    ) -> ScorerResult | None: ...


def aggregate_scores(parts: list[ScorerResult]) -> float:
    if not parts:
        return 0.0
    num = sum(p.score * p.weight for p in parts)
    den = sum(p.weight for p in parts)
    if den <= 0:
        return 0.0
    return max(0.0, min(1.0, num / den))
