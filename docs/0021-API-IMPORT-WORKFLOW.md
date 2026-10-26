# 0021 — API Import Workflow & Verified Status Documentation

Use this guide to create a new private MySpeidel recipe from a Homebrew-as-Code
recipe and brew plan. It describes the implemented workflow through `33a10fd`,
verified on October 26, 2026. It does not overwrite the existing source recipe.

## Verified outcome

Lebkuchen-Zauber 2026 and Weizen Nikolaus - HBAC API both returned live POST
HTTP 201 and passed GET verification with zero content differences. Their source
recipes remained unchanged. The Weizen result includes fermentation and maturation
and was subsequently visible in the web portal. See the
[evidence and limits](MYSPEIDEL-WRITE-INTEGRATION-STATUS.md).

## Requirements

Run in PowerShell from the repository root, with the project installed in `.venv`.
Use the existing [credential setup](MYSPEIDEL-CONTROLLED-PUT.md) or supported
interactive authentication prompts; never put credentials into commands or files
intended for Git. Keep the inspected OpenAPI JSON at
`.local/vendor/myspeidel-openapi.json`.

You need a valid brew plan, recipe-specific import settings, and a recent GET
backup supplying the intended account, equipment and ingredient references.
A recipe GET contains that recipe's references, not the complete account catalog.
Resolve missing or unnamed ingredients in MySpeidel before using the backup.

## 1. Save a source GET backup

```powershell
$Backup = ".local/myspeidel-upload-source-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_roundtrip_cli backup `
    --output $Backup
if ($LASTEXITCODE -ne 0) { throw 'GET backup failed' }
```

Select the intended source by its displayed name and confirm local backup saving.
This stage reads recipes and writes a local backup; it does not change a recipe
in the Cloud. The source is used for references and policy, not blindly cloned.

## 2. Start the import session offline

Choose the plan and settings together. The following example is for Weizen;
use the corresponding settings for a different recipe:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_guided_import start `
    --plan brew-plans/weizen-nikolaus-brew-001.yaml `
    --backup $Backup `
    --settings examples/myspeidel-weizen-import-settings.json `
    --spec .local/vendor/myspeidel-openapi.json
if ($LASTEXITCODE -ne 0) { throw 'Import session creation failed' }
```

Copy the session directory printed by the command into `$Session`:

```powershell
$Session = Read-Host 'Paste the printed session directory'
code "$Session/settings.json"
code "$Session/policy.json"
```

Review the export name, wort volume, colors and explicit process settings. For
Weizen these include a 101 °C controller setpoint, 20 L export quantity, 12 °P
final target, fermentation in hours and maturation in days. These remain planning
values, separate from measured yield or ambient room temperature.

Review account, equipment, source-derived recipe color, bitterness and specific
gravity in the policy. For the reviewed Weizen case, set `yeast_time` to
`Hauptgärung`. Set `assumptions_accepted` to `true` after review and save.
No HTTP request is made at this stage.

## 3. Prepare and confirm ingredient mappings

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_guided_import resume `
    --session $Session
```

Choose **Prepare candidate (offline)**. Select aliases by name and UUID, then
confirm the full mapping table. Account-scoped mappings are retained for reuse;
stale or renamed references require selection again. The
[Weizen completion guide](0020z-MYSPEIDEL-UPLOAD-COMPLETION.md) lists its mappings.

The candidate gets a new recipe UUID and fresh addition/process-step UUIDs.
Catalog UUIDs are reused. Prepared settings, policy and candidate files are frozen
and hash-checked. Do not edit those files after preparation. If decisions change
before any live attempt, start a new session with the corrected inputs.

## 4. Run the POST dry-run and GET checks

Run the same `resume --session $Session` command again. Select
**Run POST dry-run and GET checks** and confirm at the prompt.

Expected verified result:

- `DRY_RUN_VERIFIED`, HTTP 200 with the expected acknowledgement.
- Source unchanged before and after the request.
- New candidate UUID absent before and after the request.

This stage uses the API, including POST with `dryRun=1`. It does not establish
that the recipe was saved. The successful report is bound to the candidate and
source hashes. Do not proceed to live creation on an unverified result.

## 5. Create once and compare through GET

Resume again, choose **Create new private recipe (REAL POST)**, review the displayed
source and new recipe, and type `CREATE PRIVATE RECIPE` only when you want the
new recipe saved. This is the persistence step.

The expected outcome is `LIVE_CREATE_VERIFIED`, HTTP 201, source unchanged,
candidate present and zero content differences. Metadata differences are reported
separately and require inspection before attributing a cause to them.

The workflow records a live attempt and does not automatically retry POST.
After a live attempt, resume offers GET-only verification when valid receipt
evidence is available. If verification cannot proceed, inspect the existing
session and diagnostics; do not delete attempt markers or start another create
merely to retry an uncertain result.

## 6. Inspect status or verify later

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_guided_import status `
    --session $Session
```

`status` reads local state only. To query the saved recipe again, use `resume`
and choose **Verify saved recipe (GET only)** when offered. This sends GET
requests but does not recreate the recipe.

The Weizen portal listing appeared after a delay even though GET had already
verified persistence. Refresh or check later; do not repeat POST on that basis.
A portal listing is separate evidence from brewing-device synchronization or
execution, which these tests did not verify.

## Troubleshooting and scope

| Observation | Next action |
| --- | --- |
| Missing catalog name or UUID | Obtain a complete, reviewed reference backup; do not invent an identity |
| Export profile ID/version mismatch | Use settings for the selected recipe version |
| Schema errors | Resolve the candidate issue offline before API calls |
| Unverified schema constraints | Review limitations; schema checks alone cannot establish acceptance |
| Source changed since backup | Inspect the change and obtain a fresh backup; do not bypass comparison |
| Dry-run failure | Inspect the masked diagnostics and GET results before correcting inputs |
| Live result uncertain or interrupted | Verify existing candidate UUID; do not blindly retry creation |
| Delayed portal listing after verified GET | Check the listing later; no additional POST |

Diagnostics, backups, registry mappings and session files stay under `.local/`.
The summaries can be published after review; raw account data and credentials
must not be included in commits. This workflow creates recipes; PUT updates,
new catalog ingredients and machine commands are separate capabilities.
