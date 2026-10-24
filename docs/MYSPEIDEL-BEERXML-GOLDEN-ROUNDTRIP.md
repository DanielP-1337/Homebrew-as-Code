# MySpeidel BeerXML Golden Roundtrip (0020d)

**Experimental, offline, partial export. No HTTP; no private data in Git.**

Input: an existing private 20 L MySpeidel PUT-backup v1 under `.local/`.
Output: a new BeerXML `.xml` file and local JSON report. No overwrites.

## Export

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_beerxml_roundtrip export `
  --backup .local/weizen38-duplicate-backup.json `
  --xml .local/weizen38-roundtrip.xml `
  --report .local/weizen38-beerxml-export-report.json `
  --name 'HBAC BeerXML Roundtrip - Weizen 38' `
  --batch-size-liters 20 `
  --boil-size-liters 23 `
  --assumed-malt-yield-percent 75
```

**The three values at the end are explicit experimental inputs, NOT verified vendor values.** Verify batch size, pre-boil volume, malt yield and color units manually against the MySpeidel editor before import. This exporter interprets malt quantities as kg and hop quantities as grams using the previously observed web/cloud examples. Hop step timing is used only if explicitly present as `duration` or `hopping_duration`; otherwise the export FAILS rather than assigning a guessed schedule. BeerXML hop amount is kilograms.

The export deliberately labels itself `PARTIAL_EXPORT`: mash rests, water, yeast, fermentation, maturation, equipment and proprietary settings are **not** preserved. Review the XML and the JSON report; do **not** brew from the exported recipe without checking these fields. Source and XML hashes are recorded in the report.

## Manual MySpeidel validation

1. Keep the original private recipe intact.
2. Review the generated XML locally. If export refuses due to unknown hop timing or missing names, inspect the backup schema and extend the mapping with tests; do not invent values.
3. Navigate to MySpeidel's **Rezept hochladen**, upload the new `.xml`, inspect the preview/merge workflow and only confirm creation of a clearly named disposable private test recipe.
4. Fetch that *new* private recipe using the existing read-only backup CLI, to `.local/weizen38-reimported-backup.json`. It must have a **different** recipe UUID.
5. Compare the two backups:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_beerxml_roundtrip compare `
  --original .local/weizen38-duplicate-backup.json `
  --imported .local/weizen38-reimported-backup.json `
  --report .local/weizen38-roundtrip-compare.json
```

The comparison checks only original vs imported malt names+amounts, hop names+amounts+acid, and boiling duration. It does NOT equate UUIDs or merge ingredient identities. It explicitly reports water, mash schedule, yeast, fermentation and equipment as `unverified`. `EQUIVALENT_FOR_CHECKED_FIELDS` is **not** a lossless or authoritative verdict. Differences may reflect vendor transformations, so interpret them manually.

**Security:** `.local` must remain excluded from Git. Never upload backups, session cookies, bearer tokens, proprietary raw bodies or HTTP headers into the public repository. Offline tests require no accounts or secrets.

## Missing malt color – evidence-based override (0020d1)

MySpeidel Cloud can omit `references.malts[uuid].color` while the browser
recipe editor sends an EBC color. Supply a **0-based mash malt index** only
when the corresponding color has been confirmed in a captured web form:

```powershell
  --malt-color-override 3=24
```

For the observed private Weizenbier 38° duplicate, index 3 corresponds to
Carahell (web malt_id `1007`, web malt_color `24`). The command adds an explicit
local source entry to `malt_color_overrides` in the export report. If Cloud
already supplies a color, the override is refused. No global catalog identity
or Web-ID ↔ UUID equivalence is inferred.

## 0020d2: explicit mash rests and cautious yeast metadata

The exporter can now include mash temperature rests from the captured web form:

```powershell
  --mash-in-temp 38 --mash-step 62:30 --mash-step 72:40 --mash-step 78:10
```

These are *manual web-form observations*, not discovered Cloud schema fields. They
are recorded in `mash_steps` and `mash_schedule_source` in the private report.
Unknown rest fields or infusion volumes are **not** inferred. BeerXML 1.0 does
not preserve MySpeidel's distinct mash-water / sparge-water program, and these
remain unsupported. A recipe with unrepresented water or fermentation settings
continues to have `PARTIAL_EXPORT` status.

The Cloud yeast reference name may be emitted if the user explicitly supplies
all of `--yeast-type Wheat`, `--yeast-form Dry`, and `--yeast-amount-kg 0.015` (or other supported BeerXML 1.0
enumerations). Do not use these flags without verifying the actual yeast type
and form. The yeast mass must be independently verified in kilograms because MySpeidel amount units are not verified as BeerXML kilograms. A report of one yeast is not a guarantee of
complete fermentation reproduction. No HTTP calls, private backup overwrite,
or authoritative identity mappings are introduced.
