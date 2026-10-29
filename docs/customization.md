# How to customize mapping

Use these steps when the default engine maps the wrong column, or when you want to replay a reviewer's edits. The public call stays `MappingEngine.propose_mappings`.

## Bias scorers with weights

Pass scorer names to `MappingConfig.weights`. Missing names keep the defaults in `DEFAULT_WEIGHTS`.

| Scorer | Default weight | Signal |
| --- | --- | --- |
| `exact_name` | 1.0 | Normalized header or alias equality |
| `fuzzy_name` | 0.45 | RapidFuzz similarity on headers |
| `semantic_type` | 0.25 | Sample type versus `expected_semantic_type` |
| `header_embedding` | 0.20 | Optional FastEmbed cosine on headers |
| `value_intent` | 0.30 | Value signature versus type profile or `exemplar_samples` |

A scorer that returns `None` does not enter the weighted mean. A `semantic_type` mismatch returns score `0.0` with a weight, which lowers the pair.

```python
from tejtm import DEFAULT_WEIGHTS, MappingConfig, MappingEngine

print(DEFAULT_WEIGHTS)
config = MappingConfig(
    min_confidence=0.4,
    weights={"fuzzy_name": 0.2, "semantic_type": 1.0},
)
result = MappingEngine().propose_mappings(source, target, config=config)
```

## Force a pair with overrides

Overrides skip inference for those columns and set confidence to `1.0`. They also reserve the target field so assignment cannot reuse it.

```python
config = MappingConfig(overrides={"Contact": "phone"}, min_confidence=0.4)
```

To replay a previous `MappingResult` on the next file, copy `source_column` to `target_field` into `overrides`. High `min_confidence` then applies only to columns the reviewer did not lock.

## Disambiguate generic headers with exemplars

When two columns share a vague name shape, put example values on the target field. The value-intent scorer compares sample signatures to those exemplars.

```python
TargetField(
    "order_reference",
    expected_semantic_type="freetext",
    exemplar_samples=("ORD-500", "ORD-501"),
)
```

Sector words do not belong in library code. Put them in aliases, types, or exemplars.

## Register a custom scorer

A scorer implements `name` and `score(column, field, context)`. Return `ScorerResult` or `None`. Pass the tuple into `MappingEngine(scorers=...)`.

```python
from tejtm.engine import MappingEngine
from tejtm.models import ScorerResult
from tejtm.scorers.base import ScoringContext

class AlwaysPhone:
    name = "always_phone"

    def score(self, column, field, context: ScoringContext):
        if field.id == "phone_number":
            return ScorerResult(self.name, 0.99, 1.0, "domain hook")
        return None

engine = MappingEngine(scorers=(AlwaysPhone(),))
```

You replace the default scorer tuple when you pass `scorers`. Include the built-ins you still want.

## Build the target schema from Pydantic

Install `tejtm[pydantic]`. Field title becomes a label. Put aliases and types in `json_schema_extra`.

```python
from pydantic import BaseModel, EmailStr, Field
from tejtm.pydantic_adapter import propose_and_apply
from tejtm.models import MappingConfig

class Customer(BaseModel):
    name: str = Field(title="Full Name")
    email: EmailStr = Field(
        json_schema_extra={
            "tejtm_aliases": ["Contact", "E-mail"],
            "semantic_type": "email",
        }
    )

result = propose_and_apply(
    Customer,
    [{"Contact": "a@example.com", "Full Name": "Ada"}],
    config=MappingConfig(min_confidence=0.4),
)
print(result.column_rename)
print(result.valid_rows)
```

`propose_and_apply` maps, renames keys, coerces fields that have `semantic_type`, then calls `model_validate`. Row errors land in `result.errors`.

## Coerce cells after you rename

```python
from tejtm import coerce_value, coerce_record

coerce_value("42", "integer")  # 42
coerce_record({"amount": "$12.00"}, {"amount": "currency"})
```

Failed casts leave the original string. Email and URL stay strings.

## Save a mapping result

Install `tejtm[yaml]`. `MappingResult.to_dict()` needs no extra. YAML helpers wrap that dict.

```python
from tejtm.serialization import mapping_to_yaml, mapping_from_yaml

text = mapping_to_yaml(result)
restored = mapping_from_yaml(text)
```

This stores the proposed pairs. It does not store `MappingConfig`. Keep weights and `min_confidence` in your own config file.

## Built-in semantic types

`detect_semantic_type` labels a sample as one of `email`, `phone`, `url`, `uuid`, `date`, `datetime`, `time`, `boolean`, `currency`, `integer`, `number`, or `freetext`. Bare digit strings are not phones. Currency needs a `$`, `€`, or `£` sign, or a thousands separator. A number column can still match a currency field through type compatibility.
