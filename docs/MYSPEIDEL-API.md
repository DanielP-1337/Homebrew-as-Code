# MySpeidel API v1.0 — read-only discovery CLI

For recipe creation, use the [verified guided API import workflow](0021-API-IMPORT-WORKFLOW.md).
This page documents the older read-only discovery CLI, not the capabilities of
the whole repository.

For interactive username/password login see [MySpeidel Login](MYSPEIDEL-LOGIN.md).

Official OpenAPI v1.0: https://api.cloud.myspeidel.com/v1.0/api-spec/json

Implemented documented GET endpoints:

- `GET /v1.0/propfind/recipe` (recipe metadata collection)
- `GET /v1.0/recipe/{uuid}` (individual recipe; UUID string)

Authentication uses `Authorization: Bearer <token>` according to the published OpenAPI security scheme (`token_auth`, HTTP bearer). The API also documents `POST /v1.0/auth/authentication` for obtaining a session token using username/password. The discovery CLI remains GET-only. Separate authentication and guided-import commands implement login and the verified recipe-create path.

## Configure securely (PowerShell 7)

1. Obtain a session token using an official, trusted MySpeidel authentication flow. Do **not** paste credentials or tokens into chat or GitHub issues.
2. In the current PowerShell session only, load the token without putting it on the command line or in history:

```powershell
$secret = Read-Host 'MySpeidel bearer token' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try { $env:MYSPEIDEL_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }

# All commands print structure (keys/types), never recipe field values:
py -3.11 -m homebrew_as_code.myspeidel_cli list --machine-size 20
py -3.11 -m homebrew_as_code.myspeidel_cli get <recipe-uuid>

Remove-Item Env:MYSPEIDEL_TOKEN
```

Do not commit account metadata or token-bearing logs. The read-only CLI does not write API responses to disk. JSON structure inspection can still expose **field names**, array lengths and object layout; review terminal output before sharing. A 401 response usually indicates an absent, invalid or expired token. For the implemented interactive authentication flow, see [MySpeidel Login](MYSPEIDEL-LOGIN.md).

Replace `<recipe-uuid>` in the example before running it. Use an actual recipe ID returned by MySpeidel.

## Boundaries

- This discovery CLI does not upload recipes; use the separate guided import commands.
- The client pins the MySpeidel host, HTTPS and an allowlist of GET paths.
- It does not issue machine control commands.
- It does not print HTTP error bodies or authorization headers.
- GitHub Actions must run only offline tests; never add real MySpeidel tokens to test fixtures.
