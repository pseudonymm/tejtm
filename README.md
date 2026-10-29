# tejtm

tejtm maps messy import columns to a target schema you define. It returns one-to-one pairs with a composite confidence and a per-scorer breakdown. It does not read files, join records, or validate rows.

## Install

```bash
pip install tejtm
```

Optional extras:

```bash
pip install "tejtm[semantic,pydantic,yaml]"
```

`semantic` adds FastEmbed header similarity. `pydantic` builds a target schema from a model. `yaml` saves mapping results.

From a clone, for local development:

```bash
pip install -e ".[dev]"
```

Published package: [tejtm 0.1.0 on PyPI](https://pypi.org/project/tejtm/0.1.0/). Linked docs under `docs/` resolve on GitHub, not on the PyPI project page.

## Map columns to a target schema

The library takes column names plus sample values. You keep file I/O in your app.

```python
from tejtm import MappingEngine, MappingConfig, SourceColumn, SourceProfile, TargetField, TargetSchema

source = SourceProfile(columns=[
    SourceColumn("phone", samples=("+1 555-0100",)),
    SourceColumn("contact", samples=("user@example.com",)),
    SourceColumn("Cust Name", samples=("Ada Lovelace",)),
])
target = TargetSchema(fields=[
    TargetField("phone_number", aliases=("phone",), expected_semantic_type="phone"),
    TargetField("email", expected_semantic_type="email"),
    TargetField("full_name", aliases=("name", "customer name")),
])
result = MappingEngine().propose_mappings(
    source,
    target,
    config=MappingConfig(min_confidence=0.5),
)
for mapping in result.mappings:
    print(mapping.source_column, "->", mapping.target_field, mapping.confidence)
print("unmapped", result.unmapped_columns)
print("unmatched", result.unmatched_fields)
```

You should see `phone -> phone_number`, `contact -> email`, and `Cust Name -> full_name`. Weak pairs stay out of `mappings` and land in `unmapped_columns` or `unmatched_fields`.

Default `min_confidence` is `0.55`. Lower it for messy vendor headers, then auto-apply only the pairs above a threshold you pick.

## Apply the mapping

tejtm does not rewrite rows. Use `source_column` and `target_field` to rename keys in your own loop. For cell casting after rename, call `coerce_value` or `coerce_record`. For a Pydantic model, see [How to customize mapping](docs/customization.md).

## Fixture results

The six directories under `tests/fixtures/scenarios/` are the only sector samples in this repo. They are small synthetic tables, not a customer corpus. Treat a fixture as passing when every `expect_mappings` pair lands in `result.mappings` at that fixture's `min_confidence`.

Measured 29 Oct 2026 in this checkout, FastEmbed absent, two identical runs. `header_embedding` abstained. Scores come from `exact_name`, `fuzzy_name`, `semantic_type`, and `value_intent` only. The limiter is fixture size (2 or 3 columns) and those lowered thresholds, not production files.

| Fixture | Format | min_confidence | Mapped / expected | Lowest mapped pair |
| --- | --- | --- | --- | --- |
| `crm_contacts` | csv | 0.45 | 3 / 3 | `contact` -> `email` (0.549) |
| `edge_duplicate_generic_headers` | csv | 0.35 | 2 / 2 | `ref_a` -> `order_reference` (0.601) |
| `finance_ledger` | xlsx | 0.4 | 3 / 3 | `GL Code` -> `ledger_account` (0.752) |
| `healthcare_appointments` | csv | 0.4 | 3 / 3 | `Clinic` -> `facility_name` (0.480) |
| `hr_payroll` | csv | 0.4 | 3 / 3 | `Gross Pay` -> `gross_amount` (0.569) |
| `warehouse_inventory` | csv | 0.4 | 3 / 3 | `Bin Loc` -> `storage_location` (0.807) |

All 17 expected pairs mapped at those fixture thresholds. At the library default of `0.55`, 15 of 17 still map. The two that drop are `contact` -> `email` in `crm_contacts` (0.549) and `Clinic` -> `facility_name` in `healthcare_appointments` (0.480). See [About mapping limits](docs/limitations.md) for why demos sit below the default.

`.venv/bin/python -m pytest -q` reported 52 passed in this checkout. That count is the test suite, not a mapping-accuracy figure.

Regenerate the table:

```bash
.venv/bin/python tests/support/fixture_stats.py
```

## What to read next

- [How to customize mapping](docs/customization.md) covers weights, overrides, custom scorers, exemplars, Pydantic, and YAML.
- [About mapping limits](docs/limitations.md) covers joins, duplicate headers, optional extras, and unused config.
- [Product spec](docs/specs/schema-mapping-spec.md) is the v1 contract.
- [Glossary](docs/GLOSSARY.md) defines source column, target field, and value intent.

Run tests with the project virtualenv:

```bash
.venv/bin/python -m pytest -q
```
