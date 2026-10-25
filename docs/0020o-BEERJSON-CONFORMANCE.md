# 0020o — BeerJSON Schema Conformance & Multi-Format

## Scope and evidence

This increment adds offline schema analysis and read-only format inspection, not
a complete exporter/importer or a lossless multi-application converter. Canonical
recipe, equipment and brew-plan models remain independent (ADR-0002).

The upstream `v.1.0` reference is a **branch**, not an immutable release tag.
We pin its schema bytes to commit
`a3c0c0cce5d44ee162b5939e04d0c9fc2eccf128`. All 19 JSON schemas and their MIT
license are vendored unchanged under `src/homebrew_as_code/schemas/beerjson_v1/`.
`manifest.json` records the source, commit and SHA-256 of every upstream file.
Runtime validation verifies these hashes after CRLF-to-LF normalization and resolves references locally;
unknown references fail closed. The original `$id` URLs are identifiers, not
permission to retrieve schemas from the network. Package data includes the bundle.

### Three independent questions

1. `schema_valid`: does the document satisfy the selected pinned schema?
2. `version_policy_match`: does its declared version match this adapter's explicit
   selection of numeric 1/1.0? This is HBAC policy, not an upstream constraint.
3. `application_compatibility`: was import/reexport actually tested in a target
   application? The inspector always returns `not_tested` and `import_ready: false`.

The pinned `measureable_units.json` defines `VersionType` as only
`{"type":"number"}`. It does **not** constrain the number to 1 or 1.0. Therefore
2.06 or 3 can pass schema validation. Never silently rewrite these values, or
infer an official 2.06 release or a proprietary dialect from the number alone.
Likewise schema validity does not establish recipe completeness: empty ingredient
arrays can be structurally valid. Units and semantics still require domain checks.

## Format/version matrix

| Format | Selected evidence | This increment |
| --- | --- | --- |
| BeerXML 1.0 | Published BeerXML specification; existing HBAC serializer | Existing exporter unchanged; inspector checks root/recipe versions only |
| BeerXML 2.01 | Revision 2.01-A, 2007-09-22; unfinished successor described by BeerJSON upstream | Detect wrapper as a candidate; no XSD validation or application support claim |
| BeerJSON `v.1.0` | Immutable commit above, JSON Schema Draft 7 | Full bundled schema validation; separate version policy |
| Brewfather BeerJSON declaring 2.06 | Private supplied export | Structurally passes pinned schema; version mapping unverified |
| Brewfather native JSON | Separate private export | Conservative structure heuristic only; no public schema selected |
| Legacy HBAC draft declaring 3 | Existing `beerjson_cli` | Still incomplete; not promoted to supported standard export |

The three supplied Brewfather exports were inspected locally on 2026-10-25:
BeerJSON passed this pinned schema with version-policy mismatch; native JSON and
BeerXML were identified without claiming schema validity. No original exports,
vendor IDs, ingredient inventories, or private reports are distributed here.
These observations are not a fresh UI import/reexport test. File digests in reports
identify the exact local bytes inspected, not semantic equivalence.

## Run on Windows / PowerShell

Install the new validator dependencies first:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q

.\.venv\Scripts\python.exe -m homebrew_as_code.interoperability `
  .local/brewfather.beerjson.json `
  .local/brewfather.recipe.json `
  .local/brewfather.xml `
  --schema-target beerjson-v1-a3c0c0c `
  --report .local/0020o-interoperability-report.json
```

Use the actual local export filenames. Inputs are ordered; `input_index` maps
report entries to that order. Reports omit filenames and document values from
schema diagnostics, but paths may contain user-defined keys: keep reports private.
Files are never overwritten. Duplicate JSON keys, non-finite JSON numbers and XML
DTD/entity declarations are rejected. No credentials, network writes, ingredient
scaling, unit inference or canonical YAML updates are involved.

Exit codes:

- `0`: every input passes the selected BeerJSON schema and HBAC version policy.
- `2`: report written, but at least one input is invalid, unreadable, unknown,
  only probed, or has an unverified version. Expected for the three-format run.
- `1`: command/report failure; argparse uses `2` for usage errors.

Schema diagnostics contain instance paths, schema paths and failed keywords.
`schema_valid: null` means no schema validation was performed; it is not a pass.

## Tests and next increment

Public tests are independently authored synthetic data. They cover nested units,
required fields, unknown properties, explicit mass units, version-policy separation,
no-network operation, malformed documents, format discrimination and CLI behavior.
The existing exporter/regression tests remain applicable. There is no mandatory
private fixture dependency in CI.

Next: implement a version-specific domain-to-standard mapping and independent
Brewfather compatibility rules, then compare semantic projections across the three
formats (mass, timing, process, volume meanings, efficiencies and losses). Do not
infer equivalence merely from schema validity or similar field names. Full import,
export, normalization, packaging mappings and schema 2.06 support are not shipped
in this increment.

## Primary sources

- Pinned schemas: <https://github.com/beerjson/beerjson/tree/a3c0c0cce5d44ee162b5939e04d0c9fc2eccf128/json>
- Upstream documentation: <https://beerjson.github.io/beerjson/> (may evolve independently of the pin)
- Upstream project: <https://github.com/beerjson/beerjson>
- BeerXML 1.0: <https://www.beerxml.com/beerxml.htm>
- BeerXML 2.01 document: <https://users.speakeasy.net/~antonw/beer_xml/BeerXML_v2_01.pdf>

## 0020o1 — Windows checkout integrity fix

The initial patch hashed raw worktree bytes. Existing Git attributes forced LF
for JSON but not for the extensionless vendored LICENSE. A Windows CRLF checkout
could therefore fail at LICENSE before any schema validation (14 test failures).

The schema directory now explicitly uses LF in Git. Validation also normalizes
CRLF to LF in memory, so already-applied patches work without deleting/rechecking
out files. Manifest hashes and upstream contents remain unchanged. No other
whitespace, BOM, JSON formatting or content changes are ignored. Tests exercise
LF, CRLF and mixed endings and reject actual LICENSE/schema modifications.

A damaged schema bundle now produces command exit code 1 with its integrity error,
instead of labeling the user's document unreadable and returning inspection code 2.
Apply 0020o1 on top of the already-applied 0020o patch, not instead of it.
