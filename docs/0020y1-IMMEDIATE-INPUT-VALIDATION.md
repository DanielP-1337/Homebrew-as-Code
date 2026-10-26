# 0020y1 — Immediate Input Validation

A focused correction to the guided brew-day dialog. It does not expand batch
recording or change the MySpeidel API workflow. Recipe upload remains the main
integration priority.

The timestamp prompt now immediately rejects malformed timestamps, missing UTC
offsets, dates before the brew date and duplicate stage/instant combinations.
Equivalent instants expressed with different UTC offsets count as duplicates.
Only that prompt repeats; the selected stage and previous inputs remain intact.

Numeric prompts apply the existing record validator's limits immediately:

- Wort extract: 0–40 °P; fermentation apparent extract: -10–40 °P.
- Sample and volume temperatures: -5–110 °C.
- Measured and actual volumes: 0–100,000 L.
- Packaged beer cannot exceed a known produced volume, including zero.

These are existing software validation bounds, not instrument specifications.
Decimal commas and points are accepted; non-finite values are rejected.

A reading requires its sample temperature. A corrected-only reading prompts for
that temperature if it was previously left unknown. A volume requires its own
temperature. If neither raw nor corrected extract is supplied, a volume must be
entered so that an empty observation cannot reach confirmation. Production dates
before the brew date are re-prompted without losing the entered quantities.

`cancel` and Ctrl+C leave without saving. Confirmation, full record validation,
version backups, concurrency checks and TEST exclusion remain in place. No API
requests are made, and existing records do not require migration.

Regression tests reproduce the original accidental `2` at the timestamp prompt
and cover retry behavior, retained values, timezone-equivalent duplicates,
required temperatures, volume-only observations, yield consistency, decimal
input and negative fermentation apparent extract.
