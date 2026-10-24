# Supplier channel split (offline)

The original combined 0014 RFQ included 15 items and asked the brewing specialist to supply everyday groceries and water treatment chemicals. This is not an appropriate default for Germany. The **supplier_split_cli** creates distinct supplier-facing and shopping documents instead.

## Usage

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.supplier_split_cli `
  recipes/lebkuchen-zauber/recipe.yaml `
  --catalog catalogs/braupartner.verified.yaml `
  --output-prefix .local/lebkuchen-suppliers
```

**Outputs:** `.brewshop.{json,csv,md}`, `.grocery.{json,csv,md}`, `.water_chemistry.{json,csv,md}`, `.split-report.json` (ten files total).

- **brewshop**: five uncrushed malts, Goldings pellets, S-04. Seven documented Braupartner product offers; not a verified quote or order. Variable weight remains in grams, never misrepresented as fixed packs.
- **grocery**: honey, Ceylon cinnamon, ginger, cloves, nutmeg, orange zest. Local food shopping plan; **not** sent to Braupartner. Fresh orange zest may be obtained from an untreated suitable orange; review personally.
- **water_chemistry**: calcium chloride **dihydrate** and calcium sulfate **dihydrate**. Sources could include a pharmacy or a specialist brewing/water-treatment supplier; this is **not** a claim that a pharmacy stocks them. Confirm exact hydration state and suitability for consumption, purity, appropriate labeling, and application before purchase. Do not substitute anhydrous salts or unknown technical grade; recipe dosing would change.

`CHANNELS` in `supplier_split.py` is deliberately explicit. Any new ingredient fails closed until assigned a supplier channel in code, with regression tests. Future iterations may move policy to versioned YAML after adding strict allow-list validation. Do not assign real suppliers, stock, price or Shopware product IDs without evidence.

No emails, credentials, checkout, payment, or HTTP calls are made. All outputs are **planning/RFQ only**. Existing `supplier_rfq_cli` continues to emit the legacy combined document and is **not** replaced; use `supplier_split_cli` for the separated workflow.
