from __future__ import annotations

from typing import Any

from tejtm.models import MappingResult


def mapping_to_yaml(result: MappingResult) -> str:
    try:
        import yaml
    except ImportError as exc:
        raise ImportError("Install tejtm with yaml extra: pip install tejtm[yaml]") from exc
    return yaml.safe_dump(result.to_dict(), sort_keys=False)


def mapping_from_yaml(text: str) -> MappingResult:
    try:
        import yaml
    except ImportError as exc:
        raise ImportError("Install tejtm with yaml extra: pip install tejtm[yaml]") from exc
    data: Any = yaml.safe_load(text)
    return MappingResult.from_dict(data or {})
