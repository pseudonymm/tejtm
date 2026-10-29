# Value-sample classical methods: keep, defer, reject

Research note for **leftover cheap non-neural signals** that compare **sample cell values** when mapping import columns to canonical fields. It follows the gap inventory in [research-classical-nlp-gap.md](./research-classical-nlp-gap.md) (commit `04bf22c`), skips anything already wired in `value_profile.py` or `typing/detectors.py`, and does not treat the regex type catalog as a keep list.

**Mode.** Explanation with a decision table. No implementation, no new dependencies, no sklearn or neural models in core.

---

## Yardstick and what is already wired

**Fixture results (measured 29 Oct 2026, FastEmbed absent).** README.md and `tests/support/fixture_stats.py` report **17 of 17** expected pairs mapped at each fixture’s `min_confidence`, and **15 of 17** at the library default **`0.55`**. The two pairs below default are `contact` → `email` in `crm_contacts` (**0.549**) and `Clinic` → `facility_name` in `healthcare_appointments` (**0.480**). No new accuracy numbers were measured for the methods below.

**Wired value path today.**

| Piece | Role |
| --- | --- |
| `value_signature()` | Runs `detect_semantic_type` on samples, then scalar shape stats (length, digit, space, distinct, upper ratios) and a dominant token prefix bucket. |
| `signature_similarity()` | Blends type compatibility (0.45), shape distance (0.35), and prefix equality (0.20). |
| `ValueIntentScorer` | Takes the **max** of type-profile similarity to `expectation_from_type`, exemplar-profile similarity when `exemplar_samples` exist, and optional description embedding when FastEmbed is present. |

Instance **set overlap**, **TF-IDF column vectors**, and **character n-gram profiles of cell text** are named in the gap inventory but are **not** in `value_profile.py`. Header trigrams and RapidFuzz name metrics are wired elsewhere and are out of scope here.

