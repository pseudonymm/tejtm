from tejtm.models import FieldMapping, MappingResult
from tejtm.serialization import mapping_from_yaml, mapping_to_yaml


def test_mapping_roundtrip_yaml():
    result = MappingResult(
        mappings=(FieldMapping("a", "b", 0.9, ()),),
        unmapped_columns=("c",),
        unmatched_fields=(),
    )
    text = mapping_to_yaml(result)
    restored = mapping_from_yaml(text)
    assert restored.mappings[0].source_column == "a"
    assert restored.unmapped_columns == ("c",)
    assert restored.unmatched_fields == ()


def test_mapping_result_dict_roundtrip_keeps_unmatched_and_breakdown():
    from tejtm.models import ScorerResult

    result = MappingResult(
        mappings=(
            FieldMapping(
                "a",
                "b",
                0.9,
                (ScorerResult("exact_name", 1.0, 1.0, "alias"),),
            ),
        ),
        unmapped_columns=("c",),
        unmatched_fields=("d",),
    )
    restored = MappingResult.from_dict(result.to_dict())
    assert restored.unmatched_fields == ("d",)
    assert restored.mappings[0].breakdown[0].scorer == "exact_name"
