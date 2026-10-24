# 0019y — Read-Only Ingredient References Roundtrip

The MySpeidel server rejected replacing the name of a shared `water_types` record:
`Cannot update existing ingredient. Ingredient is referenced by more than one recipe`.
This patch tests whether a recipe PUT can avoid writing embedded shared catalog records.

## Experimental payloads

- `omit-references`: remove the entire top-level `references` property from a copy of the recipe.
- `empty-references`: replace that property with `{}`.
- `empty-reference-categories`: keep reference category keys and non-object metadata, but clear embedded category dictionaries. Brewing-step UUID references remain unchanged; embedded catalog-entry UUID keys are removed from the candidate. This is a structural diagnostic only.

The source backup, ingredient catalog, and all recipe-step UUID fields are never edited. No claim is made that any of these variants are *server-side read-only*: `PUT` may interpret omitted reference data as deletion or replacement. **Use `prepare` and confirmed `dry-run` first. `apply` is intentionally disabled for all three reference-stripping variants.**

## Commands

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_experiments `
    --backup .local/weizenbier38-golden-backup.json `
    --variant omit-references --mode prepare `
    --spec .local/vendor/myspeidel-openapi.json `
    --result .local/0019y-omit-prepare.json
```

Interpret `errors` and `unverified` as partial offline checks, not complete PUT readiness. When and only when a variant is intentionally selected for an API dry-run, use a **new** `--result` path and `--mode dry-run`; the existing explicit `DRY RUN EXPERIMENT` confirmation and GET digest check are unchanged. Enable `HBAC_MYSPEIDEL_LOCAL_HTTP_ERROR=1` to save a private `.http-error.json` on HTTP errors. Never commit `.local` reports.
