from tejtm.engine import MappingEngine
from tejtm.models import MappingConfig, SourceColumn, SourceProfile, TargetField, TargetSchema


def test_value_intent_splits_product_and_customer_columns():
    source = SourceProfile(
        columns=[
            SourceColumn("col_a", samples=("SKU-100", "SKU-200", "PART-9")),
            SourceColumn("col_b", samples=("Jane Doe", "Bob Lee")),
        ]
    )
    target = TargetSchema(
        fields=[
            TargetField("product_name", description="product title"),
            TargetField("customer_name", description="person customer"),
        ]
    )
    result = MappingEngine().propose_mappings(source, target, config=MappingConfig(min_confidence=0.35))
    got = {m.source_column: m.target_field for m in result.mappings}
    assert got.get("col_a") == "product_name"
    assert got.get("col_b") == "customer_name"
