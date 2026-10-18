# BeerJSON offline draft (0009)

The MySpeidel web screenshot advertises **BeerXML** (`.xml`) and proprietary
`.recipe` imports, **not BeerJSON**. These formats are not interchangeable.

This patch targets the *current* `beerjson/beerjson` schema, whose internal
`beerjson.version` is **3**, despite the project being described as BeerJSON 1.0.
Do not change `3` to `1` to label it "BeerJSON 1.0": the current schema does
not accept that value. Review/pin the official schema before implementing
validation. The exporter deliberately produces an **incomplete draft**, **not**
a schema-valid or upload-ready file.

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.beerjson_cli `
  recipes/lebkuchen-zauber/recipe.yaml `
  --output .local/lebkuchen-zauber.beerjson
```

Writes `.local/lebkuchen-zauber.beerjson` and a separate
`.local/lebkuchen-zauber.report.json` explaining incomplete required fields.
Do not import this draft to MySpeidel or commit local exports to public Git.

Preserved: five grain quantities (kg), honey as a fermentable, Goldings hops
(amount/alpha/timing), five spices (g/timing), original gravity (Plato), ABV,
carbonation and boil duration. `timing.duration` means **contact time within
the boil** in BeerJSON; for a normal addition at N minutes before the end,
this equals N minutes when the addition stays until flameout. This should not
be confused with MySpeidel's proprietary `boil.steps[].duration` field.

Missing required fields include recipe author, brewhouse efficiency, volume
into fermenter (packaged volume != fermenter volume), malt/honey color and
yield. Mash rest data and fermentation details are not exported until their
required fields and process semantics can be represented without guesses.
An actual MySpeidel import roundtrip requires a **separately validated
BeerXML 1.0 exporter**, planned as a follow-up. Neither API writes nor browser
uploads are implemented here.

Sources: https://github.com/beerjson/beerjson/tree/main/json
