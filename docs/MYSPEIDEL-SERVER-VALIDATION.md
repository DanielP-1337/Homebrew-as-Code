# MySpeidel PUT server-validation diagnostics (0019r)

For each opted-in experiment, 0019r attaches `validation_details` to its local
`.receipt.json` when the HTTP PUT returns a 400 diagnostic. It does **not**
change the request, add retries, or initiate an HTTP call by itself.

The summary includes a capped number of `errors[]` entries, fixed-enum error
codes, and masked path structures. UUIDs, unknown schema names, server messages,
recipe contents, tokens, and original response bytes are not included. A
`response_format` of `json_without_errors_array` means the response did not
contain a JSON `errors` array; it does not imply the server accepted the request.

Only `errors[].path` and `errors[].errorCode` are considered; if their syntax or
values cannot be safely classified they are omitted. Unknown path segments are
rendered as `<redacted>`. These generic diagnostics cannot prove the actual
server-side root cause, especially when the server returns no error paths.

Inspect a new result locally:

```powershell
$Receipt = Get-Content '.local/0019r-omit-dryrun.json.receipt.json' -Raw | ConvertFrom-Json
$Receipt.validation_details | Format-List
```

Always use a fresh `--result` filename for another explicitly authorized PUT.
Never copy raw responses from the server into the repository.
