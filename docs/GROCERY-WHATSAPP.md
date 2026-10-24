# Grocery shopping via WhatsApp (manual transfer)

This is an offline text adapter for the `grocery` channel of the supplier split.
It intentionally does **not** synchronize with WhatsApp or Android applications.
It does not contact any service, read credentials or send messages.

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.grocery_whatsapp_cli `
  recipes/lebkuchen-zauber/recipe.yaml `
  --catalog catalogs/braupartner.verified.yaml `
  --output .local/lebkuchen.grocery.whatsapp.txt

Get-Content '.local\lebkuchen.grocery.whatsapp.txt' -Raw -Encoding UTF8 | Set-Clipboard
```

Then open WhatsApp Web/Desktop, **review the pasted message**, and send it manually
in a chosen conversation. Do not assume the shopping-list app can import it.

The list is a shopping aid, not a calibrated dosing instruction. Recipe doses
are retained alongside practical *suggested* retail choices. Actual package
sizes and available variants must be decided at the store.

The adapter fails closed if the supplier classification introduces unknown
items or if this grocery-specific purchase advice has not been reviewed after
an ingredient change. Other channels (brewshop and water chemistry) are excluded.

Avoid hardcoding recipient phone numbers or sending automatically; the next
useful step is feedback from the person doing the grocery shopping.
