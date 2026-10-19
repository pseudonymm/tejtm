from __future__ import annotations

from tejtm.models import DEFAULT_WEIGHTS, ScorerResult, SourceColumn, TargetField
from tejtm.scorers.base import ScoringContext
from tejtm.typing.detectors import type_compatibility


class SemanticTypeScorer:
    name = "semantic_type"

    def score(self, column: SourceColumn, field: TargetField, context: ScoringContext) -> ScorerResult | None:
        if field.expected_semantic_type is None:
            return None
        guess = context.column_types.get(column.name)
        if guess is None:
            return None
        score = type_compatibility(guess, field.expected_semantic_type)
        if score <= 0:
            return ScorerResult(
                scorer=self.name,
                score=0.0,
                weight=context.config.weight(self.name, DEFAULT_WEIGHTS[self.name]),
                reason=f"source={guess.label} expected={field.expected_semantic_type}",
            )
        w = context.config.weight(self.name, DEFAULT_WEIGHTS[self.name])
        return ScorerResult(
            scorer=self.name,
            score=score,
            weight=w,
            reason=f"source={guess.label} expected={field.expected_semantic_type}",
        )
