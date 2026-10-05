<p align="center">
  <strong>MCPiler Manifest catalogue</strong><br />
  Reviewed and community MCPiler Engine Manifests you can run without Studio.
</p>

# MCPiler Manifest catalogue

`bartbaszt/mcpiler-manifests` is the canonical public repository of reusable **MCPiler Engine**
Manifest examples and community contributions. An entry is an ordinary, versioned MCPiler
Manifest plus separate discovery/governance metadata. Nothing here is required for Engine
execution correctness: a compatible Engine loads the Manifest through its normal loader and does
not know the catalogue exists.

```text
catalogue entry ──► materialize (instance URL) ──► ordinary Manifest ──► MCPiler Engine serve
       │                                              │
       │ catalogue.json (provenance/trust)            │ fromEnv / fromFile secrets stay local
       └── not a runtime input to Engine ─────────────┘
```

The catalogue is usable **without Studio** and without any MCPiler-hosted registry or service.
You clone an entry, materialize it with your instance URL, supply local secrets, and run Engine.

## Layout

```text
entries/<id>/
  manifest.json      ordinary MCPiler Manifest (or a bounded template with non-routable example hosts)
  catalogue.json     discovery/governance metadata, incl. bounded materialization inputs
  README.md          original docs: credential setup, inspect, instance steps
schemas/
  catalogue-entry.schema.json
tools/
  materialize/       bounded, deterministic instance-URL materializer
  validate.py        metadata + Manifest + secret-scan validation
  validate.sh        local/CI entry point
.github/workflows/
  catalogue.yml      public CI
```

## Entries

| Entry | Upstream | Reviewed version | Trust | Materialized |
| --- | --- | --- | --- | --- |
| [Trilium Notes ETAPI](entries/trilium/README.md) | [TriliumNext/Trilium](https://github.com/TriliumNext/Trilium) (AGPL-3.0) | 0.105.0 | `mcpiler-reviewed` | instance URL |
| [Homebox](entries/homebox/README.md) | [sysadminsmedia/homebox](https://github.com/sysadminsmedia/homebox) (AGPL-3.0) | 0.26.2 | `mcpiler-reviewed` | instance URL |

Trust states:

- `mcpiler-reviewed` — an MCPiler maintainer performed an explicit compatibility review against
  the named upstream revision. Automation never grants it.
- `community` — contributed and structurally valid, but not MCPiler-reviewed.

## Using an entry

1. Read the entry's `README.md` (credential setup and instance-specific steps).
2. If the entry is parameterized, materialize it:

   ```bash
   python3 tools/materialize/materialize.py \
     --entry entries/trilium \
     --instance-url https://trilium.example.com \
     --out ./trilium-materialized
   ```

3. Supply the declared secret through your environment or files (never in the Manifest).
4. Validate with Engine `inspect` before serving (see the entry README).

## Validation

```bash
bash tools/validate.sh                 # metadata + Manifest + secret scan + materialization
bash tools/validate.sh --engine <path-to-mcpiler-engine>   # also run Engine inspect
```

CI runs the same checks from a clean checkout with no access to the private MCPiler Platform
repository. Engine `inspect` is the schema/format oracle; the catalogue does not copy upstream or
Engine schemas.

## Licensing and provenance

Repository-owned code, metadata and original documentation are Apache-2.0 with a DCO sign-off
(see [`CONTRIBUTING.md`](CONTRIBUTING.md)). Upstream projects are referenced with their exact
reviewed revision and license; upstream OpenAPI/Swagger documents and large description text are
**not** copied here. See [`NOTICE`](NOTICE), [`TRADEMARKS.md`](TRADEMARKS.md) and each entry's
`catalogue.json`.

## Related

- [MCPiler Engine](https://github.com/bartbaszt/mcpiler-engine) — the open-source, Manifest-driven
  MCP runtime that loads these Manifests.
- MCPiler Studio — the commercial authoring product; not required to use this catalogue.
