# 0020r — MySpeidel POST Candidate & Catalog Identity Reuse

Requires 0020q. Offline preparation only. No HTTP client, authentication, POST,
PUT, or automatic upload is added. A successful command means a local artifact
was written, not that the API accepted it.

## Identity policy

A new recipe and each malt/hop/misc/yeast addition receive new UUIDv4 identities.
Existing catalog UUIDs are retained. Full reference objects are hydrated from a
digest-checked GET backup, matched by category, UUID and name, without modifying
them. A backup must contain every selected reference. Missing references stop
preparation; no catalog entries are invented or merged by name.

The local policy explicitly supplies owner, brewer, equipment, description,
comments, bitterness, color, specific gravity, country and schema version.
`policy` seeds these from the backup for review; these values are NOT correct
by default for another recipe. Edit every relevant field before building.
Recipe/addition content version 1, addition schema version 2, empty yeast time,
null parent and current UTC timestamps are experimental initial values. The
schema suffix `recipe_v5` does NOT imply `schema_version=5`.

Set `assumptions_accepted` to true only after reviewing this offline policy.
This flag acknowledges test assumptions; it does not grant permission to upload.
The candidate records source, policy and draft hashes and retains the complete
0020q report, including unmapped values. Historical blockers in `source_report`
describe the original draft, not the hydrated candidate.

Generated IDs are saved in the candidate. Reuse that artifact when inspecting
it; rebuilding intentionally produces a different candidate with different IDs.
Do not feed this wrapper into older backup-based upload tools.

## Optional duplicate-name selection

For ambiguous normalized names, display all candidates with clear names and
UUIDs and retain the selected existing identity. Unique matches are retained
without prompting. Enter cancels without writing. This is local selection, not
a server matching API. Missing names still fail in the 0020q builder. Fuzzy
matching, alias inference and catalog synchronization are not implemented.

```powershell
python -m homebrew_as_code.myspeidel_create_candidate select `
  --template '.local/myspeidel-template-20261025-221228.json' `
  --output '.local/myspeidel-template-selected.json'
```

Use the selected template with the existing 0020q `build` command if needed.

## Prepare and review policy

```powershell
$Backup = '.local/myspeidel-get-abgleich-20261025-220241.json'
$Draft = '.local/myspeidel-import-draft-20261025-221228.json'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Policy = ".local/myspeidel-create-policy-$Stamp.json"
$Candidate = ".local/myspeidel-create-candidate-$Stamp.json"
$Spec = '.local/0020o/myspeidel-openapi.json' # adjust to your saved specification
python -m homebrew_as_code.myspeidel_create_candidate policy `
  --backup $Backup --output $Policy
if ($LASTEXITCODE -ne 0) { throw 'Policy preparation failed' }
```

Open `$Policy`, review the recipe-specific fields and account/equipment objects,
and explicitly set `assumptions_accepted` to true. Then:

```powershell
python -m homebrew_as_code.myspeidel_create_candidate build `
  --backup $Backup --draft $Draft --policy $Policy --spec $Spec --output $Candidate
if ($LASTEXITCODE -ne 0) { throw 'Candidate preparation failed' }
```

Inspect `report.branches` for concrete field paths per POST schema branch.
The existing conservative validator does not verify all constraints, including
date-time formats. Both errors and unverified constraints remain visible.
Zero reported errors is NOT complete conformance or live-create evidence.
`upload_ready` remains false even with zero errors.

## Evidence and next step

Official contract: https://api.cloud.myspeidel.com/v1.0/api-spec/json
POST accepts a complete recipe and documents dryRun; no ingredient matching
endpoint or separate ingredient creation endpoint is documented. Client UUID
preservation, cross-recipe catalog reuse and metadata initialization need a
controlled POST dry-run followed, separately, by a live create/GET comparison.
This patch implements neither network operation.

Local verification with the supplied draft and GET backup: recipe_v5 produces
zero supported-keyword errors; 56 date-time format checks remain unverified.
This is a fixture-specific offline result, not a server acceptance result.
