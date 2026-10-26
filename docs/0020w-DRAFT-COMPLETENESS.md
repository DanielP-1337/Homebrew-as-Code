# 0020w — Draft Recipe Completeness & Brew-Plan Promotion

Incremental patch after 0020v1. Weizen Nikolaus is now a linkable domain draft
with variable yield controlled by a 12 Plato target measured after mashing.
No fixed packaged or knockout volume is invented to satisfy a validator.

## Domain versus exchange requirements

`recipes/weizen-nikolaus/recipe.yaml` is a schema-version-2 draft, loaded through
`recipe_completeness.load_draft`. It preserves known ingredients and process
steps, nullable targets, source provenance and explicit measurement context.
The historical source review and previously confirmed draft remain unchanged.

`brew-plans/weizen-nikolaus-brew-001.yaml` links this draft to the independent
Braumeister equipment profile. The plan specifies variable yield and target
12 Plato. Actual measured gravity/volume and final packaged volume remain null
until observed. Equipment capacity does not determine batch yield. Historical
20+8 L water quantities are starting-context evidence, not a fixed output.

The user measures with a hydrometer described as TÜV-calibrated and adjusts to
12 Plato after mashing. This patch records that statement without asserting an
instrument calibration certificate, sample-temperature correction, dilution
formula or evaporation model. Final post-boil OG is not inferred from a
post-mash reading. The historical API's 12 Plato is retained separately as
source evidence. Ambient fermentation temperature stays separate from beer
measurement/control. No RO water chemistry is inherited.

Schema-version-1 validation and its fixed-volume plan behavior remain unchanged.
Older exporters still use the v1 loader and reject v2 with a version error;
they are not silently fed nullable values. The brew-plan loader supports v2
explicitly, so the guided plan chooser can now display Weizen Nikolaus.
Schema 2 currently permits draft status only. This is promotion to a linkable
DRAFT plan, not approval of a completed or upload-ready brew plan.

## Check completeness offline

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.recipe_completeness
```

Output separates domain validity, plan linkage, optional unknown targets and
MySpeidel mapping blockers. Missing ABV, IBU and packaged-volume targets do not
invalidate this variable-yield draft. Current MySpeidel conversion still needs:

- Confirmed export boiling temperature (historical controller setpoint 101 C is separate).
- Explicit final OG for the external field, not inferred from the after-mash reading.
- Explicit batch/export wort volume; no equipment-size or packaged-volume fallback.
- Malt colors supplied in the per-import settings.

Optional `--settings <file.json>` checks explicit exchange settings. The report
always keeps upload_ready=false because catalog, policy, schema and live checks
remain separate. Exit 0 means a valid assessment, not permission to upload.

The 0020q builder now explicitly handles v2 through this assessment; it reports
missing mapping requirements before attempting conversion. Nullable ABV/IBU and
packaging are retained as unmapped information. Ambient fermentation and gravity
control context are retained in the report. No step automatically converts the
7 g yeast recommendation into a variable-volume dosing algorithm or applies hop
lot adjustments. Reference hop quantities remain reference quantities.

The guided prepare step uses the same check before ingredient mapping. Old
sessions stay immutable; they are not migrated or rewritten. Start a new session
to use the new recipe version. Its source GET backup must still contain valid,
complete names and metadata for the chosen ingredients; this patch does not
repair the historical unnamed water/Perle references or missing yeast catalog.

## Validation

Tests cover selection of the new plan, variable yield without invented targets,
nonfinite/invalid gravity, fixed-yield conflicts, unchanged legacy validation,
nonmutating completeness checks and contextual export blocking. All checks are
offline; no API calls or recipe changes occur.

Commit trailer: `Assisted-by: ChatGPT6-Astra`.

## Record actual brew-day measurements

See [0020x — Brew-Day Measurements & Actual Yield](0020x-BREW-DAY-MEASUREMENTS.md)
for separate batch observations, actual quantities and yearly production subtotals.
