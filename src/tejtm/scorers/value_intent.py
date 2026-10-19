from __future__ import annotations

from tejtm.models import DEFAULT_WEIGHTS, ScorerResult, SourceColumn, TargetField
from tejtm.scorers.base import ScoringContext
from tejtm.value_profile import expectation_from_type, signature_similarity, value_signature


class ValueIntentScorer:
    name = "value_intent"

    def score(self, column: SourceColumn, field: TargetField, context: ScoringContext) -> ScorerResult | None:
        column_sig = value_signature(column.samples)
        if column_sig is None:
            return None

        scores: list[tuple[float, str]] = []

        if field.expected_semantic_type:
            expected_sig = expectation_from_type(field.expected_semantic_type)
            sim = signature_similarity(column_sig, expected_sig)
            scores.append((sim, f"type_profile:{field.expected_semantic_type}:{sim:.2f}"))

        if field.exemplar_samples:
            exemplar_sig = value_signature(field.exemplar_samples)
            if exemplar_sig is not None:
                sim = signature_similarity(column_sig, exemplar_sig)
                scores.append((sim, f"exemplar:{sim:.2f}"))

        embed_score = _description_value_embedding_score(column, field, context)
        if embed_score is not None:
            scores.append((embed_score, f"desc_embed:{embed_score:.2f}"))

        if not scores:
            return None

        best_score, reason = max(scores, key=lambda t: t[0])
        if best_score <= 0:
            return None
        w = context.config.weight(self.name, DEFAULT_WEIGHTS[self.name])
        return ScorerResult(scorer=self.name, score=best_score, weight=w, reason=reason)


def _description_value_embedding_score(
    column: SourceColumn,
    field: TargetField,
    context: ScoringContext,
) -> float | None:
    if not field.description:
        return None
    if context.field_embeddings is None:
        return None
    from tejtm.scorers.header_embedding import _cosine, _embed_text, _get_embedder

    model = _get_embedder()
    if model is None:
        return None
    samples = [s for s in column.samples if s and str(s).strip()][:5]
    if not samples:
        return None
    col_text = " | ".join(samples)
    field_text = f"{field.id} {field.description}"
    col_vec = _embed_text(model, col_text)
    field_vec = context.field_embeddings.get(f"desc:{field.id}")
    if field_vec is None:
        field_vec = _embed_text(model, field_text)
        if field_vec:
            context.field_embeddings[f"desc:{field.id}"] = field_vec
    if col_vec is None or field_vec is None:
        return None
    return _cosine(col_vec, field_vec)
