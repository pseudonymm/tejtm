from __future__ import annotations

from rapidfuzz import fuzz

from tejtm.models import DEFAULT_WEIGHTS, ScorerResult, SourceColumn, TargetField
from tejtm.normalize import candidate_names, normalize_identifier, tokenize_identifier
from tejtm.scorers.base import ScoringContext


class FuzzyNameScorer:
    name = "fuzzy_name"

    def score(self, column: SourceColumn, field: TargetField, context: ScoringContext) -> ScorerResult | None:
        col_norm = normalize_identifier(column.name)
        col_tokens = " ".join(tokenize_identifier(column.name))
        if not col_norm:
            return None
        best = 0.0
        for cand in candidate_names(field.id, field.labels, field.aliases):
            scores = [
                fuzz.ratio(col_norm, cand) / 100.0,
                fuzz.WRatio(col_norm, cand) / 100.0,
                fuzz.token_sort_ratio(col_tokens or col_norm, cand) / 100.0,
                fuzz.token_set_ratio(col_tokens or col_norm, cand) / 100.0,
            ]
            best = max(best, max(scores))
        w = context.config.weight(self.name, DEFAULT_WEIGHTS[self.name])
        return ScorerResult(scorer=self.name, score=best, weight=w, reason=f"fuzzy best={best:.2f}")
