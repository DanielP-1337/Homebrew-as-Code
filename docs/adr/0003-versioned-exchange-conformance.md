# ADR-0003: Separate exchange schemas, version policy and vendor compatibility

- **Status:** Accepted for schema-analysis phase
- **Date:** 2026-10-25
- **Extends:** ADR-0001 and ADR-0002

## Context

BeerJSON models detailed process and ingredient data beyond BeerXML 1.0. A private
Brewfather export declares 2.06 while the selected upstream branch is `v.1.0`.
Its VersionType permits any number, so passing schema validation cannot establish
version identity. Vendor JSON is another format and must not become the domain.

## Decision

- Keep recipe intent, equipment references, brew plans and future measured batches
  separate. No schema or vendor field is promoted into canonical YAML implicitly.
- Pin an official schema snapshot by commit and file hashes; vendor its unchanged
  schemas and license for deterministic offline validation.
- Report schema conformance, explicit adapter version policy and observed target
  compatibility separately. Unknown versions are not relabeled or normalized.
- The standard validator is independent of vendor format probes. Future vendor
  mappings belong behind an anti-corruption layer with their own semantic tests.
- Preserve the existing BeerXML 1.0 exporter. BeerXML 2.01 remains an unsupported
  draft reference; no compatibility promise follows from a higher version number.
- Keep original application exports and reports in ignored `.local/`; public tests
  use independently authored synthetic examples.

## Consequences

Adds jsonschema/referencing dependencies and a packaged schema bundle. Schema
updates require an explicit review, new pin/hashes, version-policy decision and
regression tests. Validation is not a recipe completeness, brew-day readiness,
losslessness or import compatibility certificate. Full import/export mapping and
cross-format semantic comparison remain follow-up work.
