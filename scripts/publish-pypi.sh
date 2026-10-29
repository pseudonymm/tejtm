#!/usr/bin/env bash
# Build tejtm from this checkout and upload to PyPI.
# Bump [project].version in pyproject.toml first. PyPI rejects a filename that
# was already used (HTTP 400 File already exists), even with identical bytes.
#
# Usage:
#   ./scripts/publish-pypi.sh           # build, check, upload
#   ./scripts/publish-pypi.sh --dry-run # build and check only
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

dry_run=0
if [[ "${1:-}" == "--dry-run" ]]; then
  dry_run=1
elif [[ $# -gt 0 ]]; then
  echo "usage: $0 [--dry-run]" >&2
  exit 2
fi

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="$(command -v python3)"
fi

if command -v twine >/dev/null 2>&1; then
  TWINE=(twine)
else
  TWINE=("$PYTHON" -m twine)
fi

version="$("$PYTHON" - <<'PY'
from pathlib import Path
import re
text = Path("pyproject.toml").read_text(encoding="utf-8")
m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
if not m:
    raise SystemExit("version missing from pyproject.toml")
print(m.group(1))
PY
)"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "warning: working tree is dirty; artifacts will include uncommitted files" >&2
fi

"$PYTHON" - <<PY
import json
import sys
import urllib.error
import urllib.request

version = ${version@Q}
url = "https://pypi.org/pypi/tejtm/json"
try:
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.load(resp)
except urllib.error.HTTPError as exc:
    if exc.code == 404:
        sys.exit(0)
    raise
if version in data.get("releases", {}):
    print(
        f"error: tejtm=={version} is already on PyPI; "
        f"bump [project].version in pyproject.toml before uploading",
        file=sys.stderr,
    )
    sys.exit(1)
PY

"$PYTHON" -m pip install -q build
rm -rf dist build
"$PYTHON" -m build
"${TWINE[@]}" check dist/*

echo "built tejtm==${version}"
ls -1 dist/

if [[ "$dry_run" -eq 1 ]]; then
  echo "dry-run: skipped upload"
  exit 0
fi

"${TWINE[@]}" upload dist/*
echo "uploaded https://pypi.org/project/tejtm/${version}/"
