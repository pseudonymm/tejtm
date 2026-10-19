from __future__ import annotations

import math

from tejtm.models import DEFAULT_WEIGHTS, ScorerResult, SourceColumn, TargetField
from tejtm.normalize import candidate_names
from tejtm.scorers.base import ScoringContext

_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is False:
        return None
    if _embedder is not None and _embedder is not False:
        return _embedder
    try:
        from fastembed import TextEmbedding

        _embedder = TextEmbedding(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
    except ImportError:
        _embedder = False
    return _embedder if _embedder is not False else None


def _cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


class HeaderEmbeddingScorer:
    name = "header_embedding"

    def score(self, column: SourceColumn, field: TargetField, context: ScoringContext) -> ScorerResult | None:
        model = _get_embedder()
        if model is None:
            return None
        if context.field_embeddings is None:
            return None
        col_vec = _embed_text(model, column.name)
        if col_vec is None:
            return None
        best = 0.0
        for cand in candidate_names(field.id, field.labels, field.aliases):
            fvec = context.field_embeddings.get(cand)
            if fvec is None:
                fvec = _embed_text(model, cand)
                if fvec:
                    context.field_embeddings[cand] = fvec
            if fvec:
                best = max(best, _cosine(col_vec, fvec))
        w = context.config.weight(self.name, DEFAULT_WEIGHTS[self.name])
        return ScorerResult(scorer=self.name, score=best, weight=w, reason=f"embedding cosine={best:.2f}")


def _embed_text(model, text: str) -> tuple[float, ...] | None:
    if not text.strip():
        return None
    vectors = list(model.embed([text]))
    if not vectors:
        return None
    return tuple(float(x) for x in vectors[0])
