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

I use the following equipment for my homebrewing:

- Speidel Braumeister 20 L
- MySpeidel WLAN / Touchscreen controller
- Reverse osmosis water preparation
- KEG packaging
- Cast-iron malt mill
- Counterflow wort cooler
- [Barby + Kühner](https://barby-kuehner.de/) hydrometers from Untersiemau:
  0–7 °P for monitoring fermentation, 7–14 °P as my main brewhouse hydrometer,
  and 14–21 °P for stronger beers such as bock.

## Background

I learned to brew with Nikolaus Starkmeth.
His brewing courses are available at [Brauerei Starkmeth](https://www.bierbrauen-kurs.de/).

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

**Verified on October 26, 2026:** private recipe creation through the MySpeidel
Cloud API succeeded for **Lebkuchen-Zauber 2026** and **Weizen Nikolaus - HBAC API**.
Both returned HTTP 201 and passed subsequent GET comparison with **zero content
differences**; the source recipes remained unchanged. The Weizen import includes
fermentation and maturation steps and was also confirmed in the web portal.

Start with the [API import workflow](docs/0021-API-IMPORT-WORKFLOW.md).
The integration remains experimental and verified for the tested private 20 L
recipes/account. This does not establish general PUT/update support, ingredient
catalog creation, or successful transfer to and execution on a brewing device.

## Implemented capabilities

- Versioned recipes, separate equipment/brew plans, and draft completeness checks.
- Guided MySpeidel import with persistent, account-scoped ingredient mappings.
- Offline candidate preparation and schema inspection; explicit POST dry-run,
  live creation and before/after GET verification.
- Recipe-bound export settings, including fermentation in hours and maturation
  in days, with fresh identities for new recipe additions and process steps.
- Independent BeerXML 1.0 export and a verified manual MySpeidel web import
  for Lebkuchen-Zauber (October 25, 2026); semantic limitations remain documented.
- Pinned BeerJSON schema validation and separate export/compatibility tooling.
- Guided local brew-day observations, variable actual yield and annual quantity
  summaries that exclude TEST batches and flag unclassified records.
- Water chemistry calculations and independent supplier/catalog workflows.

## Current interoperability status

| Path | Verified scope |
| --- | --- |
| Cloud recipe GET | Private recipe listing, backups and comparison |
| Cloud POST dry-run | HTTP 200 with acknowledgement and GET verification for tested candidates |
| Cloud live POST | HTTP 201 and zero content differences in subsequent GET for two recipes |
| Web portal | API-created Weizen recipe listed with 12 °P, 14.8 IBU and 5 EBC |
| Independent BeerXML web import | Confirmed for Lebkuchen-Zauber; separate from the API create path |
| Cloud PUT/update | Separate experimental tooling; not established by the POST milestones |
| Ingredient catalog creation | No dedicated create endpoint in the inspected OpenAPI document; existing references reused |
| Device execution | Not verified by these imports |

The portal list appeared after a delay in the Weizen test. This observation does
not identify the cause; a delayed listing is not a reason to repeat POST after
successful GET verification.

See [current write status and evidence](docs/MYSPEIDEL-WRITE-INTEGRATION-STATUS.md)
and the [historical blocked-state record](docs/MYSPEIDEL-WRITE-STATUS-20261024.md).
Earlier HTTP 400/500 results describe earlier candidates and do not override the
later verified results. The original Brewfather sample helped establish the
BeerXML reference; it is not redistributed. See the
[web-import milestone](docs/0020i-MYSPEIDEL-WEB-IMPORT-MILESTONE.md) and
[semantic fidelity findings](docs/0020i-BEERXML-SEMANTIC-FIDELITY.md).

## Planned work

- Extend the verified create path to additional recipes and catalog mappings.
- Improve import usability and preserve explicit units and source provenance.
- Investigate recipe updates separately from the verified create workflow.
- Improve cross-format semantic coverage without coupling recipes to vendors.

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

Second-recipe source review and offline ingredient identity comparison:
[0020v — Second Recipe Review](docs/0020v-SECOND-RECIPE-REVIEW.md).




Variable-yield draft recipes, stage-specific completeness and plan linkage:
[0020w — Draft Completeness & Brew-Plan Promotion](docs/0020w-DRAFT-COMPLETENESS.md).
