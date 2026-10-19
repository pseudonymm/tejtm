from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence, TypeVar

from tejtm.coercion import coerce_record
from tejtm.engine import MappingEngine
from tejtm.models import MappingConfig, MappingResult, SourceColumn, SourceProfile, TargetField, TargetSchema

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ImportResult:
    valid_rows: list[Any]
    errors: list[dict[str, Any]]
    mapping: MappingResult
    column_rename: dict[str, str]


def _pydantic_field_names(model: type) -> list[tuple[str, list[str], str | None, list[str]]]:
    try:
        from pydantic import BaseModel
    except ImportError as exc:
        raise ImportError("Install tejtm with pydantic extra: pip install tejtm[pydantic]") from exc
    if not isinstance(model, type) or not issubclass(model, BaseModel):
        raise TypeError("model must be a Pydantic BaseModel subclass")

    out: list[tuple[str, list[str], str | None, list[str]]] = []
    for name, field_info in model.model_fields.items():
        aliases: list[str] = []
        extra = field_info.json_schema_extra
        if isinstance(extra, dict):
            raw = extra.get("aliases") or extra.get("tejtm_aliases")
            if isinstance(raw, str):
                aliases.append(raw)
            elif isinstance(raw, (list, tuple)):
                aliases.extend(str(a) for a in raw)
        title = field_info.title or name
        expected = None
        exemplars: list[str] = []
        if isinstance(extra, dict):
            if extra.get("semantic_type"):
                expected = str(extra["semantic_type"])
            raw_ex = extra.get("tejtm_exemplars") or extra.get("exemplar_samples")
            if isinstance(raw_ex, str):
                exemplars.append(raw_ex)
            elif isinstance(raw_ex, (list, tuple)):
                exemplars.extend(str(x) for x in raw_ex)
        out.append((name, [title, *aliases], expected, exemplars))
    return out


def target_schema_from_model(model: type) -> TargetSchema:
    fields = [
        TargetField(
            id=name,
            labels=(labels[0],) if labels else (),
            aliases=tuple(labels[1:]),
            expected_semantic_type=expected,
            exemplar_samples=tuple(exemplars),
        )
        for name, labels, expected, exemplars in _pydantic_field_names(model)
    ]
    return TargetSchema(fields=fields)


def propose_and_apply(
    model: type[T],
    rows: Sequence[Mapping[str, Any]],
    *,
    config: MappingConfig | None = None,
    engine: MappingEngine | None = None,
) -> ImportResult:
    if not rows:
        return ImportResult(valid_rows=[], errors=[], mapping=MappingResult((), (), ()), column_rename={})

    columns = list(rows[0].keys())
    samples_by_col: dict[str, list[str]] = {c: [] for c in columns}
    for row in rows[:50]:
        for c in columns:
            val = row.get(c)
            if val is not None and str(val).strip():
                samples_by_col[c].append(str(val))

    source = SourceProfile(
        columns=[SourceColumn(name=c, samples=tuple(samples_by_col[c][:20])) for c in columns]
    )
    target = target_schema_from_model(model)
    eng = engine or MappingEngine()
    mapping = eng.propose_mappings(source, target, config=config)
    rename = {m.source_column: m.target_field for m in mapping.mappings}

    valid: list[Any] = []
    errors: list[dict[str, Any]] = []
    field_types = {f.id: f.expected_semantic_type or "freetext" for f in target.fields if f.expected_semantic_type}

    for idx, row in enumerate(rows):
        renamed = {rename.get(k, k): v for k, v in row.items()}
        coerced = coerce_record(renamed, field_types)
        try:
            valid.append(model.model_validate(coerced))
        except Exception as exc:
            errors.append({"row": idx + 1, "message": str(exc)})

    return ImportResult(valid_rows=valid, errors=errors, mapping=mapping, column_rename=rename)
