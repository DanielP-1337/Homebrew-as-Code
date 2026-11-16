# Recipe sources in HBAC 0.5.0-beta.3

All sources use the same review queue, conversion rules and explicit replace-all
confirmation. Mix sources in one list of up to nine device programs. Importing or
previewing never sends a program to the device. Existing 0.4.0 configuration, stored
queue and upload-job tracking remain compatible.

## Configure providers

In HA, open HBAC's **Reconfigure** flow. Brewfather user ID/key and the Brewer’s
Friend API key are optional. Keep existing Brewfather credentials to use both
providers. Clearing both Brewfather fields disables Brewfather; clearing the
Brewer’s Friend field disables that provider. No cloud credentials are required
for a BeerXML-only installation. The selected Braumeister remains unchanged.

The key is stored in HA configuration and sent only from the server to the provider,
not returned in card state or embedded in dashboard YAML.

## Brewer’s Friend

Get your key from [Profile → Integrations](https://docs.brewersfriend.com/profile/integrations).
HBAC uses read-only requests with `X-API-KEY`:

- `GET https://api.brewersfriend.com/v1/recipes?limit=100&offset=...`
- `GET https://api.brewersfriend.com/v1/recipes/{id}.xml`

Choose **Brewer’s Friend** in the card, load the list or enter a numeric recipe ID,
then create a preview. The XML endpoint feeds the same parser used by local files.
Only recipes are supported in this beta, not Brewer’s Friend brew sessions.
Pagination is bounded at 10,000 recipes; direct IDs remain usable for larger lists.
HTTP redirects are not followed with credentials. Authentication failures, HTTP
errors, rate limiting and invalid responses produce errors without exposing the key.
A live empty-account check confirmed that the collection endpoint returns HTTP 404
with `{"message":"not-found","detail":"no recipes found"}`. Beta 2 treats only this
exact collection response as an empty list, including during setup. Other 404s and
recipe-detail failures remain errors. Live retrieval of a populated recipe library
and hardware acceptance remain pending; those paths use mocked HTTP tests.
Setup errors are attached to the failing provider field; sanitized failures are
also recorded in HA logs without credentials or response bodies.

Official references: [Recipe API](https://docs.brewersfriend.com/api/recipes) and
[Recipe BeerXML endpoint](https://docs.brewersfriend.com/api/recipes/recipe).

## BeerXML browser file upload

Choose **BeerXML · Upload file**, select an `.xml` file on your computer, then select
one of the recipes in it. Inspect the preview and add that recipe to the queue.
Repeat for additional recipes. Files are transferred through HA's authenticated
service connection, parsed in memory and not written into a public `www` folder.
The current in-memory import is lost on integration reload; recipes already added
to the persistent queue remain available. The five most recent imports are retained.

## BeerXML HA handoff folder

Create `/config/hbac/import` inside HA and place XML files there (for example using
an existing file editor or network share). You may configure another absolute path
**inside the HA runtime** through HBAC reconfiguration. A path on the browser's
computer is not a path inside HA. The folder is not created automatically.

Choose **BeerXML · HA folder**, load the list, select a file, click **Read selected
file**, then select a recipe and preview it. HBAC does not watch, move, delete or
modify files. Only direct `.xml` files are listed; nested directories and symlinks
are excluded. At most 500 filenames are listed. A missing folder produces an empty
list. The selected file is read into a snapshot, so later file changes do not
silently change a preview or a recipe already in the queue.

## Format and limits

- BeerXML v1 `<RECIPES>` containing 1–100 `<RECIPE>` records; maximum 512 KiB/file.
- Standard Celsius and minute fields are used. `DISPLAY_*` values are ignored;
  those are presentation strings and may be rounded or use different units.
- Required conversion fields include recipe `NAME`, `VERSION`, `BOIL_TIME`,
  `MASH`/`VERSION`/`MASH_STEPS`, each step's `VERSION`, `TYPE`, `STEP_TEMP`,
  `STEP_TIME`, and `HOPS` (which may be empty). Hops require `VERSION`, `NAME`,
  `USE`, `TIME`. This is a device-program importer, not a complete BeerXML validator.
- Empty optional numeric elements (INFUSE_AMOUNT, RAMP_TIME, END_TEMP) are
  treated as absent, including whitespace-only elements. Empty required fields and
  nonempty invalid numeric values remain errors.
- Existing device limits apply: 1–5 rests, integer representable temperatures and
  durations, at most six distinct boiling-hop alarms. No silent rounding or
  truncation of steps. Decoction and incompatible end temperatures are rejected.
- Ramp timing and infusion amounts produce omission warnings; zero-minute,
  whirlpool, dry-hop, mash and first-wort additions are not boiling-hop alarms.
- Default mash-in is the first rest's temperature, editable in HA. Default device
  boil temperature is 103 °C, also editable. Ingredients, water, fermentation and
  brewing measurements are not device-program fields.
- DTDs/entities, malformed XML, missing/duplicate conversion fields, non-finite
  numeric values, oversized files and paths outside the selected folder are rejected.
- Source labels remain unchanged; UI, instructions and owned error messages are
  localized in all eight bundled languages with en-US fallback.

[BeerXML v1 specification](https://www.beerxml.com/beerxml.htm).

## Quick test without cloud credentials

Use [hbac-demo.xml](examples/beerxml/hbac-demo.xml) with either import method.
It is synthetic test data, not a complete brewing recipe. Expected program:
`HBAC XML Demo`, mash-in 63 °C, rests 63 °C/40 min and 78 °C/10 min, boil 60 min
at the default 103 °C, hop alarms at 60 and 15 minutes remaining.
Stop after preview if you only want to test importing. A device upload still
requires explicitly confirming replacement of every recipe slot.

## Upgrade

Install 0.5.0-beta.3, restart HA, update the existing JavaScript-module resource to
`/hbac/hbac-card.js?v=0.5.0-beta.3` and reload the browser. Existing card YAML remains
valid. Use [dashboard/hbac-test.yaml](dashboard/hbac-test.yaml) for a new dashboard.
The Speidel integration and Bridge must include the generic recipe-upload actions
from merged upstream PR #30; merging a PR does not update installed components.
