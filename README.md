# Homebrew-as-Code

Version-controlled homebrewing recipes, water chemistry,
batch tracking, and MySpeidel Cloud synchronization.

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

## Initial recipe

Lebkuchen-Zauber 2026 - Christmas Gingerbread Ale

## Project status

Early development.

## Planned features

- Version-controlled YAML brewing recipes
- Water chemistry calculations
- Batch and ingredient tracking
- MySpeidel Cloud API integration
- BeerXML import/export
- Automated recipe validation

## Legal and tax compliance

Brewing and distributing beer may be subject to taxes, reporting obligations,
and other regulations. For Germany, see [Brewing law and beer tax](docs/LEGAL-DE.md)
(§ 41 BierStV: 500 L per calendar year for qualifying private homebrewing;
no advance notice for that exemption since 2025-01-01). Other jurisdictions
have different rules. The software does not provide tax or legal clearance.
