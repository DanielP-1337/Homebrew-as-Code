# MySpeidel recipe semantics – controlled read-only evidence

This tool supplements the offline mapper with **numeric observations** from an
existing private MySpeidel recipe. It does not infer or declare the units of
`amount` or the meaning of `boil.steps[].duration`.

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_semantics_cli
```

Enter your username/password interactively, choose a private 20 L recipe, and
type the exact word `yes` to permit printing its numeric quantities. Press
Enter or type anything else to cancel *before* fetching recipe details.

The output includes **only numeric fields** from an allowlist and reference
counts: no recipe names, UUIDs, ingredient names, credentials, or raw API
payloads. Quantities may still reveal proprietary recipes, so review results
before sharing. Nothing is written to disk. Authentication uses the official
login POST; all recipe requests are GET-only.

## How to interpret evidence

- Compare `boil_duration_raw` with individual `boil_steps[].duration_raw` and
  known hop addition times in the MySpeidel UI. One recipe may not distinguish
  *elapsed time* from *step duration*: treat the answer as unknown until verified.
- Compare `malt_amounts_raw` and hop `amount_raw` with a recipe whose quantities
  you can independently read in MySpeidel. No automatic g/kg conversion.
- `alpha_acid_raw` is the observed API number; do not assume scaling.
- `reference_counts` shows cardinalities only. No reference UUID mapping yet.
- The mapping and future upload stay explicitly blocked until these semantics,
  required fields, recipe ownership, and round-trip validation are resolved.

Official OpenAPI specification:
https://api.cloud.myspeidel.com/v1.0/api-spec/json
