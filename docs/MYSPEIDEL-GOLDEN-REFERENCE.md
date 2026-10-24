# MySpeidel Golden Reference – offline baseline

The official MySpeidel OpenAPI specification is the **vendor reference design**;
our YAML remains the independent recipe source of truth (ADR-0001).

Run from the repository root, using a previously downloaded vendor OpenAPI JSON
stored outside Git:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_golden_reference_cli `
    --spec .local/vendor/myspeidel-openapi.json `
    --output .local/myspeidel-golden-reference-report.json
```

The report contains only a SHA-256 of the specification, schema-field names,
structural **types**, counts and documented operation references. **It does
not copy the manufacturer's sample values**, identifiers or proprietary recipe
into source control. Do not publish your private recipe or specification file.

## Test phases

1. **Offline inspection (this patch)**: inspect the manufacturer example,
   identify missing required fields, and compare POST versus GET schema refs.
2. **Independent validation (future)**: validate a *locally adapted* test
   fixture with a standards-conformant JSON Schema/OpenAPI validator. Verify
   semantics (units, ingredient UUID provenance, recipe ownership).
3. **Dry-run (separate, opt-in future patch)**: only after documenting exact
   `dryRun` parameter values and verifying expected server behavior. A dry-run
   may still make an HTTP request; do not assume zero side effects.
4. **Create new private recipe (separate authorization)**: explicitly approved
   POST, never PUT against an existing recipe, and no machine start.
5. **GET + PDF comparison**: compare stored values and user-exported PDF.

The upstream sample is **not upload-ready**, even if it passes a limited shape
check: it may include unrelated owners, UUIDs and timestamps. Never POST the
manufacturer example verbatim. The tool has no HTTP, authentication or API
writer and cannot submit an order or recipe.
