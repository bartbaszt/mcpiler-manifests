#!/usr/bin/env python3
"""Deterministic tests for the bounded instance materializer.

Run: python3 tests/test_materialize.py
No third-party dependencies; exits non-zero on the first failure.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "materialize"))

import materialize as m  # noqa: E402


def expect_refusal(instance_url: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        entry = REPO_ROOT / "entries" / "trilium"
        try:
            m.materialize(entry, instance_url, Path(tmp) / "out")
        except m.MaterializeError:
            return
        raise AssertionError(f"expected refusal for {instance_url!r}")


def main() -> int:
    entry = REPO_ROOT / "entries" / "trilium"

    # 1. Deterministic output for the same input.
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        out_a = m.materialize(entry, "https://a.example.org/etapi", Path(a))
        out_b = m.materialize(entry, "https://a.example.org/etapi", Path(b))
        assert out_a.read_bytes() == out_b.read_bytes(), "materialization is not deterministic"

    # 2. baseUrl keeps its path; allowedOrigins is the exact origin.
    with tempfile.TemporaryDirectory() as tmp:
        out = m.materialize(entry, "https://notes.example.org/etapi", Path(tmp))
        manifest = json.loads(out.read_text(encoding="utf-8"))
        policy = manifest["sections"]["policy"]["inline"]
        assert policy["baseUrl"] == "https://notes.example.org/etapi", policy["baseUrl"]
        assert policy["allowedOrigins"] == ["https://notes.example.org"], policy["allowedOrigins"]

    # 3. A default port is dropped from the origin; a non-default port is kept.
    with tempfile.TemporaryDirectory() as tmp:
        out = m.materialize(entry, "https://notes.example.org:443/etapi", Path(tmp))
        policy = json.loads(out.read_text(encoding="utf-8"))["sections"]["policy"]["inline"]
        assert policy["allowedOrigins"] == ["https://notes.example.org"], policy["allowedOrigins"]
    with tempfile.TemporaryDirectory() as tmp:
        out = m.materialize(entry, "https://notes.example.org:8443/etapi", Path(tmp))
        policy = json.loads(out.read_text(encoding="utf-8"))["sections"]["policy"]["inline"]
        assert policy["allowedOrigins"] == ["https://notes.example.org:8443"], policy["allowedOrigins"]

    # 4. Trailing slash normalisation.
    with tempfile.TemporaryDirectory() as tmp:
        out = m.materialize(entry, "https://notes.example.org/etapi/", Path(tmp))
        policy = json.loads(out.read_text(encoding="utf-8"))["sections"]["policy"]["inline"]
        assert policy["baseUrl"] == "https://notes.example.org/etapi", policy["baseUrl"]

    # 5. Secret reference channels survive unchanged.
    with tempfile.TemporaryDirectory() as tmp:
        out = m.materialize(entry, "https://notes.example.org/etapi", Path(tmp))
        manifest = json.loads(out.read_text(encoding="utf-8"))
        creds = manifest["sections"]["credentials"]["inline"]["credentials"]
        assert creds[0]["value"] == {"fromEnv": "TRILIUM_ETAPI_TOKEN"}, creds

    # 6. Refusals: relative, non-http scheme, credential-bearing, query/fragment.
    for bad in (
        "notes.example.org/etapi",
        "ftp://notes.example.org",
        "https://user:pass@notes.example.org/etapi",
        "https://notes.example.org/etapi?a=1",
        "https://notes.example.org/etapi#frag",
        "",
    ):
        expect_refusal(bad)

    print("materializer tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
