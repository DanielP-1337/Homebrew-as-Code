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

Early development. **Milestone verified on October 25, 2026:** a recipe exported
from canonical Homebrew-as-Code YAML as independent BeerXML 1.0 was uploaded,
reviewed, and saved using the MySpeidel web interface. This is a manual web
workflow, **not** a supported Cloud API write integration; imported values still
require review before brewing.

## Implemented capabilities

- Canonical YAML recipes and automated recipe validation (including CI tests).
- Water chemistry calculations and independent supplier/catalog workflows.
- MySpeidel Cloud read-only inspection, private recipe backups, and reference diagnostics.
- Independent BeerXML 1.0 export from canonical YAML, including target gravity,
  malts, hops, spices, honey, yeast, and mash steps; **manual MySpeidel web
  import confirmed** for Lebkuchen-Zauber 2026 (0020i).
- Loss-aware BeerXML diagnostics and offline semantic comparison. Water volumes,
  mash-in temperature, fermentation, and device settings are not fully mapped;
  exported assumptions and actual imported values must be reviewed.
- BeerJSON export tooling (separate integration).
- Experimental, explicitly opted-in MySpeidel POST/PUT diagnostics; there is
  **no supported cloud recipe create/update workflow**.

## Current interoperability status

- Read-only MySpeidel GET and local recipe export work for tested private recipes.
- **Confirmed:** independently exported Lebkuchen-Zauber BeerXML from `recipe.yaml`
  reached ingredient matching and the MySpeidel editor and was saved to the
  personal recipe list (October 25, 2026).
- **Credit:** a Brewfather-exported BeerXML sample provided the first successful
  import reference and enabled controlled interoperability experiments. The
  exporter is independently implemented using the BeerXML 1.0 specification;
  the original Brewfather sample is **not redistributed**.
- **Historical negative result:** earlier partial/minimal BeerXML uploads returned
  HTTP 500. Retained as reproducible research history, not current capability.
- **Observed limitations:** 14 °P, 20 L, 5.1 kg malts, and three mash rests were
  transferred. MySpeidel showed 19.0 IBU versus a 21 IBU YAML target, a
  63 °C mash-in instead of 60 °C, 12 g yeast display versus 11.5 g input,
  and unpopulated structured water/fermentation fields. Malt attributes and
  brewhouse values for the test were explicitly provisional.
- Import of one genuine MySpeidel `.recipe` file reached ingredient matching;
  this does not establish a native `.recipe` exporter.
- The experimental Cloud POST `dryRun=1` candidate returned HTTP 400; live POST
  remains disabled pending a verified vendor contract.

See the [verified web-import milestone](docs/0020i-MYSPEIDEL-WEB-IMPORT-MILESTONE.md),
[semantic fidelity findings](docs/0020i-BEERXML-SEMANTIC-FIDELITY.md),
[MySpeidel Cloud write blocker](docs/MYSPEIDEL-WRITE-INTEGRATION-STATUS.md),
[earlier golden export experiments](docs/MYSPEIDEL-BEERXML-GOLDEN-ROUNDTRIP.md),
and [OpenAPI reference inventory](docs/MYSPEIDEL-OPENAPI-REFERENCE.md).

## Planned work

- Verify the separate MySpeidel Cloud API create/update contract before enabling
  direct API writes (manual web import is already demonstrated).
- Improve BeerXML semantic fidelity and ingredient identity handling, especially
  structured water/fermentation fields, mash-in temperature and yeast precision.
- Replace test assumptions with manufacturer-backed ingredient specifications
  and measured brewhouse parameters before the first brew.
- Extend batch and ingredient tracking without coupling canonical recipes to vendors.

## Legal and tax compliance

Brewing and distributing beer may be subject to taxes, reporting obligations,
and other regulations. For Germany, see [Brewing law and beer tax](docs/LEGAL-DE.md)
(§ 41 BierStV: 500 L per calendar year for qualifying private homebrewing;
no advance notice for that exemption since 2025-01-01). Other jurisdictions
have different rules. The software does not provide tax or legal clearance.

## BeerJSON schema conformance (0020o)

See [offline schema validation and multi-format inspection](docs/0020o-BEERJSON-CONFORMANCE.md)
for pinned schemas, version-policy separation and private Brewfather fixture checks.

Offline MySpeidel template extraction and brew-plan import drafts are documented
in [0020q - MySpeidel Import Builder](docs/0020q-MYSPEIDEL-IMPORT-BUILDER.md).
Drafts include explicit mapping gaps and are not upload-ready.

Offline POST candidate preparation and existing catalog identity reuse:
[0020r — MySpeidel Create Candidate](docs/0020r-MYSPEIDEL-CREATE-CANDIDATE.md).

Controlled POST dry-run with masked diagnostics and before/after GET checks:
[0020s — POST Dry-Run & GET Verification](docs/0020s-MYSPEIDEL-POST-DRY-RUN.md).

Explicit live creation with dry-run evidence binding and saved-recipe comparison:
[0020t — Live Create & GET Comparison](docs/0020t-MYSPEIDEL-LIVE-CREATE.md).

Guided recipe/plan selection, persistent account-scoped ingredient mappings and
resumable import sessions:
[0020u — Guided Import Workflow](docs/0020u-GUIDED-IMPORT-WORKFLOW.md).
