# ADR-0002: Separate recipe, equipment and brew-plan domains

- **Status:** Accepted (incremental implementation)
- **Date:** 2026-10-25
- **Extends:** [ADR-0001](0001-one-recipe-multiple-integrations.md)

## Context

The canonical Lebkuchen-Zauber YAML still contains historical device context and
provisional water quantities. An equipment-profile-first experiment showed
that changing Brewfather's generic imported profile (20 L, 70% efficiency,
24 L pre-boil) to its Speidel Braumeister 20L preset (21 L, 74%, 25.42 L)
**also changed ingredient masses**. Thus equipment presets cannot silently
modify a canonical brewing recipe. The 21 L reference batch size is not the
20 L intended packaged output of the current recipe.

## Decision

- `recipes/**/recipe.yaml`: intended beverage and schedule; canonical source.
- `equipment/*.yaml`: physical equipment references and provenance, no recipe
  ingredients and no controller commands. Values are third-party **unverified
  presets**, not measurements of the user's machine.
- `brew-plans/*.yaml`: reference a versioned recipe and an equipment profile,
  specify intended output and hold planning caveats. A plan is **not** a recipe
  dependency on equipment; dependencies point plan → recipe and plan → equipment.
- `batches/` (future): measured actuals and lot provenance, kept distinct from
  presets and targets.
- Legacy `recipe.equipment` context and water allocations remain in schema v1
  temporarily. Migration requires a new schema and regression tests; do not
  break current MySpeidel and Brewfather BeerXML interoperability.

## Safety and adapter boundaries

- No automatic ingredient scaling, implied change to OG, volume, water splits,
  hop utilization, or brew controller synchronization.
- Import/export adapters continue to consume canonical YAML unchanged. Brewfather
  imports remain compatible **to the extent already empirically confirmed**:
  this patch does not change the previously tested BeerXML serializer or source.
  A future plan-aware export must be separately implemented and tested.
- Equipment values must retain source labels and verification status.
- No original Brewfather example file or vendor-specific catalog identity is
  committed. Credit Brewfather for its preset and earlier BeerXML reference.

## Verification

`load_brew_plan(..., repo_root=...)` resolves repository-relative paths, rejects
missing or escaping references, verifies version and equipment ID, and does not
mutate or scale ingredients. Run `python -m pytest -q` in the repository.

## Open issues

Measure actual brewhouse loss, boil-off, extraction efficiency and water balance
on the physical Braumeister before declaring a brew-day-ready plan. Confirm the
meaning and applicability of preset 21 L target volume. The existing 23 L mash
+ 5 L sparge allocations remain provisional and are not derived from the new
profile's 25.42 L **pre-boil wort** volume.
