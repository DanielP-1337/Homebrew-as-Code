# Supplier RFQ packet (0014)

This is an **unsubmitted, non-binding request for quotation (RFQ)**, NOT a
Shopware order, nor a native Shopware import profile. It does not contact
Braupartner, create shopping carts, or authorize payment.

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.supplier_rfq_cli `
    recipes/lebkuchen-zauber/recipe.yaml `
    --catalog catalogs/braupartner.verified.yaml `
    --output-prefix .local/lebkuchen-braupartner
```

Outputs:
- `*.rfq.json`: stable `homebrew-as-code/supplier-order-request-v1` structure,
  all recipe positions and source attribution.
- `*.rfq.csv`: semicolon CSV, suitable for human review or custom mapping.
- `*.rfq.md`: German RFQ text with all positions; copy into an email or attach.
- `*.rfq-report.json`: blockers, counts, unsourced items and review requirements.

Send the Markdown and CSV as an *inquiry* after reviewing them; optionally
include JSON for a future importer. Keep private customer data out of Git.

Variable-weight malt SKUs retain requested weight in grams instead of a
fabricated fixed-package count. All malt is required uncrushed. The
2026-10-18 source snapshot documents 7 of 15 recipe ingredients, while 8
remain for manual supplier matching. Availability/prices are not checked live.

No address, account, price, Shopware product ID or API credential is invented.
No overwrite of existing output files. Every RFQ needs merchant and user review
before a separate, explicit purchase process.
