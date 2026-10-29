from __future__ import annotations

import sys
from pathlib import Path

_TESTS = Path(__file__).resolve().parent.parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from tejtm.engine import MappingEngine
from tejtm.models import MappingConfig

from support.loaders import (
    list_scenario_dirs,
    load_scenario,
    source_profile_from_scenario,
    target_schema_from_scenario,
)


def _fastembed_present() -> bool:
    from importlib.util import find_spec

    return find_spec("fastembed") is not None


def main() -> None:
    engine = MappingEngine()
    default_min = MappingConfig().min_confidence
    print("| Fixture | Format | min_confidence | Mapped / expected | Lowest mapped pair |")
    print("| --- | --- | --- | --- | --- |")
    total_expect = 0
    total_hit = 0
    hit_at_default = 0
    below_default: list[str] = []
    for directory in list_scenario_dirs():
        meta = load_scenario(directory)
        source = source_profile_from_scenario(directory, meta)
        target = target_schema_from_scenario(meta)
        min_c = float(meta.get("min_confidence", 0.45))
        result = engine.propose_mappings(
            source, target, config=MappingConfig(min_confidence=min_c)
        )
        got = {m.source_column: m for m in result.mappings}
        expect = meta["expect_mappings"]
        hits = 0
        lowest: tuple[float, str] | None = None
        for src, tgt in expect.items():
            total_expect += 1
            mapping = got.get(src)
            if mapping is None or mapping.target_field != tgt:
                continue
            hits += 1
            total_hit += 1
            if mapping.confidence >= default_min:
                hit_at_default += 1
            else:
                below_default.append(
                    f"`{src}` -> `{mapping.target_field}` in `{directory.name}` "
                    f"({mapping.confidence:.3f})"
                )
            label = f"`{src}` -> `{mapping.target_field}` ({mapping.confidence:.3f})"
            if lowest is None or mapping.confidence < lowest[0]:
                lowest = (mapping.confidence, label)
        lowest_cell = lowest[1] if lowest else "(none mapped)"
        print(
            f"| `{directory.name}` | {meta.get('data_format')} | {min_c:g} | "
            f"{hits} / {len(expect)} | {lowest_cell} |"
        )
    print()
    print(
        f"Expected pairs mapped at fixture min_confidence: {total_hit} / {total_expect}."
    )
    print(
        f"Expected pairs mapped at library default {default_min:g}: "
        f"{hit_at_default} / {total_expect}."
    )
    if below_default:
        print("Below default:", "; ".join(below_default) + ".")
    print(
        "FastEmbed:",
        "present (`header_embedding` can score)."
        if _fastembed_present()
        else "absent (`header_embedding` abstains).",
    )


if __name__ == "__main__":
    main()
