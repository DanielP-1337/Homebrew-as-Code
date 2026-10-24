# 0020e — MySpeidel Official POST Dry Run (Experimental)

Reference: <https://api.cloud.myspeidel.com/v1.0/api-spec/json>.

The documented `POST /v1.0/recipe` advertises `dryRun` and a dry-run HTTP 200 response.
**This tool intentionally does not support a live create request**. It always sends
`POST https://api.cloud.myspeidel.com/v1.0/recipe?dryRun=1` and never retries.

## Safety and limitations

- Reads only a digest-checked private 20 L backup created by the existing backup CLI.
- Uses a fresh candidate UUID, distinct title, and `public=0`.
- Preserves source ingredient and ownership metadata for exploratory validation;
  these are **not verified as transferable**. A 400 is valuable diagnostic feedback.
- Does not equate names or amounts to ingredient identities; does not merge records.
- No HTTP in `prepare`; a network call only happens with the separate `dry-run` command.
- User must explicitly review and supply the full SHA-256 before network use.
- Tokens are read only from an environment variable and never appear in reports.
- Server response strings are suppressed; only allowlisted validation paths are reported.
- Even an acknowledged dry run does **not** authorize an actual create operation.
- Both candidate and reports must live under gitignored `.local/` and never overwrite files.

## Commands (Windows PowerShell)

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_post_dry_run prepare `
  --backup .local/weizen38-duplicate-backup.json `
  --candidate .local/0020e-candidate.json `
  --report .local/0020e-prepare-report.json `
  --name 'HBAC POST DryRun - Weizen 38'

$sha = (Get-Content .local/0020e-prepare-report.json -Raw | ConvertFrom-Json).candidate_sha256
# Inspect the candidate and report locally; only proceed once satisfied.
$env:MYSPEIDEL_TOKEN = Read-Host 'MySpeidel token'
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_post_dry_run dry-run `
  --candidate .local/0020e-candidate.json `
  --report .local/0020e-dry-run-report.json `
  --confirm-sha256 $sha
Remove-Item Env:MYSPEIDEL_TOKEN
```

HTTP 400 / validation errors are expected while learning the documented create
contract. The request never attempts to create a real recipe. An HTTP 200 without
the explicit `DRY RUN SUCCEEDED` acknowledgement is reported as unverified.

## Observed result and project decision

For the tested cloned private 20 L recipe candidate, the server returned
**HTTP 400**. The sanitized diagnostic categorized the result as
`UNVERIFIED_RESPONSE` / `unclassified`; this neither verifies the create
schema nor proves a general API outage. The documented endpoint and the
existence of `dryRun` do **not** establish safe transferable ingredient
references or owner semantics. Live create/update remains blocked pending
vendor clarification: [write integration status](MYSPEIDEL-WRITE-INTEGRATION-STATUS.md).

The [OpenAPI inventory](MYSPEIDEL-OPENAPI-REFERENCE.md) is a separate offline
schema exploration tool, not a schema validator or authorization to write.

## Interpretation

The output is only an experimental schema/authorization diagnostic. Do not treat
`DRY_RUN_ACKNOWLEDGED` as validation of ownership transfer, reference identity,
or safe runtime behavior of a future production create workflow.
