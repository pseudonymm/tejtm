# String similarity for schema and column name matching

Research notes on metrics, normalization, libraries, and composite scoring for aligning database column (or schema element) names across heterogeneous sources. Primary sources are papers, official library documentation, and reference implementations—not blog summaries.

**Scope.** These methods score *lexical* similarity of identifiers. They complement (not replace) datatype checks, instance overlap (value Jaccard), embedding similarity, and human confirmation. Schema-matching systems such as COMA treat name similarity as one matcher among many ([Do & Rahm, 2002](#ref-coma)).

---

## 1. Problem shape

Column names are short, structured tokens: `customer_id`, `CustomerID`, `cust_id`, `id_customer`. Typical failure modes:

| Failure mode | Example | Metric family that helps |
|--------------|---------|---------------------------|
| Case / separator | `ship_date` vs `ShipDate` | Normalization + token Jaccard or token-sort ratio |
| Typo | `custmer_id` vs `customer_id` | Levenshtein, Jaro–Winkler |
| Reordered tokens | `order_id` vs `id_order` | Token-sort ratio, token-set ratio |
| Abbreviation | `cust_id` vs `customer_id` | Token subset + edit distance; synonym tables (COMA) |
| Prefix / suffix noise | `tbl_customer_id` vs `customer_id` | Affix matchers, partial ratio, path-aware matching |
| Phonetic (person names) | `Jon` vs `John` | Soundex / Metaphone (weak for technical IDs) |

Record linkage literature (Fellegi–Sunter; Winkler) optimizes *decision weights* from match/non-match training data, not ad-hoc 0–100 blends ([Fellegi & Sunter, 1969](#ref-fellegi-sunter); [Winkler, 1990](#ref-winkler-1990)).

---

## 2. Normalization (do this before metrics)

No single Unicode standard defines “split camelCase for schema matching.” Production systems define a **deterministic pipeline** and document it.

### 2.1 Recommended pipeline

1. **Unicode normalization** — Use NFC (or NFD consistently) before comparison. Levenshtein over raw code units can disagree with user-perceived characters unless the unit is specified ([Unicode UAX #15](https://www.unicode.org/reports/tr15/); [Unicode UAX #29](https://www.unicode.org/reports/tr29/); [Levenshtein distance — Unicode section](https://en.wikipedia.org/wiki/Levenshtein_distance#Unicode_and_the_unit_of_comparison)).
2. **Case folding** — Lowercase (or case-insensitive collation). COMA-style matchers assume comparable case after import ([Do & Rahm, 2002](#ref-coma)).
3. **Separator harmonization** — Map `-`, `.`, `/`, space to a single delimiter (often `_`), then split: `ship-to.address` → tokens `ship`, `to`, `address`.
4. **Compound identifier splitting** — Split `snake_case` on `_`. For **camelCase / PascalCase**, split on transitions (lower→upper, acronym boundaries). COMA’s **Name** matcher tokenizes compounds such as `POShipTo` → `{PO, Ship, To}` before matching ([Do & Rahm, 2002](#ref-coma) §4.2, Figure 3).
5. **Stop tokens (optional)** — Drop domain noise (`tbl`, `dim`, `fk`, `id` suffix handling) only with an explicit allowlist; blind removal causes false merges.
6. **Abbreviation expansion (optional)** — COMA expands acronyms in a dictionary step (e.g. `PO` → `{Purchase, Order}`) before token-level similarity ([Do & Rahm, 2002](#ref-coma)).

### 2.2 What not to do

- **Soundex/Metaphone on technical columns** — Designed for English pronunciation of names ([Russell & Odell patents](#ref-soundex); [Philips, 1990](#ref-metaphone)). COMA includes Soundex for *element names* generally, but phonetic codes collapse distinct identifiers (`Smith`/`Smyth`) and miss semantic abbreviations (`qty`/`quantity`).
- **Stemming** — Porter stemmer targets natural language, not `customer`/`customers` as schema tokens.

---

## 3. Edit-distance and character metrics

### 3.1 Levenshtein distance

**Definition.** Minimum number of single-character insertions, deletions, and substitutions to transform one string into another. Original context: error-correcting codes ([Levenshtein, 1965/1966](#ref-levenshtein)).

**Use for columns.** Strong for typos and single-character drift on short strings. Weak when token order changes (`id_customer` vs `customer_id`) unless strings are normalized to a canonical token order first.

**Weighted variants.** Insert/delete/substitution costs can differ (e.g. transpositions as two edits vs one in Damerau–Levenshtein). RapidFuzz exposes `weights=(ins, del, sub)`; uniform `(1,1,1)` is classic Levenshtein; `(1,1,2)` yields Indel-style behavior ([RapidFuzz Levenshtein docs](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/Levenshtein.html)).

**Normalization.** Similarity is often `1 - d / max(len1, len2)` (library-specific). COMA’s **EditDistance** matcher maps edit cost to a 0–1 similarity ([Do & Rahm, 2002](#ref-coma) §4.1).

### 3.2 Damerau–Levenshtein

Adds transposition as one operation. Winkler discusses Damerau–Levenshtein as a string comparator for typographical variation in names ([Winkler, 1990](#ref-winkler-1990)). Useful when adjacent character swaps are common; RapidFuzz and jellyfish both implement it.

### 3.3 `fuzz.ratio` / Indel similarity (RapidFuzz)

`rapidfuzz.fuzz.ratio` returns **normalized Indel similarity** on a 0–100 scale ([RapidFuzz fuzz.ratio](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html)). This is the usual backbone for token-sort and token-set ratios.

### 3.4 Jaro and Jaro–Winkler

**Jaro.** Compares matching characters within a window and transpositions; score in \([0,1]\). Introduced in record linkage context ([Jaro, 1989](#ref-jaro)).

**Jaro–Winkler.** Adds a prefix boost: common prefix length ℓ (max 4) scales score by \(p=0.1\) default: \(sim_{JW} = sim_J + \ell \cdot p \cdot (1 - sim_J)\) ([Winkler extension](#ref-jaro-winkler-wiki); [RapidFuzz JaroWinkler](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/JaroWinkler.html) — `prefix_weight=0.1`, max 0.25).

**Use for columns.** Good for short identifiers with prefix stability (`cust_*`, `customer_*`). Not a metric (no triangle inequality). Winkler ([1990](#ref-winkler-1990)) maps comparator values to **Fellegi–Sunter weights** via piecewise linear curves trained on labeled pairs—not fixed thresholds.

### 3.5 Partial ratio

Best contiguous substring alignment score (0–100). Helps when one name embeds the other (`customer` vs `dim_customer`). Used inside **WRatio** with length-dependent scaling ([RapidFuzz `partial_ratio`](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html); [fuzzywuzzy `WRatio`](https://github.com/seatgeek/fuzzywuzzy/blob/master/fuzzywuzzy/fuzz.py)).

---

## 4. Token-level metrics

Treat names as **sets or multisets of tokens** after §2 normalization.

### 4.1 Token-sort ratio

Sort tokens alphabetically (or by a fixed key), join, then apply character-level ratio.

- **RapidFuzz:** `token_sort_ratio` — “Sorts the words in the strings and calculates the fuzz.ratio between them” ([docs](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html)).
- **Origin:** fuzzywuzzy / SeatGeek `_token_sort` ([source](https://github.com/seatgeek/fuzzywuzzy/blob/master/fuzzywuzzy/fuzz.py)).

**Effect.** Invariant to token order → `customer_id` vs `id_customer` often scores near 100 after sort.

### 4.2 Token-set ratio

Split into intersection and symmetric differences of token *sets*, build comparison strings, take max of pairwise ratios ([RapidFuzz `token_set_ratio`](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html); [fuzzywuzzy `_token_set`](https://github.com/seatgeek/fuzzywuzzy/blob/master/fuzzywuzzy/fuzz.py)).

**Effect.** If one token set is a subset of the other, score can be 100 even when the longer string has extra tokens (documented in RapidFuzz examples). Reduces penalty for `customer_id` vs `customer_id_hash` compared to plain ratio.

### 4.3 Jaccard index on tokens

\(J(A,B) = |A \cap B| / |A \cup B|\) for token sets \(A,B\) ([Jaccard index](https://en.wikipedia.org/wiki/Jaccard_index)). COMA’s **n-gram** matchers use character n-gram sets; **Trigram** is a 3-gram variant ([Do & Rahm, 2002](#ref-coma) §4.1). **textdistance** exposes `Jaccard` with `qval=None` for word tokenization ([textdistance README](https://github.com/life4/textdistance/blob/master/README.md)).

**Relation to Dice.** COMA combines token similarities with **Dice** for set-level aggregation: \(2|matches|/(|S_1|+|S_2|)\) ([Do & Rahm, 2002](#ref-coma) §6.3). Sørensen–Dice on bigrams is standard for fuzzy name matching in PostgreSQL `pg_trgm` (trigram similarity); COMA explicitly uses trigrams on **element names**.

### 4.4 Monge–Elkan

Compare tokens with an inner edit-distance, aggregate (max or average). Useful when tokens differ by abbreviations (`cust` vs `customer`) if inner distance is Jaro–Winkler or Levenshtein ([textdistance](https://github.com/life4/textdistance/blob/master/README.md) cites Monge & Elkan, 2006).

---

## 5. n-gram (q-gram) similarity

**Idea.** Embed strings as sets (or bags) of length-\(n\) character sequences; compare via Jaccard, Dice, or cosine.

- **COMA:** character n-gram matchers (Digram, Trigram) on name strings ([Do & Rahm, 2002](#ref-coma)).
- **textdistance:** `qval` parameter — 1 = characters, ≥2 = q-grams, `None` = words ([README](https://github.com/life4/textdistance/blob/master/README.md)).

**Use for columns.** Robust to minor typos and substring overlap; sensitive to length skew on very short names. Trigram (3) is a common default in schema tools (e.g. COMA **Name** default includes Trigram; [Valentine Coma matcher](https://delftdata.github.io/valentine/matchers/) documents trigram Dice on column names).

---

## 6. Global and local alignment (Smith–Waterman, affine gaps)

**Needleman–Wunsch (1970).** Global alignment with gap penalties ([Needleman & Wunsch, 1970](https://en.wikipedia.org/wiki/Needleman%E2%80%93Wunsch_algorithm)).

**Smith–Waterman (1981).** Local alignment: best-scoring substring pair ([Smith & Waterman, 1981](https://en.wikipedia.org/wiki/Smith%E2%80%93Waterman_algorithm)).

**Affine gap costs.** Gap of length \(k\) costs \(u + k v\) (open + extend), avoiding scattered single-gap penalties; Gotoh (1982) reduces complexity to \(O(mn)\) ([Smith–Waterman — Affine gaps](https://en.wikipedia.org/wiki/Smith%E2%80%93Waterman_algorithm#Affine)).

**textdistance** implements `NeedlemanWunsch`, `Gotoh`, and `SmithWaterman` with configurable match/mismatch/gap scores ([README](https://github.com/life4/textdistance/blob/master/README.md)).

**Use for columns.** Usually **overkill** for single field names (length ≪ 64). Alignment shines when matching **path strings** (`orders.ship_to.zip` vs `purchase_order.delivery.postal_code`) with explicit gap/open costs, or when concatenating hierarchical names (COMA **NamePath** — [Do & Rahm, 2002](#ref-coma) §4.2). For typical column tokens, token-sort + Levenshtein is cheaper and easier to calibrate.

---

## 7. Phonetic encoders (names, not codes)

| Algorithm | Source | jellyfish | Typical schema use |
|-----------|--------|-----------|-------------------|
| American Soundex | Russell/Odell (1918–1922); NARA rules ([Soundex](https://en.wikipedia.org/wiki/Soundex)) | `soundex` | Person name columns only |
| Metaphone | Lawrence Philips, 1990 ([Metaphone](https://en.wikipedia.org/wiki/Metaphone)) | `metaphone` | Same |
| Double Metaphone | Philips, *C/C++ Users Journal*, June 2000 ([Double Metaphone](https://en.wikipedia.org/wiki/Metaphone#Double_Metaphone)) | via `metaphone` (single) / check library version | Surname matching |
| NYSIIS, Match Rating | jellyfish docs | yes | Legacy name linkage |

**Binary comparator.** Winkler ([1990](#ref-winkler-1990)): exact match or exact Soundex match → 1, else 0 — a minimal phonetic comparator. COMA **Soundex** matcher compares encodings of element names ([Do & Rahm, 2002](#ref-coma)).

**Column names.** Prefer **no phonetic step** unless matching human-name fields. For `Phoenix`/`Fenix`-style typos in English words, edit distance or embeddings beat Soundex.

---

## 8. Composite scores and weights

### 8.1 Fellegi–Sunter + partial agreement (statistical)

- Comparison vectors carry agreement/disagreement per field; optimal linkage rules use likelihood ratios ([Fellegi & Sunter, 1969](#ref-fellegi-sunter)).
- **Winkler (1990):** Partition string comparator output \([0,1]\) into bins; estimate match/non-match odds per bin; interpolate **piecewise linear weight** between full agreement and disagreement weights ([Resnick et al., 2020](#ref-resnick-2020) extend this to graded Jaro–Winkler bins).

**Practice.** Weights are **data-dependent** (domain, field type). Do not copy Census name weights for SKU or column identifiers without calibration.

### 8.2 COMA matcher combination (schema matching)

COMA stores per-matcher similarities in a cube, then:

1. **Aggregation** (per element pair): `Max`, `Min`, `Average`, or `Weighted` sum ([Do & Rahm, 2002](#ref-coma) §6.1).
2. **Selection:** directional best-match, threshold, MaxN, MaxDelta ([§6.2](#ref-coma)).
3. **Hybrid internal combination:** e.g. **Name** matcher defaults: constituent matchers `Trigram`, `Synonym`; aggregate with `Max`, direction `Both`, select `Max1`, combine token similarities with `Average` ([Table 4, Do & Rahm, 2002](#ref-coma)). **TypeName** uses weighted `(0.3 DataType, 0.7 Name)`.

**Lessons for column matching.**

- Run **multiple weak signals** (trigram + edit distance + token Jaccard); aggregate with **max** when matchers are complementary, **average** when equally trusted, **weighted** when one signal dominates (datatype > name for typed columns).
- Use **bidirectional** best match (`Both`) to reduce many-to-one false positives ([Do & Rahm, 2002](#ref-coma) §6.2).

### 8.3 WRatio (heuristic composite)

`rapidfuzz.fuzz.WRatio` (from fuzzywuzzy):

- Base `ratio`; if length ratio `< 1.5`, compare to `token_ratio * 0.95`.
- Else enable `partial_ratio` with scale `0.9` (or `0.6` if length ratio `> 8`).
- Return **max** of participating scores ([RapidFuzz `fuzz_py.py`](https://github.com/rapidfuzz/RapidFuzz/blob/main/src/rapidfuzz/fuzz_py.py); [fuzzywuzzy `WRatio`](https://github.com/seatgeek/fuzzywuzzy/blob/master/fuzzywuzzy/fuzz.py)).

This is a **hand-tuned ensemble**, not likelihood-optimal. Good default for fuzzy string UI search; for schema matching, prefer explicit matchers + COMA-style aggregation so weights are inspectable.

### 8.4 Suggested starter recipe (column names)

| Stage | Choice | Rationale |
|-------|--------|-----------|
| Normalize | NFC + lowercase + split camel/snake + optional abbrev table | Aligns with COMA Name tokenization |
| Primary | `max(token_sort_ratio, token_set_ratio, jaro_winkler*100)` on normalized full string and on `_`-joined sorted tokens | Order + subset + typo |
| Secondary | Trigram Dice / Jaccard on raw normalized string | COMA default family |
| Phonetic | Only if column semantics = person name | Winkler/COMA Soundex use case |
| Fuse | `max` across metrics for retrieval; **weighted average** (e.g. 0.5 token-sort, 0.3 JW, 0.2 trigram) for ranking; tune on labeled pairs | COMA Max vs Weighted |
| Decide | Threshold + mutual nearest neighbor | Valentine/COMA selection |
| Calibrate | Fit thresholds/weights on held-out manual mappings | Fellegi–Sunter / Winkler bins |

---

## 9. Python libraries

### 9.1 [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) (recommended workhorse)

- **Docs:** [Usage index](https://rapidfuzz.github.io/RapidFuzz/Usage/index.html)
- **`rapidfuzz.fuzz`:** `ratio`, `partial_ratio`, `token_sort_ratio`, `token_set_ratio`, `WRatio`, etc. ([fuzz module](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html))
- **`rapidfuzz.distance`:** Levenshtein (weighted), Damerau-Levenshtein, Jaro, JaroWinkler, LCS, OSA, … ([distance index](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/index.html))
- **`rapidfuzz.process`:** `extract`, `extractOne`, `cdist` for candidate retrieval with `score_cutoff` ([process](https://rapidfuzz.github.io/RapidFuzz/Usage/process.html))
- **Performance:** C++ core; benchmarks vs jellyfish on Jaro–Winkler in docs ([JaroWinkler performance](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/JaroWinkler.html))
- **References:** Wagner–Fischer edit distance ([WF74](https://doi.org/10.1145/321796.321811)); bit-vector Levenshtein ([Hyyrö, 2003](https://rapidfuzz.github.io/RapidFuzz/References.html))

### 9.2 [jellyfish](https://github.com/jamesturk/jellyfish)

- **README / PyPI:** [GitHub README](https://github.com/jamesturk/jellyfish/blob/master/README.md)
- **Distances:** Levenshtein, Damerau-Levenshtein, Jaccard, Jaro, Jaro-Winkler, Hamming, Match Rating
- **Phonetic:** Soundex, Metaphone, NYSIIS, Match Rating Codex
- **Role.** Thin Cython/C API for phonetic + classic distances; RapidFuzz covers most string matching faster at scale. Use jellyfish when you need Metaphone/Soundex/NYSIIS without reimplementing.

### 9.3 [textdistance](https://github.com/life4/textdistance)

- **Unified API** over 30+ algorithms; can delegate to RapidFuzz, jellyfish, `python-Levenshtein`, etc. ([README algorithms table](https://github.com/life4/textdistance/blob/master/README.md))
- **Parameters:** `qval`, `as_set` for token/q-gram modes
- **Includes:** alignment (`Gotoh`, `SmithWaterman`), `MongeElkan`, `strcmp95`, compression distances
- **Role.** Experimentation and algorithm shopping; production hot paths often call RapidFuzz directly after choosing a metric.

### 9.4 Library selection

| Need | Library |
|------|---------|
| Fast batch column–column similarity matrix | RapidFuzz `process.cdist` |
| Phonetic name key | jellyfish |
| Compare many algorithms in research | textdistance |
| Legacy fuzzywuzzy API | RapidFuzz drop-in (`rapidfuzz.fuzz`) |

---

## 10. Related schema-matching primary sources

- **COMA (2002):** Composable matchers, similarity cube, Name tokenization, EditDistance, Trigram, Soundex, aggregation strategies ([Do & Rahm, 2002](#ref-coma); [VLDB PDF mirror](https://www.vldb.org/conf/2002/S17P03.pdf)).
- **COMA 3.0 journal version:** String matcher summary ([Köpcke et al., 2007 / Information Systems](https://dbs.uni-leipzig.de/files/research/publications/2007-/pdf/IS2007.pdf)).
- **Cupid (2001):** Name + structure hybrid for XML schemas ([Madhavan et al., 2001](https://doi.org/10.1145/375663.375687)) — name similarity at leaf level combined with structural similarity.
- **Valentine (2021+):** Open benchmark and Python reimplementations (e.g. Coma, JaccardDistanceMatcher with Levenshtein/Jaro–Winkler inner metrics) ([Valentine matchers docs](https://delftdata.github.io/valentine/matchers/)).

---

## 11. References

<a id="ref-coma"></a>**Do, H.-H., & Rahm, E. (2002).** COMA — A system for flexible combination of schema matching approaches. *VLDB 2002.* PDF: [Leipzig](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf), [VLDB](https://www.vldb.org/conf/2002/S17P03.pdf).

<a id="ref-fellegi-sunter"></a>**Fellegi, I. P., & Sunter, A. B. (1969).** A theory for record linkage. *Journal of the American Statistical Association*, 64(328). DOI: [10.1080/01621459.1969.10501049](https://doi.org/10.1080/01621459.1969.10501049). PDF: [Cornell mirror](https://www.cs.cornell.edu/~shmat/courses/cs6434/fellegi-sunter.pdf).

<a id="ref-winkler-1990"></a>**Winkler, W. E. (1990).** String comparator metrics and enhanced decision rules in the Fellegi-Sunter model of record linkage. *ASA Proceedings.* PDF: [CMU mirror](https://www.stat.cmu.edu/NCRN/PUBLIC/RLClassFiles/HW/Winkler1990.pdf), ERIC: [ED325505](https://eric.ed.gov/?id=ED325505).

<a id="ref-jaro"></a>**Jaro, M. A. (1989).** Advances in record-linkage methodology as applied to matching the 1985 Census of Tampa, Florida. *JASA*, 84(406). DOI: [10.1080/01621459.1989.10478785](https://doi.org/10.1080/01621459.1989.10478785).

<a id="ref-jaro-winkler-wiki"></a>**Jaro–Winkler distance.** Definition and citations: [Wikipedia](https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance) (points to Jaro 1989 and Winkler 1990).

<a id="ref-levenshtein"></a>**Levenshtein, V. I. (1965/1966).** Binary codes capable of correcting deletions, insertions, and reversals. *Doklady Akademii Nauk SSSR* / *Soviet Physics Doklady*. Index: [Math-Net.ru](https://www.mathnet.ru/eng/dan31411).

<a id="ref-wf74"></a>**Wagner, R. A., & Fischer, M. J. (1974).** The string-to-string correction problem. *JACM*, 21(1). DOI: [10.1145/321796.321811](https://doi.org/10.1145/321796.321811).

<a id="ref-resnick-2020"></a>**Resnick, D. M., et al. (2020).** Adjusting match weights to partial levels of string agreement in data linkage. *JSM Proceedings.* PDF: [ASA](https://ww2.amstat.org/meetings/proceedings/2020/data/assets/pdf/1505367.pdf).

<a id="ref-soundex"></a>**Soundex.** History (Russell & Odell; US Census / NARA): [Wikipedia — Soundex](https://en.wikipedia.org/wiki/Soundex). NARA encoding rules: [Using the Census Soundex (GIL 55)](https://www.archives.gov/research/census/soundex).

<a id="ref-metaphone"></a>**Philips, L. (1990).** Metaphone algorithm (English pronunciation indexing). Described in [Wikipedia — Metaphone](https://en.wikipedia.org/wiki/Metaphone) with primary refs. **Double Metaphone:** Philips, *C/C++ Users Journal*, June 2000 ([Double Metaphone section](https://en.wikipedia.org/wiki/Metaphone#Double_Metaphone)).

<a id="ref-smith-waterman"></a>**Smith, T. F., & Waterman, M. S. (1981).** Identification of common molecular subsequences. *Journal of Molecular Biology*, 147(1). (Local alignment; see [Smith–Waterman algorithm](https://en.wikipedia.org/wiki/Smith%E2%80%93Waterman_algorithm).)

**Gotoh, O. (1982).** An improved algorithm for matching biological sequences. *JMB* — affine gap alignment ([cited in Smith–Waterman article](https://en.wikipedia.org/wiki/Smith%E2%80%93Waterman_algorithm#Affine)).

<a id="ref-rapidfuzz"></a>**RapidFuzz documentation (3.14.x).** [fuzz](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html), [distance](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/index.html), [process](https://rapidfuzz.github.io/RapidFuzz/Usage/process.html), [References](https://rapidfuzz.github.io/RapidFuzz/References.html). Source: [GitHub — RapidFuzz](https://github.com/rapidfuzz/RapidFuzz).

<a id="ref-fuzzywuzzy"></a>**fuzzywuzzy.** Token and WRatio logic: [seatgeek/fuzzywuzzy `fuzz.py`](https://github.com/seatgeek/fuzzywuzzy/blob/master/fuzzywuzzy/fuzz.py).

<a id="ref-jellyfish"></a>**jellyfish.** [GitHub README](https://github.com/jamesturk/jellyfish/blob/master/README.md), [PyPI](https://pypi.org/project/jellyfish/).

<a id="ref-textdistance"></a>**textdistance.** [GitHub README](https://github.com/life4/textdistance/blob/master/README.md).

<a id="ref-jaccard"></a>**Jaccard index.** Formal set ratio: [Wikipedia — Jaccard index](https://en.wikipedia.org/wiki/Jaccard_index).

<a id="ref-valentine"></a>**Valentine — Coma / JaccardDistanceMatcher.** [Matchers documentation](https://delftdata.github.io/valentine/matchers/).

---

## 12. Minimal Python sketch (RapidFuzz)

Normalization is application-specific; this shows metric fusion only:

```python
import re
import unicodedata
from rapidfuzz import fuzz, distance

def normalize_column_name(name: str) -> str:
    name = unicodedata.normalize("NFC", name).lower()
    name = re.sub(r"[_\s\-./]+", " ", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)  # camelCase split (ASCII-centric)
    return " ".join(name.split())

def composite_name_score(a: str, b: str) -> float:
    a, b = normalize_column_name(a), normalize_column_name(b)
    scores = [
        fuzz.token_sort_ratio(a, b),
        fuzz.token_set_ratio(a, b),
        distance.JaroWinkler.normalized_similarity(a, b) * 100,
        fuzz.ratio(a, b),
    ]
    return max(scores)  # COMA "Max" aggregation at metric level
```

For production, add abbrev expansion, blocked candidate generation (`process.extract`), mutual top-1 filtering, and calibration on labeled column pairs.

---

*Document generated for the tejtm project. Revise weights using domain-specific labeled mappings rather than defaults from record linkage or fuzzywuzzy.*
