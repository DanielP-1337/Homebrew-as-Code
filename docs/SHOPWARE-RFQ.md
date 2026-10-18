# Offline purchase request / Shopware 6 adapter preparation

This is a **request for quotation (RFQ)**, not a purchase order and **not** a native Shopware import file. It does not contact Braupartner or any service.

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.shopping_cli recipes/lebkuchen-zauber/recipe.yaml --output-prefix .local/lebkuchen-shopping
```

Output:
- `.local/lebkuchen-shopping.rfq.json` – structured vendor-neutral request, recipe and ingredient requirements.
- `.local/lebkuchen-shopping.rfq.csv` – UTF-8, semicolon-delimited spreadsheet for supplier staff / email attachment.
- `.local/lebkuchen-shopping.shopware-cart-preview.json` – *not ready* until every item is explicitly mapped to a verified vendor product and pack size.

Optional **private** `.local/catalog.yaml` mapping:

```yaml
"Pale Ale Malt":
  sku: "REPLACE-WITH-REAL-MERCHANT-SKU"
  pack_g: 1000
  shopware_product_id: "0123456789abcdef0123456789abcdef"
```

The values above are **fictional placeholders**, not supplier facts. Don't use them as a real catalog mapping. Provide the mapping using `--catalog .local/catalog.yaml`. Do not commit private supplier catalog or quote files without checking their content.

Supplier staff can open the CSV and **manually resolve SKU, pack quantities, stock, pricing, shipping and contact**. A supplier wishing to automate ingestion would need to implement a custom RFQ importer or map CSV columns to their processes; native Shopware Import/Export does *not* guarantee order import from this CSV. Only a supplier-approved Store API integration should later submit `/store-api/checkout/cart/line-item`; checkout/payment is intentionally not implemented.

The exporter preserves whole-grain malt requirements and includes yeast, hopping, honey, spices and water salts. It does not include packaging supplies, shipping, customer address, or payment details. Quantities in grams describe recipe requirements; `purchase_quantity` is calculated only with a supplied package size. It never guesses SKUs, IDs, packages or prices.

Official docs: https://developer.shopware.com/docs/guides/development/integrations-api/ and https://docs.shopware.com/en/shopware-en/settings/importexport
