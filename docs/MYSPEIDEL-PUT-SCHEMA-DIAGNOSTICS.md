# MySpeidel PUT validation diagnostics (0019m)

This tooling is intentionally conservative and does not enable automatic writes.

## Offline first

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_roundtrip_cli offline-schema --backup .local/put-test-7-backup.json --spec .local/vendor/myspeidel-openapi.json --report .local/put-test-7-schema-report.json
```

This validates the original GET backup independently against the published
`recipe_v4` and `recipe_v5` schemas using the repository's existing limited
OpenAPI validator. It performs **no network request or credential lookup**.
Outputs omit recipe values, credentials, UUIDs, and unknown schema paths;
only bounded issue codes and allowlisted paths are included. Unverified
constraints remain explicit; zero errors does **not** imply server acceptance.
The output file is created exclusively under `.local`, never overwritten.

## HTTP 400 diagnosis (optional, explicitly user-approved)

After a successful `verify`, a separately confirmed `dry-run` can now print
up to eight safe `errors[].path` locations when the server supplies them.
Unknown/free-text paths and messages are not displayed or stored. An API error
may therefore still result in `location=unknown` with no paths: no values are
guessed. The original payload, preflight checks, dry-run acknowledgement, and
manual confirmation gates are unchanged. `dryRun=1` is still a network PUT,
not a read-only call; do not blindly repeat it. Do not use `apply` on failure.
