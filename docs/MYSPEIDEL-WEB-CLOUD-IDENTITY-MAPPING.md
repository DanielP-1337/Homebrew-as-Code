# MySpeidel web-to-cloud ingredient identity candidates (0020b)

This offline tool compares the captured HTML recipe editor POST with an independently backed-up Cloud API recipe. It **does not assert** that a numeric web ID and a Cloud UUID are identical merely because quantities match.

## Prerequisites

1. Save Chrome DevTools **Payload → View source** as `.local/myspeidel-web-form.txt` (UTF-8); never export session cookies or authorization headers.
2. Create a **fresh** GET backup of the *same private 20 L recipe* after the web-editor changes have been saved, with `python -m homebrew_as_code.myspeidel_put_roundtrip_cli backup --output .local/roundtrip-devtools-fresh.json`. Confirm the displayed recipe name.
3. Ensure the browser submission and Cloud backup refer to equivalent recipe content. If the name differs, the report flags this; a name match alone does not prove identity.

## Run

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_identity_mapping `
    --form .local/myspeidel-web-form.txt `
    --backup .local/roundtrip-devtools-fresh.json `
    --report .local/0020b-identity-candidates.json
```

Review:

```powershell
$Report = Get-Content .local/0020b-identity-candidates.json -Raw | ConvertFrom-Json
$Report | Select-Object form_recipe_name,cloud_recipe_name,name_equal,verified_mapping_count
$Report.mappings | Select-Object web_group,web_index,web_id,web_amount,web_acid,status,candidate_cloud_uuids | Format-Table -AutoSize
```

`CANDIDATE` means one Cloud UUID agrees on available quantity and, where present on both sides, acidity. It is **not** a verified cross-system identity; `AMBIGUOUS` indicates multiple plausible UUIDs, `INCONSISTENT` means a repeated web ID has no common candidate, and `UNRESOLVED` means no candidate was found. Time/step indices and unit conventions are not assumed to be equivalent across both APIs. Names and candidate UUIDs remain in `.local` and should not be committed.

This tool makes **no HTTP requests or recipe writes**, and produces no production mapping table. To verify candidates, collect independent evidence from an authoritative source or a controlled follow-up experiment.

Assisted-by: ChatGPT6-Astra
