from __future__ import annotations

from tejtm.models import DEFAULT_WEIGHTS, ScorerResult, SourceColumn, TargetField
from tejtm.normalize import candidate_names, normalize_identifier
from tejtm.scorers.base import ScoringContext


class ExactNameScorer:
    name = "exact_name"

    def score(self, column: SourceColumn, field: TargetField, context: ScoringContext) -> ScorerResult | None:
        col = normalize_identifier(column.name)
        if not col:
            return None
        names = candidate_names(field.id, field.labels, field.aliases)
        if col in names:
            w = context.config.weight(self.name, DEFAULT_WEIGHTS[self.name])
            return ScorerResult(scorer=self.name, score=1.0, weight=w, reason="exact normalized match")
        return None
