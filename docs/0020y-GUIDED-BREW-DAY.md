# 0020y — Guided Brew-Day Recording

A local interactive workflow for selecting a recipe by name, recording brew-day
observations, and resuming a batch without editing JSON by hand. It uses the
0020x record format and validation. No API requests, recipe edits, import
promotion, or tax filing are performed.

## Start

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.guided_brew_day start
```

Choose a valid recipe/brew plan by its displayed recipe name, plan ID and equipment
model. Then explicitly choose **TEST** or **REAL**, enter the brew date, and confirm.
Enter at a selection menu cancels; there is no implicit choice of a real batch.
The resulting file is under `.local/brew-days/`, with a unique batch ID and the
recipe's display name. Initial measurements and yields remain unknown.

For a practice session, select TEST. Synthetic observations may then be entered
without contributing to annual production. TEST is a workflow classification,
not a claim that a brew actually occurred.

## Continue

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.guided_brew_day resume
```

The selection shows recipe name, brew date, TEST/REAL classification and batch ID.
Records created before this patch fall back to their recipe ID if no name was
stored. Alternatively, target a specific local record:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.guided_brew_day resume `
    --record '.local/brew-days/DATE-BATCH-ID.json'
```

Each invocation performs one selected action:

1. **Add measurement:** select a process stage, enter timestamp, instrument,
   hydrometer readings, sample temperature, optional corrected reading and its
   correction method, optional measured volume and its temperature, and a note.
2. **Record / replace actual yield:** shows existing values, then requests a
   complete replacement of produced beer, packaged beer, production date and note.
   Blank quantities mean unknown, not "retain the previous value".
3. **Show report:** read-only view of observations, yield and missing stages.
4. **Classify legacy record:** explicitly assign TEST or REAL to an older record
   which has no classification. Existing TEST/REAL classification is fixed in
   the guided workflow. Create a fresh real batch when moving on from practice.

Use a decimal comma or point. Blank numeric entries remain unknown; zero is a
real value. The measurement timestamp includes its UTC offset, for example
`2026-11-01T12:00:00+01:00`; its default is the current local time. An example date
is not an instruction to backdate a real measurement.

Type `cancel` at any prompt, or use Ctrl+C, to leave before saving. The proposed
record is validated and displayed before the final `yes` confirmation. Invalid timestamps, numeric ranges and required measurement temperatures are
re-prompted immediately, retaining earlier answers. Final record validation still
runs before saving; an unexpected record-level error stops without changing the file. Measurements are appended, not silently replaced. Correction of an
already saved observation remains outside this guided menu.

No automatic temperature correction, original-gravity selection, ABV estimate,
efficiency calculation, or inference of fermentation completion is performed.

## Persistence and concurrent changes

Each edit verifies that the selected record has not changed in the meantime.
A per-file exclusive lock coordinates guided writers. The previous bytes are
saved under `.local/brew-days/.history/` before an atomic replacement. Identity
fields and an established TEST/REAL classification cannot be changed by this
workflow. Backups are outside the normal top-level batch selection.

After a crash, a `.json.lock` file can remain. Check that no other recorder is
running before manually removing that exact lock. The workflow never removes
another writer's existing lock. A plain-text editor does not participate in this
lock protocol; avoid editing the same file concurrently. Local history is not a
tamper-proof audit log or a substitute for external backups.

## Annual production

```powershell
$Records = @(Get-ChildItem '.local/brew-days/*.json' -File |
    Select-Object -ExpandProperty FullName)
if ($Records.Count -eq 0) { throw 'No batch records found' }
.\.venv\Scripts\python.exe -m homebrew_as_code.brew_day year `
    --year 2026 --records $Records
```

Only explicitly REAL records contribute actual production quantities:

- `excluded_test_batches` lists excluded TEST records.
- `unclassified_batches` lists older records needing explicit classification.
- `unresolved_batches` lists REAL records with missing production dates or
  quantities relevant to the requested year.

These are known subtotals of supplied records, not a certificate of completeness
or tax compliance. Duplicate batch IDs still fail instead of double-counting.

The low-level `brew_day init` command now defaults to TEST. Pass `--kind real`
explicitly for a real batch, or `--kind test` for practice. The Python
`new_record` helper retains its previous default for existing callers; the guided
workflow always supplies an explicit classification.

## Validation

Regression tests exercise test exclusion, legacy classification, actual-only
annual totals, clear-name selection, decimal input, cancellation, measurement
and yield persistence, byte-preserving history, stale-read protection, locks,
failed atomic replacement and fixed batch identity.

Input validation details: [0020y1 — Immediate Input Validation](0020y1-IMMEDIATE-INPUT-VALIDATION.md).
