# 0020x — Brew-Day Measurements & Actual Yield

A recipe describes intent; a batch record stores observations. This offline CLI
creates one editable JSON record per real brew day, linked to the recipe version
and brew plan. It never changes the recipe, promotes an import candidate, contacts
MySpeidel, or writes a tax declaration. Files remain under `.local/`.

## Start a batch

Run from the repository root. Use the actual brew date; do not create a real
production entry merely to try the workflow.

```powershell
$Batch = '.local/brew-days/weizen-2026-11-01.json'
.\.venv\Scripts\python.exe -m homebrew_as_code.brew_day init `
    --plan brew-plans/weizen-nikolaus-brew-001.yaml `
    --date 2026-11-01 --kind real --output $Batch
code $Batch
```

The date above is an example. A new UUID identifies each batch. Existing files
are never overwritten by `init`. The source hash identifies the loaded plan,
recipe and equipment bundle at initialization; it is provenance, not a signature
or a guarantee that a manually edited record is unchanged.

## Record measurements

Add objects to `measurements`. This is a synthetic example, not a measured result:

```json
{
  "stage": "pre_boil_after_adjustment",
  "measured_at": "2026-11-01T12:00:00+01:00",
  "instrument": "7-14 Plato hydrometer",
  "raw_plato": 12.0,
  "sample_temperature_c": 20.0,
  "corrected_plato": 12.0,
  "correction_method": "At instrument reference temperature",
  "volume_l": null,
  "volume_temperature_c": null
}
```

| Stage | Meaning |
| --- | --- |
| `pre_boil_before_adjustment` | Reading before adjusting the pre-boil wort. |
| `pre_boil_after_adjustment` | Reading after adjustment; the Weizen plan aims for 12 °P here. |
| `post_boil` | Actual post-boil original-gravity observation, including any documented final adjustment. |
| `fermentation` | Apparent-extract observation during fermentation, not original gravity. |

Each observation requires an instrument and a timestamp with timezone. Repeated
observations at different times are allowed. Describe dilution, sampling or other
context in an optional `note`. The report retains all observations and does not
silently select the latest as a final result. It does not infer fermentation
completion from a single reading or elapsed time.

Record the sample temperature for extract readings. If entering a corrected
reading, describe the instrument scale or method used. The software performs no
automatic temperature correction. Volume temperature is a separate field: cooling
a hydrometer sample does not establish the temperature of the entire wort volume.
Raw readings can be stored without a corrected value. Unknown values remain null.

No efficiency or ABV calculation is implemented in this patch. Extract alone is
not an efficiency measurement; volume and the applicable material basis would
also be needed. Fermentation readings are retained for later calculation without
pretending they are a direct alcohol measurement.

## Actual yield and yearly totals

`actual_yield.produced_beer_l` is the explicitly recorded actual beer quantity;
`packaged_beer_l` is separate and may be lower because of losses. Neither is
inferred from equipment size, pre-boil wort volume, or a recipe target. Enter a
`production_date` explicitly with a produced quantity; year boundaries do not
silently inherit the brew date. `actual_yield.note` can document the measurement
basis. This is a personal production log, not a legal classification of when a
tax liability arises or which volume is legally decisive.

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.brew_day report --record $Batch

$Records = @(Get-ChildItem '.local/brew-days/*.json' -File |
    Select-Object -ExpandProperty FullName)
if ($Records.Count -eq 0) { throw 'No batch records found' }
.\.venv\Scripts\python.exe -m homebrew_as_code.brew_day year `
    --year 2026 --records $Records
```

The year report covers only the supplied records. Duplicate batch IDs are rejected
instead of being counted twice. Unknown production dates remain unresolved;
known dates in the selected year with missing quantities remain unresolved too.
The reported total is a known subtotal, not proof that the year's log is complete.
Packaging is never added to production, and zero is distinct from unknown.

Older advance declarations could contain planned quantities and a reference
strength. Such planning figures do not become actual batch observations. This
workflow does not normalize production to 12 °P, hard-code a historical annual
allowance, calculate tax, or determine an exemption. Legal rules belong to the
separate [legal reference](LEGAL-DE.md), not to measurement data.

## Validation

Tests cover separation of process stages, unknown values, finite numeric inputs,
measurement temperatures, timezone-aware timestamps, duplicate observations and
batch IDs, explicit year assignment, actual-versus-packaged quantities, and
exclusive local record creation without changing the plan.

## Guided recording and test batches

[0020y — Guided Brew-Day Recording](0020y-GUIDED-BREW-DAY.md) adds interactive
selection and entry. TEST records are excluded from production totals; legacy
records without a classification are listed separately until explicitly classified.
The low-level init command defaults to TEST; the real-batch example above uses
`--kind real` explicitly.
