import json
from pathlib import Path

from tejtm.engine import MappingEngine
from tejtm.models import MappingConfig, SourceColumn, SourceProfile, TargetField, TargetSchema

FIXTURES = Path(__file__).parent / "fixtures" / "golden"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_golden_basic_import():
    data = _load("basic_import.json")
    source = SourceProfile(
        columns=[
            SourceColumn(name=c["name"], samples=tuple(c.get("samples", [])))
            for c in data["source_columns"]
        ]
    )
    target = TargetSchema(
        fields=[
            TargetField(
                id=f["id"],
                aliases=tuple(f.get("aliases", [])),
                expected_semantic_type=f.get("expected_semantic_type"),
            )
            for f in data["target_fields"]
        ]
    )
    engine = MappingEngine()
    result = engine.propose_mappings(source, target, config=MappingConfig(min_confidence=0.45))
    got = {m.source_column: m.target_field for m in result.mappings}
    for src, tgt in data["expect_mappings"].items():
        assert got.get(src) == tgt


def test_override_wins():
    source = SourceProfile(columns=[SourceColumn("Contact", samples=("x@y.com",))])
    target = TargetSchema(
        fields=[
            TargetField("email", expected_semantic_type="email"),
            TargetField("phone", expected_semantic_type="phone"),
        ]
    )
    cfg = MappingConfig(overrides={"Contact": "phone"}, min_confidence=0.4)
    result = MappingEngine().propose_mappings(source, target, config=cfg)
    assert any(m.source_column == "Contact" and m.target_field == "phone" for m in result.mappings)
