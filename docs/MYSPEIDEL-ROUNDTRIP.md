# MySpeidel controlled browser-to-API roundtrip (0008)

The current code does **not** create MySpeidel recipes and has **no API write endpoints**.
Create a dedicated **private test recipe manually in the web UI**. Do not edit
existing recipes. Use distinctive, simple numeric values, for example:

- Braumeister 20 L; 60 minute boil.
- Two hop additions, at 60 and 20 **minutes before end**.
- Known malt mass, e.g. 1.20 kg; two hop amounts, e.g. 11 g and 7 g.
- Other required fields: fill in according to actual device/form constraints.

Save the web recipe. Then run:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_roundtrip_cli
```

1. Log in. Recipe ordering comes from the API and is not guaranteed stable.
   Choose `yes` to display **private recipe names and creation dates on screen**
   for unambiguous selection, or Enter (default) to see only numeric indexes.
   This prompt does not write data to disk or send additional requests.
2. Select the **test** recipe's numeric index and enter the values *as shown
   in the web editor*: `60` and `60,20`.
3. Enter `yes` to permit exactly one detail GET and display numeric evidence.
4. Compare `api_boiling_step_durations_raw`, `api_step_hop_counts`,
   and `candidate_matches` with the known web form. A matching hypothesis
   is not proof, particularly if the API inserts extra no-hop steps.

This analysis prints **no recipe names, UUIDs, credentials or complete API
responses**, and writes no files. Numeric amounts/timings may still be private,
so consent is required. The API detail is obtained via the existing restricted
GET-only MySpeidel client. Authentication uses the existing in-memory login.

**Important**: Recipe indexes are not stable. Prefer the opt-in name/date display
when multiple recipes exist. Avoid copying the displayed private names into
issue reports, CI logs or the public repository. No UUIDs are printed.

Do not place captured raw MySpeidel JSON, cookies, tokens, `.recipe` exports or
account metadata in this public Git repository. All comparison results keep
`upload_ready: false` and `api_payload: null`.

Unverified: whether `boil.steps[].duration` means step spans, remaining time,
elapsed time, or something else. Validation against multiple controlled web
recipes and catalog UUID lookup remain future work.

## Mixed-ingredient GET diagnostics (0008b)

The consented roundtrip report includes `boil_addition_diagnostics`: each step
reports counts, raw numeric amounts and acid values under `adds.hops` and
`adds.ingredients`, as well as boolean presence of UUID reference fields.
No names, UUID values, tokens or API response objects are output. Numeric
quantities are still private and require explicit confirmation before GET.

The API collection name does not prove an ingredient's botanical classification.
The reference presence flags do not establish catalog validity.
The command remains GET-only and produces `upload_ready: false` and
`api_payload: null`.
