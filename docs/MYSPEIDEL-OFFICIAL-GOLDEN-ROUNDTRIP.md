# Official Speidel Golden Recipe Roundtrip (0019w)

Reference: [Weizenbier 38°](https://www.myspeidel.com/recipes/view_recipe/2054).

The website ID `2054` **is not an API recipe UUID**. This workflow uses only a
private, user-owned copy of the recipe, not Speidel's public source recipe.
A copied recipe can differ from the public source; provenance is **attested by
the user**, not independently verified by the tooling.

1. In the MySpeidel web UI, copy the reference recipe into your account. Name
   the private copy something containing `Weizenbier` and `38` and ensure it is
   a private 20 L recipe. Do not use the public original for PUT.
2. Create a fresh GET-only backup with the existing interactive backup CLI:

   ```powershell
   .\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_put_roundtrip_cli backup `
       --output .local/weizenbier38-golden-backup.json
   ```

   Select the **new private copy**, not the earlier Roundtrip Test 001.
3. Validate the unchanged GET snapshot against both supported offline schemas:

   ```powershell
   .\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_official_golden_cli `
       --backup .local/weizenbier38-golden-backup.json `
       --mode prepare --confirm-private-copy `
       --spec .local/vendor/myspeidel-openapi.json `
       --result .local/weizenbier38-golden-prepare.json
   ```

4. After inspecting the offline checks, run the unchanged GET -> PUT dryRun=1
   -> GET experiment using the existing explicit `DRY RUN EXPERIMENT` prompt:

   ```powershell
   .\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_official_golden_cli `
       --backup .local/weizenbier38-golden-backup.json `
       --mode dry-run --confirm-private-copy `
       --result .local/weizenbier38-golden-dryrun.json
   ```

   The receipt is saved as `<result>.receipt.json`. `baseline_match` means the
   observable GET JSON matched the saved baseline, not that no side effects
   are possible. On HTTP 400, inspect the receipt before any further requests.
5. Only after an accepted dry-run and explicit review, opt into a real PUT:

   ```powershell
   .\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_official_golden_cli `
       --backup .local/weizenbier38-golden-backup.json `
       --mode apply --confirm-private-copy --allow-live-write `
       --result .local/weizenbier38-golden-apply.json
   ```

   The tool prompts `WRITE TEST RECIPE` and compares a fresh GET afterward.
   A server may normalize the recipe, so a successful PUT does not guarantee
   a byte-identical GET. Restore is **not automated** in 0019w; use the
   preserved backup and a separately reviewed restore procedure.

Keep all backups, receipts and diagnostic responses inside ignored `.local/`.
Never commit bearer tokens, passwords, private backups or raw responses.
Commits for this assisted development may use `Assisted-by: ChatGPT6-Astra`.
