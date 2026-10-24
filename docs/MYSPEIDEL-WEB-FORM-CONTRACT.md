# MySpeidel Web Form Contract Inspector (0020a)

An **offline, read-only** inspector for the URL-encoded POST body captured from Chrome DevTools while saving a personal recipe in the MySpeidel web editor.

## Capture

In Chrome DevTools > Network > `method:POST`, select the recipe editor's POST, open **Payload > View source**, and save the raw form body (not request headers) as `.local/myspeidel-web-form.txt` (UTF-8). Do not export cookies, CSRF headers, browser sessions, bearer tokens, or full HAR archives. Avoid including authentication fields from the body. The inspector excludes suspicious field names from summary output; it is not a secret scanner.

## Run

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_web_form_contract `
    --form .local/myspeidel-web-form.txt `
    --backup .local/put-test-7-backup.json `
    --report .local/0020a-web-form-report.json
```

The `--backup` argument is optional. Use a backup corresponding to the **same recipe**, ideally captured after saving the browser edit. If the backup predates the edit, differences are expected.

```powershell
$Report = Get-Content .local/0020a-web-form-report.json -Raw | ConvertFrom-Json
$Report.group_counts | Format-List
$Report.ingredient_rows | Format-Table -AutoSize
$Report.cloud_comparison | Format-List
```

## Interpretation

- Form fields such as `recipe[name]`, `malts_to_recipe[0][malt_id]`, and `hops_to_recipe[1][0][hop_id]` use an HTML form model, **not** the Cloud API's JSON PUT schema.
- The web form may submit hundreds of empty placeholder fields. Ingredient rows are reported only when a corresponding ingredient ID field is populated.
- Numeric web catalog IDs and Cloud API UUIDs must **not** be assumed equivalent. No implicit conversion is implemented.
- Some names, such as a malt selector value, may be free text instead of a numeric identifier.
- The report omits raw payloads and request headers. It includes recipe field values and ingredient identifiers: keep it inside `.local/` and review before sharing.
- Status 200 alone does not prove that a change was persisted; a fresh GET or browser re-open is needed.
- The inspector never sends HTTP requests and never updates recipes.
