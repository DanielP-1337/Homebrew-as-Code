# 0020s — POST Dry-Run & GET Verification

Requires 0020p diagnostics, 0020q and 0020r. Consumes the saved 0020r candidate
without rebuilding IDs. No live-create or PUT capability is added.

## Workflow

1. Validate candidate digest, source-backup digest, private 20 L recipe,
   new distinct recipe/addition UUIDs, size limit and supplied POST schema.
2. Display source and candidate names, candidate UUID/hash and remaining
   unsupported schema constraints. Ask once before authentication/network.
3. Reserve a new diagnostics file. Authenticate with existing credential prompt.
4. GET source: require exact canonical hash equality with the backup.
5. GET candidate UUID: require HTTP 404. Any other status blocks POST.
6. Send exactly one POST to the fixed `/v1.0/recipe?dryRun=1` endpoint.
   Body is the candidate recipe, not its local wrapper.
7. In a finally block, independently GET both source and candidate UUIDs.
   This also runs after 400/500, unexpected acknowledgement, transport error
   and KeyboardInterrupt during POST. Failure of either GET does not skip the other.
8. Save and print masked diagnostics. Exit 0 only when HTTP 200 explicitly
   acknowledges `DRY RUN SUCCEEDED`, source is unchanged and candidate returns 404.

The supplied OpenAPI is checked again; an old report alone is not trusted.
Unsupported date-time checks remain visible and do not count as validated.
Recipe and addition UUIDs are checked for canonical form and uniqueness against
source recipe/addition IDs. Full ingredient semantics are not revalidated here.

Requests have a 20-second transport timeout, no redirects and no retries.
POST response capture is bounded to 64 KiB; oversized responses cannot count as
acknowledgement. GET recipe parsing is bounded to 5 MB; diagnostic body capture
is 64 KiB and truncation is explicitly reported. Request diagnostics include the
serialized body hash, body, method, URL and headers, with credentials redacted.
Authentication request/response bodies are never included in diagnostics.

An existing diagnostics file is never reused. A process kill or login failure
can leave `STARTED_RESULTS_UNKNOWN`; it is not a success receipt. Normal network
errors are recorded. A hard process kill or power loss cannot run finally.
No automatic cleanup or retry occurs when a recipe appears or changes.

HTTP 404 means the candidate UUID is not retrievable by this account at that
moment. This check cannot rule out a server creating a different UUID, eventual
consistency or unrelated catalog changes. It is not a global no-write proof.
Likewise a successful dry-run does not establish live-create behavior.

## Windows PowerShell

Run from the repository root after applying the patch and running tests:

```powershell
$Diagnostics = ".local/myspeidel-post-dry-run-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_create_dry_run `
    --candidate '.local/myspeidel-create-candidate-20261026-110809.json' `
    --backup '.local/myspeidel-get-abgleich-20261025-220241.json' `
    --spec '.local/vendor/myspeidel-openapi.json' `
    --diagnostics $Diagnostics
$RunExit = $LASTEXITCODE
Write-Host "Diagnostics: $Diagnostics"
if ($RunExit -ne 0) {
    Write-Warning 'Dry-run failed or remains unverified. Review diagnostics before retrying.'
}
```

The CLI shows recipe names in clear text (JSON-escaped for terminal safety).
No recipe list selection is needed: both identities are fixed by the reviewed
candidate and backup. Enter `yes` to run the dry-run and GET checks. Cancellation
before login performs no HTTP requests. Exit 2 indicates failure or uncertainty;
preflight refusal sends no recipe POST. Exit 0 after cancellation means cancelled,
not server acceptance; only `DRY_RUN_VERIFIED` means all checks passed.

## Validation

Synthetic transport tests exercise exact POST body/URL, explicit acknowledgement,
400/500, redirects, timeout, interruption, oversized response, source mismatch,
preexisting candidate, authentication failures during GET, independent finally
checks, digest mismatch, UUID reuse and credential masking. No test contacts
MySpeidel. Actual server acceptance must be tested separately by the operator.

Commit trailer: `Assisted-by: ChatGPT6-Astra`.
