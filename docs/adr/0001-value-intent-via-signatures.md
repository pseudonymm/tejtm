# ADR 0001: Value intent via signatures and integrator metadata

## Status

Accepted

## Context

Homonymous headers (`name`, `id`, `date`) are common in imports. Header and type scorers alone mis-assign when two columns share a label or generic type. An early `ValueIntentScorer` hard-coded product/customer vocabulary, which conflicts with a general-purpose library.

## Decision

- Compute a **value signature** from column samples: detected semantic type, match confidence, and format statistics (length, digit ratio, uniqueness, whitespace ratio).
- Compute a **field expectation** from integrator metadata only:
  - `expected_semantic_type` maps to a generic type profile.
  - `exemplar_samples` (optional) defines what values should look like; signature similarity is the main disambiguation tool.
  - `description` (optional) participates only through the optional embedding scorer path, not keyword rules.
- Sector-specific behavior belongs in user-provided exemplars, aliases, and types—not in core code.

## Consequences

- `TargetField` gains `exemplar_samples`.
- Tests use scenario fixtures across industries; expectations are declared in manifest data, not in Python branches.