**Architectural constraint.** Valentine and COMA instance matchers usually compare **two populated columns** ([Valentine matchers — Coma instance](https://delftdata.github.io/valentine/matchers/), [COMA PDF](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf) as cited in [research-prior-art.md](./research-prior-art.md)). tejtm’s target side is mostly **metadata** plus optional **`exemplar_samples`**, not a full reference column. Any instance method must say what it compares on the field side.

---

## Comparison baseline: `value_signature` and `ValueIntentScorer`

**`value_signature`** summarizes each column (or exemplar list) into one struct. It does not retain individual cell strings after prefix bucketing, so two columns with the same stats but different literals can score identically.

**`ValueIntentScorer`** does not fuse overlap into the weighted engine mean as its own scorer. It contributes one **max** subscore per column–field pair. Methods that only help when exemplars exist compete with `exemplar:{sim}` from `signature_similarity`, not with name or `semantic_type` unless you add a new scorer and weight.

**Sherlock ([SHERLOCK] in [primary-sources.md](./primary-sources.md)).** The published system uses **1,588** hand-crafted features per column (statistics, character distributions, GloVe, paragraph vectors) fed to a **deep network**. The abstract reports support-weighted **F1 ≈ 0.89** on a 78-type task. That full stack violates this note’s bar (neural head, embedding tables, training corpus). This note only considers **non-neural slices** of the same feature families on **values**.

---

## Methods not wired (value-sample focus)

Complexity uses **S** = number of sample strings per column (fixtures: 2–3 rows), **T** = exemplar count when present, **L** = average string length, **P** = source columns × target fields scored, **V** = distinct tokens or n-grams in the run. Latency is **order-of-magnitude inference** from algorithm bounds and Valentine’s Coma performance note (schema-only vs `use_instances=True` on ~100 columns). **No in-process timings were run in this worktree.**

### 1. Exact value-set Jaccard (normalized cell strings)

**Idea.** Casefold and strip each sample; \(J = |A \cap B| / |A \cup B|\) for sets \(A\) (column samples) and \(B\) (`field.exemplar_samples` or an explicit reference set). COMA and Valentine treat instance overlap as a first-class disambiguator ([research-prior-art.md §5](./research-prior-art.md); [research-string-heuristics.md](./research-string-heuristics.md) scope line).

| | |
| --- | --- |
| Complexity | **O(S + T)** per pair after sets are built; **O(S)** once per column. |
| In-process latency | Negligible at fixture scale (sets of size ≤ 3). For **P** pairs, **O(P · (S+T))** with tiny constants. |
| vs wired | Literal overlap when exemplars list the same tokens as the file. `signature_similarity` on exemplars ignores whether `WH-1001` appears; it compares type and aggregate shape. |
| Fixture plausibility at **0.55** | **Inferred, not measured.** Scenarios with `exemplar_samples` (`warehouse_inventory`, `edge_duplicate_generic_headers`, parts of `finance_ledger`) could rank the intended field higher when samples match exemplar strings exactly. Scenarios without exemplars (`crm_contacts`, `healthcare_appointments` facility field) get **no signal**. Unlikely to fix **`contact` → `email`** (no email exemplars; overlap is not the missing cue). Unlikely to fix **`Clinic` → `facility_name`** without facility exemplars. |
| **Verdict** | **Keep** as an optional signal **when `exemplar_samples` is non-empty**, normalized exact equality only. |

### 2. Token-set Jaccard on cell values

**Idea.** Split each cell on whitespace (or a small separator set); Jaccard over **token multisets** or sets aggregated across rows ([Jaccard index](https://en.wikipedia.org/wiki/Jaccard_index); COMA n-gram family on strings in [research-string-heuristics.md §4.3–§5](./research-string-heuristics.md)).

| | |
| --- | --- |
| Complexity | **O(S · w + T · w')** to build token sets; **w** = tokens per cell. |
| In-process latency | Still sub-millisecond per pair at fixture sizes. |
| vs wired | Partially redundant with `detect_semantic_type` for emails, phones, and dates where regex already fires. Adds little when values are single-token codes. |
| Fixture plausibility at **0.55** | **Inferred.** Weak for **`contact` → `email`** (tokens are whole addresses). Weak for **`Clinic` → `facility_name`** (free-text clinic names vs no target tokens). |
| **Verdict** | **Defer.** Exact string Jaccard (§1) covers the exemplar case with less ambiguity. |

### 3. Fuzzy value-set Jaccard / Tversky (Valentine `JaccardDistanceMatcher` lineage)

**Idea.** Treat each distinct sample as a set element; declare two values equal if Levenshtein, Jaro–Winkler, or another string distance exceeds a threshold; compute Jaccard or Tversky ([Valentine README — JaccardDistanceMatcher](https://raw.githubusercontent.com/delftdata/valentine/master/README.md)).

| | |
| --- | --- |
| Complexity | **O(|A| · |B| · L²)** for naive Levenshtein per pair of distinct values; Tversky same order. |
| In-process latency | Small **S**, **T** keep this acceptable in-process without sklearn; still heavier than exact Jaccard. |
| vs wired | Typos in codes could match exemplars; tejtm fixtures use clean synthetic strings, so benefit is unproven here. |
| Fixture plausibility at **0.55** | **Inferred.** No fixture row requires fuzzy equality to separate fields. |
| **Verdict** | **Defer** until real uploads show typoed codes against exemplars. **Reject** the **Embedding** inner distance (neural extra). |

### 4. TF-IDF instance matching (COMA / Valentine Coma `use_instances=True`)

**Idea.** Each cell value is a “document”; build a global IDF over all values in scope; form a sparse vector per column; cosine similarity between columns, aggregated with a max-matching Dice-style formula ([Valentine README](https://raw.githubusercontent.com/delftdata/valentine/master/README.md); [Valentine matchers — Coma instance](https://delftdata.github.io/valentine/matchers/)).

| | |
| --- | --- |
| Complexity | **O(total cells · L)** to tokenize and count; **O(V)** vocabulary; **O(P · dim)** for column–field comparisons if field side is a pseudo-column of exemplars or reference values. |
| In-process latency | Valentine documents Coma with instances as **roughly tens of milliseconds to seconds** once column counts reach **~100** with instances enabled; fixture grids (**≤3 × ≤3** pairs, **≤3** rows) would be **far smaller** if implemented with the same shape. Dominant cost is **building the corpus once per `propose_mappings` call**, not per pair. |
| vs wired | Captures **shared rare tokens** across columns (COMA instance lineage in [research-prior-art.md](./research-prior-art.md)). tejtm already down-weights generic tokens via semantic typing for structured formats. Does not replace `expectation_from_type` profiles. |
| Fixture plausibility at **0.55** | **Inferred.** Three-row tables give **tiny IDF**; `@` in emails and shared date patterns may correlate columns but **`semantic_type` already uses those patterns**. Unlikely to lift **`contact` → `email`** by 0.001 without also changing weights. **`Clinic` → `facility_name`** needs name or semantic lift, not shared tokens alone. |
| **Verdict** | **Defer.** Worth a prototype when **many columns** and **junk headers** co-occur; needs a defined IDF scope (source-only vs source+exemplars). Pure-Python TF counts fit the dependency bar; pulling Valentine as a library does not. |

### 5. Character n-grams of **values** (Dice / Jaccard on q-gram sets)

**Idea.** For each column, union character n-grams (typically **q = 3**) over all sample strings; compare sets with Dice or Jaccard ([COMA PDF §4.1](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf) via [research-string-heuristics.md §5](./research-string-heuristics.md); Sherlock “character distributions” in [SHERLOCK]).

| | |
| --- | --- |
| Complexity | **O(S · L · q)** to build sets; set Jaccard **O(|G1| + |G2|)**. |
| In-process latency | At fixture **L**, gram sets stay small; cost scales linearly with total characters in samples. |
| vs wired | Overlaps with digit and length ratios in `ValueSignature` but adds **substring** sensitivity (e.g. shared `ORD-` prefixes, `@` runs in emails). Still not literal exemplar match. |
| Fixture plausibility at **0.55** | **Inferred.** May reinforce **`edge_duplicate_generic_headers`** (distinct `ORD-` vs `SHP-` prefixes) where prefix bucket already fires. Redundant with **`semantic_type`** for structured types. Does not address **`Clinic` → `facility_name`** header gap. |
| **Verdict** | **Defer** as a low-weight feature inside a future value scorer, not as a standalone matcher, unless profiling shows prefix bucket misses. |

### 6. Distribution-based histogram matching (`DistributionBased`)

**Idea.** Quantile histograms per column and Earth Mover’s Distance, instances only ([Valentine matchers — DistributionBased](https://delftdata.github.io/valentine/matchers/); SIGMOD 2011 paper linked there).

| | |
| --- | --- |
| Complexity | Histogram bins over numeric or categorical domains; EMD **superlinear** in bin count; clustering phases in the reference algorithm. |
| In-process latency | Heavy relative to other rows in this table for **S = 2–3** samples (unstable histograms). |
| vs wired | `ValueSignature` already carries coarse numeric shape via digit ratio and avg length. |
| Fixture plausibility at **0.55** | **Inferred.** Poor fit for tiny samples; no fixture requires EMD to disambiguate. |
| **Verdict** | **Reject** for tejtm core at current sample sizes. |

### 7. dedupe-style learned field comparators

**Idea.** Train weights on labeled pairs ([dedupe docs](https://docs.dedupe.io/en/latest/) via [research-prior-art.md §4.6](./research-prior-art.md)).

| | |
| --- | --- |
| Complexity | Training loop, blocking, and model serialization dominate. |
| In-process latency | Fast at inference after training; setup is not in-process mapping. |
| vs wired | Solves record linkage, not schema metadata mapping, unless the host supplies large labeled column pairs. |
| Fixture plausibility at **0.55** | **Not applicable** without labels. |
| **Verdict** | **Reject** for core (scope and dependency posture). |

### 8. Sherlock non-neural column features (value-only subset)

| Feature slice | Complexity / latency | vs wired | Fixture plausibility at **0.55** | Verdict |
| --- | --- | --- | --- | --- |
| Extended column stats (min, max, std, entropy of string lengths or numeric parses) | **O(S · L)** per column | Overlaps `avg_length`, `distinct_ratio`; adds tail sensitivity | **Inferred.** Fixtures too small for stable entropy | **Defer** |
| Character-class histograms (digit, punct, alpha shares) | **O(S · L)** | Overlaps `digit_ratio`, `space_ratio`, `uppercase_ratio` | **Inferred.** Marginal over current ratios | **Defer** |
| GloVe mean over in-vocabulary tokens in cells | Requires embedding table and OOV handling ([SHERLOCK]; [GLOVE] in primary-sources) | Richer than regex types for English free text | **Inferred.** Not measured; adds dependency surface | **Reject** for core |
| Paragraph vectors / any neural encoder on values | Inference-bound | Competes with optional FastEmbed description path | N/A under “no neural in core” | **Reject** |
| Full 1,588-dim vector + Sherlock NN | Training and inference cost of published system | Replaces, not complements, `detect_semantic_type` | Benchmark F1 on VizNet, not tejtm fixtures | **Reject** |

---

## Summary decisions

| Method | Verdict | Primary reason |
| --- | --- | --- |
| Exact normalized value-set Jaccard vs `exemplar_samples` | **Keep** | Cheap; targets literal pattern overlap exemplars encode; gap inventory §4 |
| Token Jaccard on cell tokens | **Defer** | Redundant with §1 or `semantic_type` on fixtures |
| Fuzzy Jaccard / Tversky on values | **Defer** | Cost without fixture evidence; reject embedding inner metric |
| TF-IDF column instance matcher | **Defer** | Classic COMA/Valentine signal; needs IDF scope design; tiny fixtures unlikely to move **0.55** yardstick |
| Character n-grams on values | **Defer** | Sherlock-adjacent; partial overlap with prefix bucket and type detectors |
| DistributionBased / EMD | **Reject** | Wrong sample size regime |
| dedupe learned comparators | **Reject** | Wrong problem and training burden |
| Sherlock GloVe / NN / full feature stack | **Reject** | Dependencies and neural bar |

**Net effect on 17 fixture pairs at default 0.55 (qualitative).** Nothing in the **Keep** row applies to the two sub-threshold pairs, because those fields lack exemplars and the failures are **aggregate confidence** (`contact` vs `email` header, **`Clinic` vs `facility_name` name**), not missing literal overlap. **Keep** methods mainly defend **exemplar-driven** scenarios already served in part by `signature_similarity`. **Defer** methods need measurement on larger, dirtier extracts before they earn weight in `aggregate_scores`.

---

## References

| ID | Source |
| --- | --- |
| Gap inventory | [research-classical-nlp-gap.md](./research-classical-nlp-gap.md) (`04bf22c`), §4 |
| COMA | [Do & Rahm, 2002 PDF](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf) |
| Valentine Coma / Jaccard / DistributionBased | [Matchers documentation](https://delftdata.github.io/valentine/matchers/), [README](https://raw.githubusercontent.com/delftdata/valentine/master/README.md) |
| Instance overlap pattern | [research-prior-art.md §5](./research-prior-art.md) |
| Value Jaccard in lexical index | [research-string-heuristics.md](./research-string-heuristics.md) |
| Sherlock features | [SHERLOCK] in [primary-sources.md](./primary-sources.md) |
| Wired code | `src/tejtm/value_profile.py`, `src/tejtm/scorers/value_intent.py` |
| Fixture yardstick | `tests/support/fixture_stats.py`, README.md (measured 29 Oct 2026) |

---

*Branch `research/classical-nlp-values`. Value-sample slice of classical NLP research; revise when `value_profile.py` or fixtures change.*
