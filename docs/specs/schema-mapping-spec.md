Status: ready-for-agent

# Schema mapping library — product spec

## Problem Statement

Teams building import features must hand-roll fuzzy header matching, type guessing, and confidence display. Strict schema validation rejects useful files when labels differ slightly from the canonical model. Users want automatic mapping suggestions they can trust and override, without binding to one web framework or one file format.

## Solution

A small Python library that accepts a **source column profile** (names + value samples) and a **user-defined target schema**, then returns ranked one-to-one mappings with **composite confidence** and **per-factor explanations**. The library stays CPU-only by default and loads optional embedding support when installed.

## User Stories

1. As an application developer, I want to define a target schema in code, so that I can map arbitrary uploads to my domain model.
2. As an application developer, I want each target field to accept aliases, so that common vendor header variants map without custom code.
3. As an application developer, I want optional expected semantic types on fields, so that value-based scoring can disambiguate ambiguous headers.
4. As an application developer, I want to pass column names and row samples without reading a file inside the library, so that I control I/O and security.
5. As an application developer, I want a single call that returns all proposed mappings, so that I can render a review screen in one round trip.
6. As an application developer, I want unmapped source columns listed explicitly, so that I can ask the user to ignore or rename them.
7. As an application developer, I want unmatched target fields listed explicitly, so that I can flag required missing data.
8. As an application developer, I want a numeric confidence per mapping, so that I can auto-apply high-confidence pairs only.
9. As an application developer, I want a structured score breakdown per mapping, so that I can show why the engine chose a pair.
10. As an application developer, I want to tune scorer weights, so that I can bias toward names or toward value types per domain.
11. As an application developer, I want to register custom scorers, so that I can add domain dictionaries without forking the library.
12. As an application developer, I want string normalization applied consistently, so that `CustomerName` and `customer_name` match the same field.
13. As an import user, I want `phone` to map to `phone_number`, so that I do not fix labels manually.
14. As an import user, I want `contact` to map to `email` when values look like emails, so that misleading headers still work.
15. As an import user, I want `id` to map to `order_number` when values match order id patterns, so that generic headers resolve correctly.
16. As an import user, I want two columns both named `name` to map to different fields when one holds products and one holds people, so that homonyms do not collapse.
17. As a data engineer, I want built-in detectors for email, phone, url, date, datetime, time, uuid, currency, and freetext, so that type agreement boosts correct pairs.
18. As a data engineer, I want detectors to report confidence from sample match rate, so that sparse or dirty columns score honestly.
19. As a localization owner, I want multilingual header similarity without GPU, so that non-English exports still map.
20. As a security-conscious developer, I want the core package to avoid network calls, so that mapping runs offline.
21. As a packager, I want semantic embeddings behind an optional extra, so that minimal installs stay small.
22. As a tester, I want deterministic scoring given fixed inputs and seeds, so that unit tests are stable.
23. As a maintainer, I want global one-to-one assignment, so that two source columns cannot claim the same target field.
24. As a maintainer, I want a configurable minimum score threshold, so that weak guesses stay unmapped.
25. As an integrator, I want to save and reload mapping configuration as data, so that repeat imports skip inference.
26. As an integrator, I want manual overrides to take precedence over inference, so that users can fix one column without disabling automation.
27. As a performance owner, I want mapping for dozens of columns to finish in sub-second time on CPU, so that uploads feel instant.
28. As a documentation reader, I want clear extension points, so that I know where validation and coercion belong (outside this library).
29. As a library consumer, I want typed result objects, so that IDEs autocomplete mapping fields.
30. As a library consumer, I want abstaining scorers to be ignored in aggregation, so that missing optional deps do not zero out scores incorrectly.

## Implementation Decisions

