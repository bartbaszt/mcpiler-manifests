# Changelog

All notable changes to the MCPiler Manifest catalogue are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this repository uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) for the catalogue layout and tooling.

Entries are versioned by their own reviewed upstream revision inside `catalogue.json`, not by the
repository version.

## [Unreleased]

### Added

- Repository scaffold: Apache-2.0 license, DCO contribution policy, security and trademark policy.
- `schemas/catalogue-entry.schema.json` defining catalogue discovery/governance metadata.
- `entries/trilium/` — MCPiler-reviewed Trilium Notes ETAPI Manifest (upstream 0.105.0).
- `entries/homebox/` — MCPiler-reviewed Homebox inventory Manifest (upstream 0.26.2).
- `tools/materialize/` — bounded, deterministic instance-URL materializer for parameterized entries.
- `.github/workflows/catalogue.yml` — public CI: metadata, Manifest and secret validation,
  deterministic materialization and pinned Engine `inspect`.
