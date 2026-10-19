# Wayfinder map: schema-mapping library

Status: open

## Destination

A **ready-for-agent** product spec and glossary for a general-purpose Python library. The library maps freeform source columns to a user-defined target schema. It exposes composite confidence scores (string heuristics, semantic type fit, header embedding similarity, optional value-intent signals). The library stays lightweight on CPU and does not require a GPU.

## Notes

- Domain: tabular import, ETL header alignment, CRM field mapping.
- Research artifacts: `writeups/research-*.md`, `writeups/primary-sources.md`.
- User-facing prose in `writeups/` uses ASD-STE100 strict style where marked.
- Skills: `research`, `to-spec`, `grilling`, `domain-modeling`, `asd-ste100`.
- Product spec path: `writeups/specs/schema-mapping-spec.md`.

## Decisions so far

- [Global assignment](issues/05-global-assignment-grilling.md): Hungarian one-to-one with `min_confidence` cutoff.
- [v1 scope](issues/06-library-boundaries-grilling.md): mapping, coercion, Pydantic adapter, optional `[semantic]` embeddings.
- [Prior art and ecosystem survey](writeups/research-prior-art.md): Composite matchers (COMA, Cupid) and import tools (RapidFuzz pipelines, Valentine, infermap, tabmodel) set the design pattern — normalize, score all pairs, global assignment, human review for low confidence.
- [String heuristic survey](writeups/research-string-heuristics.md): Use normalized labels plus RapidFuzz token metrics and Jaro-Winkler; aggregate with explicit weights like COMA.
- [Type detection survey](writeups/research-type-detection.md): Layer regex and library validators on sampled values; emit a semantic type label and a confidence per column.
- [Semantic similarity survey](writeups/research-semantic-similarity.md): Default header embeddings via FastEmbed + `paraphrase-multilingual-MiniLM-L12-v2`; optional value typing via Sherlock-style features when samples exist.

## Not yet specified

- Default global assignment: Hungarian one-to-one vs greedy with locks vs allow unmapped.
- Whether N:1 column merges (e.g. `first_name` + `last_name` → `full_name`) belong in v1 or a later transform layer.
- Optional LLM scorer: stub only vs omit entirely for lightweight positioning.
- Packaging name (`tejtm` working title) and minimum Python version.
- Calibration of raw scores to probabilities (infermap-style) vs raw weighted sums only.

## Out of scope

- Full interactive mapping UI (Clio-style) — library only; hosts own review screens.
- Deep ontology alignment (OWL, OAEI benchmarks) — tabular headers and cell samples only.
- GPU-required transformer models for default install.
