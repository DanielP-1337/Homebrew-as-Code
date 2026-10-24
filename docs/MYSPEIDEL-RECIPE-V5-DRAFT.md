# MySpeidel recipe_v5 offline draft (0019b)

**Safety boundary:** This is a **non-uploadable schema investigation**, not a
working `POST /v1.0/recipe` payload. It neither authenticates nor accesses the
network. It deliberately omits missing required fields rather than inventing
UUIDs, account owners, timestamps, catalogue references or process defaults.

## Input

Download the vendor specification privately, per
`docs/MYSPEIDEL-OPENAPI-REFERENCE.md`:

```powershell
New-Item -ItemType Directory -Force .local/vendor | Out-Null
Invoke-WebRequest 'https://api.cloud.myspeidel.com/v1.0/api-spec/json' `
  -OutFile .local/vendor/myspeidel-openapi.json
```

The local vendor specification is not redistributed in this repository.

## Run

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_recipe_v5_draft_cli `
  recipes/lebkuchen-zauber/recipe.yaml `
  --spec .local/vendor/myspeidel-openapi.json `
  --output-prefix .local/lebkuchen-recipe-v5
```

Output:

- `*.candidate.json`: a **partial fragment**, NEVER submit to MySpeidel.
- `*.report.json`: missing fields, structural findings, semantic blockers,
  OpenAPI file SHA-256. Private API examples/recipes are not written.

The structural checker handles a limited subset: `type`, `required`,
`properties`, `additionalProperties`, `items`, `enum`, `$ref` and `nullable`.
Compositions (`allOf`, `anyOf`, `oneOf`, `not`, discriminators) are reported as
unsupported, **not** passed silently. It is not a complete OpenAPI 3.0 / JSON
Schema validator. Format checks, constraints, defaults, readOnly/writeOnly,
server-side POST behavior, numeric unit semantics and reference existence
remain unverified. A clean subset check MUST NOT mean upload-ready.

The current projection includes only `name` and a candidate `bitterness` scalar;
even bitterness units/ranges still need confirmation. Existing mash/boil and
ingredient mapping modules remain useful *evidence*, but are intentionally not
combined into an API object until the complete nested schemas are validated.

Before a `dryRun` can be considered, resolve the reported blockers, validate a
complete payload with an independent OpenAPI-aware validator and verify POST
semantics against the vendor's documented example and controlled GET data.
No write operations are part of 0019b.
