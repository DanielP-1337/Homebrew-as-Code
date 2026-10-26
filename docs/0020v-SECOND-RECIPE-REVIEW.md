# 0020v — Second Recipe Review & Cross-Recipe Mapping Verification

Baseline: 0020u / commit 17bfbf4. This milestone adds the historical Weizen
Nikolaus source review and an offline backup-review command. The supplied backup
has unresolved water/hop identities and no yeast; no complete canonical recipe
or selectable brew plan can be honestly derived yet.

`recipes/weizen-nikolaus/source-review.yaml` preserves known recipe values and
explicit nulls. It is intentionally not named recipe.yaml and is not a canonical
recipe. No account UUIDs or private reports are committed. Existing import paths
and transport guards are unchanged.

## Review the real backup against saved ingredient mappings

```powershell
$Review = ".local/weizen-nikolaus-review-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_recipe_review `
    --backup '.local/weizenbier38-golden-backup.json' `
    --mapping '.local/myspeidel-ingredient-mapping.json' `
    --output $Review
if ($LASTEXITCODE -ne 0) { throw 'Recipe review failed' }
code $Review
```

The digest-checked backup remains unchanged. An absent mapping file means no
saved mappings are available. Exit 0 means the review artifact was generated,
NOT that the recipe is ready to import. Reports always state upload_ready=false.
The command neither changes the mapping registry nor sends API requests.

Mapping classifications distinguish same-account/category UUID+name reuse,
a matching name with another UUID, new entries, missing names and deleted rows.
A name match does not establish product identity. Alias mappings can be recognized
through their existing UUID/name. This is evidence from the supplied snapshot,
not a live catalog query. No merging or automatic correction takes place.

## Findings and required decisions

- 3.5 kg Weizen, 0.5 kg Muenchner and 0.5 kg Pilsner are recorded.
- First hop: Hallertauer Mittelfrueh, 28 g, 3.2% alpha, 70 min remaining.
- Second hop: 13 g at 15 min; missing name; addition alpha 3.2% vs catalog 9%.
- Water: 20 L mash and 8 L sparge; unnamed catalog reference.
- Yeast and fermentation schedule are absent.
- Malt/recipe colors are zero/null. Confirm actual product colors separately.
- The recorded 101 C boiling setpoint is preserved pending review.
- water_recast=20 L is wort volume, not proof of packaged volume.
- Packaging and other mandatory canonical targets need explicit decisions.

The current backup shares no ingredient UUIDs with the reviewed Lebkuchen backup.
Do not infer that Muenchner means the same product as Munich Malt Type II. RO
water may become a shared reference if explicitly selected and present in a
fresh source backup. The guided workflow still requires full metadata for every
selected ingredient in its chosen backup.

Next: confirm missing values, update source evidence as appropriate, then author
the canonical recipe, independent brew plan and recipe-specific settings. These
remain pending user brewing decisions. The historical source review should stay
unchanged as provenance, distinct from the future canonical recipe.

Tests use synthetic second-recipe data for conflict preservation, missing values,
account isolation and UUID reuse. No network tests or upload are performed.

Commit trailer: `Assisted-by: ChatGPT6-Astra`.

User-confirmed corrections and lot-specific Perle quantity preparation are now
recorded separately in [0020v1](0020v1-CONFIRMED-WEIZEN-REFERENCE.md). The historical
review remains unchanged; see `recipes/weizen-nikolaus/confirmed-draft.yaml`.
