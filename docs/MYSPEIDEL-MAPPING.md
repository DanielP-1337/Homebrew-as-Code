# MySpeidel recipe mapping: confirmed offline subset

Run from repository root:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.myspeidel_mapper_cli
```

The command requires **no MySpeidel credentials** and performs **no network calls**.
It prints an explicitly non-uploadable JSON *fragment* with only fields seen
in a successful read-only inspection of an existing 20 L recipe:

| Local YAML | MySpeidel detail field |
| --- | --- |
| `mash.mash_in_temperature_c` | `mashing.temperature` |
| `mash.steps[].temperature_c` | `rest.steps[].temperature` |
| `mash.steps[].duration_min` | `rest.steps[].duration` |
| `boil.temperature_c` | `boil.boiling_temperature` |
| `boil.duration_min` | `boil.boiling_duration` |
| `water.mash_l` | `mashing.adds.water.water_amount_start` |
| `water.sparge_l` | `rest.water_amount_addition` |

The water amounts are *tentative semantic mappings* based on API field names;
confirm their units and practical interpretation on a known recipe before
allowing a writer. Likewise, ensure the device interprets the rest and boil
times as expected. The source contains 3 rests; the inspected example had 4,
which is not a conflict.

**Not implemented:** hop scheduling (`boil.steps[].duration` meaning is not
verified), hop/malt/other ingredient IDs and amounts, water type UUID, required
recipe_v5 envelope/metadata, fermentation, maturation, keg parameters,
validation against MySpeidel write schema, upload and machine synchronization.

Do **not** send this JSON fragment to MySpeidel `POST` or `PUT` endpoints.
It is for comparing structure before implementing an API writer.
