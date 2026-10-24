# MySpeidel catalog references – offline discovery and resolution (0019d)

This is an **offline-only**, conservative reference resolver. It does **not**
add endpoints to `MySpeidelClient`, perform a cloud GET, or POST any recipe.
It inventories candidate catalog GET paths from the official locally downloaded
OpenAPI 3.0 document; paths in the report are **not automatically approved for
access**. User confirmation of the source and type of each entry is required.

1. Download the official OpenAPI document to `.local/vendor/myspeidel-openapi.json`
   as documented for patch 0019a.
2. Copy `catalogs/myspeidel.catalog-snapshot.example.yaml` into
   `.local/myspeidel.catalog-snapshot.yaml`.
3. Inspect the API GET inventory in the report. Obtain an authorized catalog
   response separately if such an endpoint exists and is permitted. Never use
   a guessed endpoint or scrape account data.
4. Populate snapshot entries with actual UUIDs, exactly documented GET paths,
   matching catalog categories and manually confirmed names. Keep snapshots
   and reports under `.local/` and out of public Git.
5. Run:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_catalog_resolver_cli `
    recipes/lebkuchen-zauber/recipe.yaml `
    --spec .local/vendor/myspeidel-openapi.json `
    --snapshot .local/myspeidel.catalog-snapshot.yaml `
    --output .local/myspeidel-catalog-resolution.json
```

Inspect `documented_catalog_get_endpoints` and `rows` in the report. The report
may contain real catalog UUIDs, so **do not paste it publicly without review**.
Empty snapshots are valid and produce an unresolved report. All ambiguous,
missing, wrong-category and unconfirmed entries remain blocked. The source
schema does not guarantee that a hop-like spice belongs to the `ingredient`
container: our controlled MySpeidel test observed cinnamon under `adds.hops`.

No catalog UUID, timestamp, merchant identifier or API payload is guessed.
A positive match **does not** imply a validated `recipe_v5` write request.
