# MySpeidel single-recipe inspection (read-only)

This step inspects one existing private recipe associated with the 20-liter
machine class and compares its **structure only** with the local recipe.
It does not create, modify, delete, synchronize, or start recipes.

## Run from the repository root (PowerShell 7)

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_inspect_cli
```

Enter your MySpeidel username and password interactively. Select a numbered
recipe; pressing Enter cancels before the recipe-detail request. No credential,
UUID, recipe name, or ingredient value is printed. The script prints a JSON
structure (field names, types, array lengths), a small local-section inventory,
and a clear `NOT_IMPLEMENTED` mapping status.

The collection is filtered to private recipes whose `machine_type.size` equals
20. The device assignment is verified **from collection metadata only**;
this does not establish that a given recipe is installed on the physical
Braumeister or that every detailed field maps to our YAML format.

Array schemas are sampled from the first element by the current generic
inspector, so inspect multiple recipes if their structures differ. Do not
assume a missing field is unsupported just because it was absent in one
example. Inspect the output before posting: arbitrary JSON field *names*
could themselves disclose private information.

All network recipe requests are GET-only. Authentication is the existing
explicit POST to the documented login endpoint. No API payloads are persisted.

## Next step

Confirm actual `recipe_v5` field semantics and supported data types from the
published OpenAPI schema and a local read-only inspection. Build a separate
validated mapper only after those fields are understood; the present command
is not a MySpeidel exporter.
