# MySpeidel login and read-only live test (v0.3.0)

The official API documents `POST /v1.0/auth/authentication` with JSON
`{ "username": "...", "pass": "..." }` and a response containing `token`.
See: https://api.cloud.myspeidel.com/v1.0/api-spec/json

Run in an interactive PowerShell 7 terminal:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_auth_cli
```

Enter the username and password **locally at the prompts**. The password is
entered with Python's `getpass` (hidden input). The one-shot command logs in,
fetches the private recipe listing for the 20 L device class, prints **JSON
field names and types only**, and discards the token when the process exits.
Nothing is written to a credential file. Do not paste passwords, session
keys, raw API responses, or sensitive account metadata into public issues.

This is a read-only verification of recipes. The API login necessarily uses
POST to establish a session, but this patch has **no recipe POST/PUT/DELETE**.
If login fails, ensure your username/password works on myspeidel.com and
report the status code only, without credentials. A web session is not proof
that the separate API credentials have been accepted.

Implementation notes:
- `GET /v1.0/propfind/recipe` filters use query parameter `size` and
  integer `includePublic` 0/1 (corrected from v0.2.0).
- Recipe UUIDs are 36-character strings, not decimal IDs (corrected).
- The old `myspeidel_cli` continues to support `MYSPEIDEL_TOKEN`.
