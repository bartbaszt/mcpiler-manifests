# Security Policy

The MCPiler Manifest catalogue is a collection of example and community Manifests that a
standalone MCPiler Engine may load. Manifests are runtime contracts, so a catalogue contribution
can influence what an Engine deployment exposes and which upstream credentials it uses. Security
reports are handled privately.

## Supported versions

Security fixes target the latest state of the `main` branch.

Manifest format support is pinned by each entry's `manifestFormatVersion` and by the Engine
release the catalogue CI uses for `inspect`. A security fix to a Manifest does not imply a Manifest
format change, and a Manifest format change requires a compatibility review for the affected
entries.

## Reporting a vulnerability

Do not open a public issue for a security report. Email the maintainer privately at
`security@bbasztura.eu`, ideally with:

- the affected file and entry;
- the Manifest field or tooling input involved;
- a minimal reproduction (a Manifest snippet plus the materialize/inspect command);
- the impact you believe it has.

Please allow time for a fix and a coordinated disclosure before publishing details.

## In scope

- a catalogue entry whose Manifest, when materialized and loaded, causes Engine to contact a host
  or credential the entry does not declare;
- plaintext secret material or private Platform fixtures entering a published entry;
- a materializer input that widens a Manifest's base URL/allowed origins beyond its declared,
  bounded instance input, or that accepts a secret value for embedding;
- a CI check that can be bypassed to publish an entry that misrepresents its trust state.

## Out of scope

- vulnerabilities in the upstream projects the entries reference (report those upstream);
- an explicit `inline` secret that a user chooses to add locally to their own copy;
- the security of a user's own instance URL or network topology.
