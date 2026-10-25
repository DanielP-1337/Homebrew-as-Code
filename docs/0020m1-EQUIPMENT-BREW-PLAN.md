# 0020m1 — Equipment Domain Separation & Brew Plan Architecture

An additive DDD/TDD milestone: the recipe, 0020i exporter, and 0020l comparison
are unchanged. This introduces an independent equipment catalog entry and a
separate draft brew plan. Source: user-observed Brewfather Speidel Braumeister
20L preset and BeerXML re-export on 2026-10-25, **unverified on the machine**.

- Equipment: `equipment/speidel-braumeister-20l.yaml`
- Plan: `brew-plans/lebkuchen-zauber-brew-001.yaml`
- Domain resolver: `src/homebrew_as_code/brew_plan.py`
- Architecture: [ADR-0002](adr/0002-equipment-brew-plan-boundaries.md)

Example offline validation:

```powershell
@'
from pathlib import Path
from homebrew_as_code.brew_plan import load_brew_plan
repo = Path.cwd()
result = load_brew_plan(repo / 'brew-plans/lebkuchen-zauber-brew-001.yaml', repo_root=repo)
print(result['plan']['brew_plan']['id'])
print(result['equipment']['reference']['verification'])
for warning in result['warnings']:
    print('WARN:', warning)
'@ | .\.venv\Scripts\python.exe -
```

Existing tested BeerXML generation remains **exactly the same**, including
explicit assumptions (`--boil-size-liters`, `--efficiency-percent` and private
malt property JSON). It is not automatically populated from this profile.
This is intentional: otherwise the 21 L/74% preset could silently alter the
20 L recipe and invalidate the proven MySpeidel/Brewfather import pathway.

Re-run the full test suite, and check staged files to avoid `.local/`, account
identifiers and downloaded Brewfather originals.
