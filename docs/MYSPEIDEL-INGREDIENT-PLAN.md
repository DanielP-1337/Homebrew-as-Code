# MySpeidel ingredient mapping — safe offline plan (0007)

Run from repository root (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_ingredients_cli recipes/lebkuchen-zauber/recipe.yaml
```

This command performs **no network calls, authentication, API writes or disk exports**.
Output is a reproducible **planning manifest**, NOT an API `recipe_v5` payload.
`upload_ready` is always `false`, and `api_payload` is always `null`.

## Confirmed UI units and conversions

- `fermentables[].amount_g / 1000` → `malts[].amount_kg`; MySpeidel web form uses kg.
- Hop and other-boil-ingredient amounts remain grams; web form uses g for hops.
- `alpha_acid_percent` remains a percent, matching the hop form field.
- `remaining_min` is represented as **minutes before end** in a **web-form timeline** only.
  This does **not** claim that `boil.steps[].duration` uses that convention.
- Mash rests must be nondecreasing; boil duration must not exceed 180 minutes.

Every ingredient has `catalog_uuid: null` and `resolution: REQUIRED` until
matched to the actual MySpeidel catalog. We do **not** guess UUIDs or store
private catalog records in the repository. Any missing mapping blocks upload.

## Controlled reverse engineering with a `.recipe` export

A small, dedicated test recipe created **manually on the MySpeidel website** is
an excellent reference. Export it as `.recipe`, inspect for personal/account
metadata before sharing, and compare the export to a **GET-only** API detail
read of that exact test recipe. Use distinctive test values and multiple hop
times (e.g., 60 and 10 min before end) to discriminate cumulative versus
segment durations. Do not upload or replay the export to an API endpoint.

**The web form and an exported `.recipe` file do not themselves establish**
the complete `recipe_v5` API write format. Verify the export schema and API
response independently before implementing any writer.

## Outstanding blockers

1. Authoritative catalog lookups and explicitly verified ingredient UUIDs.
2. Meaning and ordering of `boil.steps[].duration` in API detail reads.
3. Required recipe-v5 metadata, references, water type, fermentation and
   maturation fields; potentially machine-specific constraints.
4. An explicit, opt-in write implementation with safe preflight and duplicate
   protection (future patch only).
