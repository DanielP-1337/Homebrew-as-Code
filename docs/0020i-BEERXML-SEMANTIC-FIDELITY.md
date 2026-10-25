# 0020i — BeerXML Semantic Fidelity & MySpeidel Roundtrip

## Evidence and scope

A locally generated Homebrew-as-Code BeerXML export successfully reached the
MySpeidel ingredient matching dialog and was saved into the user's recipe list
on 2026-10-25. The original 0020h export SHA-256 was
`78841ca35d4d175c2f315488aef2c273f758e538e9f14a8237451f1faa5094b3`.

Observed in MySpeidel: mash rests 63 C/20 min, 72 C/45 min, 78 C/10 min;
mash-in displayed 63 C versus YAML 60 C; UI original gravity initially 0 Plato;
UI IBU 31.5 versus YAML target 21; UI color 32.2 EBC with assumed malt colors.
These are observations, not claims of a verified lossless roundtrip.

## Features

- Optional `--emit-target-og`: calculate BeerXML `OG` (SG) from the canonical
  *target* Plato using a standard conversion approximation. BeerXML `OG` has no
  universally distinguished target-vs-measured semantic, so enabling this is a
  deliberately labelled MySpeidel interoperability experiment. Verify in UI.
- Optional `--fermentation-days` and `--fermentation-temp-c`: both must be supplied.
  The temperature must be within the YAML 18–20 C range. There is no inferred
  fermentation duration; the Brewfather sample's 14 days are **not reused**.
- `beerxml_myspeidel_compare` accepts manually recorded, numeric, private UI
  observations and emits a conservative field comparison. Missing observations
  remain `NOT_OBSERVED`; IBU/color/mash-in remain explicitly unverified.
- No `BF_*`, no cloud writes, no automated catalog merge.

## New export example (PowerShell)

From the project root, re-use previously declared experimental properties:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.beerxml_v1 `
  --recipe recipes/lebkuchen-zauber/recipe.yaml `
  --properties-json .local/beerxml-properties.json `
  --boil-size-liters 24 --efficiency-percent 70 `
  --emit-target-og `
  --name 'Lebkuchen-Zauber 2026 - HBAC 0020i TEST' `
  --xml .local/lebkuchen-zauber-0020i-test.xml `
  --report .local/lebkuchen-zauber-0020i-report.json
```

The OG will be roughly 1.057 SG for a target of 14 Plato. **Do not interpret this
as an actual measured gravity.** To test fermentation schedule only after agreeing
on trial assumptions, add both `--fermentation-days N --fermentation-temp-c 19`.

## Manual comparison

Put only observed UI values in `.local/0020i-myspeidel-observations.json`:

```json
{
  "batch_size_l": 20,
  "boil_duration_min": 60,
  "mash_in_c": 63,
  "og_sg": 1.057,
  "bitterness_ibu": 31.5,
  "color_ebc": 32.2,
  "yeast_amount_g": 11.5
}
```

Replace these illustrative values with actual observations from the **0020i** import;
do not silently reuse observations from 0020h. Then:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.beerxml_myspeidel_compare `
  --xml .local/lebkuchen-zauber-0020i-test.xml `
  --observations-json .local/0020i-myspeidel-observations.json `
  --report .local/0020i-semantic-comparison.json
```

## On IBU and recirculation

MySpeidel appears to calculate IBU based on its recipe parameters rather than
simply copying a supplied target: Brewfather listed 19.8 IBU while MySpeidel
showed 12.2, and the 0020h YAML target 21 resulted in 31.5 displayed IBU.
The specific MySpeidel algorithm is **not** established. A Braumeister pump
recirculates wort through the malt pipe during *mashing*; the degree to which
machine geometry, boil utilization, or circulation affects bittering needs
independent evidence. Do not claim pump-based IBU calculation or compensate
alpha-acid additions without verified boil conditions and brewing measurements.

## Safety

Source YAML, previous 0020h export, and private assumptions are unchanged.
The XML contains trial assumptions; never use it as a brew-day recipe without
independently reviewing water, grain properties, bitterness, gravity, yeast,
fermentation, equipment and ingredient mappings.

## Confirmed import milestone (2026-10-25)

See [0020i MySpeidel web-import milestone](0020i-MYSPEIDEL-WEB-IMPORT-MILESTONE.md)
for observed editor results, Brewfather attribution, quantitative caveats and remaining
semantic differences. The 0020i UI showed 14 °P and 19.0 IBU; the example
comparison JSON earlier in this document is illustrative, not a measurement.
