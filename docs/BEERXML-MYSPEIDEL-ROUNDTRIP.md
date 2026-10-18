# BeerXML 1.0: manual MySpeidel import roundtrip

The MySpeidel website advertises import of **BeerXML** or native `.recipe` files, **not BeerJSON**. This exporter never logs in, uploads, or edits a cloud recipe.

## Phase 1 — export an incomplete draft

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.beerxml_cli recipes/lebkuchen-zauber/recipe.yaml --output .local/lebkuchen-draft.xml
```

Read `.local/lebkuchen-draft.report.json`. The XML draft is **not import-ready**: the repository does not know brewer name, **fermenter** batch size (20 L is packaged volume), pre-boil volume, brewhouse efficiency, grain color/yield, or yeast type/form. Never fabricate these values merely to satisfy the format.

## Phase 2 — add confirmed local parameters

Create `.local/beerxml-parameters.yaml` (never commit it):

```yaml
brewer: "<your preferred display name>"
batch_size_l: null        # measured/planned volume into the fermenter
boil_size_l: null         # measured/planned pre-boil volume
efficiency_percent: null  # measured brewhouse efficiency
malts:
  Pale Ale Malt: {yield_percent: null, color_srm: null}
  Munich Malt Type II: {yield_percent: null, color_srm: null}
  CaraMunich II: {yield_percent: null, color_srm: null}
  Melanoidin Malt: {yield_percent: null, color_srm: null}
  Chocolate Malt: {yield_percent: null, color_srm: null}
honey: {yield_percent: null, color_srm: null}
yeast: {type: Ale, form: Dry} # verify against the actual product
```

Replace all `null` placeholders with verified brewing inputs. **Do not use the synthetic values from automated tests.**

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.beerxml_cli `
    recipes/lebkuchen-zauber/recipe.yaml `
    --parameters .local/beerxml-parameters.yaml `
    --output .local/lebkuchen-import-test.xml
```

Open the resulting `.report.json` and review losses. `import_candidate: true` means the exporter's checked required fields are present; it **does not mean MySpeidel will accept the file or preserve all semantics**.

## Phase 3 — manual browser import and GET comparison

1. **Back up/export any important existing recipes first.** In the MySpeidel browser, use *Rezept importieren* → the new XML file. Keep it private; do not overwrite an existing recipe.
2. Open the newly imported recipe and verify name, 5 grains, hop at 60 min, honey at 10 min, 5 spices at 5 min, mash rests 63/72/78 C, boil time 60 min and yeast. BeerXML does **not** reliably encode honey's exact boil-addition moment, so the exporter records it as a note. Correct manually if necessary.
3. Run `python -m homebrew_as_code.myspeidel_roundtrip_cli`, enable names, select **the newly imported recipe**, enter verified WEB boil time and hop step times. Compare the GET report with the editor. Never assume recipe list order is fixed.
4. Report differences and preserve the local output files; **do not publish private MySpeidel HTML, identifiers or raw API responses**.

### Known losses

BeerXML v1 cannot faithfully model all local brewing details here. RO-water ion profile/salts, mash/sparge water amounts, pH targets, post-flameout spice contact, fermentation temperature range and keg settings require manual review. The converter stores honey timing in its fermentable NOTES because BeerXML FERMENTABLE does not have a generic precise boil timing field. Miscs are exported as `Spice`, hop as `HOP`, and honey as `Sugar` fermentable; MySpeidel may map them differently in its proprietary API.
