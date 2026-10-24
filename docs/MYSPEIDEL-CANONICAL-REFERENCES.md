# 0019z – Canonical Ingredient Reference Resolution (offline-first)

## Evidence

The MySpeidel PUT API rejects a modified shared `water_types` record. An empty
`references` object fails reference integrity (`mashing.adds.water.uuid`).
A valid schema alone **does not establish** permission to change shared records.

## Discover documented read endpoints

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_canonical_references `
  --spec .local/vendor/myspeidel-openapi.json `
  --report .local/0019z-endpoints.json
```

The inspector reads the local OpenAPI specification; it does not guess endpoints
or make any network requests. Review `documented_get_routes` to determine whether
a genuine read-only catalog API exists.

## Canonical reference export

If a documented GET endpoint yields canonical entries, export them **locally**
into a normalized JSON object keyed by *actual* category and UUID. This shape is
an input contract for our tool, **not** a claim about the API's native format:

```json
{
  "water_types": {"EXISTING_WATER_UUID": {"name": "Actual catalog name"}},
  "hops": {"EXISTING_HOP_UUID": {"name": "Actual catalog name"}}
}
```

Store this only in `.local/canonical-reference-export.json`. Do not invent names
or copy reference names from unrelated UUIDs. Verify catalog provenance.

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_canonical_references `
  --backup .local/weizenbier38-golden-backup.json `
  --catalog .local/canonical-reference-export.json `
  --report .local/0019z-reference-report.json `
  --candidate .local/0019z-candidate.json
```

The backup is never modified. Existing IDs and recipe additions are preserved;
only null reference names may be filled using matching canonical UUIDs. Missing
canonical records and conflicting existing fields are counted, never silently
invented or overwritten. The candidate is **not upload-ready**: even using the
original catalog name may trigger a shared-ingredient UPDATE on the server.
There is deliberately **no PUT** in this patch, including dry-run and apply.
Do not commit `.local/` files.
