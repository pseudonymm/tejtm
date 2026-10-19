from tejtm.engine import MappingEngine
from tejtm.models import MappingConfig, SourceColumn, SourceProfile, TargetField, TargetSchema
from support.loaders import load_scenario, source_profile_from_scenario, target_schema_from_scenario

SCENARIO = (
    __import__("pathlib").Path(__file__).parent / "fixtures" / "scenarios" / "crm_contacts"
)


def test_legacy_golden_alias_of_crm_scenario():
    meta = load_scenario(SCENARIO)
    source = source_profile_from_scenario(SCENARIO, meta)
    target = target_schema_from_scenario(meta)
    result = MappingEngine().propose_mappings(
        source, target, config=MappingConfig(min_confidence=0.45)
    )
    got = {m.source_column: m.target_field for m in result.mappings}
    for src, tgt in meta["expect_mappings"].items():
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
