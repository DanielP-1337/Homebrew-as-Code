# 0019x: Local HTTP Error Envelope Capture

Enable only when debugging an explicitly approved PUT dry-run:

```powershell
$env:HBAC_MYSPEIDEL_LOCAL_HTTP_ERROR = '1'
try {
    .\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_experiments `
        --backup .local/weizenbier38-golden-backup.json `
        --variant nonempty-reference-names `
        --mode dry-run `
        --result .local/0019x-weizen-nikolaus-dryrun.json
} finally {
    Remove-Item Env:\HBAC_MYSPEIDEL_LOCAL_HTTP_ERROR -ErrorAction SilentlyContinue
}
```

This example assumes the backup contains your private **Weizen Nikolaus** recipe;
confirm the actual backup before running. Never reuse an existing result filename.
The request still requires the `DRY RUN EXPERIMENT` confirmation.

When the API returns an HTTP error, inspect only the locally written sidecar:

```powershell
$Report = Get-Content '.local/0019x-weizen-nikolaus-dryrun.json.http-error.json' -Raw | ConvertFrom-Json
$Report.response | Format-List http_status, content_type, body_truncated, body_bytes_captured, body_text
```

The HTTP response body is captured up to `MAX_RESPONSE_BYTES`, UTF-8 decoded
with replacement on malformed input; `body_truncated` indicates that capture
was incomplete. No request headers, bearer tokens, or cookies are included.
**Server response content may itself contain private identifiers.** Keep this
file under `.local/` and do not publish it. Normal `.receipt.json` remains
safe and does not include this raw envelope. No retries or restore operations
are performed by this feature.
