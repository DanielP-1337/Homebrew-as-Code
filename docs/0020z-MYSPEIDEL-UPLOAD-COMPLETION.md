# 0020z — MySpeidel Upload Candidate Completion

Complete the existing guided import path for Weizen Nikolaus. The patch supplies
explicit exchange settings, maps fermentation and maturation, and gives new
process steps fresh identities. It reuses the established POST dry-run, live
creation and GET comparison implementations. No network operation runs when the
patch is applied or the candidate is prepared.

## Confirmed exchange settings

`examples/myspeidel-weizen-import-settings.json` is bound to recipe ID
`weizen-nikolaus`, version `0.3.0`. It contains:

| Export field | Value / interpretation |
| --- | --- |
| New recipe name | Weizen Nikolaus - HBAC API |
| Wort volume | 20 L export planning value; not measured or fixed packaged yield |
| Final original-gravity target | 12 °P, separate from after-mash adjustment |
| Boil controller setpoint | 101 °C, not a physical boiling-point measurement |
| Malt addition colors | Weizen 4, Muenchner 15, Pilsner 2 EBC |
| Fermentation | 22 °C, 168 hours |
| Maturation | 7 °C, 21 days, 1.6 bar |

The phase duration units were checked against the user's MySpeidel web form and
GET export: fermentation hours, maturation days. The settings do not silently
turn the canonical ambient-room observation of 21.5 °C into a measured beer
temperature. They describe the desired Cloud recipe. All source recipe and
brew-plan files remain unchanged.

Colors come from the reviewed recipe additions; null catalog colors remain null.
Perle retains 13 g at 5.2% for 15 minutes remaining. Its catalog alpha of 9% is
preserved as catalog metadata and never overrides the recipe addition. No lot
adjustment or IBU recalculation is performed by this patch.

## Start a new import session

Use the latest reviewed backup, not an earlier snapshot with unnamed references.
From the repository root:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_guided_import start `
    --plan brew-plans/weizen-nikolaus-brew-001.yaml `
    --backup .local/weizen-upload-source-20261026-153341.json `
    --settings examples/myspeidel-weizen-import-settings.json `
    --spec .local/vendor/myspeidel-openapi.json
```

Use the session directory printed by the command:

```powershell
$Session = '.local/myspeidel-imports/REPLACE-WITH-PRINTED-SESSION'
code "$Session/settings.json"
code "$Session/policy.json"
```

In the policy, review the source-derived account/equipment and top-level values.
The latest reviewed source has recipe color 5, bitterness 14.8 and specific
gravity 1.048. These are source metadata, not independently calculated results.
Set `yeast_time` to `Hauptgärung`. After reviewing the actual policy, set
`assumptions_accepted` to `true`. That authorizes offline preparation, not a POST.
Adjust `export_name` in settings before preparation if a different new name is
wanted. The source recipe remains separate and is not overwritten.

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_guided_import resume `
    --session $Session
```

Select **Prepare candidate (offline)**. The resolver reuses valid saved mappings
or asks for an explicit selection. Confirm these aliases using the displayed
names and UUIDs; do not rely on a particular menu number:

| Recipe name | Reviewed Cloud catalog name |
| --- | --- |
| Münchener Leitungswasser | Leitungswasser mittelhart |
| Weizen | Weizen Malz |
| Muenchner | Muenchner |
| Pilsner | Pilsener |
| Hallertauer Mittelfrüh | Hallertauer Mittelfrüh |
| Perle | Perle |
| Zymoferm GERMAN WHEAT | GERMAN WHEAT Trockenhefe og |

The mapping is account-scoped and persisted only after confirmation. Catalog
objects are reused unchanged. The new recipe, additions, fermentation steps and
maturation steps all receive new UUIDs and explicit creation metadata. Process
step UUIDs participate in duplicate and source-identity collision checks.

## Continue to the API check

Resume the same session again and select **Run POST dry-run and GET checks**.
Use the existing confirmations. This is the first network stage: GET checks,
POST with `dryRun=1`, and subsequent GET verification. Inspect its outcome before
selecting live creation on a later resume. A successful schema check alone is
not proof of acceptance or persistence. Live creation retains its existing
explicit confirmation and subsequent GET comparison; no automatic POST retries
are introduced.

Prepared session inputs are frozen. Do not edit settings or policy after
preparation; start a new session if an export decision changes. Keep all private
backups, session data, candidates and diagnostics under `.local/`.

## Validation

Synthetic tests cover profile binding, explicit duration units, invalid numeric
values, alias preservation, nonmutation of domain data, addition colors,
reference alpha separation, fresh process-step identities and preflight collision
checks. The actual supplied GET export and local OpenAPI document were also used
for an offline integration check; neither is included as a public test fixture.
