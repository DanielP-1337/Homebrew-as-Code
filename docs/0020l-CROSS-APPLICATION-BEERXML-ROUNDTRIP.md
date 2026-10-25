# 0020l — Cross-Application BeerXML Roundtrip (2026-10-25)

## Scientific status and credit

**Observed:** Homebrew-as-Code (HBAC) exported independent BeerXML 1.0 from
`recipes/lebkuchen-zauber/recipe.yaml`. The same export reached the MySpeidel
recipe editor and was saved through manual ingredient matching. It was also
imported successfully by Brewfather, which reexported a BeerXML document.

**Credit:** A BeerXML sample *exported by Brewfather* was the first confirmed
successful MySpeidel web-import reference and enabled controlled compatibility
experiments. The HBAC exporter is independently implemented against the public
BeerXML 1.0 specification: <https://www.beerxml.com/beerxml.htm>.
The original Brewfather sample and its complete reexport are **not redistributed**.
Brewfather and MySpeidel are third-party trademarks; this project is not endorsed
by either vendor.

## Observations from the Brewfather UI and returned BeerXML

| Check | HBAC source | Brewfather observed | Interpretation |
| --- | --- | --- | --- |
| Packaged volume | 20 L | 20 L | Matched |
| Preboil volume | 24 L (explicit *test assumption*) | 24 L | Matched |
| Efficiency | 70% (explicit *test assumption*) | 70% | Matched |
| Malts | Five, 5.1 kg total | Five, 5.1 kg | Matched in visible data |
| Honey | 250 g fermentable | 250 g sugar | Matched |
| Goldings | 60 g, 2.9%, 60 min | Same | Matched |
| Spices | Five at 5 min, including 0.2 g cloves and 0.3 g nutmeg | All five displayed | Matched |
| Yeast | 11.5 g S-04 (0.0115 kg, weight flag true) | UI 11.5 g; reexport `AMOUNT=11.5`, no `AMOUNT_IS_WEIGHT` | **Semantic hazard** on reexport |
| Mash rests | 63/20, 72/45, 78/10 | Same | Matched |
| Carbonation | 2.2 volumes | 2.2 volumes | Matched |
| IBU | YAML target 21; source not a calculated IBU assertion | 21.2 (Brewfather), vs 19.0 (MySpeidel) | Different calculations; algorithm unverified |
| Colour | Malt properties *assumed* | 32.5 EBC, vs 32.2 in MySpeidel | Calculation difference; not calibrated |
| ABV | YAML target 5.7% | 6.17% forecast | **Not equivalent** |
| Water split | YAML notes: 23 L mash + 5 L sparge | 13.77 L + 13.35 L, calculated using equipment profile | **Not equivalent** |
| Fermentation duration | Not specified in YAML | 14 days, 20 °C from Brewfather profile | **Not authoritative** |

The numeric estimates above are UI readings and reexport observations, not
brewhouse measurements. No live brew has been conducted. Ingredient identities,
water chemistry, equipment losses and calculated bitterness are not validated for
brew-day use. The separate MySpeidel Cloud POST/PUT contract remains unverified;
manual BeerXML web import is the supported experimental path demonstrated here.

## Offline, private semantic comparison

Keep both full documents under `.local/` (ignored by Git). Example:

```powershell
.\.venv\Scripts\python.exe -m homebrew_as_code.beerxml_cross_app `
  --source-xml .local/lebkuchen-zauber-0020i-test.xml `
  --reexport-xml .local/Brewfather_BeerXML_LebkuchenZauber2026HBAC0020iTEST_20261025.xml `
  --report .local/0020l-cross-app-report.json
```

This tool compares standard-field ingredient multisets, masses, hop times,
mash rests, basic volumes and efficiencies, and flags yeast quantity semantics
rather than trusting a user-interface `DISPLAY_AMOUNT`. It does **not** parse
Brewfather proprietary IDs or claim an all-fields/lossless conversion. A report
with ingredient names and quantities is private; do not stage it. Never use
Brewfather-generated equipment or fermentation defaults to update canonical YAML
without separate evidence.

## Reproducibility and remaining work

- Source recipe: `recipes/lebkuchen-zauber/recipe.yaml` v1.3.0.
- Exporter: independent 0020i BeerXML implementation.
- MySpeidel upload/save: observed 2026-10-25; 14 °P, 20 L, 5.1 kg malt,
  three mash rests and 19.0 IBU displayed; structured water and fermentation
  empty; mash-in 63 °C instead of YAML's 60 °C.
- Brewfather import/reexport: observed 2026-10-25; source and reexport retained
  locally only, with corresponding private checksums to be captured by tester.
- Unresolved: Brewfather yeast XML amount semantics, water/equipment defaults,
  fermenter profile defaults, differences in IBU/colour/ABV calculations.
- Requirement for a future **lossless** claim: verify all recipe attributes,
  exact ingredient semantics and idempotent re-import across the applications.
