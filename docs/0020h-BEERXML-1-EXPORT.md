# 0020h — Independent BeerXML 1.0 export (experimental)

Homebrew-as-Code exports its own canonical `recipe.yaml` to BeerXML 1.0.
This uses the public BeerXML field semantics, **not** Brewfather's file contents,
`BF_ID`, other proprietary extensions, or an undocumented MySpeidel API.

Reference: <https://www.beerxml.com/beerxml.htm>.

## Important limitations

- The module includes a **focused structural/semantic validator**, **not** a full BeerXML XSD or independent spec conformance suite. `STRUCTURALLY_VALIDATED_NOT_IMPORT_VERIFIED` does not mean MySpeidel accepts the XML.
- This exporter currently targets the *Lebkuchen-Zauber* schema and known ingredients. Do not use it for arbitrary recipes without extending and testing the ingredient classification.
- `BOIL_SIZE`, actual brewhouse `EFFICIENCY`, five malt yields/colors and honey yield/color are **not in the canonical YAML**. They must be supplied explicitly. **Do not copy values from Brewfather's Sample Blonde Ale.**
- The recipe's `packaged_volume_l` is used for BeerXML `BATCH_SIZE` as a documented approximation; loss from end of boil to package is not known.
- STYLE is a **user-defined custom classification**, not a verified BJCP category. MySpeidel may require additional style metadata; this remains to be tested.
- Hop use is encoded as `Boil`; spices in `MISCS` with `TYPE=Spice`, honey as `FERMENTABLE` with `TYPE=Sugar`, 11.5 g dry yeast as 0.0115 kg. Honey timing, salt additions, 23/5 L mash/sparge split and fermentation temperature range are preserved in NOTES because BeerXML 1.0 does not express all details equivalently.
- `GRAIN_TEMP` means **grain temperature**; it is omitted unless independently measured/declared. Mash-in water temperature stays in NOTES. `MASH_STEPS` represent rests.
- No raw Brewfather sample, account data, tokens or proprietary IDs are included.
- The web import workflow requires **manual ingredient matching and inspection before saving**. The confirmed Brewfather import does **not** establish this export's MySpeidel compatibility.

## Usage (PowerShell 7, Windows)

Prepare a local JSON at `.local/beerxml-properties.json`, entering verified or **clearly marked assumed** properties for *your actual grain products*:

```json
{
  "malt_specs": {
    "0": {"yield_percent": null, "color_lovibond": null},
    "1": {"yield_percent": null, "color_lovibond": null},
    "2": {"yield_percent": null, "color_lovibond": null},
    "3": {"yield_percent": null, "color_lovibond": null},
    "4": {"yield_percent": null, "color_lovibond": null}
  },
  "honey_yield_percent": null,
  "honey_color_lovibond": null
}
```

Do not run until all null values are replaced with explicitly researched or declared assumptions; BeerXML `COLOR` is in °Lovibond, **not EBC**. Before export, determine actual **pre-boil** volume and explicitly select an efficiency assumption if not yet measured.

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.beerxml_v1 `
  --recipe recipes/lebkuchen-zauber/recipe.yaml `
  --properties-json .local/beerxml-properties.json `
  --boil-size-liters <ACTUAL_OR_EXPLICITLY_ASSUMED_PREBOIL_L> `
  --efficiency-percent <MEASURED_OR_EXPLICITLY_ASSUMED_PERCENT> `
  --xml .local/lebkuchen-zauber-0020h.xml `
  --report .local/lebkuchen-zauber-0020h-report.json
```

The CLI refuses to overwrite either output. Review generated `NOTES`, `MISCS`, `FERMENTABLES`, `YEASTS`, mash rests, report, and all MySpeidel editor values before saving.

## Next steps

1. Record the vendor-backed actual malt yields and colors, honey data, pre-boil volume and brewhouse efficiency assumptions in a private provenance record.
2. Perform a controlled manual MySpeidel upload, inspect field-by-field, and record whether it reached the matching screen, editor, and persisted list.
3. Separate any MySpeidel-specific compatibility adaptations from the BeerXML core. Do not add `BF_*` or silently fabricate required data.
