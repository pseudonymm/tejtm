import importlib.util

import pytest

import tejtm
from tejtm.engine import MappingEngine
from tejtm.models import MappingConfig, SourceColumn, SourceProfile, TargetField, TargetSchema
from tejtm.scorers.exact import ExactNameScorer


def test_public_api_has_no_join_or_identity_entry_points():
    banned = ("join", "dedup", "correlat", "identity", "mdm", "entity")
    names = {n.lower() for n in tejtm.__all__}
    assert "default_weights" in names
    assert not any(b in n for n in names for b in banned)


def test_duplicate_column_names_are_rejected():
    with pytest.raises(ValueError, match="unique"):
        SourceProfile(
            columns=[
                SourceColumn("name", samples=("Acme",)),
                SourceColumn("name", samples=("Ada",)),
            ]
        )


def test_duplicate_field_ids_are_rejected():
    with pytest.raises(ValueError, match="unique"):
        TargetSchema(fields=[TargetField("email"), TargetField("email")])


def test_extra_source_column_is_unmapped():
    source = SourceProfile(
        columns=[
            SourceColumn("contact", samples=("a@x.com", "b@y.com")),
            SourceColumn("notes", samples=("hello", "world")),
        ]
    )
    target = TargetSchema(fields=[TargetField("email", expected_semantic_type="email")])
    result = MappingEngine().propose_mappings(source, target, config=MappingConfig(min_confidence=0.4))
    got = {m.source_column: m.target_field for m in result.mappings}
    assert got.get("contact") == "email"
    assert "notes" in result.unmapped_columns
    assert "email" not in result.unmatched_fields


def test_extra_target_field_is_unmatched():
    source = SourceProfile(columns=[SourceColumn("contact", samples=("a@x.com", "b@y.com"))])
    target = TargetSchema(
        fields=[
            TargetField("email", expected_semantic_type="email"),
            TargetField("phone_number", expected_semantic_type="phone"),
        ]
    )
    result = MappingEngine().propose_mappings(source, target, config=MappingConfig(min_confidence=0.4))
    got = {m.source_column: m.target_field for m in result.mappings}
    assert got.get("contact") == "email"
    assert "phone_number" in result.unmatched_fields


def test_one_to_one_under_alias_conflict():
    source = SourceProfile(
        columns=[
            SourceColumn("a", samples=("x",)),
            SourceColumn("b", samples=("y",)),
        ]
    )
    target = TargetSchema(fields=[TargetField("only", aliases=("a", "b"))])
    result = MappingEngine().propose_mappings(source, target, config=MappingConfig(min_confidence=0.5))
    targets = [m.target_field for m in result.mappings]
    assert targets.count("only") == 1
    assert len(result.unmapped_columns) == 1
    assert result.unmatched_fields == ()


def test_mapping_includes_score_breakdown():
    source = SourceProfile(columns=[SourceColumn("phone", samples=("+1 555-0100",))])
    target = TargetSchema(
        fields=[TargetField("phone_number", aliases=("phone",), expected_semantic_type="phone")]
    )
    result = MappingEngine().propose_mappings(source, target, config=MappingConfig(min_confidence=0.4))
    mapping = next(m for m in result.mappings if m.source_column == "phone")
    assert mapping.breakdown
    scorers = {part.scorer for part in mapping.breakdown}
    assert scorers <= {"exact_name", "fuzzy_name", "semantic_type", "header_embedding", "value_intent"}
    assert all(0.0 <= part.score <= 1.0 for part in mapping.breakdown)
    if importlib.util.find_spec("fastembed") is None:
        assert "header_embedding" not in scorers


