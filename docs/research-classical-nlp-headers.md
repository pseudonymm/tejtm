# Classical header-only matchers: keep, defer, reject

Research note for **documented-not-wired** header signals in [research-classical-nlp-gap.md](./research-classical-nlp-gap.md) sections 1 and 2. Value-instance methods (value Jaccard, instance TF-IDF), type detectors, and neural scorers are out of scope. This note recommends keep, defer, or reject for wiring. It does not change `src/tejtm/`.

**Mode.** Explanation with a decision table. Facts about the current engine come from `normalize.py`, `scorers/fuzzy.py`, and a local engine run on 29 Oct 2026 in this worktree (FastEmbed absent).

---

## How header signals meet the default cutoff

`FuzzyNameScorer` takes the max of four RapidFuzz metrics per column and candidate string, then the max over candidates ([`fuzzy.py`](../src/tejtm/scorers/fuzzy.py)). Other scorers run in parallel. The mapping confidence is a **weighted mean** of non-abstaining scorers ([`aggregate_scores`](../src/tejtm/scorers/base.py)). Default weights sum to `exact_name` 1.0, `fuzzy_name` 0.45, `semantic_type` 0.25, `value_intent` 0.30 ([`DEFAULT_WEIGHTS`](../src/tejtm/models.py)). `MappingConfig.min_confidence` defaults to **0.55** ([`limitations.md`](./limitations.md)).

Measured fixture aggregates (README.md, 29 Oct 2026, no FastEmbed):

| Pair | Aggregate confidence | Gap to 0.55 |
|------|----------------------|-------------|
| `contact` -> `email` (`crm_contacts`) | 0.549 | 0.001 below |
| `Clinic` -> `facility_name` (`healthcare_appointments`) | 0.480 | 0.070 below |

Measured scorer breakdown for those pairs (same checkout, `MappingEngine`, `min_confidence=0`):

| Pair | `fuzzy_name` | `semantic_type` | `value_intent` |
|------|--------------|-----------------|----------------|
| `contact` -> `email` | 0.167 | 1.000 | 0.746 |
| `Clinic` -> `facility_name` | 0.450 | 0.500 | 0.509 |

Header-only methods can move the aggregate only by raising `fuzzy_name` or by changing normalized strings before fuzzy runs. They do not replace `semantic_type` or `value_intent`, which already carry `contact` -> `email`.

---

## Summary decisions

| Method | Decision | One-line rationale |
|--------|----------|-------------------|
| Porter / Snowball stemming | **Reject** | Index explicitly avoids it; wrong tool for identifier tokens ([research-string-heuristics.md §2.2](./research-string-heuristics.md)). |
| Stop-token drop lists | **Defer** | Low cost, but blind drops risk false merges; neither fixture pair needs noise tokens removed. |
| Abbreviation / acronym expansion | **Defer** | COMA-style dictionaries help `cust`/`customer`, not `contact`/`email` or `Clinic`/`facility_name` without curated entries. |
| Small synonym tables | **Defer** | Same as abbrev expansion; high maintenance, sector-specific. |
| Phonetic codes (Soundex, Metaphone, NYSIIS) | **Reject** for default headers | Index warns on technical columns; English pronunciation does not encode semantics ([research-string-heuristics.md §2.2](./research-string-heuristics.md), [COMA PDF](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf)). |
| Token-set Jaccard | **Defer** | Cheap, but `token_set_ratio` already rewards subset overlap; measured token Jaccard is 0.000 on both fixture pairs. |
| Character n-grams (trigram Jaccard or Dice) | **Defer** | COMA default family; measured trigram Jaccard 0.000 on both pairs; adds code path overlap with RapidFuzz ratios. |
| TF-IDF on header tokens | **Reject** for v1 | Needs a corpus and IDF table; with three target fields per fixture, IDF is unstable and does not fix synonym headers. |
| Jaro-Winkler (RapidFuzz `distance.JaroWinkler`) | **Keep** | Documented in [architecture-frontier.md](./architecture-frontier.md) but absent from `fuzzy.py`; measured lift on `fuzzy_name` for `contact` -> `email`; closes default cutoff gap if fused as a fifth max term. |

Wired methods in the gap inventory (`ratio`, `WRatio`, `token_sort_ratio`, `token_set_ratio`, NFKC pipeline) are not repeated here.

---

## Stemming (Porter / Snowball)

**Status.** Documented-not-wired; [research-string-heuristics.md §2.2](./research-string-heuristics.md) lists stemming under "What not to do."

