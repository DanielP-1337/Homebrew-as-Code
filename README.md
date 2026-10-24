# Homebrew-as-Code

Version-controlled homebrewing recipes, water chemistry,
batch tracking, and experimental MySpeidel Cloud integrations.

## Architecture

**One recipe. Multiple integrations. No vendor lock-in.**

The canonical YAML recipe defines what to brew, not how a particular machine
controls heaters, pumps or valves. MySpeidel, BeerXML / BeerJSON and supplier
integrations are independent adapters; actual batch records are kept separate.
See [ADR-0001](docs/adr/0001-one-recipe-multiple-integrations.md) for the
accepted decision, dependency rules and integration boundaries.

## Equipment

- Speidel Braumeister 20 L
- MySpeidel WLAN / Touchscreen controller
- Reverse osmosis water preparation
- KEG packaging
- Cast-iron malt mill

## Featured recipe — Lebkuchen-Zauber 2026

[![Lebkuchen-Zauber 2026 — Christmas Brown Ale](recipes/lebkuchen-zauber/assets/lebkuchen-zauber.png)](recipes/lebkuchen-zauber/README.md)

**Lebkuchen-Zauber 2026** is our first signature homebrew recipe: a festive
Christmas Brown Ale featuring honey, cinnamon, ginger, cloves, nutmeg, and
orange zest.

**20 L · 14 °P · 5.7% ABV (target) · 21 IBU**

Designed for the Speidel Braumeister 20 L.

[Explore the recipe](recipes/lebkuchen-zauber/README.md) ·
[View canonical YAML](recipes/lebkuchen-zauber/recipe.yaml)

*AI-generated concept image. The first batch has not yet been brewed.*

## Project status

Early development. The following components are implemented, but not all
integrations are production-ready.

## Implemented capabilities

- Canonical YAML recipes and automated recipe validation (including CI tests).
- Water chemistry calculations and independent supplier/catalog workflows.
- MySpeidel Cloud read-only inspection, private recipe backups, and reference diagnostics.
- BeerXML and BeerJSON export tooling; MySpeidel BeerXML golden export remains
  **experimental and partial** (water, yeast, fermentation, and device settings
  may be unrepresented).
- Experimental, explicitly opted-in MySpeidel POST/PUT diagnostics; there is
  **no supported cloud recipe create/update workflow**.

## Current interoperability status

- Read-only MySpeidel GET and local recipe export work for tested private recipes.
- MySpeidel web import of generated BeerXML and minimal BeerXML returned HTTP 500;
  successful MySpeidel BeerXML import has **not** been demonstrated.
- Import of one genuine MySpeidel `.recipe` file reached ingredient matching;
  this does not establish a native `.recipe` exporter.
- The experimental Cloud POST `dryRun=1` candidate returned HTTP 400; live POST
  remains disabled pending a verified vendor contract.

See [MySpeidel write status](docs/MYSPEIDEL-WRITE-INTEGRATION-STATUS.md),
[BeerXML golden export](docs/MYSPEIDEL-BEERXML-GOLDEN-ROUNDTRIP.md), and
[OpenAPI reference inventory](docs/MYSPEIDEL-OPENAPI-REFERENCE.md).

## Planned work

- Verify an end-to-end MySpeidel recipe creation contract before enabling writes.
- Improve loss-aware BeerXML interoperability and ingredient identity handling.
- Extend batch and ingredient tracking without coupling canonical recipes to vendors.

## Legal and tax compliance

Brewing and distributing beer may be subject to taxes, reporting obligations,
and other regulations. For Germany, see [Brewing law and beer tax](docs/LEGAL-DE.md)
(§ 41 BierStV: 500 L per calendar year for qualifying private homebrewing;
no advance notice for that exemption since 2025-01-01). Other jurisdictions
have different rules. The software does not provide tax or legal clearance.
