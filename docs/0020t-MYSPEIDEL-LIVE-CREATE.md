# 0020t — Live Create & GET Comparison

Requires 0020s and the unchanged 0020r candidate plus successful 0020s JSON
report. This command performs a REAL create after explicit confirmation.
No live network tests were performed while developing this patch.

## Contract and evidence

The CLI rechecks candidate/source digests and the local POST schema. The receipt
must show DRY_RUN_VERIFIED, matching candidate/source hashes, successful pre/post
GET checks and the exact dry-run request body. This is local evidence, not a
server-signed receipt. Do not edit the candidate or report to bypass validation.

After showing clear recipe names, UUID and digest, live mode requires typing
`CREATE PRIVATE RECIPE`. GET checks then require an unchanged source and HTTP
404 for the candidate UUID. Only then is a new exclusive attempt marker created
at `.local/myspeidel-create-attempts/<candidate-uuid>.json`, before the POST.
A preexisting marker blocks another live invocation for that UUID, regardless
of diagnostics filename. Markers are retained after success and failure.
This is a guard within this repository checkout, not server-side idempotency.

Exactly one POST sends the saved candidate to `/v1.0/recipe` without dryRun.
No redirects, retries, PUT, deletion or automatic cleanup are implemented.
POST response is bounded to 64 KiB; GET parsing to 5 MB. Authentication reuses
the existing credential prompt with redirects disabled. Tokens remain in memory.

After POST, independent GET checks run for source and candidate, even after
HTTP failure, timeout or KeyboardInterrupt. Hard termination/power loss cannot
run finally. Failed/uncertain calls are not repeated automatically.

`LIVE_CREATE_VERIFIED` requires HTTP 201 with `HTTP 201 Created`, an unchanged
source, and a GET of the candidate that matches all content fields. Timestamp
and content-version changes are separately reported. UUIDs, schema versions,
amounts, references, order and every other field are compared strictly. There
is no unit conversion, tolerance, sorting, padding or silent normalization.
Metadata-only differences may pass, but are retained with old/new values.
Additional server fields count as differences unless in the metadata list.

The final report retains the complete parsed candidate GET (within the size
limit), comparison paths/values and masked diagnostics. It is not a PUT backup
wrapper. Source GET diagnostics are bounded to 64 KiB and compared by full hash.
No claim is made about unrelated recipes or changes to the entire catalog.
A missing candidate UUID does not prove the server did not create a different ID.

## Run once

```powershell
$Result = ".local/myspeidel-live-create-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_live_create `
    --candidate '.local/myspeidel-create-candidate-20261026-110809.json' `
    --backup '.local/myspeidel-get-abgleich-20261025-220241.json' `
    --receipt '.local/myspeidel-post-dry-run-20261026-111723.json' `
    --spec '.local/vendor/myspeidel-openapi.json' `
    --diagnostics $Result
$CreateExit = $LASTEXITCODE
Write-Host "Report: $Result"
if ($CreateExit -ne 0) {
    Write-Warning 'Review the report. Do not repeat live POST; use --verify-only.'
}
```

Default terminal output is compact. Add `--verbose` for full masked diagnostics.
The JSON report is written in either mode. Cancellation before login performs
no HTTP. Exit 0 after cancellation does not mean a recipe was created.
Failures/uncertainty return 2. A login failure or hard interruption may leave a
`STARTED_RESULTS_UNKNOWN` diagnostics file; use a new path for later checks.

## Read-only verification after an uncertain result

Use the same command with `--verify-only` and a NEW diagnostics filename.
It authenticates, then GETs source and candidate without any recipe POST.
The attempt marker is neither required nor removed. `GET_COMPARISON_VERIFIED`
means current content matches, not that a past POST acknowledgement was observed.
If the source changed independently, the result remains unverified.
Never delete the marker or rebuild IDs just to retry an uncertain create.

The four metadata keys are `created_on`, `creation_date`, `update_on` and
`content_version`. All differences remain inspectable in
`after_candidate.comparison.differences`; recipe data is in
`after_candidate.recipe`.

Commit trailer: `Assisted-by: ChatGPT6-Astra`.
