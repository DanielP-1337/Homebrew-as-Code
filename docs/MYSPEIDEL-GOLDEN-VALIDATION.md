# Golden reference: conservative offline validation (0019h)

Use the previously downloaded manufacturer OpenAPI file under `.local/vendor`.
The command creates a **private** derived manufacturer sample (contains potentially
foreign UUIDs/owner information), plus a sanitized structural report:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_golden_validation_cli `
    --spec .local/vendor/myspeidel-openapi.json `
    --candidate .local/myspeidel-golden-candidate.json `
    --report .local/myspeidel-golden-validation.json
```

Exit status **0** means all encountered *supported* constraints passed and no
unverified constraints were found; **2** means issues or unsupported constraints;
**1** means setup/input/output failure. A successful offline check **does not**
mean the manufacturer server will accept a POST. Existing output files are not
overwritten. The candidate is explicitly never upload-ready.

Three missing sample fields use values observed from one private GET test:
`public=0`, `recipe_type=0`, `water_plato=12`. These values are NOT general API
defaults. There is **no correction** of foreign owner/UUID/timestamps or nested
ingredient references. Do not use the candidate for network requests.

The conservative, dependency-free checker validates referenced types, nested
required fields, primitive ranges, enums, object/array constraints and core
compositions. It reports unknown keywords, unsupported formats and certain
context-dependent constraints as **unverified**, never as a clean success.
This is **not** a complete standards-conformant OpenAPI 3.0 validator, nor
semantic validation of units, identities, or machine behavior. The offline
report omits all example values, identifiers, and input data.

Inspect safely:

```powershell
$R = Get-Content '.local/myspeidel-golden-validation.json' -Raw | ConvertFrom-Json
$R | Select-Object schema_check_passed, upload_ready
$R.schema_errors | Format-Table path,code
$R.unverified_constraints | Format-Table path,code
```

Never commit files from `.local`. No HTTP clients, credentials, POST, PUT or
physical machine control are imported or used by this feature.
