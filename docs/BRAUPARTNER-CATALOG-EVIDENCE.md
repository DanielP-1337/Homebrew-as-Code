# Braupartner catalog evidence — 2026-10-18

This is a public, **historical product evidence snapshot**, NOT a live catalog, inventory, price quote, or authorized Shopware API integration. `catalogs/braupartner.verified.yaml` stores vendor-published SKU and size data, without customer data or secret tokens.

## Confirmed exact offers

| YAML ingredient | Merchant SKU | Sales unit | Source |
| --- | --- | --- | --- |
| Pale Ale Malt | `10-303A-UGS` | uncrushed, variable kg, from 1 kg, 0.5 kg increments | https://www.braupartner.de/pale-ale-malz-ungeschrotet |
| Munich Malt Type II | `10-302A-UGS` | same, availability may be unavailable | https://www.braupartner.de/muenchner-malz-typ-ii-ungeschrotet |
| CaraMunich II | `10-210A-UGS` | same; Weyermann CARAMÜNCH II | https://www.braupartner.de/caramuench-r-ii-malz-ungeschrotet |
| Melanoidin Malt | `10-308A-UGS` | same | https://www.braupartner.de/melanoidin-malz-ungeschrotet |
| Chocolate Malt | `10-009A-KLU` | 100 g uncrushed fixed pack | https://www.braupartner.de/malz |
| Goldings pellets | `30-509A` | variable purchase in 100 g steps; 100 g equivalent purchasing unit | https://www.braupartner.de/goldings-hopfenpellets |
| Fermentis SafAle S-04 | `237-S-04-115` | 11.5 g dry yeast sachet | https://www.braupartner.de/hefe |

The Goldings SKU is actually weight-variable in the merchant UI (100 g increments); the catalog treats a 100 g increment as an **offline purchasing unit for the RFQ only**, not a confirmed Shopware API quantity unit. The same caveat applies to all SKU quantities until the merchant confirms API cart semantics.

Four variable-weight malts intentionally have **no fake 500 g pack** under `packs`. They use separate `offer` metadata: minimum 1,000 g, increment 500 g. Thus 450 g CARAMÜNCH II becomes an RFQ quantity of 1,000 g; 250 g Melanoidin also becomes 1,000 g. The 0012 resolver ignores `offer`, so a misleading cart is impossible.

Chocolate's standard variable-weight listing `10-009A-UGS` was reported unavailable when checked, but 100 g uncrushed SKU `10-009A-KLU` is listed separately. Inventory and prices change: do not treat the saved availability as current or buy without confirmation.

## Usage

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.supplier_evidence_cli recipes/lebkuchen-zauber/recipe.yaml --catalog catalogs/braupartner.verified.yaml --output .local/lebkuchen-evidence.json
.\.venv\Scripts\python.exe -m homebrew_as_code.supplier_catalog_cli recipes/lebkuchen-zauber/recipe.yaml --source catalogs/braupartner.verified.yaml --output-prefix .local/lebkuchen-verified
.\.venv\Scripts\python.exe -m homebrew_as_code.shopping_cli recipes/lebkuchen-zauber/recipe.yaml --catalog .local/lebkuchen-verified.catalog.yaml --output-prefix .local/lebkuchen-rfq-003
```

All commands run locally; no network calls, no orders or checkout. Existing files are not overwritten. To share the RFQ with Braupartner, include the evidence JSON and CSV and ask them to confirm quantities and fulfillment. No Shopware internal 32-character product IDs have been inferred.

## Limits and follow-up

Unresolved recipe items: mild honey, cinnamon sticks, fresh ginger, cloves, nutmeg, orange zest, calcium chloride and calcium sulfate. Only source-verified identical products may be added. Do not assume spices and salts have identical grades or fit for brewing. Malts are uncrushed by design. Brewery-side BeerXML extract yields, beer color and current prices are **not** derived from these SKUs. Public vendor pages may change at any time.
