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
recipes in the personal cloud recipe library. Beta 2 localization has not yet had
live dashboard acceptance testing.

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

No live Brewfather account, running user HA instance or Braumeister was contacted.
The card interaction test is not a screenshot/browser layout test. The localization
still needs user acceptance on the actual HA dashboard. PR #30 was open
at implementation time; matching Bridge/HA versions are required.

The install ZIP contains only the HBAC integration, card and documentation. It does
not update the Bridge or the Speidel integration, and contains no account data.
