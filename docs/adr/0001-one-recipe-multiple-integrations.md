# ADR-0001: One recipe. Multiple integrations. No vendor lock-in.

- **Status:** Accepted
- **Date:** 2026-10-18
- **Scope:** Homebrew-as-Code architecture and ownership of brewing data

## Context

Homebrew-as-Code maintains version-controlled brewing recipes. Its first
real-world equipment target is the **Speidel Braumeister 20 L**, with recipes
transferred through the MySpeidel cloud and the existing Wi-Fi controller.
Other consumers include BeerXML / BeerJSON export, supplier shopping workflows
and a possible future handover to a commercial brewery.

A brewing recipe must not become coupled to one controller, storefront or
industrial automation platform. Conversely, an equipment-specific protocol
must not dictate the canonical recipe schema. The current YAML contains an
`equipment` section describing the original brewing context; that is
**metadata**, not permission to embed controller commands in the domain model.

## Decision

**One recipe. Multiple integrations. No vendor lock-in.**

1. **Recipe domain (`recipe.yaml`) is the source of truth for the intended
   beer.** It describes ingredients, quantities, intended brewing stages
   (including mash temperature rests, boil duration and addition timing), and
   target product characteristics. A mash rest is a brewing requirement, not
   a PLC command.
2. **Equipment adapters translate, never own, recipe semantics.** The
   MySpeidel adapter maps supported recipe data to and from the cloud / device
   ecosystem. Heating control, pump cycles, valves, WLAN communications and
   device safety remain the responsibility of the vendor's controller.
3. **Exchange-format adapters** (BeerXML, BeerJSON) serialize the domain
   model for interoperability. They are not equipment adapters and must
   report missing or lossy fields rather than silently invent values.
4. **Supplier integrations** derive shopping requirements from the recipe.
   Merchant SKUs, Shopware IDs, prices, availability, packaging rules and
   payment credentials live in separate catalog / integration data, never
   in the canonical recipe. A request for quotation is not a purchase order.
5. **Brew sessions / batch records** capture what actually happened:
   measurements, ingredient lots, timestamps, deviations and outcomes.
   These records reference a version of the recipe without rewriting it.
6. **Commercial brewing** may receive an independent handover / production
   specification. No ISA-88, PLC, MES, or brewery-specific import schema is
   assumed until a real production partner confirms its requirements.
7. **Integration behavior must be explicit and reversible.** Read-only
   inspection, offline generation and manual review are the defaults. Cloud
   writes, device control, supplier orders and payments require separately
   designed, authorized workflows; no implicit execution is permitted.

## Dependency direction

```text
                        recipe.yaml
                            |
                    Recipe domain model
                            |
             validation / calculations / projections
                            |
      +---------------------+------------------------+
      |                     |                        |
  MySpeidel adapter     Format adapters        Supplier adapters
  (cloud/device)       (BeerXML/BeerJSON)      (RFQ / shopping)
      |
  Vendor-operated controller

  Brew session records ---> reference recipe ID + version
  Commercial handover  ---> derived independently when required
```

Dependencies point **from adapters to the domain**, never from the domain to
an adapter. Integration configuration and generated outputs are separate from
`recipes/`. Existing recipe files are not modified just to make an export fit.

## Data ownership and placement

| Concern | Owner / location | Not part of canonical recipe |
| --- | --- | --- |
| Intended ingredients, rest temperatures, addition timing, targets | `recipes/**/recipe.yaml` | No |
| Device UUIDs, cloud mappings, credentials | MySpeidel adapter / private config | Yes |
| Serialization defaults, validation and loss reports | Format adapter / generated reports | Yes |
| Shop IDs, supplier packs, live prices | `catalogs/`, private integration config | Yes |
| Real measurements and raw material lots | Future brew-session / batch records | Yes |
| Pump, valve, heating and PLC setpoints | Vendor/device-specific control system | Yes |

The current `equipment` recipe metadata may identify the originally tested
setup; operational controller configuration belongs outside the recipe. A
future schema revision can refine this distinction without breaking existing
recipes.

## Consequences

- One maintained recipe can be exported through multiple adapters without
  changing its identity or source data.
- Lossless roundtrips are tested where possible; deviations and unsupported
  fields are surfaced in a report and reviewed by a person.
- Equipment-specific calculations and commercial scale-up require confirmed
  equipment and process parameters; multiplying every ingredient by a volume
  factor does not produce an approved production recipe.
- Avoid generic abstractions for integrations that have no validated use case.
  The primary supported use case remains Braumeister 20 L via MySpeidel.

## Non-goals

- Replacing Speidel's controller or remotely driving pumps / heaters.
- Implementing a universal industrial brewery control standard in the recipe.
- Automatically submitting supplier orders or payments.
- Claiming any undocumented API writes or manufacturer import capabilities.

## Verification for future changes

Review changes against these questions:

1. Can the recipe be understood without importing a vendor SDK or an API model?
2. Could a second equipment adapter use the same recipe unchanged?
3. Are assumptions, rounding, unsupported fields and lossy mappings disclosed?
4. Are actual batch measurements recorded separately from target values?
5. Does any external write / order / equipment operation require explicit
   authorization and a separately reviewed implementation?

If the answer to any question is **no**, revise the design or record a new ADR
that explicitly supersedes this decision.
