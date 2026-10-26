# 0020v1 — Confirmed Weizen Reference & Batch Hop Adjustment

Incremental patch on top of the already applied 0020v review patch. Historical
source-review.yaml remains unchanged. confirmed-draft.yaml records subsequent
user corrections separately; it is not a canonical schema-version-1 recipe yet.

Confirmed: Perle 13 g at 5.2% alpha, 15 minutes remaining; Zymoferm GERMAN WHEAT,
one 7 g pack; unfiltered Munich tap water for which the recipe was designed;
fermentation at approximately 21.5 C ambient. Ambient temperature is not beer
setpoint/measurement. Manufacturer ranges and attenuation are stored as
user-supplied product information, not measured fermentation outcomes.

The first Hallertauer addition remains the historical 28 g at 3.2%, 70 minutes
remaining. Perle's old unnamed 3.2%/9% conflict is superseded for the NEW draft by
the confirmed original reference of 5.2%. Historical 13.3 IBU is retained only as
historical evidence, not a recalculated target. Water treatment/salt quantities
are unspecified; no RO salts are copied.

## Batch quantity

Keep reference quantities in the recipe. Write a separate local batch adjustment
with a concrete alpha value from the selected hop lot:

```powershell
# Example calculation for a 6.5% lot, not an assertion about your actual lot.
$Adjustment = ".local/weizen-perle-adjustment-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
.\.venv\Scripts\python.exe -m homebrew_as_code.hop_batch_adjustment `
    --batch-alpha 6.5 --output $Adjustment
if ($LASTEXITCODE -ne 0) { throw 'Hop adjustment failed' }
```

Formula: reference grams * reference alpha / batch alpha. Thus 13 g * 5.2 / 6.5
= 10.4 g, or approximately 9.521 g at 7.1%. No midpoint of a range is chosen.
The JSON retains the unrounded result, recipe hash/version, addition ID and
unchanged timing. This conserves nominal alpha-acid mass; it does not calculate
IBU or account for utilization, storage degradation or hop-form changes.
The adjustment is not automatically consumed by the MySpeidel payload builder.

## Remaining boundary

A complete selectable brew plan still needs confirmed packaged volume, mandatory
canonical ABV/IBU targets, packaging, malt colors and boil-temperature intent.
The current v1 canonical validator requires values for some of these fields.
It is not loosened and no invented defaults are supplied merely to pass it.
Actual MySpeidel references for the corrected water, Perle and yeast must also
be available in the chosen GET backup before guided import. Editing the historical
backup and recalculating its hash is not a substitute for fresh source evidence.

The older offline recipe-review command still reports the historical backup's
issues; it intentionally does not silently overlay these corrections. The new
draft is the explicit corrected intent, pending promotion to canonical format.

Commit trailer: `Assisted-by: ChatGPT6-Astra`.
