# MySpeidel controlled PUT experiment (0019i)

**This is a REAL write-capable tool.** Use only an expendable, manually created
private 20 L test recipe you own. The original read-only client remains unchanged.
Do NOT feed it the Swagger example or the 0019h Golden Reference candidate.
There is no automatic rollback; a successful PUT may alter timestamps, versions,
or normalize server-side data even when the request JSON is unchanged.

The workflow is manual and three-stage. Paths must be under the project's ignored
`.local` folder. Outputs use exclusive creation; **never commit** backups, receipt,
result marker, credentials, identifiers or responses.

```powershell
# Stage 1: select your test recipe by list index; only GET + local private backup
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_roundtrip_cli backup `
  --output .local/put-test-7-backup.json

# Stage 2: inspect same backed-up recipe; PUT dryRun=1, followed by GET check
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_roundtrip_cli dry-run `
  --backup .local/put-test-7-backup.json `
  --receipt .local/put-test-7-dryrun.json

# Stage 3: REAL PUT, only after checking Stage 2 and explicitly accepting risk
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_roundtrip_cli apply `
  --backup .local/put-test-7-backup.json `
  --receipt .local/put-test-7-dryrun.json `
  --result .local/put-test-7-attempt.json
```

`backup` is **GET-only** and saves the FULL private JSON (sensitive). `dry-run`
uses the documented PUT endpoint and `dryRun=1`; request bodies are **unchanged**
from GET. The CLI checks that a fresh GET matches the saved snapshot both before
and after dry-run. HTTP 200 alone is not a proof of zero side effects.

`apply` uses the same saved payload only after checking matching receipt and
current server digest, then asks for exact `WRITE PRIVATE RECIPE` consent.
A local **attempt marker is created before sending**, so an interrupted request
cannot accidentally be retried with the same result file. If the operation fails
or connection drops, server state may be indeterminate: investigate via manual
GET before considering any new operation. Successful PUT is followed by GET,
reporting whether the resulting JSON equals the baseline. **Never claim zero
side effects from equality alone**. There is no delete, POST or arbitrary PUT.

This tests whether a GET payload is accepted by PUT. It does not prove that
other recipes are valid, establish permissions to modify third-party recipes,
or test a new-recipe POST. Do not treat an existing recipe's identity as a
general template. No API credentials are saved by this tool.

## Safe diagnostics (0019k)

HTTP PUT rejection responses are inspected only in memory with a 64 KiB limit.
The console reports an HTTP status, a coarse fixed category and a known top-level
schema area. Server messages, raw JSON, URLs, credentials, recipe values, identifiers
and arbitrary error paths are **never printed or saved**. A generic category does
not mean the server returned no useful information; it means safe classification
was not possible. PUT payloads, endpoint and `dryRun=1` are unchanged.

`dry-run` only creates a success receipt if HTTP 200 includes an explicit
`DRY RUN SUCCEEDED` acknowledgement and the subsequent GET digest matches.
If Speidel uses an undocumented acknowledgement shape, this check deliberately
fails closed rather than creating a receipt. An HTTP 200 without a verified
acknowledgement is **not** evidence that `dryRun` is safe.

After a failed dry-run, run `verify` (GET-only) against the original backup
before any new attempt. Do not invoke `apply` without a successful receipt.

## Optional Windows Credential Manager integration (0019l-auth)

Credentials remain in the signed-in Windows user's credential store (Generic
credential `Homebrew-as-Code/MySpeidel/v1`), **not** in `.local`, source files,
Git, environment variables, or application logs. A Windows user or process
running with access to that account can retrieve the credential; this is
convenient local protection, not isolation from malware in the same user session.
The password is stored by Windows; no Cloud API token is persisted.

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_credentials_cli setup
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_credentials_cli status
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_credentials_cli clear
```

Setup prompts once for username and hidden password, and requires explicit
`yes` before saving. Status prints only configured/not configured; clear
requires explicit consent. The existing PUT workflow then uses this credential
implicitly for login; if absent it asks interactively as before. No changes to
request methods, payloads, GET/PUT safeguards or cloud write authorization.
Wrong or expired stored credentials are **not** automatically overwritten;
run `setup` again to update them. Credential access failures fail closed.
Windows-only; no additional Python dependencies.
