# Trilium Notes ETAPI

A narrow MCP surface over [TriliumNext/Trilium](https://github.com/TriliumNext/Trilium)'s ETAPI.
The default `read-only` surface exposes search, note metadata and note content; the `full`
surface additionally exposes note creation and deletion. Both require the `trilium.read` scope, and
`full` also requires `trilium.write`.

- **Upstream:** TriliumNext/Trilium (AGPL-3.0)
- **Reviewed version:** 0.105.0
- **Trust:** `mcpiler-reviewed`
- **Manifest format:** 0.3

## Credential

Trilium exposes a per-user ETAPI token, sent as an `Authorization: Bearer` header.

1. In Trilium, open **Options → ETAPI** and create a token.
2. Provide it to Engine through the environment variable the Manifest references. Never write the
   token into the Manifest.

```bash
export TRILIUM_ETAPI_TOKEN="<your-etapi-token>"
```

## Materialize

The Manifest ships with a non-routable example host. Set your own instance before serving:

```bash
python3 tools/materialize/materialize.py \
  --entry entries/trilium \
  --instance-url https://trilium.example.com/etapi \
  --out ./trilium-materialized
```

This rewrites only `policy.baseUrl` and `policy.allowedOrigins`. It does not touch operations,
credentials or any secret reference. The origin for `allowedOrigins` is derived from the instance
URL's scheme and host.

## Validate and serve

```bash
mcpiler-engine inspect ./trilium-materialized/manifest.json
mcpiler-engine serve  ./trilium-materialized/manifest.json
```

Engine is a standalone runtime: it needs only the Manifest, a compatible Engine build and the
locally supplied `TRILIUM_ETAPI_TOKEN`. Studio is not involved.

## Network topology

Trilium ETAPI must be reachable from the Engine process at the materialized `baseUrl`, and its
origin must appear in `policy.allowedOrigins`. A typical deployment runs Engine next to a
self-hosted Trilium over a private network.

## Notes

- Only the reviewed ETAPI subset is exposed: `GET /notes`, `GET /notes/{noteId}`,
  `GET /notes/{noteId}/content`, `POST /create-note`, `DELETE /notes/{noteId}`.
- Upstream Trilium is AGPL-3.0. This entry references it and does not redistribute its source or
  OpenAPI document.