- **Public entry:** `MappingEngine` with `propose_mappings(source: SourceProfile, target: TargetSchema, *, config: MappingConfig | None) -> MappingResult`.
- **Source profile:** Ordered list of `SourceColumn(name, samples: Sequence[str], optional stats cache)`.
- **Target schema:** List of `TargetField(id, labels, aliases, optional expected_semantic_type, optional description, optional exemplar_samples)`.
- **Scorers:** Protocol `Scorer.score(column, field, context) -> ScorerResult | None`. Built-ins: ExactName, FuzzyName, SemanticType, HeaderEmbedding (optional), ValueIntent (conditional).
- **Aggregation:** Weighted average over non-abstaining scorers; weights from `MappingConfig.weights` with documented defaults matching [architecture-frontier.md](../architecture-frontier.md).
- **Assignment:** Hungarian algorithm on score matrix (scipy `linear_sum_assignment` when available); respect `min_confidence`; produce unmapped/unmatched lists.
- **Normalization:** Shared `normalize_identifier(text) -> str` used by all name scorers; tokenization for camel/snake.
- **Type detection:** `ColumnTyper.detect(samples) -> TypeGuess(label, confidence, evidence)` with pluggable registry; built-in catalog per research doc.
- **Value intent:** Compare column value signatures to generic type profiles, field `exemplar_samples`, and optional description embeddings. No sector-specific keyword rules in core code.
- **Embeddings:** Lazy import of FastEmbed when `[semantic]` installed; cache field-side embeddings per `TargetSchema` instance.
- **Persistence:** `MappingResult.to_dict()` / `from_dict()` and optional YAML helper in `[yaml]` extra; not required for core.
- **Coercion:** `tejtm.coercion.coerce_value(value, semantic_type)` and `coerce_record(record, field_types)` for post-map cell casting (email/url left as str; dates via `datetime.date.fromisoformat` where possible).
- **Pydantic adapter:** `tejtm.pydantic_adapter.propose_and_apply(model, rows, ...)` builds `TargetSchema` from model fields + `Aliases` metadata pattern; returns validated models and mapping metadata.
- **Transforms (merge/split):** Out of v1 core; document pattern as host responsibility or future `tejtm.transforms` module.
- **LLM scorer:** Out of v1; interface reserved for optional plugin later.
- **Dependencies:** Core `rapidfuzz`; optional `fastembed`, `phonenumbers`, `scipy`, `pyyaml`.

## Testing Decisions

- **Seams:** (1) **Engine integration:** `MappingEngine.propose_mappings` for end-to-end mapping, unmapped lists, and thresholds. (2) **Public scorer contracts:** Each built-in `Scorer` is part of the stable API; each has golden table tests for `score(column, field, context)` on fixed inputs (normalization edge cases, abstain when optional deps missing, score in `[0,1]`).
- **Good tests:** Engine tests use table-driven `SourceProfile` + `TargetSchema` fixtures (homonyms, alias wins, `contact`→email via types). Scorer tests stay independent of assignment so custom scorers can mirror the same contract tests.
- **Prior art:** pytest; sector scenarios under `tests/fixtures/scenarios/` with CSV/XLSX data and `scenario.json` manifests; loaders in `tests/support/` only (library does not read files).
- **Property tests (optional later):** Assignment never maps two sources to one target; aggregated confidence in `[0,1]`.
- **Modules under test:** `engine`, `assignment`, each module under `scorers/`, `typing.detectors`, `normalize`.

## Out of Scope

- Reading CSV, Excel, or Parquet inside the library.
- Row-level validation, coercion, or duplicate detection (use Pandera, Pydantic, or Frictionless after mapping).
- Interactive web UI for mapping review.
- Ontology alignment (OWL/RDF) and structural XML schema matching.
- GPU inference and large language models in default distribution.
- Automatic many-to-one column merges in v1.

## Further Notes

- Research basis: [docs/README.md](../README.md).
- Resolved: Hungarian one-to-one + `min_confidence`; v1 includes coercion helpers and Pydantic adapter; embeddings behind `[semantic]`.
- Competitor positioning: complementary to tabmodel (Pydantic import) and infermap (file-first); this library targets schema-to-schema with maximal transparency.
- Suggested package layout: `src/tejtm/` with `engine.py`, `models.py`, `scorers/`, `typing/`, `assignment.py`, `normalize.py`.
