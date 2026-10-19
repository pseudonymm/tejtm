from __future__ import annotations

from tejtm.assignment import assign_one_to_one
from tejtm.models import (
    FieldMapping,
    MappingConfig,
    MappingResult,
    SourceColumn,
    SourceProfile,
    TargetField,
    TargetSchema,
)
from tejtm.scorers import DEFAULT_SCORERS
from tejtm.scorers.base import Scorer, ScoringContext, aggregate_scores
from tejtm.scorers.header_embedding import HeaderEmbeddingScorer, _get_embedder
from tejtm.typing.detectors import detect_semantic_type


class MappingEngine:
    def __init__(self, scorers: tuple[Scorer, ...] | None = None) -> None:
        self._scorers = scorers if scorers is not None else DEFAULT_SCORERS

    def propose_mappings(
        self,
        source: SourceProfile,
        target: TargetSchema,
        *,
        config: MappingConfig | None = None,
    ) -> MappingResult:
        cfg = config or MappingConfig()
        column_types = {col.name: detect_semantic_type(col.samples) for col in source.columns}
        field_embeddings: dict[str, tuple[float, ...]] | None = {} if _get_embedder() else None
        context = ScoringContext(
            config=cfg,
            column_types=column_types,
            field_embeddings=field_embeddings,
        )

        fields = list(target.fields)
        columns = list(source.columns)
        field_ids = [f.id for f in fields]

        override_mappings: list[FieldMapping] = []
        override_sources: set[str] = set()
        override_targets: set[str] = set()
        for src_name, tgt_id in cfg.overrides.items():
            if any(c.name == src_name for c in columns) and tgt_id in field_ids:
                override_mappings.append(
                    FieldMapping(
                        source_column=src_name,
                        target_field=tgt_id,
                        confidence=1.0,
                        breakdown=(),
                    )
                )
                override_sources.add(src_name)
                override_targets.add(tgt_id)

        score_matrix: list[list[float]] = []
        breakdowns: list[list[tuple]] = []
        for col in columns:
            row_scores: list[float] = []
            row_breakdowns: list[tuple] = []
            for fld in fields:
                parts = self._score_pair(col, fld, context)
                conf = aggregate_scores(parts)
                row_scores.append(conf)
                row_breakdowns.append(tuple(parts))
            score_matrix.append(row_scores)
            breakdowns.append(row_breakdowns)

        assignments = assign_one_to_one(score_matrix, cfg.min_confidence)
        mappings: list[FieldMapping] = list(override_mappings)
        mapped_sources = set(override_sources)
        mapped_targets = set(override_targets)

        for row_idx, pair in enumerate(assignments):
            if pair is None:
                continue
            col = columns[row_idx]
            if col.name in mapped_sources:
                continue
            _, col_idx = pair
            fld = fields[col_idx]
            if fld.id in mapped_targets:
                continue
            conf = score_matrix[row_idx][col_idx]
            mappings.append(
                FieldMapping(
                    source_column=col.name,
                    target_field=fld.id,
                    confidence=conf,
                    breakdown=breakdowns[row_idx][col_idx],
                )
            )
            mapped_sources.add(col.name)
            mapped_targets.add(fld.id)

        unmapped = tuple(c.name for c in columns if c.name not in mapped_sources)
        unmatched = tuple(f.id for f in fields if f.id not in mapped_targets)
        mappings.sort(key=lambda m: (-m.confidence, m.source_column))
        return MappingResult(
            mappings=tuple(mappings),
            unmapped_columns=unmapped,
            unmatched_fields=unmatched,
        )

    def _score_pair(self, column: SourceColumn, field: TargetField, context: ScoringContext) -> list:
        parts = []
        for scorer in self._scorers:
            if isinstance(scorer, HeaderEmbeddingScorer) and context.field_embeddings is None:
                continue
            result = scorer.score(column, field, context)
            if result is not None:
                parts.append(result)
        return parts
