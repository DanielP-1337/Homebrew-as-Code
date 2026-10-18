# Controlled MySpeidel boil-timing evidence (0008d)

All output remains **offline only**. No API writer is implemented. `upload_ready`
is always `false`, `api_payload` is always `null`, and reference UUIDs
are never synthesized. Do **not** POST the offline draft.

## Evidence from one private, manually created 20 L test recipe

After re-saving and reopening the web editor, the boil temperature was 100 C,
total boiling time was 60 minutes, and the three additions were:

| Web time before end | Web entry | GET `boil.steps[].duration` | GET `adds.hops` |
| --- | --- | --- | --- |
| 60 min | hop, 11 g, 5% acid | 60 | one entry (11 g, acid 5) |
| 20 min | hop, 7 g, 5% acid | 20 | one entry (7 g, acid 5) |
| 5 min | Ceylon cinnamon, 5 g, 0% acid | 5 | one entry (5 g, acid 0) |

API `boil.boiling_duration` was 60 and `boil.boiling_temperature` was 100.
These step values represent the **minutes-before-end** input for this test;
they are not additive step spans. `adds.ingredients` was absent in this test.
The cinnamon row had `uuid` and `hop_uuid` fields present, but
`ingredient_uuid` was absent. Reference VALUES were not disclosed.

## Offline draft, not a Speidel API request

`myspeidel_ingredients_cli` now emits `boil_steps_offline_draft`: a deterministic,
ordered list of step durations and entries under an observed `adds.hops`-shaped
container. Entry names/source categories and an explicit `evidence` annotation
belong to **our internal draft**, not the verified MySpeidel write schema.

Only **Ceylon cinnamon** has been confirmed to appear in the API hop container
as a non-hop ingredient. Honey, ginger, cloves, nutmeg and orange zest still
require individual checks, and catalog UUID resolution remains a blocker.
Likewise, `hop_uuid: null` is a placeholder in our draft, **not** a valid API
reference or permission to submit it. Additional mandatory envelope fields,
fermentation and maturation are still unresolved.

Never put raw API responses, token-bearing logs, private recipe data, or exported
`.recipe` files in the public repository.
