# About mapping limits

tejtm proposes column-to-field pairs. Host code owns files, row transforms, and identity. This page is the boundary, not a backlog of features to expect in the engine.

## Column mapping is not record correlation

The engine never joins two tables, matches people across systems, or flags duplicate rows. Spec out of scope lists duplicate detection next to file readers and web UI. If you need MDM or fuzzy entity match, run that after you rename columns.

`tejtm.__all__` exports mapping types, `MappingEngine`, and coercion helpers. It does not export join or identity APIs.

## One source column, one target field

Assignment is global one-to-one. Two source columns cannot share a target field. Weak pairs fall below `min_confidence` and stay unmapped. Automatic many-to-one merges (split first name plus last name into `full_name`) are out of v1. Do those transforms in the host after mapping.

## Duplicate headers are illegal

`SourceProfile` requires unique `SourceColumn.name` values. `TargetSchema` requires unique field ids. Two Excel columns both labeled `Name` must be uniquified before you call the engine (`Name`, `Name_2`). The engine keys unmapped sets by those names, so a silent collision would drop a column.

Homonyms with different names (`ref_a` versus `ref_b`, or `name` versus `product`) can still split with aliases, types, or `exemplar_samples`.

## You own I/O and validation

The library does not read CSV, Excel, or Parquet. Tests load fixtures through `tests/support/loaders.py` as a host pattern, not as a public module. After mapping, validate with Pydantic, Pandera, or Frictionless. `propose_and_apply` is a convenience adapter, not the core engine.

## Default threshold is stricter than the demos

`MappingConfig.min_confidence` defaults to `0.55`. Sector fixtures often use `0.35` to `0.45`. If you keep the default on messy vendor files, more columns stay unmapped. That is intentional. Auto-apply only what you trust.

## Optional extras change scores

Without `fastembed`, `HeaderEmbeddingScorer` abstains. Scenario tests then run name, type, and value-intent scorers only. Install `tejtm[semantic]` and the first FastEmbed call may download the multilingual MiniLM model. Core mapping does not open network sockets. The embedding extra can.

Without `scipy`, assignment uses a greedy cost fallback instead of the Hungarian algorithm. Pairings can differ on crowded score matrices. Install SciPy if you need the Hungarian path.

Without `openpyxl`, the finance XLSX scenario test cannot load. Production mapping never opens workbooks.

`pyproject.toml` declares a `phone` extra that installs `phonenumbers`. Detectors do not import that package. Phone matching uses the regex in `tejtm.typing.detectors`.

## What architecture docs list that code does not

`docs/architecture-frontier.md` mentions `postal_code`, `country_code`, and `address_line`. `detect_semantic_type` does not implement those labels. They score as `freetext` or `integer` today. Put postal meaning in aliases and exemplars, or register a custom scorer.

`MappingConfig.intent_margin` exists on the dataclass and has no runtime consumer. Setting it does nothing.

Value intent always runs when it can build a signature. `intent_margin` does not gate it.

## LLM scoring and ontology alignment

There is no LLM scorer in the default distribution. OWL, RDF, and structural XML matching are out of scope.

## Confidence is a ranking aid

A high score is not a proof that the column is that field in the business sense. Show `breakdown` to reviewers. Keep a human override path. Replay those overrides on the next file.
