# Recipe development guide

## Local setup (Windows / PowerShell 7)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m homebrew_as_code.cli validate recipes/lebkuchen-zauber/recipe.yaml
.\.venv\Scripts\python.exe -m homebrew_as_code.cli water recipes/lebkuchen-zauber/recipe.yaml
.\.venv\Scripts\python.exe -m pytest -q
```

## Current scope

- The YAML file is the canonical recipe specification. It is **not** a MySpeidel payload.
- `water` reports *added ions* from specified dihydrate salts, assuming mineral-free RO water. It does not predict mash pH, alkalinity, or account for source water residuals.
- Do not substitute 33% calcium chloride solution by mass without converting the composition from CaCl2·2H2O to anhydrous CaCl2. Verify the supplier's specification.
- Goldings hop mass corresponds to a provisional 2.9% alpha-acid lot. Recalculate against the actual package label and measured boil conditions.
- 70% brewhouse efficiency and water losses are provisional; compare against the operator's historical logs.
- Recipe water volumes and ingredient amounts must be rechecked before the first batch. No automation starts any brewing device.
- MySpeidel read-only schema discovery and authenticated sync are reserved for a later milestone.

## Project conventions

- Public repository: never commit credentials, tokens, brewing-account exports, or personal account identifiers.
- Recipe purchases use whole/uncrushed malt. Brewing is done with a Speidel Braumeister 20 L, and packaging is in kegs.
- Commit measured batch data separately from the target recipe.
