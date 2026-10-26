# 0020q - MySpeidel Recipe Template & Import Payload Builder

This increment extracts a reusable reference template from an integrity-checked
private 20 L GET backup and builds an offline import draft from an independent
brew plan. It makes no HTTP requests. It does not create recipes.

## Boundaries

The template contains only categorized ingredient names and catalog UUIDs. It
contains no source recipe UUID, addition UUIDs, owner, brewer, dates, versions,
comments, amounts or process defaults. Catalog IDs remain account-specific;
this is not an anonymized or globally portable catalog. Keep it under `.local/`.
Resolution uses category plus case-insensitive, whitespace-normalized exact name.
Missing and ambiguous names fail; no fuzzy matching or invented references.
Only used references enter the candidate. Additional recipes need their own
brew plan, settings and sufficient reference entries. Template extraction retains
the existing backup tool's private 20 L scope.

The candidate is intentionally incomplete and is wrapped with its report. Never
send that wrapper or the candidate to an API. Recipe/addition identity policy,
server metadata, reference metadata and equipment identity need separate work.
Neither existing transport nor its permissions are changed.

The locally supplied OpenAPI contract documents POST `/v1.0/recipe` with `dryRun`
and recipe schema alternatives including `recipe_v5`. These schema names are not
values to blindly assign to `schema_version`. The schema requires identity and
metadata fields; its structural requirements do not establish who generates
those fields on create. PUT dry-run success is not evidence of POST success.
`--spec` runs the existing conservative validator against the POST body schema;
errors and unsupported constraints remain visible. No schema-valid or upload-ready
claim is made. `spec_sha256` hashes canonical JSON, not original file bytes.

## Mapping decisions

- Malt grams become kilograms; hop, other ingredient and yeast amounts stay grams.
- All process values come from the canonical recipe, never from the GET template.
- Boil groups sort by remaining minutes descending and receive consistent step numbers.
- Every non-hop ingredient requires explicit remaining minutes in settings. This
  resolves the legacy YAML conflict between five minutes remaining and five minutes
  contact after flameout without guessing from ingredient names.
- Zero remaining minutes means addition at boil end, not five minutes contact.
- The report retains unmapped contact time, fermentation temperature range, water
  chemistry, packaging, target ABV and target IBU. No fermentation duration is invented.
- Wort volume is explicit; packaged volume is not silently reused. Malt colors are
  explicit reviewed settings. Example colors are provisional, not vendor guarantees.
- Equipment is loaded and validated through the brew plan but is not automatically
  converted into a MySpeidel machine reference. No scaling occurs.
- The canonical example has 11.5 g yeast and 100 C boiling temperature. The manually
  edited cloud reference has 12 g and 99 C: the builder does not inherit those changes.

## Windows workflow

Apply on the repository with 0020o/o1 and 0020p already installed.

```powershell
Set-Location 'C:\dev\Homebrew-as-Code'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Template = ".local/myspeidel-template-$Stamp.json"
$Draft = ".local/myspeidel-import-draft-$Stamp.json"

.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_import_builder_cli template `
    --backup '.local/myspeidel-get-abgleich-20261025-220241.json' `
    --output $Template
if ($LASTEXITCODE -ne 0) { throw 'Template extraction failed' }

.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_import_builder_cli build `
    --plan 'brew-plans/lebkuchen-zauber-brew-001.yaml' `
    --template $Template `
    --settings 'examples/myspeidel-import-settings.json' `
    --output $Draft
if ($LASTEXITCODE -ne 0) { throw 'Draft generation failed' }
```

Optionally add `--spec '.local/vendor/myspeidel-openapi.json'` to build, using an
existing downloaded specification. Outputs are exclusive-create files under
`.local/`; originals are never overwritten. Exit 0 means the local artifact was
built, NOT that it is upload-ready. Inspect `candidate`, `report.blockers`,
`report.unmapped` and, when supplied, `report.create_contract`.

## Validation

Synthetic fixtures test unit conversion, chronological grouping, step numbering,
reference minimization, isolation from source metadata, other recipe values,
missing/duplicate references, malformed identities, null names, non-finite values,
missing colors and explicit timing requirements. No real recipe backups, account
identities or access credentials are included in this patch.

Next stage: resolve POST identity semantics and equipment/reference metadata,
validate a complete candidate, then implement a separately reviewed POST dry-run
workflow. A live create is outside this increment.
