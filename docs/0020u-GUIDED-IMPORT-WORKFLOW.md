# 0020u — Guided Import Workflow & Persistent Ingredient Mapping

Requires 0020q through 0020t (baseline commit 5589212). Adds a coordinator around
the existing offline builders, POST dry-run and guarded live-create commands.
No new transport or automatic live upload is introduced. Code/docs are EN-US;
recipe and ingredient names are displayed as supplied, escaped for terminal safety.

## Start with a recipe / brew plan

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_guided_import start
```

The wizard lists valid `brew-plans/*.yaml` with recipe name, brew-plan ID and
equipment model. Selecting a plan selects its linked recipe; recipes, equipment
and plans remain separate domains. It then lists digest-checked GET backup files
from the top level of `.local`, with recipe names and filenames. Invalid backups
are omitted. An arbitrary recipe without a valid brew plan is not imported.

Optional explicit paths:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_guided_import start `
    --plan 'brew-plans/lebkuchen-zauber-brew-001.yaml' `
    --backup '.local/myspeidel-get-abgleich-20261025-220241.json' `
    --settings 'examples/myspeidel-import-settings.json' `
    --spec '.local/vendor/myspeidel-openapi.json'
```

`start` is offline. It creates one unique directory under
`.local/myspeidel-imports/<import-id>/`, holding:

- `session.json`: identity, source hashes, frozen input hashes and report history.
- `plan-snapshot.json`: separate loaded recipe, plan, equipment and warnings.
- `backup.json`, `spec.json`: immutable snapshots for repeatable checks.
- `settings.json`, `policy.json`: editable configuration before preparation.

The existing Lebkuchen recipe has already been imported successfully. Starting
another session does not detect duplicate recipe names or intent: a newly
prepared candidate gets a new UUID. Use a second brew plan for the next real
import, or stop after offline preparation while evaluating the wizard.
The coordinator does not adopt old standalone imports automatically.

## Review configuration once per import

Open the two paths printed by `start` in VS Code. Review water name/volume,
malt colors and timing decisions in `settings.json`. The bundled settings are
specific to Lebkuchen-Zauber, not generic defaults for every recipe.

Review all recipe fields in `policy.json`: description, comments, bitterness,
color, specific gravity, account, equipment and versions. These begin as copies
from the source backup, not calculated values for the selected new recipe.
Set `assumptions_accepted` to true after review. Equipment scaling and automatic
water calculations are not implemented. Unmapped canonical values remain in the
0020q report. UTF-8 with or without BOM is accepted for these editable JSON files.

## Resume by clear name

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_guided_import resume
```

Choose the import by recipe name and import ID, then the available action:

1. **Prepare candidate (offline)** resolves ingredient mappings and writes the
   template, draft, mapping decisions and candidate. Confirm the displayed
   mapping table once. Missing/ambiguous names offer numbered category-specific
   choices with clear catalog names and UUIDs. Enter cancels. No matching catalog
   entries means preparation stops without inventing ingredients.
2. **Run POST dry-run** invokes 0020s, including its confirmation, credential
   prompt, checks and diagnostics. A successful matching receipt enables create.
3. **Create new private recipe** invokes 0020t with its existing explicit
   `CREATE PRIVATE RECIPE` confirmation and durable attempt marker.
4. **Verify saved recipe** uses 0020t `--verify-only`, including source comparison.
   After live intent or a marker exists, resume never offers another live POST.

Each invocation performs one selected step, returns its exit code and saves the
report location. Run `resume` again to continue. No credentials are persisted.

To inspect state without authentication or API calls:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_guided_import status
```

Both commands support `--session '.local/myspeidel-imports/<import-id>'` to skip
the session chooser. Status checks local evidence; it does not refresh the server.

## Persistent mapping

`.local/myspeidel-ingredient-mapping.json` stores mappings by source-account UUID,
category and normalized canonical ingredient name. Each entry contains the
selected catalog UUID and actual name. An explicit selection can map an alias
such as a canonical hop name to a differently named existing catalog entry.
The remote catalog name is preserved in the resulting payload.

Unique exact normalized names are proposed automatically. Before preparation,
the table distinguishes saved, exact-name and explicitly selected mappings.
Saved mappings are reused only if the same UUID/name is present and not marked
deleted in the current source backup. Stale mappings require selection again.
Another account gets a separate namespace; categories are never mixed.

The registry is not a complete remote catalog, nor an authority on ingredient
chemistry or product identity. Every used entry must exist in the chosen GET
backup, because its full metadata is required by 0020r. To add unavailable
catalog entries, obtain a suitable source GET backup first; this patch neither
merges multiple backup catalogs nor creates ingredients through the API.
A session records the actual decisions even when registry mappings later change.

## Resume and integrity rules

Fixed snapshots are hash checked. After candidate creation, settings, policy,
template, draft, mapping decisions and candidate are frozen by hash. Edits are
rejected rather than silently regenerating UUIDs. Reusing the session reuses
exactly the saved candidate. To change recipe intent, create a separate session;
never do this merely to bypass an uncertain live attempt.

Report filenames are journaled before invoking a child CLI. Resume reads actual
reports and validates the 0020s receipt against the candidate and source. A child
that returns before writing diagnostics made no HTTP calls; a cancelled live
step can therefore be offered again. A hard interruption with unresolved live
intent only allows GET verification. A surviving 0020t marker also blocks live
repetition, even if session history was lost.

Session and registry files use atomic replacement; exclusive local lock files
prevent overlapping wizard operations. After a process kill, a stale lock may
remain. Confirm no other process is running before removing ONLY that lock.
Never remove the live-create attempt marker to bypass the guard. Locks and
markers are local checkout safeguards, not distributed/server idempotency.
If interruption occurs immediately after candidate write, the wizard recovers
its prepared-input hashes and preserves the existing UUIDs.

## Terminal and diagnostics

0020s now prints a compact summary by default, like 0020t. Standalone commands
accept `--verbose` to print the full masked report. Full JSON diagnostics remain
saved under the original capture limits regardless of verbosity. The wizard
uses compact mode. Credentials remain masked by the existing transport tools.

No network requests run during start, preparation, status or automated tests.
Live acceptance for a second recipe must be verified separately.

Commit trailer: `Assisted-by: ChatGPT6-Astra`.
