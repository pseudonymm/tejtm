# Prior art: schema/column mapping, fuzzy headers, and ontology alignment

Research notes for **import-file column mapping** (CSV/spreadsheet headers → canonical schema), **fuzzy header matching**, and **schema/ontology alignment**. Each factual claim below links to a primary source (official docs, papers, or first-party repositories).

---

## 1. Vocabulary and problem shape

**Schema matching** is the task of finding semantic correspondences between elements of two schemas; it arises in data integration, warehouse loading, XML message mapping, and similar settings ([Rahm & Bernstein, VLDB Journal 2001](https://doi.org/10.1007/s007780100057); [Do & Rahm, COMA, VLDB 2002](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf)).

**Import column mapping** (this project’s focus) is a constrained instance:

| Layer | Typical inputs | Typical output |
|--------|----------------|----------------|
| **Header / label** | Source column names (`cust_nm`, `Customer Name`) | Map to canonical field ids |
| **Type / constraint** | Inferred or declared types | Cast rules, validation |
| **Instance** (optional) | Sample cell values | Disambiguate homonyms, typos |
| **Structure** (optional) | FK-like co-occurrence, table context | Rare in flat imports |

Surveys distinguish **schema-level vs instance-level**, **element-level vs structure-level**, and **language-based vs constraint-based** matchers ([Rahm & Bernstein, 2001](https://doi.org/10.1007/s007780100057); [Microsoft Research TR-2001-17](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2001-17.pdf)). **Composite** systems run several matchers and merge scores ([COMA](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf)).

**Ontology alignment** extends the same correspondence problem to richer logical models (classes, properties, axioms). Shvaiko & Euzenat treat schema and ontology matching as overlapping: techniques can cross-pollinate, though ontologies carry explicit semantics and richer constructs ([Shvaiko & Euzenat, Journal on Data Semantics IV, 2005](https://exmo.inria.fr/files/publications/shvaiko2005a.pdf)).

---

## 2. Canonical surveys and taxonomies

### 2.1 Rahm & Bernstein (database schema matching)

- **Publication:** *A survey of approaches to automatic schema matching*, The VLDB Journal 10(4), 334–350, 2001.  
  **DOI:** [https://doi.org/10.1007/s007780100057](https://doi.org/10.1007/s007780100057)  
  **Author PDF (Leipzig):** [https://dbs.uni-leipzig.de/files/research/publications/2001-1/pdf/VLDBJ-Dec2001.pdf](https://dbs.uni-leipzig.de/files/research/publications/2001-1/pdf/VLDBJ-Dec2001.pdf)

**Claims (from abstract / introduction):** Schema matching is usually manual in production systems; research proposes partial automation. The paper presents a **taxonomy** of approaches and reviews implementations in terms of which part of the solution space they cover ([DOI page](https://doi.org/10.1007/s007780100057)).

**IBM / industry thread in the same lineage:** The extended technical report *On Matching Schemas Automatically* (Microsoft Research MSR-TR-2001-17, co-authored by Rahm and Philip A. Bernstein) reviews prototypes including **Clio** at IBM Almaden: semi-automatic, user-assisted creation of mappings between a target schema and a new source, with a Correspondence Engine and Mapping Generator ([MSR-TR-2001-17 PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2001-17.pdf)).

### 2.2 Shvaiko & Euzenat (schema + ontology matching)

- **Publication:** *A Survey of Schema-Based Matching Approaches*, in *Journal on Data Semantics IV*, LNCS 3730, pp. 146–171, Springer, 2005.  
  **PDF:** [https://exmo.inria.fr/files/publications/shvaiko2005a.pdf](https://exmo.inria.fr/files/publications/shvaiko2005a.pdf)  
  **Alternate copy:** [http://dit.unitn.it/~pavel/Publications/SurveyShvaikoEuzenat.pdf](http://dit.unitn.it/~pavel/Publications/SurveyShvaikoEuzenat.pdf)

**Claims:** Builds on Rahm & Bernstein’s classification; adds criteria for (i) general properties of techniques, (ii) interpretation of input, (iii) kind of input. Distinguishes **heuristic vs exact** at schema level and **syntactic, external, semantic** at element/structure level. Overview explicitly places systems such as **Cupid** (schema-level) and **COMA** (schema-level) alongside ontology matchers ([PDF §1–2](https://exmo.inria.fr/files/publications/shvaiko2005a.pdf)).

### 2.3 Ontology alignment evaluation (OAEI)

The **Ontology Alignment Evaluation Initiative** provides benchmarks and consensus evaluation for schema/ontology matchers ([OAEI home](https://oaei.ontologymatching.org/)). OAEI is the standard reference for **ontology** alignment competitions; tabular column mapping tools (e.g. Valentine) cite academic matchers but target DataFrame discovery rather than OWL/RDF reasoning.

---

## 3. Landmark automatic matchers

### 3.1 Cupid (linguistic + structural, generic)

- **Paper:** Madhavan, Bernstein, Rahm — *Generic Schema Matching with Cupid* (VLDB 2001; extended MSR-TR-2001-58).  
  **Microsoft Research page:** [https://www.microsoft.com/en-us/research/publication/generic-schema-matching-with-cupid/](https://www.microsoft.com/en-us/research/publication/generic-schema-matching-with-cupid/)  
  **VLDB PDF:** [https://www.vldb.org/conf/2001/P049.pdf](https://www.vldb.org/conf/2001/P049.pdf)

**Claims (MSR abstract):** Cupid discovers mappings using **names, data types, constraints, and schema structure**; innovations include integrated **linguistic and structural** matching, context-dependent matching of shared types, and emphasis on **leaf** elements where content often lives ([MSR page](https://www.microsoft.com/en-us/research/publication/generic-schema-matching-with-cupid/)).

**Python reuse:** The [Valentine](https://github.com/delftdata/valentine) library ships a Python `Cupid(...)` matcher implementing that paper ([Valentine README](https://raw.githubusercontent.com/delftdata/valentine/master/README.md)).

### 3.2 COMA / COMA++ (composite matcher platform)

- **Paper:** Do & Rahm — *COMA — A System for Flexible Combination of Schema Matching Approaches*, VLDB 2002.  
  **PDF:** [https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf)  
  **Publication index:** [https://dbs.uni-leipzig.de/research/publications/coma-a-system-for-flexible-combination-of-schema-matching-approaches](https://dbs.uni-leipzig.de/research/publications/coma-a-system-for-flexible-combination-of-schema-matching-approaches)

**Claims:** COMA is a **platform to combine multiple matchers** (name, type, structure, reuse from prior matches, etc.) with flexible **composition** of results; evaluation on real-world schemas shows combined approaches outperform single techniques ([COMA PDF abstract](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf)).

**Community edition:** [COMA CE on SourceForge](https://sourceforge.net/projects/coma-ce/) — parsers, matcher library, framework, sample GUI; initiated at Leipzig in 2002 ([SourceForge project page](https://sourceforge.net/projects/coma-ce/)).

**Python reuse:** Valentine’s `Coma(...)` is described as a pure-Python implementation of **COMA 3.0**, with optional TF-IDF **instance** matching and schema-based name/path/structure matching ([Valentine README](https://raw.githubusercontent.com/delftdata/valentine/master/README.md)).

### 3.3 Clio (IBM semi-automatic mapping)

Described in Rahm & Bernstein’s survey report: **Clio** (IBM Almaden / Toronto) targets **semi-automatic, user-assisted** mapping from a source schema to a **fixed target** schema, using schema readers, a correspondence engine, and mapping generation ([MSR-TR-2001-17](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2001-17.pdf)). This is closer to **interactive ETL / mapping UI** than to unattended CSV import, but it defines the industry pattern: suggest correspondences, human confirms, generate transforms.

### 3.4 Recent Python products (import-focused)

| Project | Role | Primary source |
|---------|------|----------------|
| **infermap** | Multi-scorer pipeline (exact, alias, fuzzy name, pattern type from values, profile stats), Hungarian assignment, reusable YAML config | [GitHub README (goldenmatch monorepo)](https://github.com/benzsevern/goldenmatch) |
| **tabmodel** | Pydantic-driven CSV/Excel import; fuzzy header match + `Aliases` + manual `mapping=` overrides | [PyPI tabmodel](https://pypi.org/project/tabmodel/) |
| **tabularmapper** | XLSX header-row detection + synonym/fuzzy column map; review gate for uncertain columns | [PyPI tabularmapper](https://pypi.org/project/tabularmapper/) |
| **rolodexter** | Contact-field canonicalization: exact → normalized → fuzzy → value-shape heuristics | [PyPI rolodexter](https://pypi.org/project/rolodexter/) |

**Differentiation target for this library:** Framework-agnostic schema objects (not only Pydantic or one file format), explicit per-factor score breakdown, pluggable scorers, lightweight core with optional semantic extra, and value-intent disambiguation when two headers look alike.

### 3.5 Valentine (tabular dataset discovery benchmark + matchers)

- **Repo:** [https://github.com/delftdata/valentine](https://github.com/delftdata/valentine)  
- **ICDE 2021 paper:** *Valentine: Evaluating Matching Techniques for Dataset Discovery* (bibtex in [README](https://raw.githubusercontent.com/delftdata/valentine/master/README.md)).

**Claims:** Valentine **matches columns across pandas/Polars DataFrames**, exposes multiple matchers (Coma, Cupid, distribution-based, Jaccard/Tversky baselines, etc.), and returns ranked `ColumnPair` → score maps ([README — Matching DataFrames](https://raw.githubusercontent.com/delftdata/valentine/master/README.md)). It is the most direct **off-the-shelf Python** bridge from academic schema matching to **flat import files**.

---

## 4. Python and ecosystem libraries (by role)

### 4.1 Declarative table schema + infer/validate (Frictionless)

**Specs — Table Schema:** Portable JSON schema for tabular columns: required `name`, optional `title`, `type`, `format`, `constraints`, optional `rdfType` for semantic types ([Table Schema spec](https://specs.frictionlessdata.io/table-schema/)).

**Framework — describe / infer:** `Resource.infer()` and high-level `describe` infer encoding, field types, stats from files ([Describing Data — Inferring Metadata](https://framework.frictionlessdata.io/docs/guides/describing-data.html)). Table Schema is used to validate tabular resources and drive UIs ([Describing a Schema](https://framework.frictionlessdata.io/docs/guides/describing-data.html)).

**Validate:** `validate()` checks data against schema; header issues (e.g. duplicate labels) surface as structured errors ([Validating Data](https://framework.frictionlessdata.io/docs/guides/validating-data.html)).

**Relevance to column mapping:** Frictionless solves **canonical schema + validation** and **type inference from data**; it does **not** automatically align an unknown upload’s headers to your canonical schema. Mapping is still application logic (often fuzzy match + user confirmation).

### 4.2 DataFrame validation (Pandera)

**Role:** `DataFrameSchema` / `Column` validate pandas (and other backends) with strictness, ordered columns, coercion, and `add_missing_columns` for ingest pipelines ([DataFrame Schemas](https://pandera.readthedocs.io/en/stable/dataframe_schemas.html)).

**Relevance:** After you **rename/map** columns, Pandera enforces the target contract. It is not a header-matching library.

### 4.3 Record serialization / API schemas (Marshmallow)

**Role:** `Schema` classes map attribute names ↔ `fields.*`; `load` / `dump` for deserialization and serialization; `partial` loading for incomplete payloads ([Quickstart](https://marshmallow.readthedocs.io/en/stable/quickstart.html)).

**Relevance:** Same as Pandera for **post-mapping** validation/transform of row dicts; field names are fixed at schema definition time unless you add a custom pre-load rename step.

### 4.4 Profiling → expectations (Great Expectations)

**GX Core:** Framework for **Expectations** (assertions about data) and **Validation** workflows ([GX Core overview](https://docs.greatexpectations.io/docs/core/introduction/gx_overview/)).

**Data Assistants (profiling):** Pre-configured utilities that introspect **Batches**, compute **Metrics**, and propose an **Expectation Suite**; supports multi-batch introspection and metric plots ([Data Assistant term — profiling](https://docs.greatexpectations.io/docs/reference/learn/terms/data_assistant/)).

**Relevance:** Profiling discovers **distributional** facts (null rates, min/max, value sets), not semantic alignment between `client_id` and `customer_identifier`. Useful **after** mapping to bootstrap data-quality rules; orthogonal to header matching.

### 4.5 Fuzzy string matching (TheFuzz / RapidFuzz)

**Lineage:** The SeatGeek **fuzzywuzzy** repo is **archived**; maintenance moved to **TheFuzz**, which depends on **RapidFuzz** ([fuzzywuzzy GitHub](https://github.com/seatgeek/fuzzywuzzy); [TheFuzz README](https://raw.githubusercontent.com/seatgeek/thefuzz/master/README.rst)).

**Scorers (TheFuzz / RapidFuzz):**

| Scorer | Typical use for headers |
|--------|-------------------------|
| `ratio` | Full-string edit distance similarity |
| `partial_ratio` | Short label contained in long header |
| `token_sort_ratio` / `token_set_ratio` | Reordered or duplicated tokens (`Customer Name` vs `Name, Customer`) |
| `WRatio` | Weighted blend (RapidFuzz default in `extract`) |

Examples: [TheFuzz README — Usage](https://raw.githubusercontent.com/seatgeek/thefuzz/master/README.rst); [RapidFuzz `fuzz` module](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html).

**Batch best match:** `process.extract` / `extractOne` rank choices; optional `scorer`, `processor` (normalize case/punctuation), `score_cutoff` ([RapidFuzz `process`](https://rapidfuzz.github.io/RapidFuzz/Usage/process.html)). For **N source columns × M canonical fields**, `process.cdist` builds a similarity matrix ([`process.cdist`](https://rapidfuzz.github.io/RapidFuzz/Usage/process.html)).

**Relevance:** This is the **default industry pattern** for fuzzy **header** mapping: normalize strings → score all pairs → take best above threshold → human review for ambiguous cases.

### 4.6 Entity resolution / record linkage (dedupe)

**Role:** ML-based **duplicate detection** and **linking** on structured records; human **training labels** drive weights and blocking rules ([dedupe docs home](https://docs.dedupe.io/en/latest/); [PyPI description](https://pypi.org/project/dedupe/)).

**Variables:** Field comparators include `String` (affine gap / edit distance), `ShortString`, `Text`, and `Custom` comparators; variables define which **record fields** participate ([Variable Definitions](https://docs.dedupe.io/en/latest/Variable-definition.html)).

**Relevance:** Solves **row-level** “same entity?” not **column-level** “same field?” — but the same stack (blocking + learned weights + string comparators) appears in **schema matching with instance data** (cf. COMA instance matchers, Valentine distribution/Jaccard matchers). Useful when mapping must use **value overlap** (e.g. matching on sample values when headers are junk).

### 4.7 Company-name normalization (cleanco)

**Role:** Strip legal suffixes and classify organization names (`basename`, `typesources`, `matches`) — **not** general column mapping ([cleanco PyPI](https://pypi.org/project/cleanco/); [GitHub](https://github.com/psolin/cleanco)).

**Relevance:** Example of **domain-specific normalizers** you might apply **before** fuzzy header match or **after** mapping to a canonical “organization name” field.

### 4.8 Import mechanics (pandas)

`read_csv` defaults to **`header='infer'`** and builds column labels from the first row unless `names` is supplied; **`usecols`** selects columns by name or index ([pandas.read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)). Callable `usecols` enables rule-based column selection (e.g. uppercase name in allowlist).

**Relevance:** pandas performs **no semantic mapping**; it only applies explicit rename/selection after you decide mappings.

---

## 5. Usage patterns (import column mapping)

Patterns observed across docs and matcher literature:

1. **Normalize labels** — casefold, strip punctuation, split camelCase/snake_case, expand abbreviations (application-specific). Optional domain cleaners ([cleanco](https://pypi.org/project/cleanco/)) for known entity fields.

2. **Candidate generation** — for each source header, score against canonical field `name`, `title`, and aliases using [RapidFuzz `cdist`](https://rapidfuzz.github.io/RapidFuzz/Usage/process.html) or [`extractOne`](https://rapidfuzz.github.io/RapidFuzz/Usage/process.html). Prefer **`token_set_ratio`** or **`WRatio`** when word order varies ([TheFuzz examples](https://raw.githubusercontent.com/seatgeek/thefuzz/master/README.rst)).

3. **Disambiguation signals** (when headers collide):
   - **Type/format** agreement ([Table Schema types](https://specs.frictionlessdata.io/table-schema/))
   - **Instance overlap** (Valentine Coma `use_instances`, Jaccard/Tversky; COMA instance matchers — [Valentine README](https://raw.githubusercontent.com/delftdata/valentine/master/README.md))
   - **Structural** context (Cupid/COMA — overkill for single-table CSV, relevant for nested/XML) ([Cupid](https://www.microsoft.com/en-us/research/publication/generic-schema-matching-with-cupid/); [COMA](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf))

4. **Composite scoring** — weighted blend of name + type + instance scores mirrors **COMA’s composite architecture** ([COMA PDF](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf)); Valentine exposes per-sub-matcher breakdown for Coma ([Valentine README — Match details](https://raw.githubusercontent.com/delftdata/valentine/master/README.md)).

5. **Human in the loop** — Clio-style confirmation for low-confidence pairs ([MSR-TR-2001-17](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2001-17.pdf)); dedupe-style active learning for record linkage ([dedupe docs](https://docs.dedupe.io/en/latest/)).

6. **Apply mapping → validate** — rename columns, then enforce with [Pandera](https://pandera.readthedocs.io/en/stable/dataframe_schemas.html), [Frictionless validate](https://framework.frictionlessdata.io/docs/guides/validating-data.html), or [Marshmallow](https://marshmallow.readthedocs.io/en/stable/quickstart.html) on row records.

7. **Profile for quality (optional)** — [Great Expectations Data Assistant](https://docs.greatexpectations.io/docs/reference/learn/terms/data_assistant/) to propose expectations on **mapped** data.

---

## 6. Comparative matrix (quick reference)

| Tool | Primary job | Header / schema alignment? | Primary sources |
|------|-------------|----------------------------|-----------------|
| **Valentine** | Column matching across DataFrames | **Yes** (multiple matchers) | [GitHub](https://github.com/delftdata/valentine), [README](https://raw.githubusercontent.com/delftdata/valentine/master/README.md) |
| **RapidFuzz / TheFuzz** | Fuzzy string similarity | **Yes** (labels only) | [RapidFuzz](https://rapidfuzz.github.io/RapidFuzz/), [TheFuzz README](https://raw.githubusercontent.com/seatgeek/thefuzz/master/README.rst) |
| **Frictionless** | Table Schema, infer, validate | Infer **types** only; no target alignment | [Table Schema](https://specs.frictionlessdata.io/table-schema/), [Describe](https://framework.frictionlessdata.io/docs/guides/describing-data.html) |
| **Pandera** | DataFrame schema validation | No (expects known column names) | [DataFrame Schemas](https://pandera.readthedocs.io/en/stable/dataframe_schemas.html) |
| **Marshmallow** | Object ↔ dict schema | No (fixed fields) | [Quickstart](https://marshmallow.readthedocs.io/en/stable/quickstart.html) |
| **Great Expectations** | Expectations / validation | Profiling ≠ mapping | [GX Core](https://docs.greatexpectations.io/docs/core/introduction/gx_overview/), [Data Assistant](https://docs.greatexpectations.io/docs/reference/learn/terms/data_assistant/) |
| **dedupe** | Entity resolution | No (row fields, not schema) | [docs](https://docs.dedupe.io/en/latest/), [Variables](https://docs.dedupe.io/en/latest/Variable-definition.html) |
| **cleanco** | Company name cleaning | No | [PyPI](https://pypi.org/project/cleanco/) |
| **COMA / Cupid (Java)** | Research / integration matchers | **Yes** (full schema) | [COMA PDF](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf), [Cupid](https://www.microsoft.com/en-us/research/publication/generic-schema-matching-with-cupid/) |

---

## 7. Implications for building import mapping

1. **No single library** covers “upload CSV → map to our canonical schema” end-to-end; production systems combine **fuzzy label match** ([RapidFuzz](https://rapidfuzz.github.io/RapidFuzz/Usage/process.html)), optional **Valentine/COMA/Cupid-style** scoring when you have two table snapshots, and **validation** ([Frictionless](https://framework.frictionlessdata.io/docs/guides/validating-data.html) / [Pandera](https://pandera.readthedocs.io/en/stable/dataframe_schemas.html)).

2. **Academic optimum** is often **composite matchers** ([COMA](https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf)); **pragmatic MVP** is RapidFuzz + type checks + user confirmation.

3. **Ontology alignment** tooling ([OAEI](https://oaei.ontologymatching.org/), surveys in [Shvaiko & Euzenat, 2005](https://exmo.inria.fr/files/publications/shvaiko2005a.pdf)) matters when canonical fields carry **SKOS/OWL/IRI** semantics (cf. Table Schema `rdfType` — [spec](https://specs.frictionlessdata.io/table-schema/)).

4. **Profiling** ([Great Expectations Data Assistant](https://docs.greatexpectations.io/docs/reference/learn/terms/data_assistant/)) complements but does not replace mapping.

5. **Entity resolution** ([dedupe](https://docs.dedupe.io/en/latest/)) is adjacent: use when the product must link rows across imports, not only rename columns.

---

## 8. Primary bibliography (URLs)

| Resource | URL |
|----------|-----|
| Rahm & Bernstein survey (DOI) | https://doi.org/10.1007/s007780100057 |
| Rahm & Bernstein survey (PDF) | https://dbs.uni-leipzig.de/files/research/publications/2001-1/pdf/VLDBJ-Dec2001.pdf |
| On Matching Schemas Automatically (MSR-TR-2001-17) | https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2001-17.pdf |
| Cupid (MSR publication page) | https://www.microsoft.com/en-us/research/publication/generic-schema-matching-with-cupid/ |
| Cupid (VLDB PDF) | https://www.vldb.org/conf/2001/P049.pdf |
| COMA (VLDB 2002 PDF) | https://dbs.uni-leipzig.de/files/research/publications/2002-1/pdf/COMA.pdf |
| Shvaiko & Euzenat survey (PDF) | https://exmo.inria.fr/files/publications/shvaiko2005a.pdf |
| COMA Community Edition | https://sourceforge.net/projects/coma-ce/ |
| OAEI | https://oaei.ontologymatching.org/ |
| Valentine | https://github.com/delftdata/valentine |
| Frictionless Table Schema | https://specs.frictionlessdata.io/table-schema/ |
| Frictionless describe / infer | https://framework.frictionlessdata.io/docs/guides/describing-data.html |
| Frictionless validate | https://framework.frictionlessdata.io/docs/guides/validating-data.html |
| Pandera DataFrame schemas | https://pandera.readthedocs.io/en/stable/dataframe_schemas.html |
| Marshmallow quickstart | https://marshmallow.readthedocs.io/en/stable/quickstart.html |
| Great Expectations GX Core | https://docs.greatexpectations.io/docs/core/introduction/gx_overview/ |
| Great Expectations Data Assistant | https://docs.greatexpectations.io/docs/reference/learn/terms/data_assistant/ |
| RapidFuzz | https://rapidfuzz.github.io/RapidFuzz/ |
| TheFuzz (fuzzywuzzy successor) | https://github.com/seatgeek/thefuzz |
| fuzzywuzzy (archived) | https://github.com/seatgeek/fuzzywuzzy |
| dedupe | https://docs.dedupe.io/en/latest/ |
| cleanco | https://pypi.org/project/cleanco/ |
| pandas.read_csv | https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html |

---

*Document generated for tejtm prior-art review. Re-verify URLs and library versions before implementation decisions.*
