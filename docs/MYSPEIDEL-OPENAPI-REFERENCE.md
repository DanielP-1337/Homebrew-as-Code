# MySpeidel OpenAPI reference inventory (0019a)

**Scope:** offline-only inspection of the public MySpeidel OpenAPI 3.x
specification, `recipe_v5` and the vendor-supplied recipe example.
This is **not** an API client, schema-conformant recipe encoder, validation
of brewing semantics, or authorization to upload a recipe.

## Authoritative vendor references

- [OpenAPI JSON](https://api.cloud.myspeidel.com/v1.0/api-spec/json)
- [Browsable specification](https://api.cloud.myspeidel.com/v1.0/api-spec/json-view)
- [Swagger UI](https://api.cloud.myspeidel.com/v1.0/api-docs/)

The spec identifies license `UNLICENSED`; **do not commit downloaded vendor
specification, sample recipe or private recipe data** without permission.
Keep vendor files and generated reports under `.local/` (git-ignored).

## Download from your Windows development machine

```powershell
Set-Location 'C:\dev\Homebrew-as-Code'
New-Item -ItemType Directory -Force '.local\vendor' | Out-Null
Invoke-WebRequest 'https://api.cloud.myspeidel.com/v1.0/api-spec/json' `
    -OutFile '.local\vendor\myspeidel-openapi.json'

.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_openapi_reference_cli `
    recipes/lebkuchen-zauber/recipe.yaml `
    --spec .local/vendor/myspeidel-openapi.json `
    --output .local/myspeidel-openapi-reference-report.json
```

Review required fields and source-domain candidates:

```powershell
$r = Get-Content '.local/myspeidel-openapi-reference-report.json' -Raw | ConvertFrom-Json
$r.api_required_fields
$r.fields | Format-Table api_field,required,domain_candidate,source_present,mapping_verified,status
```

The report contains **field names and schema metadata only**; it does not
export the vendor example content. It records a SHA-256 fingerprint for
reproducibility. The download command is the only network operation shown;
the Python inspection tool itself does not use the network.

`mapping_verified` is always `false`: detecting a name such as `boil` or
`mashing` does **not** establish matching time semantics, units, references,
required sub-objects or serialization. Some source fields can be candidates,
but none are automatically accepted as ready for upload.

### Gate before any POST dry run

1. Record/specify exact required types, nested fields and unit semantics.
2. Confirm ingredient identifiers and reference handling from official examples
   and controlled read-only GET observations; do not invent UUIDs.
3. Implement real payload validation against the applicable `recipe_v5` schema.
4. Review request semantics, especially the documented `dryRun` parameter.
5. Only then implement a separate explicitly opt-in network write test.

Do not confuse a MySpeidel dry run with a verified no-side-effect guarantee;
confirm behavior before sending private recipes. No recipe POST/PUT is
performed by this patch. No direct machine control is ever in scope.
