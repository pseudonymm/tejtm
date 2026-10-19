# tejtm

Python library for mapping messy import columns to a canonical schema with composite confidence scores.

## Install

```bash
pip install -e ".[dev]"
pip install -e ".[semantic,pydantic,yaml]"  # optional extras
```

## Quick start

```python
from tejtm import MappingEngine, MappingConfig, SourceColumn, SourceProfile, TargetField, TargetSchema

source = SourceProfile(columns=[
    SourceColumn("phone", samples=("+1 555-0100",)),
    SourceColumn("contact", samples=("user@example.com",)),
])
target = TargetSchema(fields=[
    TargetField("phone_number", aliases=("phone",), expected_semantic_type="phone"),
    TargetField("email", expected_semantic_type="email"),
])
result = MappingEngine().propose_mappings(source, target, config=MappingConfig(min_confidence=0.5))
for m in result.mappings:
    print(m.source_column, "->", m.target_field, m.confidence)
```

See [docs/specs/schema-mapping-spec.md](docs/specs/schema-mapping-spec.md) and [docs/README.md](docs/README.md).
