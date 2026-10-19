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
| ValueIntent | Agreement when types collide (e.g. two `name` columns) | 0.30 | Runs only when header scores are tied; uses value features |

Weights are user-tunable. A scorer that abstains does not contribute to the denominator.

## Semantic type catalog (built-in)

`boolean`, `integer`, `number`, `freetext`, `email`, `phone`, `url`, `uuid`, `date`, `datetime`, `time`, `currency`, `postal_code`, `country_code`, `address_line`.

Each detector returns match rate on the sample and a reason string for debugging.

## Value intent (homonym disambiguation)

When two source columns score high for the same target type or label:

1. Sample up to *N* non-null distinct values per column.
2. Classify each column’s value distribution with lightweight features (length, digit ratio, uppercase ratio, token count, regex hits).
3. Compare to prototype sketches for field intents (product title vs person name vs organization name). Use embedding of `field_id + top values` only when the optional semantic extra is installed.
4. Boost the column whose intent matches the target field description or expected type.

Sherlock and Sato motivate value-side typing ([research-semantic-similarity.md](./research-semantic-similarity.md)). v1 can use rules plus embeddings without full Sherlock reimplementation.

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
