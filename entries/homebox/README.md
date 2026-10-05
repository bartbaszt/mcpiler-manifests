# Homebox

A narrow MCP surface over [sysadminsmedia/homebox](https://github.com/sysadminsmedia/homebox)'s
REST API. The default `read-only` surface exposes instance info, currency, entity search and read,
entity types, tags, groups and the current user; the `full` surface additionally exposes entity
create, update and delete. Both require the `homebox.read` scope, and `full` also requires
`homebox.write`.

- **Upstream:** sysadminsmedia/homebox (AGPL-3.0)
- **Reviewed version:** 0.26.2
- **Trust:** `mcpiler-reviewed`
- **Manifest format:** 0.3

## Credential

Homebox issues a per-user API key, sent as an `Authorization: Bearer` header (normally prefixed
`hb_`).

1. In Homebox, open your user profile and create an API key.
2. Provide it to Engine through the environment variable the Manifest references. Never write the
   key into the Manifest.

```bash
export HOMEBOX_TOKEN="hb_<your-api-key>"
```

## Materialize

The Manifest ships with a non-routable example host. Set your own instance before serving:

```bash
python3 tools/materialize/materialize.py \
  --entry entries/homebox \
  --instance-url https://homebox.example.com/api \
  --out ./homebox-materialized
```

This rewrites only `policy.baseUrl` and `policy.allowedOrigins`. It does not touch operations,
credentials or any secret reference. The origin for `allowedOrigins` is derived from the instance
URL's scheme and host.

## Validate and serve

```bash
mcpiler-engine inspect ./homebox-materialized/manifest.json
mcpiler-engine serve  ./homebox-materialized/manifest.json
```

Engine is a standalone runtime: it needs only the Manifest, a compatible Engine build and the
locally supplied `HOMEBOX_TOKEN`. Studio is not involved.

## Notes

- `GET /v1/status` is a convenient preflight: it returns the running version and service status.
- Homebox groups scope entity visibility; `GET /v1/groups` and `GET /v1/users/self` help an agent
  orient before searching.
- Upstream Homebox is AGPL-3.0. This entry references it and does not redistribute its source or
  OpenAPI document.