**Mechanism.** Porter and Snowball stemmers strip English inflectional suffixes for IR ([Porter stemmer definition](https://tartarus.org/martin/PorterStemmer/def.txt); [Snowball English stemmer](https://snowball.tartarus.org/algorithms/english/stemmer.html)).

**Complexity.** O(total token length) per identifier with a small rule set; stdlib-only ports exist, but the project bar allows RapidFuzz, not a stemmer dependency.

**In-process latency.** Sub-millisecond per column name at typical header lengths (under 40 characters). Dominated by Python token loop in `tokenize_identifier`, not stem rules.

**Fixture pairs (guess).** `contact` and `email` do not share a stem; `clinic` and `facility` do not. Stemming would not change normalized tokens for these strings, so `fuzzy_name` stays 0.167 and 0.450.

**Decision.** **Reject.** The research index already rejects stemming for schema tokens; wiring it fights that guidance and does not address the two sub-0.55 pairs.

---

## Stop-token drop lists

**Status.** Documented-not-wired ([research-string-heuristics.md §2.1 step 5](./research-string-heuristics.md)).

**Mechanism.** Remove allowlisted noise tokens (`tbl`, `dim`, `fk`, ...) before similarity. UAX #15 normalization is already wired as NFKC in `normalize_identifier` ([Unicode TR15](https://www.unicode.org/reports/tr15/)); stop lists are a separate optional step.

**Complexity.** O(number of tokens) with a fixed set lookup; stdlib `set` membership.

**In-process latency.** Negligible next to RapidFuzz.

**Fixture pairs (guess).** `contact` and `Clinic` are single-token headers. `facility_name` tokenizes to `facility` and `name`; dropping `name` might raise lexical match to `clinic` vs `facility`, but that requires a policy that strips generic suffix tokens and risks merging distinct fields company-wide.

**Decision.** **Defer.** Useful only with an explicit allowlist per integrator; not the lever for the README fixture pair that misses 0.55 by 0.001.

---

## Abbreviation expansion and small synonym tables

**Status.** Documented-not-wired ([gap §1](./research-classical-nlp-gap.md); [COMA PDF](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf) synonym and abbreviation steps).

**Mechanism.** Replace acronyms or map synonyms to token sets before token metrics (for example `PO` to `{purchase, order}`). COMA composes synonym matchers with n-gram and edit metrics ([Do and Rahm, 2002](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf) section 4).

**Complexity.** O(tokens times dictionary size) with a hash map; stdlib only.

**In-process latency.** Microseconds per header if the table stays small (hundreds of entries).

**Fixture pairs (guess).** No default table maps `contact` to `email` or `Clinic` to `facility_name` without domain knowledge. A healthcare integrator could add `clinic` -> `facility`, but that is product configuration, not a generic header method.

**Decision.** **Defer** for optional host-supplied tables. **Reject** as a required core dependency for the library default install.

---

## Phonetic codes (Soundex, Metaphone, NYSIIS)

**Status.** Documented-not-wired ([research-string-heuristics.md §7](./research-string-heuristics.md)).

**Mechanism.** Map strings to pronunciation keys for person-name linkage. COMA exposes Soundex on element names; the tejtm index warns that codes collapse distinct identifiers and miss abbreviations like `qty`/`quantity`.

**Complexity.** O(string length) per token; stdlib implementations are short; RapidFuzz does not ship phonetic encoders, so this is pure Python or a new optional dependency.

**In-process latency.** Still sub-millisecond per header.

**Fixture pairs (guess).** `contact` and `email` encode to different keys; `clinic` and `facility` likewise. Phonetic similarity does not encode "clinic means facility."

**Decision.** **Reject** for default column-to-field mapping in tejtm.

---

## Token-set Jaccard

**Status.** Documented-not-wired ([research-string-heuristics.md §4.3](./research-string-heuristics.md)).

**Mechanism.** \(J(A,B) = |A \cap B| / |A \cup B|\) on token sets from `tokenize_identifier`.

**Complexity.** O(|A| + |B|) with small sets; stdlib sets.

**In-process latency.** Negligible.

**Fixture pairs (measured).** After `normalize.py` tokenization, token Jaccard is **0.000** for `contact` vs `email` and for `Clinic` vs `facility_name` (local probe, same normalization as production).

**Effect on aggregate (inferred).** Adding Jaccard to the fuzzy max without beating existing RapidFuzz scores leaves `fuzzy_name` unchanged, so aggregates stay 0.549 and 0.480.

**Decision.** **Defer.** Useful for debugging or a COMA-style parallel matcher; low priority because `token_set_ratio` already covers subset-style header overlap (note `Clinic` already reaches fuzzy 0.450 via wired metrics).

---

## Character n-grams (trigram Jaccard)

**Status.** Documented-not-wired ([research-string-heuristics.md §5](./research-string-heuristics.md); COMA Digram/Trigram matchers).

**Mechanism.** Build character q-gram sets on normalized strings; compare with Jaccard or Dice.

**Complexity.** O(L) per string of length L; stdlib sets.

**In-process latency.** Microseconds for L under 40.

**Fixture pairs (measured).** Trigram Jaccard **0.000** on both pairs (local probe on normalized strings).

**Decision.** **Defer.** Aligns with COMA priors but duplicates signal already captured by `ratio`/`WRatio` on short strings; no measured path to 0.55 on the two README pairs.

---

## TF-IDF on header tokens

**Status.** Not wired for headers. Gap inventory cites instance-level TF-IDF via Valentine ([research-classical-nlp-gap.md §4](./research-classical-nlp-gap.md)). Header TF-IDF would treat target field tokens as a mini-corpus and compare column token vectors.

**Mechanism.** Term frequency in the header times inverse document frequency across fields in the target schema.

**Complexity.** O(F times L) to build IDF over F fields once per schema, O(tokens) per pair; stdlib plus arithmetic.

**In-process latency.** Still in-process and small for F under 100, but vector bookkeeping exceeds a single RapidFuzz call.

**Fixture pairs (guess).** Each healthcare fixture exposes three fields. Rare tokens like `facility` get moderate IDF, but `contact` shares no token with `email`, so cosine similarity stays near zero. IDF does not solve intentional synonym headers (`contact` holding emails).

**Decision.** **Reject** for v1 header matching. Revisit only with larger target schemas and labeled calibration data.

---

## Jaro-Winkler (architecture gap)

**Status.** Documented-not-wired. [architecture-frontier.md](./architecture-frontier.md) lists Jaro-Winkler in the FuzzyName row; [`fuzzy.py`](../src/tejtm/scorers/fuzzy.py) imports only `rapidfuzz.fuzz`, not `distance.JaroWinkler` ([gap §2](./research-classical-nlp-gap.md)).

**Mechanism.** Jaro similarity on matching characters within a window; Jaro-Winkler adds a prefix scale with default prefix weight 0.1 ([RapidFuzz JaroWinkler](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/JaroWinkler.html)). [research-string-heuristics.md §3.4](./research-string-heuristics.md) and the starter recipe in section 12 show fusion via `max(..., normalized_similarity * 100)`.

**Complexity.** O(L) per pair; implemented in RapidFuzz C++ ([JaroWinkler performance notes](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/JaroWinkler.html)).

**In-process latency.** Same order as existing fuzz calls: microseconds per candidate on short headers. A fifth metric in the existing candidate loop adds one C++ call per candidate, not a new dependency.

**Fixture pairs (measured).** On normalized strings from `normalize.py`:

| Column | Candidate | Wired fuzzy max | Jaro-Winkler |
|--------|-----------|-----------------|--------------|
| `contact` | `email` | 0.167 | 0.448 |
| `contact` | `e mail` (alias) | 0.154 | 0.437 |
| `Clinic` | `facility_name` | 0.450 | 0.575 |

**Effect on aggregate at 0.55 (inferred).** With only fuzzy, semantic, and value weights active (no exact match), raising `fuzzy_name` to the max including Jaro-Winkler changes the weighted mean linearly:

- `contact` -> `email`: fuzzy 0.167 to 0.448 gives aggregate about **0.675**, above 0.55.
- `Clinic` -> `facility_name`: fuzzy 0.450 to 0.575 gives aggregate about **0.536**, still below 0.55.

Jaro-Winkler therefore fixes the near-miss at default cutoff for `contact` -> `email` if wired exactly like the index recipe (max fusion inside `fuzzy_name`). It does not alone lift `Clinic` -> `facility_name` to 0.55; that pair still needs lower cutoff, stronger value or type signals, or embeddings.

**Decision.** **Keep.** Closes the documented architecture drift and addresses one of two README pairs at default `min_confidence` with no new dependency.

---

## Primary references

| Topic | Source |
|-------|--------|
| COMA composition and n-gram/synonym matchers | [COMA PDF](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf) |
| RapidFuzz fuzz and distance APIs | [RapidFuzz usage index](https://rapidfuzz.github.io/RapidFuzz/Usage/index.html) |
| Unicode normalization | [Unicode TR15](https://www.unicode.org/reports/tr15/) |
| Porter stemmer | [Porter definition](https://tartarus.org/martin/PorterStemmer/def.txt) |
| Snowball English stemmer | [Snowball English algorithm](https://snowball.tartarus.org/algorithms/english/stemmer.html) |
| Gap inventory | [research-classical-nlp-gap.md](./research-classical-nlp-gap.md) |

---

*Header-only classical NLP research on branch `research/classical-nlp-headers`. Revise when `fuzzy.py` or fixture thresholds change.*