def test_weights_prefer_value_type_over_misleading_header():
    source = SourceProfile(
        columns=[
            SourceColumn("email_addr", samples=("+1 555-0100", "555-0199")),
            SourceColumn("contact", samples=("a@x.com", "b@y.com")),
        ]
    )
    target = TargetSchema(
        fields=[
            TargetField("email", expected_semantic_type="email"),
            TargetField("phone_number", expected_semantic_type="phone"),
        ]
    )
    by_name = MappingEngine().propose_mappings(
        source,
        target,
        config=MappingConfig(min_confidence=0.3, weights={"fuzzy_name": 1.0, "semantic_type": 0.0, "value_intent": 0.0}),
    )
    by_type = MappingEngine().propose_mappings(
        source,
        target,
        config=MappingConfig(min_confidence=0.3, weights={"fuzzy_name": 0.0, "exact_name": 0.0, "semantic_type": 1.0}),
    )
    name_map = {m.source_column: m.target_field for m in by_name.mappings}
    type_map = {m.source_column: m.target_field for m in by_type.mappings}
    assert name_map.get("email_addr") == "email"
    assert type_map.get("email_addr") == "phone_number"
    assert type_map.get("contact") == "email"


def test_abstaining_scorer_does_not_zero_confidence():
    source = SourceProfile(columns=[SourceColumn("phone", samples=("+1 555-0100",))])
    target = TargetSchema(fields=[TargetField("phone_number", aliases=("phone",))])

    class Abstain:
        name = "noop"

        def score(self, column, field, context):
            return None

    solo = MappingEngine(scorers=(ExactNameScorer(),)).propose_mappings(
        source, target, config=MappingConfig(min_confidence=0.5)
    )
    mixed = MappingEngine(scorers=(ExactNameScorer(), Abstain())).propose_mappings(
        source, target, config=MappingConfig(min_confidence=0.5)
    )
    assert solo.mappings[0].confidence == mixed.mappings[0].confidence
    assert mixed.mappings[0].target_field == "phone_number"


def test_saved_mappings_replay_as_overrides():
    source = SourceProfile(columns=[SourceColumn("contact", samples=("a@x.com",))])
    target = TargetSchema(
        fields=[
            TargetField("email", expected_semantic_type="email"),
            TargetField("phone", expected_semantic_type="phone"),
        ]
    )
    engine = MappingEngine()
    first = engine.propose_mappings(source, target, config=MappingConfig(min_confidence=0.4))
    overrides = {m.source_column: m.target_field for m in first.mappings}
    replay = engine.propose_mappings(
        source,
        target,
        config=MappingConfig(overrides=overrides, min_confidence=0.99),
    )
    assert {m.source_column: m.target_field for m in replay.mappings} == overrides
    assert all(m.confidence == 1.0 for m in replay.mappings)


def test_non_english_header_maps_via_value_type():
    source = SourceProfile(
        columns=[SourceColumn("Téléphone", samples=("+1 555-0100", "555-0199"))]
    )
    target = TargetSchema(fields=[TargetField("phone_number", expected_semantic_type="phone")])
    result = MappingEngine().propose_mappings(source, target, config=MappingConfig(min_confidence=0.45))
    got = {m.source_column: m.target_field for m in result.mappings}
    assert got.get("Téléphone") == "phone_number"


def test_homonym_headers_disambiguate_with_exemplars():
    source = SourceProfile(
        columns=[
            SourceColumn("name", samples=("Ada Lovelace", "Grace Hopper")),
            SourceColumn("product", samples=("Widget A", "Widget B")),
        ]
    )
    target = TargetSchema(
        fields=[
            TargetField(
                "person_name",
                aliases=("name",),
                expected_semantic_type="freetext",
                exemplar_samples=("Ada Lovelace", "Alan Turing"),
            ),
            TargetField(
                "product_name",
                aliases=("product",),
                expected_semantic_type="freetext",
                exemplar_samples=("Widget A", "Gadget 9"),
            ),
        ]
    )
    result = MappingEngine().propose_mappings(source, target, config=MappingConfig(min_confidence=0.35))
    got = {m.source_column: m.target_field for m in result.mappings}
    assert got.get("name") == "person_name"
    assert got.get("product") == "product_name"
