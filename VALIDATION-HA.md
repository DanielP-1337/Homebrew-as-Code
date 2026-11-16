# HBAC 0.5.0-beta.2 – empty Brewer’s Friend account fix, 2026-11-16

The user reported setup failure with a newly created, empty Brewer’s Friend account.
A read-only live collection request confirmed HTTP 404 with the JSON object
`{"message":"not-found","detail":"no recipes found"}`. No recipe data or account
credentials are included in this record or the test fixtures.

Only this exact response from the collection endpoint is normalized to an empty
list. A 404 for a recipe detail or another error payload remains an error. Setup
errors now identify the provider field, sanitized diagnostic logging is available,
and the reconfiguration heading describes all recipe sources in all eight locales.

79 HA tests passed, including empty-account setup, catalog handling, rejection of
other 404 responses and safe provider-specific diagnostics. Frontend/i18n tests
and Ruff passed. Populated-account import and new-source device upload still need
live acceptance. The records below describe preceding versions.

---

# HBAC 0.5.0-beta.1 – source import verification, 2026-11-16

- 74 HA/converter/API tests passed in Linux Docker (Python 3.13.18, HA 2026.2.3).
- New coverage: Brewer’s Friend list pagination, repeated-page detection, API-key
  header, XML detail endpoint, HTTP/auth/rate-limit/redirect failures, bounded
  responses and invalid IDs; no key leakage in error messages.
- BeerXML coverage: multi-recipe selection, canonical Celsius/minute units,
  legacy XML encoding, XML entity/DTD rejection, malformed/oversized documents,
  duplicate/missing fields, fractional/non-finite values, unsupported rests,
  file path traversal and symlink rejection, source snapshots and no device calls.
- Full HA service import without a cloud account, and adding Brewer’s Friend to an
  existing Brewfather entry, passed. Existing queue/upload tests still pass.
- Frontend interaction tests now cover provider selection, browser file input,
  oversized file rejection before reading, folder/file/recipe selection and preview.
- Eight locale catalogs each contain 195 complete keys; i18n and guide tests passed.
- Ruff and Git whitespace checks passed. Automated UI tests use a minimal DOM,
  not a real browser. No live Brewer’s Friend account or new device upload was tested.

The synthetic test file and manual acceptance steps are in [SOURCES.md](SOURCES.md).
The earlier hardware and localization acceptance records below remain historical;
they do not establish hardware acceptance of the new source adapters.

---

# HBAC 0.4.0-beta.2 – verification, 2026-11-15

## Beta 2 localization

- 39 HA/conversion/API tests passed, including native error translation keys,
  static serving of locale JSON and both card types, and eight native HA catalogs.
- Eight complete catalogs, each with 165 keys; key/type/placeholder parity checked.
- Frontend tests cover the operating card and guide, HA profile language changes,
  per-card overrides, regional fallback, partial additional user JSON, malformed
  JSON, invalid placeholders, safe locale paths and complete offline en-US fallback.
- Persisted Beta 1 German messages are translated for display without changing
  the stored recipe programs. Language changes do not send service calls.
- Existing card interaction tests still pass. Device conversion/upload logic is
  unchanged; the full 547 core tests passed for the preceding publication.

The user reported a successful Beta 1 two-recipe Brewfather upload with subsequent
matching content readback on 15 November 2026. MySpeidel's device view also showed
the names and the selected recipe's rests. This does not establish creation of full
recipes in the personal cloud recipe library.

## User-operated Beta 2 localization acceptance, 2026-11-15

The user installed Beta 2 in their existing HA instance and confirmed that language
switching works after placing `language` inside each card configuration. The supplied
screenshot shows the HBAC operating card in English while the surrounding HA editor
still displays German ("Fertig"). Visible translated content includes the introduction,
instruction heading, source selection, buttons, recipe/batch ID, mash-in temperature
and boiling temperature. This is live dashboard evidence in addition to the automated
tests, not an automated browser test.

The preceding configuration example used Dutch (`nl`), but the screenshot shows
English; it is not evidence that all eight languages or every help section were
manually reviewed. Those remain covered by catalog/rendering tests, with broader
native-speaker acceptance still welcome. No new hardware upload is claimed for this
localization test. The screenshot is retained in the conversation, not published.

See [the full dashboard language example](I18N.md#select-a-language). Set `language`
on both the operating card and help card, not at dashboard or view level. Remove
both overrides to follow the HA user's profile language.

## Results

- **36 original HA/converter/API tests passed** in Linux Docker, Python 3.13.18,
  Home Assistant 2026.2.3, pytest-homeassistant-custom-component 0.13.316.
- **12 existing HBAC Bridge export/upload tests passed** on Python 3.11.2.
- **18 checks passed against the actual PR #30 Bridge encoder**: all nine slots
  in Celsius and Fahrenheit. No network or device connection is made by this check.
- Dashboard interaction test passed under Node.js with a minimal DOM and simulated
  HA WebSocket responses: batch selection, preview, review, explicit replacement
  confirmation, one upload request, job status, mash-in override and safe source-name rendering.
- JavaScript syntax check passed; Ruff checks passed for all new Python modules/tests/scripts.

## Covered behavior

HA setup registers services and static card resources, loads the upload sensor,
and unloads cleanly. Config flow validates access to both recipe and batch scopes;
reconfiguration replaces credentials without changing the selected Bridge entry.
The workflow calls the real HA service registry with simulated Bridge handlers.

Conversion uses the batch recipe snapshot, preserves source data, validates whole
numbers/capacities, groups simultaneous hop alarms, reports omitted additions,
and rejects unsupported rests. Preview snapshots cannot change underneath an upload.

Upload tests cover readiness refusal, stale revision, explicit replacement consent,
lost POST response, cancellation, restart with unknown submission, known-job status
after restart, expired/mismatched job responses, and persistent error visibility.
API tests cover pagination, batch details, authentication failures, 404, 429 cooldown
and refusal to follow redirects. No real credentials are included in fixtures.

## Reproduce

From the HBAC source directory:

```text
pytest -c tests_ha/pytest.ini tests_ha -q
PYTHONPATH=src pytest tests/test_bridge_export.py tests/test_bridge_upload.py -q
node tests_frontend/card.test.cjs
node --check custom_components/hbac/frontend/hbac-card.js
python scripts/check_bridge_contract.py PATH_TO_PR30/braumeister_bridge/app/bridge.py
```

The HA test dependencies are pinned in `requirements_test_ha.txt`.

## Limits

The automated tests did not contact a live Brewfather account, running user HA
instance or Braumeister. The card interaction test is not a screenshot/browser
layout test; the separate user-operated checks are described above. PR #30 was open
at implementation time; matching Bridge/HA versions are required.

The install ZIP contains only the HBAC integration, card and documentation. It does
not update the Bridge or the Speidel integration, and contains no account data.
