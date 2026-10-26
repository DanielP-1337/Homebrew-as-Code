# MySpeidel write integration — verified private recipe creation

Status as of **October 26, 2026**, implementation through commit `33a10fd`.

Private recipe creation is implemented and experimentally verified for two 20 L
recipes in the tested account. Use the [guided API import workflow](0021-API-IMPORT-WORKFLOW.md).
The repository remains the source of recipe intent; the adapter supplies explicit
exchange decisions, account-specific references and creation metadata.

## Evidence

| Recipe | Dry-run | Live POST | Subsequent GET | Source |
| --- | --- | --- | --- | --- |
| Lebkuchen-Zauber 2026 | Verified, HTTP 200 | HTTP 201 | Zero content differences; 28 metadata differences | Unchanged |
| Weizen Nikolaus - HBAC API | Verified, HTTP 200 | HTTP 201 | Zero content differences; 18 metadata differences | Unchanged |

The Lebkuchen metadata differences were inspected and were timestamp normalization.
The Weizen report's 18 metadata differences have not been individually analyzed;
do not describe them as confirmed timestamp-only changes. Content and metadata
are separate comparison categories, not a claim of byte-identical responses.

The Weizen web portal listing was also confirmed, showing 12 °P, 14.8 IBU and
5 EBC. Its creation includes the reviewed fermentation and maturation settings.
These are transferred recipe values, not independently measured beer properties.
The Windows test suite passed **535 tests** at commit `33a10fd`.

The evidence consists of local diagnostics, user-reported terminal results and a
portal screenshot. Private raw files and account identifiers are not published
here. The screenshot confirms listing, not brewing-device execution. The portal
list appeared after a delay; its cause and general timing are unverified.

## Operational boundaries

- POST creates a new private recipe. It does not update the source recipe.
- Dry-run success alone is not persistence; live HTTP 201 plus GET verification
  established persistence for the tested candidates.
- Existing catalog identities are resolved and reused. Matching names alone do
  not justify merging catalog entries. No dedicated ingredient creation endpoint
  was present in the inspected OpenAPI document.
- Schema checks can report unverified constraints; passing them is not API acceptance.
- PUT remains a separate experimental path, not validated by these POST results.
- Device synchronization and execution remain outside this evidence.
- Frozen inputs, dry-run evidence binding, explicit live confirmation, attempt
  tracking and GET comparison are retained. There are no automatic POST retries.

## Historical findings

The [October 24 blocked-state snapshot](MYSPEIDEL-WRITE-STATUS-20261024.md) preserves
the earlier failed requests and conclusions as history. Later milestones include
the [independent BeerXML web import](0020i-MYSPEIDEL-WEB-IMPORT-MILESTONE.md),
[verified live create implementation](0020t-MYSPEIDEL-LIVE-CREATE.md), and
[Weizen candidate completion](0020z-MYSPEIDEL-UPLOAD-COMPLETION.md).

Keep credentials, backups, candidate files and raw diagnostics under `.local/`.
Publish only reviewed summaries and synthetic fixtures.
