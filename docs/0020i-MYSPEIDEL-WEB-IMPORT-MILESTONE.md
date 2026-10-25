# Milestone 0020i — Independent BeerXML import into MySpeidel

**Date:** 2026-10-25
**Status:** Confirmed manual web-import workflow; semantic differences remain
**Recipe:** `recipes/lebkuchen-zauber/recipe.yaml` (Lebkuchen-Zauber 2026)
**Scope:** Web upload, interactive ingredient matching, recipe editor and saved recipe; **not** a direct Cloud API write contract.

## Acknowledgment: Brewfather reference

The investigation was unblocked by exporting Brewfather's **Sample Blonde Ale** as BeerXML and successfully importing it using the MySpeidel website. That working reference demonstrated a usable format and gave us the first reliable comparison case after earlier failing experimental XML uploads. Credit for this reference export and the successful starting point belongs to **Brewfather**.

Homebrew-as-Code subsequently implemented an **independent** BeerXML 1.0 exporter for its own canonical YAML recipe. It does not redistribute the Brewfather sample or copy proprietary `BF_*` extensions. BeerXML format interoperability does not imply a partnership, endorsement or official certification by Brewfather or Speidel. Product names are trademarks of their respective owners.

## Confirmed workflow and integrity

1. Exported `Lebkuchen-Zauber 2026 - HBAC 0020h TEST` from the canonical YAML with explicit, **unverified trial assumptions** for missing product and brewhouse values.
2. Uploaded the independently generated XML via MySpeidel's web interface, reached the ingredient matching screen, reviewed the recipe and saved it in the personal recipe list on 2026-10-25.
3. Original **0020h** local XML SHA-256: `78841ca35d4d175c2f315488aef2c273f758e538e9f14a8237451f1faa5094b3`.
4. **0020i** added optional `--emit-target-og` to encode the YAML 14 °Plato **target** as calculated BeerXML SG. A subsequent MySpeidel editor observation showed 14 °P / 1.057 SG. The distinct 0020i file digest was not captured here; do not attribute the 0020h digest to 0020i.
5. User reported **282 local pytest tests passed** after applying 0020i. This confirms local regression tests, not independent full BeerXML conformance.

The successful Brewfather reference contained a Sample Blonde Ale, **not** the Lebkuchen-Zauber recipe. The original reference XML remains private and is **not committed**.

## Observed semantic fidelity — 0020i MySpeidel editor

| Field | Canonical YAML / intended export | Observed MySpeidel UI | Interpretation |
| --- | --- | --- | --- |
| Original gravity | **Target** 14 °P | 14 °P / 1.057 SG | Target representation recognized; not a measured original gravity |
| Packaged/batch volume | 20 L (documented BeerXML approximation) | 20 L | UI agrees, packaging loss unverified |
| Grains | Five malts, **5.1 kg total** | Five named malts, 5.1 kg | Quantities and displayed names matched |
| Mash steps | 63 °C/20 min; 72 °C/45 min; 78 °C/10 min | Same three active rests | Matched; zero-minute placeholders also appear |
| Mash-in temperature | 60 °C | 63 °C | **Difference:** MySpeidel displays first rest temperature; exact importer mapping not established |
| Boil | 60 min | 60 min | Matched; UI shows 99 °C versus YAML 100 °C |
| Hop | Goldings pellets, 60 g, 2.9% alpha, 60 min remaining | Same | Ingredient and timing matched |
| Honey | 250 g; 10 min remaining | 250 g displayed with first hop stage (60 min remaining) | **Timing is not preserved**; do not infer correct honey schedule |
| Spices | 5-min additions incl. cinnamon, ginger, orange zest, cloves and nutmeg | Cinnamon 5 g, ginger 12 g, orange zest 8 g shown in 5-min stage | Partial visual confirmation; check cloves/nutmeg in editor |
| Yeast | S-04, 11.5 g | S-04, 12 g displayed | Could be UI rounding or data loss; verify raw stored quantity |
| Fermentation | Temperature target 18–20 °C; no defined duration | 0 °C / 0 h | Structured phase not exported without explicitly declared duration |
| Mash/sparge water | 23 L / 5 L | 0 / 0 L | In NOTES only; not mapped to structured MySpeidel fields |
| Beer color | No manufacturer-verified values | 32.2 EBC | Calculated from trial malt colors; **not brew-day approved** |
| Bitterness | 21 IBU desired target | 19.0 IBU | MySpeidel-derived value differs; algorithm unknown |

**Do not treat this import as brew-day approval.** Color/yield inputs, 24 L pre-boil volume, 70% efficiency, water characteristics and ingredient identity matching were explicitly experimental. Check product specifications, water chemistry, hop utilization and actual equipment behavior before brewing.

## IBU calculation: evidence vs hypotheses

- With the same nominal Goldings addition, the **0020h** recipe with no structured OG displayed **31.5 IBU**; the **0020i** recipe with an exported 14 °P target OG displayed **19.0 IBU**. This correlation suggests the importer recalculates bitterness and that gravity may be relevant. **It does not identify or prove the MySpeidel formula.**
- Water chemistry can affect wort pH, hop bitter substance extraction/utilization and perceived bitterness. Bicarbonate controls much of water alkalinity, calcium influences mash chemistry, sulfate accentuates perceived bitterness and chloride tends to emphasize fullness. **Perceived bitterness and analytical IBU are different quantities.**
- Both trial XML files retained 23/5 L brewing water and salts only as human-readable NOTES. No verified structured water-profile input to MySpeidel's IBU calculation was demonstrated. Thus there is **no evidence here that MySpeidel incorporates water chemistry into its numeric IBU estimate**.
- Braumeister recirculation through the malt pipe is characteristic of **mashing**. Effects on boil-stage hop utilization and any machine-specific correction factors must be established independently, rather than inferred from the pump feature.

General scientific background (not proof of MySpeidel implementation):
- [BJCP: Brewing Water](https://www.bjcp.org/exam-certification/program/studying/beer-exam-study-guide/water/)
- [American Homebrewers Association: Understanding Water for Homebrewing](https://homebrewersassociation.org/how-to-brew/understanding-water-for-homebrewing/)
- [A Hands-On Guide to Brewing and Analyzing Beer in the Laboratory](https://pmc.ncbi.nlm.nih.gov/articles/PMC9286407/)
- [Brewfather: Water Chemistry & Adjustments](https://docs.brewfather.app/brewing-knowledge/water-chemistry)

## Integration boundary and follow-up

- **Confirmed:** Independent BeerXML -> MySpeidel web upload -> manual catalog review -> editor -> saved personal recipe.
- **Still blocked:** Official MySpeidel **Cloud API** create/update contract. Do not characterize the web upload as a REST API solution.
- **Not proven:** Lossless roundtrip, authoritative ingredient identity matching, preserved honey addition time, structured water/fermentation, recipe calculated IBU equivalence or verified equipment performance.
- Preserve the private, unmodified Brewfather reference and XML/test reports outside Git (`.local/`). Publish only our own independent exporter, tests, notes and non-sensitive observations.
- Record further observations through the offline 0020i comparison tool and investigate individually; avoid generalizing a single UI behavior to the entire vendor format.

**Acknowledgment:** Thank you to Brewfather for providing the interoperable BeerXML reference that enabled this milestone, and to MySpeidel/Speidel for supporting the interactive web import workflow.
