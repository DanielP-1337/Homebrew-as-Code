# MySpeidel Write Integration – Blocked by Vendor Contract

**Status:** BLOCKED / WRITE EXPERIMENTS PAUSED

**Decision date:** 2026-10-24
**Scope:** Homebrew-as-Code MySpeidel integration

## Decision

Homebrew-as-Code keeps vendor-neutral YAML recipes as the source of truth. MySpeidel Cloud API access is treated as **read-only for supported workflows** until a documented, verified create/update contract is available. Writing or merging MySpeidel catalog ingredients is not part of the supported integration.

This is a **vendor-contract dependency**, not a claim that all MySpeidel write operations are broken. A request has already been sent to Speidel support/sales; a response is pending.

## Evidence from controlled experiments

| Path | Observation | Conclusion |
| --- | --- | --- |
| Cloud GET and private-recipe backup | Successfully reads private recipes, references, and brew process data | Usable as read-only integration |
| Cloud PUT with `dryRun=1` | HTTP 400, including validation/shared-ingredient-reference errors | No verified update contract |
| Cloud POST `/v1.0/recipe?dryRun=1` | HTTP 400 for a cloned 20 L private recipe candidate with new recipe UUID; sanitized report `UNVERIFIED_RESPONSE` / `unclassified` | No validated create request; do not attempt live POST |
| Web upload of Homebrew-as-Code BeerXML | HTTP 500 at `/recipes/upload_recipe_post` | Not demonstrated compatible with Speidel import |
| Web upload of minimal BeerXML | Same HTTP 500 | Failure is not isolated to specific generated hop/malt fields |
| Web upload of genuine `.recipe` | HTTP 200, proceeds to manual similar-ingredient matching screen | Native import path works for this tested file, not evidence we can generate native files |

The precise server-side cause of the BeerXML failures is unknown. HTTP status codes alone do not establish an implementation defect. File-format cryptography and internals of `.recipe` remain unverified.

## BeerXML export: implemented, experimental

The offline `homebrew_as_code.myspeidel_beerxml_roundtrip export` command writes a BeerXML 1.0 file and a separate loss/assumption report from a private MySpeidel backup. **It performs no network operations** and does not modify the original backup.

For the local *Weizenbier 38°* test case the user verified export of **4 malts**, **3 hop additions**, and **3 temperature mash rests**; the local test suite passed **256 tests** after patch 0020d2. Malt color uses EBC-to-SRM conversion, with a separately evidenced Carahell override and recorded provenance. Mash rests are manually transcribed from web-form evidence, not inferred Cloud semantics.

The export deliberately remains `PARTIAL_EXPORT`:

- Yeast omitted without independently confirmed type, form, and amount (the observed run emitted zero yeast entries).
- Separate mash and sparge water volumes are not losslessly represented by the current BeerXML 1.0 mapping.
- Fermentation, maturation, and machine-specific controls are not fully represented.
- Batch/boil volumes and malt yield can include explicit test assumptions; validate before practical use.
- Generated BeerXML **has not been successfully imported into MySpeidel**. Do not advertise a verified roundtrip.

See `docs/MYSPEIDEL-BEERXML-GOLDEN-ROUNDTRIP.md` for commands, safeguards, and field caveats.

## Ingredient identity safety

Ingredient labels, quantities, EBC color, and alpha-acid values do **not** establish shared identity. Distinct MySpeidel UUIDs remain distinct even with matching attributes. Candidate Web-ID-to-Cloud-UUID matches are not authoritative. Do not perform an automatic identity merge, rewrite shared catalog entities, or transfer ownership metadata on that basis.

## Resume only when evidence changes

1. Speidel supplies a supported end-to-end POST/PUT example, including create-schema version, valid references, ingredient ownership semantics, and precise dry-run behavior; **or** a verified supported create path is captured with appropriate permissions.
2. An offline fixture test reproduces the vendor contract without private account data.
3. Any real write is independently reviewed and explicitly opted into, with backup and post-write GET verification.
4. Independently verify a third-party BeerXML reference import before changing the exporter to accommodate undocumented MySpeidel behavior.

## Privacy and publishing

Never commit `.local/`, Cloud backups, candidate recipes, API tokens, cookies, session headers, raw HTTP error bodies, or browser HAR files. Publish sanitized status, schema findings, and non-sensitive test results only.

## Local repository handoff

The user's working tree includes patches 0020b–0020e applied locally, including the BeerXML exporter. GitHub may lag this working tree until reviewed and pushed. Before committing, run the complete test suite and review `git diff --cached` and the staged path list; exclude `.local/` and other private files.
