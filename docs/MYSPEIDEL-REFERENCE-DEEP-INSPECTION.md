# MySpeidel recipe_v5 reference deep inspection (0019c)

This is an **offline, diagnostic-only** inspection of a locally downloaded official
MySpeidel OpenAPI document. No server calls, recipe creation, dry runs, or writes.
The copyrighted/unlicensed vendor specification and its example are **never
redistributed**, and the generated report contains only structural metadata.

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_reference_deep_cli `
    recipes/lebkuchen-zauber/recipe.yaml `
    --spec .local/vendor/myspeidel-openapi.json `
    --output .local/myspeidel-reference-deep.json
```

Inspect key outputs:

```powershell
$r = Get-Content .local/myspeidel-reference-deep.json -Raw | ConvertFrom-Json
$r.example_missing_required
$r.fields | Format-Table field, required, in_example, classification -AutoSize
$r.nested_schema.boil | Format-Table path, types, required_in_parent, example_present -AutoSize
$r.post_schema_references
$r.get_schema_references
$r.blockers
```

* Classifications are **investigation categories**, not verified field mappings.
* `example_present` is a structural observation, not evidence a value is valid.
* `post_get_share_recipe_v5` only confirms schema references; it **does not**
  establish POST behavior for UUIDs, timestamps, owner, or other server fields.
* The inspector follows properties and array items (up to depth 9), and flags
  composition rules (`allOf`, `oneOf`, `anyOf`) that need a standards-compliant
  validator. It does not check all numeric limits, units, or nested semantics.
* All candidate payloads stay blocked. See ADR-0001 for architecture boundaries.
* Keep downloaded vendor specs, raw API responses, report files, and credentials
  under `.local/` (never commit them).
