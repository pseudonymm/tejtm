import pytest

from tejtm.engine import MappingEngine
from tejtm.models import MappingConfig
from support.loaders import list_scenario_dirs, load_scenario, source_profile_from_scenario, target_schema_from_scenario


@pytest.mark.parametrize("scenario_dir", list_scenario_dirs(), ids=lambda p: p.name)
def test_sector_scenario_mapping(scenario_dir):
    meta = load_scenario(scenario_dir)
    source = source_profile_from_scenario(scenario_dir, meta)
    target = target_schema_from_scenario(meta)
    engine = MappingEngine()
    result = engine.propose_mappings(
        source,
        target,
        config=MappingConfig(min_confidence=float(meta.get("min_confidence", 0.45))),
    )
    got = {m.source_column: m.target_field for m in result.mappings}
    for src, tgt in meta["expect_mappings"].items():
        assert got.get(src) == tgt, f"{scenario_dir.name}: {src} -> {got.get(src)} expected {tgt}"
