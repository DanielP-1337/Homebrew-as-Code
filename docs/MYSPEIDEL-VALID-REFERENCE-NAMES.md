# 0019v — Valid reference names experiment

`nonempty-reference-names` is a deliberately narrow PUT experiment for the
**private, disposable test recipe**. It replaces exactly one `name: null` in
each of `references.water_types` and `references.hops` with nonempty test
strings (`Test Water Reference`, `Test Hop Reference`). It leaves the top-level
recipe name, `recipe_type`, reference UUID keys and all unrelated fields alone.
The strings are test labels, **not verified ingredient names**.

The variant fails closed if either category does not contain exactly one
`name: null`; this avoids silently sending partially changed candidates.
The original backup is never rewritten.

Run offline first:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_experiments `
  --backup .local/put-test-7-backup.json `
  --variant nonempty-reference-names --mode prepare `
  --spec .local/vendor/myspeidel-openapi.json `
  --result .local/0019v-nonempty-prepare.json
```

The supported offline schema check is partial; `unverified` rules remain.
Inspect the result before using network operations. A separate result path is
required for every run because markers and receipts are exclusive.

```powershell
$env:HBAC_MYSPEIDEL_LOCAL_FULL_ERRORS = '1'
try {
  .\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_experiments `
    --backup .local/put-test-7-backup.json `
    --variant nonempty-reference-names --mode dry-run `
    --result .local/0019v-nonempty-dryrun.json
} finally {
  Remove-Item Env:\HBAC_MYSPEIDEL_LOCAL_FULL_ERRORS -ErrorAction SilentlyContinue
}
```

The dry-run sends a **real PUT** with `dryRun=1`; it is not assumed to be
side-effect free. Interactive confirmation and pre-/post-GET verification remain
mandatory. A live write uses the existing `--mode apply --allow-live-write`
and interactive confirmation; do **not** run that until the dry-run is accepted
and the resulting payload is reviewed. Cloud backups do not by themselves
prove API rollback. Keep all results in `.local/`, never commit credentials.

AI assistance: `Assisted-by: ChatGPT6-Astra` (commit trailer).
