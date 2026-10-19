# Heuristic column type detection from sample values

Research notes from **primary sources** (official specs, library docs, and source code). Focus: inferring semantic and primitive column types from messy tabular strings.

**Date:** 2026-10-19

---

## Summary

Most tabular type inference is **not** semantic email/phone/URL detection. It is **(1) try cast / parse each cell**, **(2) accumulate scores or eliminate candidates**, **(3) pick a winner** with tie-break rules. Semantic formats (email, URI, UUID) appear mainly in **validation** when a schema already declares `type` + `format`, or in **profiling** layers that add optional types (e.g. URL in ydata-profiling).

| Semantic type | messytables | Table Schema / frictionless-py | pandas `infer_dtype` | ydata-profiling typeset | clean-text | libphonenumber | validators | dateutil |
|---------------|-------------|--------------------------------|------------------------|-------------------------|------------|----------------|------------|----------|
| Email | — | validate `string` + `format: email` | — | — | regex replace/detect | — | `validators.email` | — |
| Phone | — | — | — | — | regex replace/detect | parse + `isValidNumber` | — | — |
| URL | — | validate `string` + `format: uri` | — | optional `URL` (`urlparse`) | regex replace/detect | — | `validators.url` | — |
| Date/datetime | `DateType` / `DateUtilType` | `date` / `time` / `datetime` candidates | `datetime64`, `date`, `time` | `DateTime` via `pd.to_datetime` | — | — | — | `parser.parse` |
| Address (postal) | — | — (geo: `geopoint`, `geojson`) | — | — | — | — | — | — |
| UUID | — | validate `string` + `format: uuid` | — | — | — | — | `validators.uuid` | — |
| Currency | `CurrencyType` (prefix strip) | `number` + locale chars | — | — | `CURRENCY_REGEX` | — | — | — |
| Boolean | `BoolType` lexicon | `boolean` candidate + true/false lists | `boolean` | `Boolean` + mapping config | — | — | — | — |
| Integer vs float | `IntegerType` vs `DecimalType` + weights | `integer` vs `number` (+ `float_number`) | `integer` / `floating` / `mixed-*` | `Numeric` (pandas numeric dtypes) | `NUMBERS_REGEX` (NLP) | — | — | — |
| Freetext | `StringType` fallback | `string` default / `any` | `string` / `mixed` | `Text` | default after cleaning | — | — | — |

---

## Common heuristic patterns

### 1. Cast voting with type priority (messytables)

For each column, every cell is tested with each `CellType.test()` (default: `cast()` without exception). Successful types add that type’s **`guessing_weight`**. The winning type is the highest score; **ties go to the first type in the fixed instance list** (documented as relying on Python’s `max` ordering).

Types and weights in default `TYPES`: `BoolType` (7), `IntegerType` (6), `DecimalType` (4), `DateType` instances / `DateUtilType` (3), `StringType` (1). `CurrencyType` and `PercentageType` extend decimal parsing but use weight 0 unless explicitly included.

**Strict mode:** any single failing cell removes that type from the column entirely; surviving types get their weight as score.

