#!/usr/bin/env python3
"""Bounded MCPiler Manifest instance materializer.

This tool applies exactly one class of change to an entry's ordinary Manifest: it rewrites the
declared instance URL into ``policy.baseUrl`` and derives the exact allowed origin for
``policy.allowedOrigins``. Nothing else is touched, and the set of writable members is a closed
allow-list encoded here rather than a template language.

It is deliberately NOT a general templating engine:

* the only input kind is ``instance-url`` (an absolute ``http(s)`` URL);
* the only writable targets are ``policy.baseUrl`` and ``policy.allowedOrigins``;
* only those members are read from the entry's ``catalogue.json`` ``materializeInputs``;
* secret references (``fromEnv``/``fromFile``) are never read, resolved or written;
* ``fromProvider`` is rejected outright, matching the catalogue contract.

The output is a new directory containing the materialized ``manifest.json``. The entry is never
modified in place.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit

# The closed set of Manifest members the materializer may rewrite. Anything outside this set is a
# programming error, not a user error.
_WRITABLE_TARGETS = {"policy.baseUrl", "policy.allowedOrigins"}

# Secret value channels that must never appear in a catalogue Manifest.
_FORBIDDEN_SECRET_CHANNELS = {"fromProvider"}


class MaterializeError(Exception):
    """A refusal that is safe to show the user verbatim."""


def _parse_instance_url(raw: str) -> tuple[str, str]:
    """Return (base_url, origin) for an absolute http(s) instance URL.

    The base URL keeps its path (for example ``/etapi`` or ``/api``); the origin is scheme + host
    (+ non-default port) with no path, which is exactly what ``policy.allowedOrigins`` admits.
    """
    if not isinstance(raw, str) or not raw.strip():
        raise MaterializeError("instance URL must be a non-empty string")

    url = raw.strip()
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise MaterializeError("instance URL must be an absolute http(s) URL")
    if not parts.netloc:
        raise MaterializeError("instance URL must include a host")
    if parts.username or parts.password:
        raise MaterializeError("instance URL must not carry credentials")
    if parts.query or parts.fragment:
        raise MaterializeError("instance URL must not carry a query or fragment")

    base_url = url.rstrip("/")

    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    origin = f"{scheme}://{host}" if port is None or default_port else f"{scheme}://{host}:{port}"
    return base_url, origin


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise MaterializeError(f"missing file: {path}") from error
    except json.JSONDecodeError as error:
        raise MaterializeError(f"invalid JSON in {path}: {error}") from error


def _reject_forbidden_secret_channels(node: object, path: str = "manifest") -> None:
    """Fail closed if a Manifest declares a provider-resolved secret.

    The catalogue contract admits only ``fromEnv`` and ``fromFile``. This is checked structurally so
    the refusal does not depend on a key ordering or textual layout.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            if key in _FORBIDDEN_SECRET_CHANNELS:
                raise MaterializeError(
                    f"secret reference '{key}' is not permitted in the catalogue (found at {path}.{key})"
                )
            _reject_forbidden_secret_channels(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _reject_forbidden_secret_channels(item, f"{path}[{index}]")


def _read_materialize_inputs(catalogue: dict) -> dict[str, str]:
    """Return the entry's declared instance-URL inputs keyed by their declared target."""
    inputs: dict[str, str] = {}
    for entry in catalogue.get("materializeInputs", []) or []:
        if not isinstance(entry, dict):
            raise MaterializeError("materializeInputs entries must be objects")
        kind = entry.get("kind")
        target = entry.get("target")
        if kind != "instance-url":
            raise MaterializeError(f"unsupported materialize input kind: {kind!r}")
        if target not in _WRITABLE_TARGETS:
            raise MaterializeError(f"materialize target is outside the allow-list: {target!r}")
        inputs[target] = entry.get("name", target)
    return inputs


def materialize(entry_dir: Path, instance_url: str, out_dir: Path) -> Path:
    """Materialize ``entry_dir`` with ``instance_url`` into ``out_dir``; return the Manifest path."""
    catalogue_path = entry_dir / "catalogue.json"
    manifest_path = entry_dir / "manifest.json"
    catalogue = _load_json(catalogue_path)
    manifest = _load_json(manifest_path)

    declared_targets = _read_materialize_inputs(catalogue)
    if not declared_targets:
        raise MaterializeError(f"entry '{entry_dir.name}' declares no materializeInputs")

    _reject_forbidden_secret_channels(manifest)

    base_url, origin = _parse_instance_url(instance_url)

    policy = manifest.get("sections", {}).get("policy", {}).get("inline")
    if not isinstance(policy, dict):
        raise MaterializeError("manifest has no inline policy section to materialize")

    for target in declared_targets:
        if target == "policy.baseUrl":
            policy["baseUrl"] = base_url
        elif target == "policy.allowedOrigins":
            # Allowed origins are DERIVED from the instance URL, never merged with the template's
            # placeholder host. The allow-list must name exactly the instance an operator selected;
            # carrying a non-routable example host forward would be a stale, widened SSRF allow-list.
            policy["allowedOrigins"] = [origin]

    out_dir.mkdir(parents=True, exist_ok=True)
    out_manifest = out_dir / "manifest.json"
    out_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # The README travels with the materialized output so the operator keeps the setup notes.
    readme = entry_dir / "README.md"
    if readme.exists():
        shutil.copy2(readme, out_dir / "README.md")

    return out_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize a bounded instance URL into a catalogue entry Manifest.")
    parser.add_argument("--entry", required=True, type=Path, help="Entry directory (contains catalogue.json and manifest.json).")
    parser.add_argument("--instance-url", required=True, help="Absolute http(s) URL of the target instance.")
    parser.add_argument("--out", required=True, type=Path, help="Output directory for the materialized Manifest.")
    args = parser.parse_args(argv)

    try:
        manifest_path = materialize(args.entry, args.instance_url, args.out)
    except MaterializeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(f"materialized: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
