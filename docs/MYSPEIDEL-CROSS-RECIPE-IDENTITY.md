# 0020c – MySpeidel cross-recipe identity corroboration

This is a **read-only/offline** audit of browser form IDs versus Cloud API UUIDs across multiple privately captured recipe pairs. It extends the 0020b candidate resolver. It does **not** persist a verified ingredient registry and does **not** send HTTP requests.

## Inputs

Capture the POST form body for each distinct private recipe using browser DevTools **Payload → View source**. Do not save request headers, cookies, credentials or authentication fields. Store each form body under `.local/`. Obtain the corresponding, fresh Cloud API GET backup using the existing explicit recipe backup flow. Never use an unrelated or stale backup.

Create `.local/0020c-manifest.json`:

```json
[
  {"form": ".local/myspeidel-web-form.txt", "backup": ".local/roundtrip-devtools-fresh.json"},
  {"form": ".local/another-recipe-form.txt", "backup": ".local/another-recipe-fresh.json"}
]
```

Run from repository root:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_cross_recipe_identity `
    --manifest .local/0020c-manifest.json `
    --report .local/0020c-cross-recipe-report.json
```

Inspect locally:

```powershell
$Report = Get-Content .local/0020c-cross-recipe-report.json -Raw | ConvertFrom-Json
$Report.identities | Format-Table kind,web_id,status,distinct_eligible_recipes -AutoSize
```

## Status semantics

- `SINGLE_RECIPE_CANDIDATE`: only one distinct eligible recipe supports the singleton.
- `CROSS_RECIPE_CORROBORATED`: at least two distinct recipe UUIDs support the same singleton Cloud UUID, without conflicting eligible evidence.
- `CONFLICT`: eligible distinct recipes support different singleton UUIDs.
- `AMBIGUOUS_OR_INCOMPLETE`: an eligible recipe has unresolved, ambiguous or internally inconsistent candidates.
- `INSUFFICIENT_EVIDENCE`: no eligible recipe pair for that web ID.

Eligibility requires exact recipe-name equality and equal ingredient-occurrence counts. Matching only a recipe name is **not** sufficient to establish a same-recipe identity; supply the correct captured form and backup. Repeated occurrences within one recipe count as one source. A second capture or backup of the same recipe UUID is rejected. The audit deliberately does not infer chronology, normalize units, or assert that matching quantities and acidity independently prove identity. **All results remain provisional; `verified_mapping_count` is always zero.**

Do not commit `.local/` captures, backups, manifests or reports. Reports contain ingredient IDs and private recipe UUIDs. The CLI only reads inputs below `.local/`, refuses to overwrite an existing report, and never modifies recipe data.
