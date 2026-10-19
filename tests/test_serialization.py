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
