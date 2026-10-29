# Classical text methods: wired vs research index

Gap inventory for **cheap non-neural** column-to-field signals in tejtm. Compares implementation in `normalize.py`, `scorers/exact.py`, `scorers/fuzzy.py`, `typing/detectors.py`, `value_profile.py`, and `scorers/header_embedding.py` (boundary only) against the indexes `research-string-heuristics.md`, `research-type-detection.md`, and `research-prior-art.md`. Those three files point at primary sources (engine, [RapidFuzz](https://rapidfuzz.github.io/RapidFuzz/Usage/index.html), [Unicode UAX #15](https://www.unicode.org/reports/tr15/), [COMA PDF](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf), frictionless/messytables repos, and related papers). This note does not recommend keep or reject.

**Status labels**

| Status | Meaning |
|--------|---------|
| Wired | Implemented in the scoped modules under `src/tejtm/` (or only reachable from them on the mapping path). |
| Documented-not-wired | Named in one of the three research indexes (or their cited primaries) for header, type, or value disambiguation, but not implemented in those scoped modules. |
| Undocumented | Implemented in a scoped module but not named in the three research indexes. |

**Neural boundary.** `HeaderEmbeddingScorer` and the description branch in `value_intent` use FastEmbed ([research-semantic-similarity.md](./research-semantic-similarity.md)). They are out of scope for the classical inventory except where noted.

**Fixture context (measured 29 Oct 2026).** With FastEmbed absent, README.md reports all 17 expected fixture pairs map at per-fixture `min_confidence` thresholds using `exact_name`, `fuzzy_name`, `semantic_type`, and `value_intent` only; `header_embedding` abstained. That run does not exercise every row in the tables below.

---

## 1. Name normalization and candidate strings

Primary pipeline in [research-string-heuristics.md §2](./research-string-heuristics.md) and [research-prior-art.md §5.1](./research-prior-art.md). Implementation: `src/tejtm/normalize.py`.

| Method | Status | Evidence |
|--------|--------|----------|
| Unicode normalization before compare | Wired | `unicodedata.normalize("NFKC", ...)` in `normalize_identifier` / `tokenize_identifier`. Research index recommends NFC ([UAX #15](https://www.unicode.org/reports/tr15/)); NFKC is stricter compatibility normalization, not called out in the index. |
| NFC (or NFD) as the chosen form | Documented-not-wired | [research-string-heuristics.md §2.1](./research-string-heuristics.md) step 1; code uses NFKC instead. |
| Case folding / lowercase | Wired | `.casefold()` after normalize ([COMA name matching assumption](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf) cited in index). |
| Separator harmonization (`-`, `.`, `/`, space to one delimiter) | Wired | `_NON_ALNUM` maps punctuation to spaces; underscores split in `tokenize_identifier`. Matches index step 3 in spirit. |
| camelCase / PascalCase token split | Wired | `_CAMEL_BOUNDARY` in `tokenize_identifier` ([COMA Name tokenization](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf) §4.2, cited in index). |
| Per-token re-normalization after split | Undocumented | Each camel/snake piece runs through `normalize_identifier` again; index describes a single pipeline, not this two-pass token loop. |
| Stop-token drop list (`tbl`, `dim`, `fk`, …) | Documented-not-wired | [research-string-heuristics.md §2.1](./research-string-heuristics.md) step 5. |
| Abbreviation / acronym expansion dictionary | Documented-not-wired | [research-string-heuristics.md §2.1](./research-string-heuristics.md) step 6; [COMA PDF](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf) synonym step. |
| Domain cleaners (e.g. company suffix strip) | Documented-not-wired | [research-prior-art.md §4.8](./research-prior-art.md) [cleanco](https://pypi.org/project/cleanco/). |
| `candidate_names(field_id, labels, aliases)` deduped normalized strings | Undocumented | Used by name scorers; indexes discuss aliases in products, not this helper. |
| Porter / NLP stemming on identifiers | Documented-not-wired | [research-string-heuristics.md §2.2](./research-string-heuristics.md) (explicit avoid). |

---

## 2. Header string similarity (lexical scorers)

Indexes: [research-string-heuristics.md §3 to §5, §8.3 to §8.4](./research-string-heuristics.md), [research-prior-art.md §4.5](./research-prior-art.md). Wired surface: [`scorers/exact.py`](src/tejtm/scorers/exact.py), [`scorers/fuzzy.py`](src/tejtm/scorers/fuzzy.py).

| Method | Status | Evidence |
|--------|--------|----------|
| Exact match on normalized full string | Wired | `ExactNameScorer`: `col in candidate_names(...)`. |
| `rapidfuzz.fuzz.ratio` (normalized Indel, 0 to 100 scaled) | Wired | `FuzzyNameScorer` ([RapidFuzz fuzz.ratio](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html)). |
| `rapidfuzz.fuzz.WRatio` | Wired | `FuzzyNameScorer`; index describes length-dependent mix with `partial_ratio` ([RapidFuzz WRatio / fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy/blob/master/fuzzywuzzy/fuzz.py)). |
| `token_sort_ratio` on token-joined column string | Wired | `FuzzyNameScorer` uses `" ".join(tokenize_identifier(column.name))` ([RapidFuzz token_sort_ratio](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html)). |
| `token_set_ratio` on same token string | Wired | Same loop in `FuzzyNameScorer`. |
| Max over candidates and over metrics | Wired | `best = max(best, max(scores))`; mirrors COMA **Max** at metric level ([research-string-heuristics.md §8.2](./research-string-heuristics.md)). |
| `partial_ratio` as its own scorer | Documented-not-wired | [research-prior-art.md §4.5](./research-prior-art.md) table; only indirect via `WRatio` in code. |
| `token_ratio` (unordered multiset ratio) | Documented-not-wired | [RapidFuzz fuzz module](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html); not called in `fuzzy.py`. |
| Levenshtein / weighted Levenshtein distance | Documented-not-wired | [research-string-heuristics.md §3.1](./research-string-heuristics.md); [RapidFuzz Levenshtein](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/Levenshtein.html). `ratio` is Indel-related, not explicit Levenshtein API. |
| Damerau-Levenshtein | Documented-not-wired | [research-string-heuristics.md §3.2](./research-string-heuristics.md). |
| Jaro / Jaro-Winkler | Documented-not-wired | [research-string-heuristics.md §3.4](./research-string-heuristics.md); starter recipe §8.4; [architecture-frontier.md](./architecture-frontier.md) names JW for FuzzyName but `fuzzy.py` does not import `distance.JaroWinkler`. |
| Token-set Jaccard index | Documented-not-wired | [research-string-heuristics.md §4.3](./research-string-heuristics.md); [Jaccard index](https://en.wikipedia.org/wiki/Jaccard_index). |
| Character n-gram / trigram (Dice, Jaccard) | Documented-not-wired | [research-string-heuristics.md §5](./research-string-heuristics.md); [COMA PDF](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf) §4.1. |
| Monge-Elkan token inner distance | Documented-not-wired | [research-string-heuristics.md §4.4](./research-string-heuristics.md). |
| Smith-Waterman / Needleman-Wunsch / Gotoh alignment | Documented-not-wired | [research-string-heuristics.md §6](./research-string-heuristics.md). |
| Soundex / Metaphone / NYSIIS | Documented-not-wired | [research-string-heuristics.md §7](./research-string-heuristics.md); [jellyfish README](https://github.com/jamesturk/jellyfish/blob/master/README.md). |
| `rapidfuzz.process.extract` / `cdist` blocking | Documented-not-wired | [research-prior-art.md §4.5](./research-prior-art.md); [RapidFuzz process](https://rapidfuzz.github.io/RapidFuzz/Usage/process.html). Engine scores full column-field grid without `cdist`. |
| Fellegi-Sunter / Winkler bin weights | Documented-not-wired | [research-string-heuristics.md §8.1](./research-string-heuristics.md); [Winkler 1990 PDF](https://www.stat.cmu.edu/NCRN/PUBLIC/RLClassFiles/HW/Winkler1990.pdf). |
| COMA cube aggregation (Min, Average, directional MaxN) | Documented-not-wired | [research-string-heuristics.md §8.2](./research-string-heuristics.md); cross-scorer fusion in tejtm is a **weighted mean** in `aggregate_scores` (`scorers/base.py`), not in the six-file scope. |
| Valentine / Coma / Cupid matcher packages | Documented-not-wired | [research-prior-art.md §3.4 and §3.5](./research-prior-art.md); [Valentine README](https://raw.githubusercontent.com/delftdata/valentine/master/README.md). |

---

## 3. Semantic type detection from cell samples

Index: [research-type-detection.md](./research-type-detection.md). Wired: [`typing/detectors.py`](src/tejtm/typing/detectors.py) (also consumed by `SemanticTypeScorer` outside this file list).

| Method | Status | Evidence |
|--------|--------|----------|
| Per-type predicate + sample **match rate**; winner by max rate | Wired | `detect_semantic_type`: ordered checks, `best_rate` threshold 0.5 for non-`freetext`. Aligns with index § "Semantic promotion" and validators heuristic, not identical to messytables weights. |
| Regex / strict literal email | Wired | `_EMAIL` anchor pattern; index cites `validators.email` and frictionless format ([validators](https://github.com/python-validators/validators)). |
| Regex URL with `http(s)://` | Wired | `_URL`; stricter than ydata `urlparse` scheme+netloc or frictionless URI ([research-type-detection.md § ydata / frictionless](./research-type-detection.md)). |
| Regex UUID | Wired | `_UUID`; index frictionless `format: uuid`. |
| Heuristic phone (digit count, not pure digits) | Wired | `_PHONE` + `_is_phone`; index contrasts regex ([clean-text PHONE_REGEX](https://github.com/jfilter/clean-text/blob/main/cleantext/constants.py)) vs [libphonenumber](https://github.com/google/libphonenumber/blob/master/README.md). |
| ISO `YYYY-MM-DD` + `strptime` verify | Wired | `_DATE`; index messytables `DateType` / frictionless `date`. |
| ISO-like datetime prefix | Wired | `_DATETIME`; not full `dateutil` fuzzy parse. |
| Time `HH:MM(:SS)` | Wired | `_TIME`; in frictionless candidate list in index table; not highlighted in tejtm research table row. |
| Boolean token set | Wired | `_BOOL`; overlaps messytables / frictionless ideas in index. |
| Currency symbol + grouped number regex | Wired | `_CURRENCY`; index messytables `CurrencyType` and clean-text `CURRENCY_REGEX`. |
| Integer vs float parse (`int` / `float` with comma strip) | Wired | `_is_int`, `_is_number`; index frictionless integer/number candidates and pandas kinds. |
| `type_compatibility` with related-type pairs | Undocumented | `integer`/`number`, `date`/`datetime`, etc.; not spelled out in the three indexes. |
| `validators` library calls | Documented-not-wired | [research-type-detection.md § validators](./research-type-detection.md). |
| `dateutil.parser.parse` (incl. fuzzy) | Documented-not-wired | [research-type-detection.md § dateutil](./research-type-detection.md); messytables `DateUtilType`. |
| `pd.to_datetime` / `pd.to_numeric` probes | Documented-not-wired | [research-type-detection.md § ydata / pandas](./research-type-detection.md). |
| messytables weighted `guessing_weight` + strict mode | Documented-not-wired | [messytables types.py](https://github.com/okfn/messytables/blob/master/messytables/types.py). |
| frictionless ordered candidate race + 0.9 confidence | Documented-not-wired | [detector.py](https://github.com/frictionlessdata/frictionless-py/blob/main/frictionless/detector/detector.py), [settings.py](https://github.com/frictionlessdata/frictionless-py/blob/main/frictionless/settings.py). |
| ydata / Visions relation graph (Text to Numeric, URL optional) | Documented-not-wired | [typeset_relations.py](https://github.com/Data-Centric-AI-Community/fg-data-profiling/blob/develop/src/data_profiling/model/typeset_relations.py). |
| pandas `infer_dtype` on materialized values | Documented-not-wired | [pandas infer_dtype](https://pandas.pydata.org/docs/reference/api/pandas.api.types.infer_dtype.html). |
| clean-text regex library as pattern source | Documented-not-wired | [clean-text constants.py](https://github.com/jfilter/clean-text/blob/main/cleantext/constants.py). |
| libphonenumber / `phonenumbers` validation ladder | Documented-not-wired | [research-type-detection.md § libphonenumber](./research-type-detection.md). |
| Postal address inference | Documented-not-wired | [research-type-detection.md § Gaps](./research-type-detection.md). |
| Cardinality-based Categorical vs Text | Documented-not-wired | [research-type-detection.md § ydata](./research-type-detection.md). |

---

## 4. Value profiles, shape stats, and instance overlap

Indexes: [research-string-heuristics.md](./research-string-heuristics.md) (value Jaccard in scope line), [research-type-detection.md § Practical composition](./research-type-detection.md), [research-prior-art.md §5.3](./research-prior-art.md) (instance overlap). Wired: [`value_profile.py`](src/tejtm/value_profile.py).

| Method | Status | Evidence |
|--------|--------|----------|
| Reuse `detect_semantic_type` on column samples | Wired | `value_signature` calls `detect_semantic_type`. |
| Scalar shape features (length, digit/space/upper ratios, distinct ratio) | Wired | `ValueSignature` fields; related to infermap "profile stats" in [research-prior-art.md §3.4](./research-prior-art.md) but not enumerated there. |
| Dominant token prefix bucket (`-` prefix or first 3 chars) | Undocumented | `_dominant_prefix`; rolodexter "value-shape heuristics" cited in prior art without this rule. |
| Fixed expectation profiles per semantic type | Undocumented | `expectation_from_type` table; not in the three indexes. |
| Blended similarity (type + shape + prefix weights 0.45 / 0.35 / 0.20) | Undocumented | `signature_similarity`; not in indexes. |
| Loose type pairs when compatibility score is zero | Undocumented | `_types_loosely_compatible`. |
| **Value-set Jaccard** on sample cell strings | Documented-not-wired | [research-string-heuristics.md](./research-string-heuristics.md) scope; Valentine / COMA instance matchers in [research-prior-art.md §5.3](./research-prior-art.md). |
| Distribution / TF-IDF instance matchers | Documented-not-wired | [Valentine README](https://raw.githubusercontent.com/delftdata/valentine/master/README.md) via prior art. |
| dedupe-style learned field comparators | Documented-not-wired | [research-prior-art.md §4.6](./research-prior-art.md). |

---

## 5. Neural scorers (boundary)

| Method | Status | Evidence |
|--------|--------|----------|
| Header name embedding cosine (FastEmbed MiniLM) | Wired (neural) | [`scorers/header_embedding.py`](src/tejtm/scorers/header_embedding.py); optional extra in [research-semantic-similarity.md](./research-semantic-similarity.md), not the three classical indexes. |
| Value vs field description embedding | Wired (neural) | `_description_value_embedding_score` in `value_intent.py` imports header embedder; classical indexes do not describe it. |

---

## 6. Cross-index summary

Counts are **method rows** in sections 1 to 4 (excluding neural §5). One method can appear once.

| Status | §1 Normalization | §2 Header lexical | §3 Type detection | §4 Value profile | Total |
|--------|------------------|-------------------|-------------------|------------------|-------|
| Wired | 4 | 6 | 11 | 2 | 23 |
| Documented-not-wired | 5 | 18 | 12 | 3 | 38 |
| Undocumented | 2 | 0 | 1 | 4 | 7 |

**Interpretation.** tejtm already wires a **narrow RapidFuzz bundle** (ratio, WRatio, token sort/set) plus **NFKC normalization**, **exact normalized match**, and a **regex-first type ladder** with **hand-tuned value shape stats**. The research indexes catalog a much wider classical surface (edit distances, Jaro-Winkler, n-grams, phonetic codes, alignment, COMA/Valentine composition, frictionless/messytables races, validators/dateutil/libphonenumber, instance Jaccard) that does not appear in the scoped modules. Seven behaviors are **undocumented** in the three indexes, including NFKC choice, `candidate_names`, extra type-compatibility pairs, and the full value-signature blend.

---

## 7. Primary references (quick links)

| Topic | URL |
|-------|-----|
| COMA | https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf |
| RapidFuzz usage | https://rapidfuzz.github.io/RapidFuzz/Usage/index.html |
| Unicode normalization (UAX #15) | https://www.unicode.org/reports/tr15/ |
| Frictionless Table Schema | https://specs.frictionlessdata.io/table-schema/ |
| messytables types | https://github.com/okfn/messytables/blob/master/messytables/types.py |
| Valentine matchers | https://delftdata.github.io/valentine/matchers/ |

See also [primary-sources.md](./primary-sources.md) for COMA PDF mirrors and embedding IDs.

---

*Gap inventory for tejtm classical NLP on branch `research/classical-nlp-gap`. Revise when scoped modules or research indexes change.*
