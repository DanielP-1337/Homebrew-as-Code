# Supplier Catalog Mapping — offline MVP

This is **not a native Shopware import**, nor an order, and there are no network calls.
Use merchant-confirmed package sizes, SKUs, and optionally Store API product IDs.

1. Copy `catalogs/braupartner.example.yaml` to `.local/braupartner.catalog.yaml`.
2. For each ingredient add confirmed package variants (`packs:`), e.g.:

   ```yaml
   CaraMunich II:
     packs:
       - pack_g: 500
         sku: "confirmed-merchant-sku"
         whole_grain: true
         verified: true
         availability: unknown
         # shopware_product_id: 32-hex-id-only-if-merchant-confirmed
   ```

   This is an **illustrative structure**, not a claim about actual available packs or SKUs.
   Malts must have `whole_grain: true`. Unverified variants are ignored.
3. Run:

   ```powershell
   python -m homebrew_as_code.supplier_catalog_cli recipes/lebkuchen-zauber/recipe.yaml --source .local/braupartner.catalog.yaml --output-prefix .local/lebkuchen-catalog
   python -m homebrew_as_code.shopping_cli recipes/lebkuchen-zauber/recipe.yaml --catalog .local/lebkuchen-catalog.catalog.yaml --output-prefix .local/lebkuchen-rfq-002
   ```

4. Review `.local/lebkuchen-catalog.catalog-report.json` and the RFQ before sending externally.

The algorithm chooses **one verified SKU per ingredient**, minimizing excess grams, then number of packs. It does not combine different SKUs, assume stock/price, or place orders. Missing ingredients are marked `UNMAPPED`; missing confirmed IDs or stock are marked for review. The existing Shopware cart preview remains blocked unless all entries have valid merchant product IDs, SKUs and package sizes. `cart_ready` is a *data-review signal only*, not permission to transmit or checkout.

A 32-character hexadecimal Shopware ID is only syntax-checked; ownership/existence can be verified only by the merchant. The package `verified` flag is a manually asserted source record, not proof of availability.
