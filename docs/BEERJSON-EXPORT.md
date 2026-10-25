# BeerJSON offline draft (0009)

The MySpeidel web screenshot advertises **BeerXML** (`.xml`) and proprietary
`.recipe` imports, **not BeerJSON**. These formats are not interchangeable.

The legacy exporter emits a document declaring version **3** and deliberately
produces an **incomplete draft**, not a schema-valid or upload-ready file.
The earlier moving-`main` schema statement is not an immutable conformance
contract. [0020o](0020o-BEERJSON-CONFORMANCE.md) now provides an explicitly pinned
`v.1.0` schema validator with a separate version policy. That snapshot's
`VersionType` accepts any number; schema validity alone does not establish
version support. The draft is not automatically relabeled or promoted by 0020o.

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
