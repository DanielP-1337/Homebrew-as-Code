# MySpeidel API v1.0 — read-only discovery

For interactive username/password login see [MySpeidel Login](MYSPEIDEL-LOGIN.md).

Official OpenAPI v1.0: https://api.cloud.myspeidel.com/v1.0/api-spec/json

Implemented documented GET endpoints:

- `GET /v1.0/propfind/recipe` (recipe metadata collection)
- `GET /v1.0/recipe/{uuid}` (individual recipe; numeric UUID)

Authentication uses `Authorization: Bearer <token>` according to the published OpenAPI security scheme (`token_auth`, HTTP bearer). The API also documents `POST /v1.0/auth/authentication` for obtaining a session token using username/password. **This development milestone deliberately does not implement password login, token creation, uploads, or any other POST/PUT/DELETE operation.**

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
py -3.11 -m homebrew_as_code.myspeidel_cli get 12345

Remove-Item Env:MYSPEIDEL_TOKEN
```

Do not commit account metadata or token-bearing logs. The read-only CLI does not write API responses to disk. JSON structure inspection can still expose **field names**, array lengths and object layout; review terminal output before sharing. A 401 response usually indicates an absent, invalid or expired token. Token acquisition and login should be implemented separately only after determining the officially supported account authentication process.

The number in the `get` example is a placeholder. Use an actual recipe ID returned by MySpeidel.

## Boundaries

- No recipe upload/synchronization in v0.2.0.
- The client pins the MySpeidel host, HTTPS and an allowlist of GET paths.
- It does not issue machine control commands.
- It does not print HTTP error bodies or authorization headers.
- GitHub Actions must run only offline tests; never add real MySpeidel tokens to test fixtures.