Source: [messytables `types.py`](https://github.com/okfn/messytables/blob/master/messytables/types.py).

### 2. Schema candidate racing with confidence threshold (frictionless-py)

`Detector.detect_schema()` iterates a **fixed ordered list** of field type candidates (`DEFAULT_FIELD_CANDIDATES`: yearmonth, geopoint, duration, geojson, object, array, datetime, time, date, integer, number, boolean, year, string). For each column, each candidate field gets a **score** by calling `read_cell()` on sample rows (+1 success, −1 on validation notes). Missing values reduce the effective sample size. A type wins when `score >= max_score * field_confidence` (default **0.9**).

This infers **Table Schema `type`**, not `string` **format** (email/uri/uuid). Those formats are validated only when declared on a `StringField`.

Sources:

- [frictionless `detector.py`](https://github.com/frictionlessdata/frictionless-py/blob/main/frictionless/detector/detector.py)
- [frictionless `settings.py`](https://github.com/frictionlessdata/frictionless-py/blob/main/frictionless/settings.py) (`DEFAULT_FIELD_CANDIDATES`, `DEFAULT_FIELD_CONFIDENCE`, `DEFAULT_SAMPLE_SIZE`)

### 3. Logical type graph (ydata-profiling / Visions)

Profiling builds a **Visions** typeset: base types (`Unsupported`, `Boolean`, `Numeric`, `Text`, `Categorical`, `DateTime`) plus optional `URL`, `Path`, `File`, `Image`, `TimeSeries`. Detection walks **inference relations** (e.g. Text → Numeric if `string_is_numeric`, Text → DateTime if `string_is_datetime`).

Important behaviors:

- **Boolean strings:** configurable lowercase mapping; column must match keys exactly (`str.lower().isin(k.keys()).all()`).
- **Numeric strings:** `pd.to_numeric(..., errors="coerce")`, reject if all NaN; exclude bool-like and low-cardinality numeric (treated as category).
- **Datetime strings:** success if `pd.to_datetime` yields at least one non-NaT (pandas 2+: `format="mixed"`).
- **URL:** every value must parse with `urlparse` and have **both** `scheme` and `netloc` (optional type, config-gated).
- **Categorical:** cardinality thresholds vs row count; not bool.

Sources:

- [fg-data-profiling `typeset.py`](https://github.com/Data-Centric-AI-Community/fg-data-profiling/blob/develop/src/data_profiling/model/typeset.py) (current profiling codebase lineage from ydata-profiling)
- [fg-data-profiling `typeset_relations.py`](https://github.com/Data-Centric-AI-Community/fg-data-profiling/blob/develop/src/data_profiling/model/typeset_relations.py)

### 4. Element-kind aggregation (pandas)

`pandas.api.types.infer_dtype` inspects **already materialized** values (list-like / array), classifying storage-level kinds: string, integer, floating, boolean, datetime64, mixed-*, etc. It does **not** parse date strings or detect emails; for object columns of strings it returns `string` only if all non-null elements are strings.

Implementation lives in Cython [`pandas/_libs/lib.pyx`](https://github.com/pandas-dev/pandas/blob/main/pandas/_libs/lib.pyx) (`infer_dtype`); public contract in [pandas API docs](https://pandas.pydata.org/docs/reference/api/pandas.api.types.infer_dtype.html).

**Integer vs float:** if all values are numeric floats but each is whole, behavior depends on mix (`integer`, `floating`, `mixed-integer-float`). This is distinct from `read_csv` dtype inference.

---

## Tool reference

### messytables

Legacy OKFN library for messy CSV-like tables; README points maintainers to [tabulator-py](https://github.com/frictionlessdata/tabulator-py). Still a clear reference for **weighted cast guessing**.

| Mechanism | Detail |
|-----------|--------|
| Integer | Parse as float or `locale.atoi`; require `value.is_integer()` |
| Decimal | `decimal.Decimal` or `locale.atof` |
| Boolean | Lowercased token sets (`true_values` / `false_values`; defaults include yes/no/true/false and **0/1 with non-obvious mapping**) |
| Date | Many `strptime` patterns from generated `DATE_FORMATS`; pre-filter via `is_date()` regex |
| Date (fast) | `DateUtilType` uses `dateutil.parser.parse` when `is_date()` passes |
| Currency | Take substring before first space, then decimal cast |
| Time | Fixed substring positions (fragile on varied formats) |

Date pre-filter (`^\d{1,4}[-\/\.\s]\S+[-\/\.\s]\S+`, length ≠ 1): [messytables `dateparser.py`](https://github.com/okfn/messytables/blob/master/messytables/dateparser.py).

**Not covered:** email, phone, URL, UUID, postal address.

---

### Table Schema (spec) and frictionless-py (implementation)

**Table Schema** defines logical `type` and optional `format`. Tabular **inference** in frictionless-py selects among **structural** types only (see candidate list above).

**String formats** (validation, not auto-inferred from data):

| `format` | Meaning (spec) |
|----------|----------------|
| `default` | Any string |
| `email` | Valid email |
| `uri` | Valid URI |
| `uuid` | UUID string |
| `binary` | Base64 binary |

Spec: [Frictionless Table Schema — Types and string formats](https://specs.frictionlessdata.io/table-schema/#string).

**Implementation** (`StringField.create_value_reader`):

- **uri:** RFC 3986 validator, scheme required ([`string.py`](https://github.com/frictionlessdata/frictionless-py/blob/main/frictionless/fields/string.py))
- **email / uuid:** `platform.validators.email` / `platform.validators.uuid` (Python **validators** package bundled via frictionless platform layer)

**Rich semantics:** optional `rdfType` URI (e.g. Schema.org) — semantic hint for consumers, not automatic inference.

**Integer vs number:** separate candidates; `NumberField` supports `float_number`, `decimal_char`, `group_char`, optional stripping of non-digits when `bare_number` is false ([`number.py`](https://github.com/frictionlessdata/frictionless-py/blob/main/frictionless/fields/number.py)).

**Geo “address-like” data:** `geopoint` / `geojson` types, not postal addresses.

Historical note: **tableschema-py** was the earlier Python implementation; current work is **frictionless-py** against the same spec.

---

### pandas `infer_dtype`

Use when values are already typed or for **post-load** column kind summary. Pair with `pd.to_datetime` / `pd.to_numeric` for string parsing (as profiling does), not built into `infer_dtype` itself.

Docs: [infer_dtype](https://pandas.pydata.org/docs/reference/api/pandas.api.types.infer_dtype.html). Source: [lib.pyx `infer_dtype`](https://github.com/pandas-dev/pandas/blob/main/pandas/_libs/lib.pyx).

---

### ydata-profiling

Column typing for reports uses the **Visions typeset** described above. Semantic URL detection is **heuristic and strict** (all rows must look like URLs). There is **no built-in Email, Phone, UUID, or Address** type in the default typeset.

Upstream repo has moved; profiling typeset source cited above lives under [Data-Centric-AI-Community/fg-data-profiling](https://github.com/Data-Centric-AI-Community/fg-data-profiling) (`develop` branch as of research).

---

### clean-text (`cleantext`, not `cleantext` on PyPI)

Purpose: **normalize free text**, not infer CSV column schemas. Relevant for type detection as a **pattern library**: hand-crafted regexes to find/replace emails, phones, URLs, currency symbols, numbers, etc.

Package name: **`clean-text`**; import `from cleantext import clean`. README explicitly lists RegEx rules and points to [`cleantext/clean.py`](https://github.com/jfilter/clean-text/blob/main/cleantext/clean.py).

Example patterns ([`cleantext/constants.py`](https://github.com/jfilter/clean-text/blob/main/cleantext/constants.py)):

- **EMAIL_REGEX** — permissive ASCII/Unicode local-part and domain
- **PHONE_REGEX** — international prefixes, parentheses, extensions (heuristic, not libphonenumber)
- **URL_REGEX** — http(s), ftp, bare domains, IPv4/IPv6
- **CURRENCY_REGEX** — union of known currency symbols
- **NUMBERS_REGEX** — localized grouping/decimal variants

**Column-level use:** run regex match rate on sample cells (e.g. ≥95% match ⇒ candidate type), understanding high false-positive/negative rates vs dedicated validators.

---

### libphonenumber

Google’s library for **parsing, formatting, and validating** international phone numbers (Java/C++/JS; Python ecosystem typically uses **`phonenumbers`** port). Not integrated into messytables, frictionless detector, or ydata typeset.

Validation ladder (README):

- `isPossibleNumber` — length/heuristic, fast
- `isValidNumber` — full region-aware validation
- `findNumbers` — extract from free text

Source: [libphonenumber README](https://github.com/google/libphonenumber/blob/master/README.md). Demo: [libphonenumber.appspot.com](https://libphonenumber.appspot.com/).

**Column heuristic:** parse with default or column-derived region; require `isValidNumber` (or softer `isPossibleNumber` for sparse data). Costlier than regex but far more accurate.

---

### python-dateutil `parser`

Generic **string → datetime** parser for messy human dates. Used directly by messytables `DateUtilType.cast()`.

`parser.parse(timestr, fuzzy=False, ...)`: **`fuzzy=True`** allows non-date tokens in the string (e.g. “Today is January 1, 2047 at 8:21:00AM”). **`fuzzy_with_tokens=True`** returns parsed datetime plus leftover tokens.

Docs: [dateutil parser module](https://dateutil.readthedocs.io/en/stable/parser.html).

**Column heuristic:** attempt parse on sample; track success rate and ambiguity (multiple formats). Prefer **strict** parsing when inferring types to avoid bool/int false positives; use fuzzy only for proven freetext-date columns.

---

### validators

Single-value validators without schema boilerplate: `validators.email()`, `validators.url()`, `validators.uuid()`, etc.

Docs: [python-validators documentation](https://nandgator.github.io/pyvalidators/) (maintainer fork; see [project README](https://github.com/python-validators/validators/blob/master/README.md)). Used by frictionless `StringField` for email and uuid formats.

**Column heuristic:** for candidate semantic type `T`, compute `mean(validators.T(cell) for cell in sample)`; promote if above threshold and beats alternates. Good for **email / url / uuid**; does not cover phone (use libphonenumber) or address.

---

## Gaps and pitfalls

1. **Postal address** — none of these tools infer street addresses from samples; use external geocoding or ML, or `rdfType` only as a declared semantic tag.
2. **Phone** — regex (clean-text) vs libphonenumber differ by orders of magnitude in precision; frictionless/messytables/ydata omit phone inference.
3. **Boolean false positives** — messytables bool tokens overlap numeric strings; ydata excludes numeric categoricals from bool; frictionless uses explicit true/false lists.
4. **Date false positives** — dateutil and `pd.to_datetime(format="mixed")` can interpret ambiguous numeric strings; messytables uses `is_date()` pre-filter to reduce this.
5. **URL vs URI** — ydata requires `scheme` + `netloc`; frictionless URI uses RFC 3986 with required scheme; bare `example.com` may fail URI rules while regex URL matchers accept it.
6. **Currency** — messytables assumes `"USD 12.34"`-style space split; clean-text only finds symbol runs, not ISO currency codes alone.
7. **Sample size** — frictionless defaults (`DEFAULT_SAMPLE_SIZE = 100`); profiling uses full series for relations but reports may subsample elsewhere — check config when comparing tools.
8. **Strict vs soft inference** — messytables `strict=True` is column-safe for ETL; soft mode tolerates outliers and drifts toward highest-weight compatible type.

---

## Practical composition for a column type detector

A layered design aligned with these sources:

1. **Missing / empty** — frictionless missing-value handling; messytables skips empty cells in scoring.
2. **Primitive race** — frictionless-style candidates or messytables weights for bool / int / decimal / date / string.
3. **Parse probes** — `pd.to_numeric`, `pd.to_datetime`, `dateutil.parser.parse` (strict first).
4. **Semantic promotion** (on string columns or high string score):
   - UUID, email, URL: **validators** (+ frictionless-equivalent RFC 3986 for URI if needed)
   - Phone: **libphonenumber** (region-aware)
   - Currency: decimal parse + currency symbol / ISO code table
   - Freetext: default when no semantic type clears threshold
5. **Cardinality** — ydata-style rules to split **Categorical** vs **Text** vs numeric-coded categories.

Use **clean-text regexes** as cheap pre-filters or feature flags, not as ground truth.

---

## Primary source index

| Resource | URL |
|----------|-----|
| messytables types | https://github.com/okfn/messytables/blob/master/messytables/types.py |
| messytables date prefilter | https://github.com/okfn/messytables/blob/master/messytables/dateparser.py |
| Frictionless Table Schema | https://specs.frictionlessdata.io/table-schema/ |
| frictionless detector | https://github.com/frictionlessdata/frictionless-py/blob/main/frictionless/detector/detector.py |
| frictionless settings | https://github.com/frictionlessdata/frictionless-py/blob/main/frictionless/settings.py |
| frictionless StringField | https://github.com/frictionlessdata/frictionless-py/blob/main/frictionless/fields/string.py |
| frictionless NumberField | https://github.com/frictionlessdata/frictionless-py/blob/main/frictionless/fields/number.py |
| pandas infer_dtype API | https://pandas.pydata.org/docs/reference/api/pandas.api.types.infer_dtype.html |
| pandas infer_dtype implementation | https://github.com/pandas-dev/pandas/blob/main/pandas/_libs/lib.pyx |
| ydata / profiling typeset | https://github.com/Data-Centric-AI-Community/fg-data-profiling/blob/develop/src/data_profiling/model/typeset.py |
| ydata typeset relations | https://github.com/Data-Centric-AI-Community/fg-data-profiling/blob/develop/src/data_profiling/model/typeset_relations.py |
| clean-text README | https://github.com/jfilter/clean-text/blob/main/README.md |
| clean-text regex constants | https://github.com/jfilter/clean-text/blob/main/cleantext/constants.py |
| libphonenumber | https://github.com/google/libphonenumber/blob/master/README.md |
| dateutil parser | https://dateutil.readthedocs.io/en/stable/parser.html |
| validators project | https://github.com/python-validators/validators |
| validators docs | https://nandgator.github.io/pyvalidators/ |
