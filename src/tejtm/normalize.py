import re
import unicodedata
from typing import Sequence

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_NON_ALNUM = re.compile(r"[^\w\s]+", re.UNICODE)
_WS = re.compile(r"\s+")


def normalize_identifier(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.strip().casefold()
    text = _NON_ALNUM.sub(" ", text)
    text = _WS.sub(" ", text).strip()
    return text


def tokenize_identifier(text: str) -> tuple[str, ...]:
    if not text:
        return ()
    raw = unicodedata.normalize("NFKC", text.strip())
    raw = _NON_ALNUM.sub(" ", raw)
    parts: list[str] = []
    for chunk in _WS.split(raw):
        if not chunk:
            continue
        for piece in _CAMEL_BOUNDARY.sub(" ", chunk.replace("_", " ")).split():
            piece = normalize_identifier(piece)
            if piece:
                parts.append(piece)
    return tuple(parts)


def candidate_names(field_id: str, labels: Sequence[str], aliases: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in (field_id, *labels, *aliases):
        norm = normalize_identifier(raw)
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)
    return tuple(out)
