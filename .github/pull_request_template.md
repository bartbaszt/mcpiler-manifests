## Summary

<!-- One or two sentences: what entry or tooling change does this make? -->

## Type of change

- [ ] New catalogue entry
- [ ] Update to an existing entry (reviewed revision / operations)
- [ ] Tooling or schema change
- [ ] Documentation only

## Entry checklist (for entry changes)

- [ ] `entries/<id>/catalogue.json` validates against `schemas/catalogue-entry.schema.json`
- [ ] `entries/<id>/manifest.json` is an ordinary MCPiler Manifest (no MCPiler-specific extensions)
- [ ] Secrets use `fromEnv` or `fromFile` only; no `fromProvider`, no inline values
- [ ] Bounded instance URL materialization is declared in `materializeInputs` when the entry is parameterized
- [ ] `README.md` documents credential creation and `inspect`
- [ ] `bash tools/validate.sh` passes locally

## Trust state

- [ ] New entry is `community` (automation MUST NOT set `mcpiler-reviewed`)
- [ ] `mcpiler-reviewed` change: a maintainer review is recorded in `review.reviewedBy`/`reviewedAt` and `upstream.reviewedRevision`

## Provenance

- [ ] Upstream repository, reviewed version and reviewed revision are named
- [ ] No upstream specification/documentation text is copied unless a compatible treatment is recorded

## DCO

- [ ] Commits are signed off (`git commit -s`)
