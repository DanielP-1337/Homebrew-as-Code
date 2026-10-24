# 0019q — MySpeidel PUT compatibility experiments

Test **only your own expendable private 20 L recipe**. This harness never alters the
backup and never touches the production GET-only client. The two observed GET/schema
conflicts are `references.water_types.*.name=null` and
`references.hops.*.name=null` (documented PUT schema expects a string).

## Offline first

Run from repository root with the existing Python venv:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_experiments `
  --backup .local/put-test-7-backup.json --variant omit-null-names `
  --mode prepare --spec .local/vendor/myspeidel-openapi.json `
  --result .local/0019q-omit-prepare.json
```

Try `original`, `omit-null-names`, `empty-string-names` with **different**
`--result` paths. The first variant is a baseline, the second omits only null
`name` properties in `water_types` and `hops`, and the third replaces those
nulls with empty strings. Reference keys, UUIDs and other recipe fields remain
unchanged. Reports contain *counts and digests*, never recipe values.
`unverified` schema checks remain explicit; zero errors is not server proof.

## Network experiments — explicit PUT

Every network command creates an exclusive attempt marker **before login**.
If it fails or the terminal closes, do not blindly retry: inspect current GET
state and choose a different result filename only after reconciling the state.
The current GET must match the original backup digest before the PUT is sent.

```powershell
# This sends HTTP PUT with dryRun=1; dryRun is NOT guaranteed side-effect free.
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_experiments `
  --backup .local/put-test-7-backup.json --variant omit-null-names `
  --mode dry-run --result .local/0019q-omit-dryrun-attempt.json

# REAL WRITE: dryRun=0; only when ready to change the disposable test recipe.
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_experiments `
  --backup .local/put-test-7-backup.json --variant omit-null-names `
  --mode apply --allow-live-write `
  --result .local/0019q-omit-live-attempt.json
```

The CLI requests exact interactive consent for either network action, and
prints a post-attempt GET digest comparison (baseline / candidate / neither /
unavailable). Successful HTTP responses do not guarantee that no side effects
occurred; server timestamps may change. HTTP 400 responses are surfaced only
via the existing sanitized PUT diagnostics. The attempt marker intentionally
remains `indeterminate_until_verified`, because it is written before the
request and is never falsely promoted to a durable success receipt.

**Restoration is deliberately not automated**. A backup file plus a cloud backup
does not prove rollback works. A failed or successful live PUT may normalize or
remove fields. Restore the baseline only through a separately authorized action,
using the existing guarded workflow after verifying the current server state.
Do not put `.local` artifacts or credentials in Git. Never print private recipe
objects or raw server responses when seeking assistance.
