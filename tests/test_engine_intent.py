from tejtm.engine import MappingEngine
from tejtm.models import MappingConfig, SourceColumn, SourceProfile, TargetField, TargetSchema


def test_exemplar_samples_disambiguate_generic_columns():
    source = SourceProfile(
        columns=[
            SourceColumn("col_a", samples=("ORD-100", "ORD-200")),
            SourceColumn("col_b", samples=("SHP-900", "SHP-901")),
        ]
    )
    target = TargetSchema(
        fields=[
            TargetField(
                "order_reference",
                exemplar_samples=("ORD-500", "ORD-501"),
            ),
            TargetField(
                "shipment_reference",
                exemplar_samples=("SHP-800", "SHP-801"),
            ),
        ]
    )
    result = MappingEngine().propose_mappings(source, target, config=MappingConfig(min_confidence=0.35))
    got = {m.source_column: m.target_field for m in result.mappings}
    assert got.get("col_a") == "order_reference"
    assert got.get("col_b") == "shipment_reference"
