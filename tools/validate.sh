#!/usr/bin/env bash
# Catalogue validation entry point. Runs the metadata/Manifest/secret/materialization checks and,
# when an Engine build is supplied, Engine `inspect` on every materialized entry.
#
# Usage:
#   bash tools/validate.sh
#   bash tools/validate.sh --engine /path/to/mcpiler-engine
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Linux CI provides python3; some local shells (Git Bash on Windows) expose a python3 shim that
# resolves but does not run, so each candidate must prove it actually executes.
PYTHON=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" --version >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done
if [[ -z "$PYTHON" ]]; then
  echo "a working python3 (or python) is required" >&2
  exit 3
fi

engine=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --engine)
      engine="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

"$PYTHON" tools/validate.py

if [[ -n "$engine" ]]; then
  echo "running Engine inspect against materialized entries"
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT
  mkdir -p "$tmpdir/fs"
  for entry in entries/*/; do
    id="$(basename "$entry")"
    url="$("$PYTHON" - "$entry" <<'PY'
import json, sys
catalogue = json.load(open(sys.argv[1] + "catalogue.json", encoding="utf-8"))
for item in catalogue.get("materializeInputs", []):
    if item.get("target") == "policy.baseUrl":
        print(item.get("example", ""))
        break
PY
)"
    [[ -z "$url" ]] && continue
    out="$tmpdir/$id"
    "$PYTHON" tools/materialize/materialize.py --entry "$entry" --instance-url "$url" --out "$out" >/dev/null
    echo "inspect $id"
    # The entries require authorization, so inspect needs an issuer and a validation strategy;
    # these are placeholder values used only to let inspect complete its structural report.
    # MSYS_NO_PATHCONV stops Git Bash on Windows from rewriting '/<id>' and the mount directory;
    # cygpath converts the POSIX temp path to a Windows path when that shell is in use. Both are
    # no-ops on Linux CI.
    MSYS_NO_PATHCONV=1 dotnet "$engine" inspect \
      --mount "/$id=$(cygpath -w "$out" 2>/dev/null || printf '%s' "$out")" \
      --file-store-root "$(cygpath -w "$tmpdir/fs" 2>/dev/null || printf '%s' "$tmpdir/fs")" \
      --issuer https://issuer.example.org \
      --token-validation jwks
  done
fi

echo "validation complete"
