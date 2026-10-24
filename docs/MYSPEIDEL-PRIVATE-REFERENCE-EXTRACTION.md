# MySpeidel private recipe references (0019e)

This integration is deliberately GET-only. It uses **one explicitly selected
PRIVATE 20 L reference recipe**, not arbitrary account-wide harvesting. Never
commit actual recipe UUIDs, catalog UUIDs, credentials, private snapshots or
reports: store outputs under `.local/`.

## 1. Create a controlled private reference recipe in the web UI

Use a few **unambiguously identifiable** ingredients, preferably one entry
per category/time slot. Note the exact order and identity shown in the UI.

## 2. Fetch observations (authorized GET only)

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_private_references_cli fetch `
    --output .local/myspeidel-reference-observations.json
```

Select an existing private recipe by number; type exact `yes` to permit
GET and local write. The persisted observations contain ONLY reference UUIDs,
array indices and source paths (no recipe name, raw recipe, login or token).
These UUIDs are still sensitive account-derived data. No catalog identity is
inferred. If the private recipe detail lacks a required reference UUID, the
command fails closed.

## 3. Explicit manual confirmation

Create `.local/myspeidel-confirmations.yaml` and enter the observation indices
that correspond to ingredients you independently identified in the website:

```yaml
confirmations:
  - observation_index: 0
    kind: malt
    name: Pale Ale Malt
    web_verified: true
```

The index is an **example only**. Inspect the local observations before setting
it; never automatically assume order, matching UUID or name from index.
A non-hop such as cinnamon can be in `adds.hops[]`; manual confirmation is
required even if the array type is surprising.

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_private_references_cli confirm `
    recipes/lebkuchen-zauber/recipe.yaml `
    --observations .local/myspeidel-reference-observations.json `
    --decisions .local/myspeidel-confirmations.yaml `
    --output .local/myspeidel.confirmed-catalog.yaml
```

No fuzzy matching: duplicate observation indices or ingredient names fail.
The output uses an **explicit private recipe GET provenance** rather than
pretending a public catalog endpoint exists. The 0019d resolver recognizes
this provenance only when both `confirmed` and `web_verified` are true.

## 4. Reuse the 0019d offline resolver

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_catalog_resolver_cli `
    recipes/lebkuchen-zauber/recipe.yaml `
    --spec .local/vendor/myspeidel-openapi.json `
    --snapshot .local/myspeidel.confirmed-catalog.yaml `
    --output .local/myspeidel-confirmed-resolution.json
```

Important: the result **remains non-uploadable** and the supplier matching
still cannot verify availability of ingredient catalog objects in future
recipes. An observation is not the same as a documented catalog lookup.
No POST/PUT/dryRun is implemented.
