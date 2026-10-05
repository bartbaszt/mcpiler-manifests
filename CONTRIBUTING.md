# Contributing to the MCPiler Manifest catalogue

Thank you for your interest. This document explains the licensing terms your contribution
is made under and the rules for entries.

## Licence and sign-off

This catalogue is licensed under the Apache License, Version 2.0. Contributions are
accepted under the same licence, as provided by section 5 of that licence. There is no
Contributor License Agreement.

Every commit MUST carry a Developer Certificate of Origin sign-off:

```bash
git commit -s -m "your message"
```

This appends a line of the form:

```text
Signed-off-by: Your Name <your.email@example.com>
```

The name and address must be real and must match your commit author identity. CI rejects
pull requests containing commits without a valid sign-off.

### Developer Certificate of Origin 1.1

```text
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.


Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

## What this repository is

An ordinary versioned MCPiler Manifest plus separate discovery/governance metadata. Nothing
here is required for Engine execution correctness: Engine loads the Manifest through its normal
loader and knows nothing about catalogue metadata.

## Scope rules

Please do not propose changes that:

- add catalogue-specific behaviour to Engine (a runtime template language, catalogue lookup,
  a generic base-URL override, or source-contract parsing);
- require `fromProvider` (a Studio/Platform-only reference) in a standalone entry;
- embed a plaintext secret value or a private Platform fixture/URL in a published entry;
- copy an upstream OpenAPI/Swagger document or large description text into this Apache-2.0
  repository unless its redistribution treatment is deliberately established and recorded.

Those concerns belong to the upstream project (for contracts) or to MCPiler Studio (for
authoring sources). Keep the public catalogue runtime-facing.

## Entry rules

Each entry lives under `entries/<id>/` and contains:

- `catalogue.json` — discovery/governance metadata, validated against `schemas/catalogue-entry.schema.json`, including bounded instance-URL inputs under `materializeInputs`;
- `manifest.json` — an ordinary MCPiler Manifest (or a template with bounded declared inputs);
- `README.md` — original, concise documentation: how to create the upstream credential, how to
  run `inspect`, and any instance-specific steps.

Every entry MUST:

- reference credentials only through local Engine references (`fromEnv`, `fromFile`);
- identify the upstream repository and the exact reviewed version/revision;
- record a trust state: `mcpiler-reviewed` or `community`;
- declare the Manifest format compatibility range it targets;
- pass `tools/materialize` (when parameterized) and Engine `inspect`.

## Trust states

`mcpiler-reviewed` means an MCPiler maintainer performed an explicit compatibility review
against the named upstream revision. It is **never** granted by automation. A contribution that
passes every automated check is eligible for review but remains `community` until a maintainer
updates the trust state. Changing an entry's reviewed upstream version without a fresh
compatibility review MUST NOT retain `mcpiler-reviewed`.

## Quality gates

```bash
# metadata + Manifest + secret scan + materialization + inspect
bash tools/validate.sh

# DCO is enforced in CI on the pull-request range
```

Warnings are errors in the tooling. A behavior change to an entry (Manifest fields, base
URL/origins, credentials) requires the deterministic CI checks to pass for the materialized
output, not only the template.

## Reporting security issues

Follow [`SECURITY.md`](SECURITY.md). Do not open a public issue, discussion or pull request for
a suspected vulnerability before private triage.
