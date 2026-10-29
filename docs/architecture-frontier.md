# Architecture frontier

ASD-STE100 strict summary. Detail lives in linked research files.

## Problem

Import features often reject files when headers do not match a fixed schema. Users need automatic mapping with visible confidence. The library must work for any user-defined target schema and any messy source headers.

## Reference pipeline

1. **Ingest profiles.** Read source column names and a sample of values per column. Read target field ids, labels, aliases, and optional expected types.
2. **Normalize names.** Apply Unicode normalization, casefold, punctuation cleanup, and camelCase or snake_case tokenization.
3. **Profile values.** Run semantic type detectors on samples. Store type label and confidence per column and per field expectation.
4. **Score pairs.** For each source column and target field, run scorers. Combine with explicit weights into one score and a breakdown.
5. **Assign globally.** Solve one-to-one assignment on the score matrix. Mark low scores as unmapped.
6. **Return result.** Emit mappings, unmapped columns, unmatched fields, and per-pair breakdowns. The host applies renames, transforms, and validation.

This mirrors COMA-style composition ([COMA PDF](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf)) and products such as infermap and tabmodel.

## Scorer set (recommended v1)

| Scorer | Signal | Default weight | Notes |
|--------|--------|----------------|-------|
| ExactName | Normalized id or alias equality | 1.0 | Highest priority |
| FuzzyName | Jaro-Winkler, ratio, token_sort, token_set max or blend | 0.45 | See [research-string-heuristics.md](./research-string-heuristics.md) |
| SemanticType | Agreement between detected source type and field expectation | 0.25 | See [research-type-detection.md](./research-type-detection.md) |
| HeaderEmbedding | Cosine similarity of column name vs field name+aliases | 0.20 | Optional extra; see [research-semantic-similarity.md](./research-semantic-similarity.md) |
| ValueIntent | Value signature versus type profile or `exemplar_samples` | 0.30 | Runs on every pair that has a signature. Not gated on header ties. |

Weights are user-tunable. A scorer that returns `None` does not enter the denominator. A score of `0.0` still does.

## Semantic type catalog (built-in)

Implemented by `detect_semantic_type`: `boolean`, `integer`, `number`, `freetext`, `email`, `phone`, `url`, `uuid`, `date`, `datetime`, `time`, `currency`.

Not implemented: `postal_code`, `country_code`, `address_line`. Use aliases, exemplars, or a custom scorer.

Each detector returns match rate on the sample and a reason string for debugging.

## Value intent (homonym disambiguation)

General-purpose only:

1. Build a **value signature** per column (semantic type + format stats + dominant token prefix).
2. Compare to **field expectation** from `expected_semantic_type` (generic type profile), `exemplar_samples` (integrator-provided), and optional description embedding when `[semantic]` is installed.
3. No sector keywords in core code. See ADR `docs/adr/0001-value-intent-via-signatures.md`.

## Assignment

Use the Hungarian algorithm on the negated score matrix for one-to-one assignment. Enforce a minimum score cutoff. Leave source columns and target fields unpaired when below cutoff.

Greedy assignment is a fallback when scipy is not installed. Document the dependency.

## Lightweight default install

- **Core:** Python 3.11+, `rapidfuzz`, stdlib `re` / `datetime` / `unicodedata`.
- **Optional `[semantic]`:** `fastembed` for header embeddings.
- **Optional `[phone]`:** `phonenumbers` for stricter phone detection.
- **No GPU.** No PyTorch in the default wheel.

## Differentiation from existing packages

| Need | infermap / tabmodel | This library |
|------|---------------------|--------------|
| Framework | Often tied to files or Pydantic | Schema objects only; host supplies data |
| Score transparency | Partial | Required breakdown per mapping |
| Extensibility | Fixed scorer list | Register custom scorers and weights |
| Value intent | Profile stats | Explicit homonym disambiguation pass |

## Open decisions (grilling)

See wayfinder tickets [05-global-assignment-grilling](../.scratch/schema-mapping/issues/05-global-assignment-grilling.md) and [06-library-boundaries-grilling](../.scratch/schema-mapping/issues/06-library-boundaries-grilling.md). The spec uses recommended defaults until you confirm otherwise.
