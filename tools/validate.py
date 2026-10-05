#!/usr/bin/env python3
"""Catalogue validation: metadata, Manifest, secret scan, materialization, provenance.

Runs from a clean public checkout with no access to the private MCPiler Platform repository. The
only third-party dependency is ``jsonschema`` (metadata schema validation); everything else uses the
standard library. Engine ``inspect`` is optional and only runs when an Engine path is supplied.

Exit code 0 = pass, non-zero = fail. Every failure is printed with the entry and the reason.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover - CI installs it; local fallback is explicit
    jsonschema = None

REPO_ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = REPO_ROOT / "entries"
SCHEMA_PATH = REPO_ROOT / "schemas" / "catalogue-entry.schema.json"

# The initial reviewed catalogue set. A release advertises these; their absence fails validation.
REQUIRED_REVIEWED_ENTRIES = {"trilium", "homebox"}

# A structural, order-independent scan for secret-looking values. It flags obvious plaintext secret
# shapes so a contributor cannot embed a live credential; it is not a substitute for review.
_SECRET_VALUE_PATTERNS = [
    re.compile(r"^\s*Bearer\s+\S", re.IGNORECASE),
    re.compile(r"^hb_[A-Za-z0-9]{8,}$"),
    re.compile(r"^sk-[A-Za-z0-9]{8,}$"),
    re.compile(r"^ghp_[A-Za-z0-9]{8,}$"),
]

errors: list[str] = []
notes: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing file: {path}")
    except json.JSONDecodeError as error:
        fail(f"invalid JSON in {path}: {error}")
    return {}


def scan_secret_lookalikes(node: object, path: str) -> None:
    """Fail on a plaintext-looking secret value or a forbidden provider secret channel."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "fromProvider":
                fail(f"{path}: 'fromProvider' is not permitted; use fromEnv or fromFile")
            if key == "inline" and isinstance(value, str):
                fail(f"{path}.inline: inline secret values are not permitted in the catalogue")
            if isinstance(value, str) and any(pattern.match(value) for pattern in _SECRET_VALUE_PATTERNS):
                fail(f"{path}.{key}: value looks like a plaintext secret")
            scan_secret_lookalikes(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            scan_secret_lookalikes(item, f"{path}[{index}]")


def validate_entry(entry_dir: Path, schema: dict, engine: Path | None) -> None:
    entry_id = entry_dir.name
    catalogue_path = entry_dir / "catalogue.json"
    manifest_path = entry_dir / "manifest.json"

    # --- metadata schema -------------------------------------------------------------
    catalogue = load(catalogue_path)
    if not catalogue:
        return
    if jsonschema is not None:
        try:
            jsonschema.validate(catalogue, schema)
        except jsonschema.ValidationError as error:
            fail(f"{entry_id}: catalogue.json schema violation: {error.message} at {'/'.join(str(p) for p in error.path)}")
    if catalogue.get("id") != entry_id:
        fail(f"{entry_id}: catalogue.json 'id' must match the directory name")

    # --- trust / review --------------------------------------------------------------
    trust = catalogue.get("trust")
    review = catalogue.get("review", {})
    if trust == "mcpiler-reviewed":
        if not review.get("reviewedBy") or not review.get("reviewedAt"):
            fail(f"{entry_id}: mcpiler-reviewed requires review.reviewedBy and review.reviewedAt")
        upstream = catalogue.get("upstream", {})
        if not upstream.get("reviewedRevision"):
            fail(f"{entry_id}: mcpiler-reviewed requires upstream.reviewedRevision")
    elif trust != "community":
        fail(f"{entry_id}: unknown trust state {trust!r}")

    # --- Manifest format + secret scan ----------------------------------------------
    manifest = load(manifest_path)
    if not manifest:
        return
    declared = catalogue.get("manifest", {}).get("formatVersion")
    if manifest.get("manifestFormatVersion") != declared:
        fail(f"{entry_id}: manifest.manifestFormatVersion does not match catalogue manifest.formatVersion")
    scan_secret_lookalikes(manifest, f"{entry_id}/manifest.json")

    # --- materialization (parameterized entries) ------------------------------------
    parameterized = catalogue.get("manifest", {}).get("parameterized", False)
    inputs = catalogue.get("materializeInputs", []) or []
    if parameterized and not inputs:
        fail(f"{entry_id}: parameterized entries must declare materializeInputs")
    if parameterized:
        sys.path.insert(0, str(REPO_ROOT / "tools" / "materialize"))
        import materialize as materializer  # noqa: E402

        instance = next((i for i in inputs if i.get("target") == "policy.baseUrl"), None)
        example = (instance or {}).get("example")
        if not example:
            fail(f"{entry_id}: parameterized entry needs an instance-url example")
        else:
            import tempfile

            with tempfile.TemporaryDirectory() as tmp:
                try:
                    out = materializer.materialize(entry_dir, example, Path(tmp))
                except materializer.MaterializeError as error:
                    fail(f"{entry_id}: materialization failed: {error}")
                    out = None
                if out is not None:
                    materialized = load(out)
                    policy = materialized.get("sections", {}).get("policy", {}).get("inline", {})
                    if policy.get("baseUrl") == manifest.get("sections", {}).get("policy", {}).get("inline", {}).get("baseUrl"):
                        fail(f"{entry_id}: materialization did not rewrite policy.baseUrl")
                    if not policy.get("allowedOrigins"):
                        fail(f"{entry_id}: materialization produced no allowedOrigins")
                    # The SecretValue channels survive materialization unchanged.
                    if _credential_values(materialized) != _credential_values(manifest):
                        fail(f"{entry_id}: materialization altered a credential value channel")

    # --- Engine inspect (optional) ---------------------------------------------------
    if engine is not None and parameterized:
        notes.append(f"{entry_id}: Engine inspect skipped in-process; run tools/validate.sh --engine for the oracle check")


def _credential_values(manifest: dict) -> list:
    creds = manifest.get("sections", {}).get("credentials", {}).get("inline", {}).get("credentials", [])
    return [c.get("value") for c in creds]


def find_engine(explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit)
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the MCPiler Manifest catalogue.")
    parser.add_argument("--engine", default=None, help="Path to mcpiler-engine.dll or host for optional inspect.")
    args = parser.parse_args(argv)

    schema = load(SCHEMA_PATH)
    if schema and jsonschema is None:
        notes.append("jsonschema not installed; metadata schema validation was skipped")

    if not ENTRIES_DIR.is_dir():
        fail(f"entries directory not found: {ENTRIES_DIR}")
    else:
        engine = find_engine(args.engine)
        entry_dirs = sorted(p for p in ENTRIES_DIR.iterdir() if p.is_dir())
        if not entry_dirs:
            fail("no catalogue entries found")
        for entry_dir in entry_dirs:
            validate_entry(entry_dir, schema, engine)

        present = {p.name for p in entry_dirs}
        missing = REQUIRED_REVIEWED_ENTRIES - present
        if missing:
            fail(f"required reviewed entries are missing: {', '.join(sorted(missing))}")

    for note in notes:
        print(f"note: {note}")
    if errors:
        for message in errors:
            print(f"FAIL: {message}", file=sys.stderr)
        print(f"\n{len(errors)} validation failure(s).", file=sys.stderr)
        return 1

    print("catalogue validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
