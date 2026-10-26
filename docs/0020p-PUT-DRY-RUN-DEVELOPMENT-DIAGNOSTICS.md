# 0020p — PUT dry-run development diagnostics

Base: b3ef48f (0020o including Windows schema-integrity fix).

## Purpose

Capture the request envelope and response together when investigating rejected
MySpeidel PUT dry runs. Development recipe names, identifiers, owner metadata,
recipe values and server validation messages are intentionally visible. Passwords,
authorization/cookie fields and tokens are masked. Reports remain under `.local/`
and are not public fixtures. No payload conversion or live write is added.

## Command (PowerShell)

```powershell
Set-Location 'C:\dev\Homebrew-as-Code'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_roundtrip_cli `
    dry-run `
    --backup '.local/myspeidel-get-abgleich-20261025-204436.json' `
    --receipt ".local/myspeidel-put-receipt-$Stamp.json" `
    --diagnostics ".local/myspeidel-put-diagnostics-$Stamp.json"
```

Optional: append `--spec '.local/vendor/myspeidel-openapi.json'` to include the
existing conservative offline v4/v5 schema comparison in `offline_contract`.
This is local analysis, not a claim that the server uses that exact schema.
Without this option `offline_contract` is null. An unknown check is not a pass.
The specification is not downloaded automatically and is not redistributed.

## Evidence and limits

- `request_prepared`: method, URL including `dryRun=1`, Request-object headers,
  exact compact JSON serialization except credential masking, payload byte length,
  SHA-256 of the actual unmasked outgoing bytes, root keys and wrapper detection.
  A prepared event records a send attempt, not proof of server receipt.
- Header capture is at the urllib Request boundary. Transport-generated headers
  such as Host and Content-Length are not a packet capture and may not appear.
- `response`: HTTP status, masked response headers, JSON body (parsed for recursive
  masking) or text body. The existing 65,536-byte capture limit remains; truncation
  and captured length are explicit. JSON formatting may change; values are retained
  except credentials. No credentials from the login request are logged.
- Known bearer tokens are removed even when echoed as ordinary text. Credential
  keys, Bearer/Basic strings, cookie headers and common text assignments are masked.
  Arbitrary unknown secrets embedded in prose cannot be classified perfectly;
  inspect a diagnostic before publishing it outside the development conversation.
- `server_validation` retains the existing sanitized structural summary separately
  from the response body. Do not equate offline findings with server findings.
- A finally-block attempts GET after the PUT path, including HTTP rejection,
  transport uncertainty, unrecognized dry-run acknowledgment or interruption.
  Results are `unchanged`, `changed` or `unverified`, with independent hashes when
  available. Abrupt process termination cannot guarantee cleanup or GET completion.
- The CLI prints the masked report and saves it without overwriting existing files.
  Diagnostic and receipt paths must differ. The recipe body is not modified.
- Failure still exits 1 and creates no success receipt. Only acknowledged dry-run
  success plus an identical GET produces a receipt. No automatic retry occurs.
- Existing `backup` recipe selection continues to display clear recipe names.
  `dry-run` uses the identity from the digest-checked backup.

The post-error GET behavior also applies without `--diagnostics`; verbose capture
is opt-in. Live `apply` is unchanged and cannot enable this capture option.

## Validation

Offline mocked HTTP tests cover real Request bytes/digests, HTTP 400 JSON details,
credential masking in headers and nested bodies, text responses and truncation,
and success/failure combinations with unchanged/changed/unavailable GET outcomes.
The repository test suite is run with `python -m pytest -q`. No live Cloud request
is made while creating or testing this patch.

Suggested commit:

```text
feat(myspeidel): diagnose PUT dry runs and verify failed attempts

Capture masked request envelopes and response bodies for development.
Verify the server snapshot after successful and failed dry-run attempts.
Keep offline contract findings separate from server validation evidence.

Assisted-by: ChatGPT6-Astra
```
