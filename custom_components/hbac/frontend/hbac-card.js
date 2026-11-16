/* BEGIN GENERATED I18N: run scripts/build_frontend_i18n.py after editing en-US/message_sources/core */
const HBAC_VERSION = "0.5.0-beta.1";
const HBAC_EN_US = {"ui.subtitle": "Review recipes and transfer them to the Braumeister", "ui.loading": "Connecting to HBAC…", "ui.reconnect": "Reconnect", "ui.select_step": "1 · Select a recipe or batch", "ui.source": "Source", "ui.recipes": "Recipes", "ui.batches": "Batches (their own recipe)", "ui.load_catalog": "Load source list", "ui.selection": "Selection", "ui.choose": "Please select", "ui.empty_catalog": "No entries found. You can also enter a known ID.", "ui.source_id": "Recipe/batch ID (direct entry supported)", "ui.mash_in": "Mash-in temperature °C – blank: first rest", "ui.boil_temperature": "Boil temperature °C", "ui.preview": "Fetch and preview", "ui.choose_error": "Select a recipe or batch, or enter its ID.", "ui.review_step": "2 · Review conversion", "ui.add": "Reviewed · Add to upload list", "ui.queue": "3 · Upload list ({count}/9)", "ui.program_details": "Device program and notes", "ui.up": "Move recipe up", "ui.down": "Move recipe down", "ui.remove": "Remove", "ui.empty_queue": "No recipes added yet.", "ui.replace_warning": "Uploading replaces ALL recipes on the device with this list in the displayed order.", "ui.consent": "I have reviewed the list and want to replace all device slots.", "ui.readiness": "Check device readiness", "ui.upload": "Replace all device slots", "ui.status_title": "Device and upload job", "ui.ready": "Ready at last check (checked again before upload).", "ui.not_ready": "Not ready: {reasons}", "ui.receipt": "Job: {id} · confirmed slots: {written}", "ui.refresh_status": "Check job status again", "ui.recovery": "Manual recovery", "ui.recovery_warning": "Use only after checking the device and Bridge and confirming no job is running. An interrupted upload can leave an incomplete recipe list.", "ui.release": "Device checked, job ended · Unlock", "ui.release_confirm": "No upload is running and you checked the device manually? This does not send a recipe.", "ui.no_job": "No upload started yet.", "ui.program": "Mash-in {mash} °C · Boil {minutes} min at {boil} °C", "ui.rests": "Rests: {rests}", "ui.hops": "Hop alarms (minutes remaining in boil): {times}", "ui.none": "none", "ui.omitted": "Not transferred: {items}", "ui.help": "Instructions and test workflow", "status.queued": "Queued", "status.sending": "Uploading", "status.submitting": "Requesting upload", "status.confirmed": "Recipe count confirmed by device", "status.state_changed": "Aborted: device state changed", "status.unconfirmed": "Upload not confirmed", "status.outcome_unknown": "Upload outcome unknown – do not resend", "status.manually_released": "Unlocked after manual device check", "verify.matched": "Content verified by readback", "verify.mismatch": "ERROR: readback content differs", "verify.not_available": "Content verification pending / no readback available", "reason.upload_disabled": "Uploads disabled in Bridge", "reason.device_status_stale": "Device status is stale", "reason.device_status_unreadable": "Device status cannot be read", "reason.device_not_idle": "Main menu required, pump and heater off", "reason.busy": "Device busy", "batch.Planning": "Planning", "batch.Brewing": "Brewing", "batch.Fermenting": "Fermenting", "batch.Conditioning": "Conditioning", "batch.Completed": "Completed", "batch.Archived": "Archived", "runtime.integer": "{field}: a whole number from {low} to {high} is required.", "runtime.bad_source": "Invalid Brewfather record.", "runtime.no_batch_recipe": "The batch does not contain a complete recipe.", "runtime.no_name": "Recipe name is missing.", "runtime.bad_name": "Recipe name has no characters supported by the device.", "runtime.name_changed": "Device name: {original} → {name}", "runtime.rest_count": "The device requires 1 to 5 mash rests.", "runtime.bad_rest": "Rest {index}: invalid data.", "runtime.rest_type": "Rest {index}: type {type} is not supported.", "runtime.rest_temp": "Rest {index}, temperature", "runtime.rest_minutes": "Rest {index}, minutes", "runtime.ramp": "Rest {index}: ramp time not transferred; the device controls heating.", "runtime.end_temp": "Rest {index}: a different end temperature cannot be represented.", "runtime.infusion": "Rest {index}: infusion water amount not transferred.", "runtime.mash_default": "Mash-in suggested from the first rest; adjust in HA if needed.", "runtime.mash_override": "Mash-in temperature specified in HA.", "runtime.boil_duration": "Boil duration", "runtime.hops_list": "Hop additions must be a list.", "runtime.bad_hop": "Invalid hop addition.", "runtime.hop_unit": "{label}: boil hop time must be in minutes.", "runtime.flameout": "{label}: flameout addition at 0 minutes not transferred as a device alarm.", "runtime.remaining": "{label}, remaining boil time", "runtime.hop_omitted": "{label}: {use} not transferred as a boil hop alarm.", "runtime.unknown_hop": "{label}: unknown hop use {use}.", "runtime.grouped": "Simultaneous boil hop additions grouped into one device alarm.", "runtime.hop_count": "More than six distinct boil hop times.", "runtime.boil_default": "Boil temperature is a device setting (default 103 °C), editable in HA.", "runtime.mash_field": "Mash-in temperature", "runtime.boil_field": "Boil temperature", "runtime.ingredients": "Ingredients and amounts", "runtime.water": "Water and water chemistry", "runtime.fermentation": "Fermentation and packaging", "runtime.targets": "Targets and measurements", "runtime.other_additions": "Whirlpool, dry hops and other ingredients", "runtime.unknown_source": "Unknown source.", "runtime.rate_limit": "Brewfather request limit reached. Please try again later.", "runtime.bad_id": "Invalid Brewfather ID.", "runtime.auth": "Brewfather access or recipe/batch read permissions are missing.", "runtime.http": "Brewfather request failed (HTTP {status}).", "runtime.connection": "Brewfather unreachable or invalid response.", "runtime.response": "Unexpected Brewfather response format.", "runtime.catalog_entry": "Invalid Brewfather catalog entry.", "runtime.pagination": "Could not complete Brewfather pagination.", "runtime.bridge_missing": "Bridge actions from PR #30 are missing. Update the HA integration and Bridge.", "runtime.bridge_response": "Invalid Bridge response.", "runtime.locked": "Upload running or outcome unknown. Check the job first.", "runtime.stale_revision": "The list has changed. Refresh the view.", "runtime.capacity": "Maximum nine device slots.", "runtime.preview_expired": "Preview expired. Review the recipe again.", "runtime.duplicate": "The shortened device name is already in the list.", "runtime.bad_slot": "Unknown list slot.", "runtime.bad_target": "Invalid target slot.", "runtime.confirm": "Review the current list and confirm replacing all device slots.", "runtime.queue_count": "The upload list must contain 1 to 9 recipes.", "runtime.not_ready": "Device not ready: {reasons}", "runtime.no_receipt": "Upload response has no job ID.", "runtime.bad_status": "Invalid job status.", "runtime.unknown_outcome": "Upload outcome unknown. Do not resend; check the device and Bridge.", "runtime.release_check": "Unlock only after manually checking the device and confirming the job has ended.", "runtime.unknown_action": "Unknown HBAC action.", "runtime.no_job_id": "No job ID available. Check the device and Bridge manually.", "runtime.wrong_job": "Bridge response belongs to an unexpected job.", "runtime.poll_failed": "Job status currently unavailable. Do not upload again; check status later.", "runtime.entry": "HBAC entry missing or ambiguous. Specify entry_id.", "help.fetch.title": "1 · Fetch and review", "help.fetch.body": "Select Recipes or Batches and load the Brewfather list. Select an item or enter its ID. Leave mash-in blank to use the first rest, or enter a temperature. Fetch a preview and check the device name, rests, boil duration, temperature and hop alarms. Read the omitted-data notes, then add the reviewed preview to the upload list. A batch uses its own adjusted recipe. No recipe is sent to the device at this stage.", "help.upload.title": "2 · Review the list and upload", "help.upload.body": "Arrange 1–9 recipes using the arrows and review each device program. Put the Braumeister in its main menu with pump and heater off. Recipe uploads must be enabled in the Bridge. Check readiness. Uploading replaces ALL existing device slots, even when the list contains only one recipe. Only after reviewing the list, tick the confirmation and select Replace all device slots. No brewing program starts automatically.", "help.result.title": "3 · Verify the result", "help.result.body": "The bottom of the card shows the job and confirmed slots. Recipe count confirmed only confirms the number. Content verified by readback confirms a matching device recipe list. Pending verification means no readback is available yet; a mismatch means you must check the device. You can request job status again without resending recipes. Also check the recipe selection on the Braumeister. If the outcome is unknown, do not blindly upload again. Unlock only after manually checking the device and Bridge and confirming no job is running.", "help.setup.title": "Setup and troubleshooting", "help.setup.body": "Register {resource} as a JavaScript module under Settings → Dashboards → Resources, then reload the browser. This loads both the operating card and this help card. Brewfather needs recipes.read and batches.read. Store credentials in the HBAC integration, never in dashboard YAML. The Bridge needs the three upload actions from PR #30. With several HBAC entries, set entry_id in each operating card; use the HBAC configuration ID from the upload sensor attribute, not the device ID. Integration updates require an HA restart; a new integration with UI setup can load immediately in Marketplace.", "config.setup": "Connect Brewfather and Braumeister", "config.description": "Select a Braumeister. Cloud accounts are optional: configure Brewfather, Brewer’s Friend, both, or only BeerXML. Empty credentials disable that provider.", "config.user_id": "Brewfather User ID", "config.api_key": "Brewfather API key", "config.reconfigure": "Update Brewfather credentials", "config.invalid_auth": "Invalid API credentials or missing read access.", "config.cannot_connect": "Recipe provider unavailable or invalid response.", "config.no_bridge": "Set up the Speidel Braumeister integration first.", "config.already_configured": "HBAC is already configured for this Braumeister.", "config.updated": "Credentials updated.", "ui.state": "Read list and status", "ui.clear": "Clear local list", "ui.move": "Move list slot", "ui.revision": "Current list revision", "ui.preview_id": "Preview ID", "ui.index": "List index (0–8)", "ui.target": "Target index (0–8)", "ui.refresh": "Refresh cache", "ui.idle": "Idle", "hop.Dry Hop": "Dry hopping", "hop.Aroma": "Aroma/whirlpool", "hop.Whirlpool": "Whirlpool", "hop.Mash": "Mash hopping", "hop.First Wort": "First wort hopping", "rest.Decoction": "Decoction", "rest.Infusion": "Infusion", "rest.Temperature": "Temperature", "ui.folder": "BeerXML · HA folder", "ui.file_upload": "BeerXML · Upload file", "ui.file": "XML file", "ui.open_file": "Read selected file", "ui.file_hint": "XML files up to 512 KiB. Choose a recipe after importing; no automatic upload to the device.", "ui.folder_hint": "Folder configured in HBAC setup. Refresh the list manually; source files remain unchanged.", "config.brewersfriend_api_key": "Brewer’s Friend API key (optional)", "config.import_directory": "BeerXML folder in HA", "config.incomplete_brewfather": "Provide both Brewfather user ID and API key, or leave both empty.", "config.invalid_directory": "Use an absolute folder path inside HA.", "help.sources.title": "Additional recipe sources", "help.sources.body": "Add a Brewer’s Friend API key through HBAC reconfiguration, then select Brewer’s Friend and load the list or enter a recipe ID. For BeerXML, upload a file or select an XML file from the configured HA folder (default /config/hbac/import). Create that folder yourself if needed. Files stay unchanged. Select one recipe, preview it and add it to the shared list; repeat for other recipes. Imports never start a device upload. BeerXML uses standard Celsius and minute fields; unsupported steps or fractional device values are rejected.", "runtime.xml_size": "BeerXML: empty file or file larger than 512 KiB.", "runtime.xml_invalid": "BeerXML: invalid or unsafe XML.", "runtime.xml_root": "BeerXML: expected RECIPES with 1 to 100 recipes.", "runtime.xml_field": "BeerXML: missing or duplicate field {key}.", "runtime.xml_number": "BeerXML: invalid number in {key}.", "runtime.xml_version": "BeerXML: only version 1 is supported.", "runtime.xml_folder": "BeerXML: import folder is not accessible.", "runtime.xml_selection": "BeerXML: invalid file selection.", "runtime.xml_file": "BeerXML: file is not accessible.", "runtime.xml_expired": "BeerXML: selection expired. Load the file again.", "runtime.source_missing": "Recipe source is not configured.", "runtime.bf_rate": "Brewer's Friend: rate limit reached. Try again later.", "runtime.bf_auth": "Brewer's Friend: invalid API key or missing access.", "runtime.bf_http": "Brewer's Friend: request failed (HTTP {status}).", "runtime.bf_size": "Brewer's Friend: response is too large.", "runtime.bf_invalid": "Brewer's Friend: unavailable or invalid response.", "runtime.bf_many": "Brewer's Friend: too many recipes. Use a recipe ID.", "runtime.bf_id": "Brewer's Friend: invalid recipe ID."};
const HBAC_MESSAGE_PATTERNS = [["runtime.integer", "^(.*?):\\ ganze\\ Zahl\\ zwischen\\ (.*?)\\ und\\ (.*?)\\ erforderlich\\.$", ["field", "low", "high"]], ["runtime.bad_source", "^Ungültiger\\ Brewfather\\-Datensatz\\.$", []], ["runtime.no_batch_recipe", "^Der\\ Batch\\ enthält\\ kein\\ vollständiges\\ Rezept\\.$", []], ["runtime.no_name", "^Rezeptname\\ fehlt\\.$", []], ["runtime.bad_name", "^Rezeptname\\ enthält\\ keine\\ für\\ das\\ Gerät\\ nutzbaren\\ Zeichen\\.$", []], ["runtime.name_changed", "^Gerätename:\\ (.*?)\\ →\\ (.*?)$", ["original", "name"]], ["runtime.rest_count", "^Das\\ Gerät\\ benötigt\\ 1\\ bis\\ 5\\ Maischerasten\\.$", []], ["runtime.bad_rest", "^Rast\\ (.*?):\\ ungültige\\ Daten\\.$", ["index"]], ["runtime.rest_type", "^Rast\\ (.*?):\\ Rasttyp\\ (.*?)\\ wird\\ nicht\\ unterstützt\\.$", ["index", "type"]], ["runtime.rest_temp", "^Rast\\ (.*?),\\ Temperatur$", ["index"]], ["runtime.rest_minutes", "^Rast\\ (.*?),\\ Minuten$", ["index"]], ["runtime.ramp", "^Rast\\ (.*?):\\ Rampenzeit\\ nicht\\ übertragen;\\ das\\ Gerät\\ regelt\\ die\\ Aufheizung\\.$", ["index"]], ["runtime.end_temp", "^Rast\\ (.*?):\\ abweichende\\ Endtemperatur\\ ist\\ nicht\\ darstellbar\\.$", ["index"]], ["runtime.infusion", "^Rast\\ (.*?):\\ Infusionswassermenge\\ nicht\\ übertragen\\.$", ["index"]], ["runtime.mash_default", "^Einmaischtemperatur\\ aus\\ erster\\ Rast\\ vorgeschlagen;\\ bei\\ Bedarf\\ in\\ HA\\ ändern\\.$", []], ["runtime.mash_override", "^Einmaischtemperatur\\ in\\ HA\\ vorgegeben\\.$", []], ["runtime.boil_duration", "^Kochdauer$", []], ["runtime.hops_list", "^Hopfengaben\\ müssen\\ eine\\ Liste\\ sein\\.$", []], ["runtime.bad_hop", "^Ungültige\\ Hopfengabe\\.$", []], ["runtime.hop_unit", "^(.*?):\\ Kochhopfen\\-Zeit\\ muss\\ in\\ Minuten\\ vorliegen\\.$", ["label"]], ["runtime.flameout", "^(.*?):\\ Flameout\\-Gabe\\ bei\\ 0\\ Minuten\\ nicht\\ als\\ Gerätealarm\\ übertragen\\.$", ["label"]], ["runtime.remaining", "^(.*?),\\ Restkochzeit$", ["label"]], ["runtime.hop_omitted", "^(.*?):\\ (.*?)\\ nicht\\ als\\ Kochhopfenalarm\\ übertragen\\.$", ["label", "use"]], ["runtime.unknown_hop", "^(.*?):\\ unbekannte\\ Hopfenverwendung\\ (.*?)\\.$", ["label", "use"]], ["runtime.grouped", "^Gleichzeitige\\ Kochhopfengaben\\ zu\\ einem\\ Gerätealarm\\ zusammengefasst\\.$", []], ["runtime.hop_count", "^Mehr\\ als\\ sechs\\ unterschiedliche\\ Kochhopfen\\-Zeitpunkte\\.$", []], ["runtime.boil_default", "^Kochtemperatur\\ ist\\ ein\\ Geräteparameter\\ \\(Vorgabe\\ 103\\ °C\\),\\ in\\ HA\\ änderbar\\.$", []], ["runtime.mash_field", "^Einmaischtemperatur$", []], ["runtime.boil_field", "^Kochtemperatur$", []], ["runtime.ingredients", "^Zutaten\\ und\\ Mengen$", []], ["runtime.water", "^Wasser\\ und\\ Wasserchemie$", []], ["runtime.fermentation", "^Gärung\\ und\\ Abfüllung$", []], ["runtime.targets", "^Zielwerte\\ und\\ Messwerte$", []], ["runtime.other_additions", "^Whirlpool,\\ Stopfhopfen\\ und\\ weitere\\ Zutaten$", []], ["runtime.unknown_source", "^Unbekannte\\ Quelle\\.$", []], ["runtime.rate_limit", "^Brewfather\\-Anfragelimit\\ erreicht\\.\\ Bitte\\ später\\ erneut\\ versuchen\\.$", []], ["runtime.bad_id", "^Ungültige\\ Brewfather\\-ID\\.$", []], ["runtime.auth", "^Brewfather\\-Zugang\\ oder\\ Leserechte\\ für\\ Rezepte/Batches\\ fehlen\\.$", []], ["runtime.http", "^Brewfather\\-Abruf\\ fehlgeschlagen\\ \\(HTTP\\ (.*?)\\)\\.$", ["status"]], ["runtime.connection", "^Brewfather\\ nicht\\ erreichbar\\ oder\\ ungültige\\ Antwort\\.$", []], ["runtime.response", "^Unerwartetes\\ Brewfather\\-Antwortformat\\.$", []], ["runtime.catalog_entry", "^Ungültiger\\ Brewfather\\-Katalogeintrag\\.$", []], ["runtime.pagination", "^Brewfather\\-Paginierung\\ konnte\\ nicht\\ abgeschlossen\\ werden\\.$", []], ["runtime.bridge_missing", "^Bridge\\-Aktionen\\ aus\\ PR\\ \\#30\\ fehlen\\.\\ HA\\-Integration\\ und\\ Bridge\\ aktualisieren\\.$", []], ["runtime.bridge_response", "^Ungültige\\ Bridge\\-Antwort\\.$", []], ["runtime.locked", "^Upload\\ läuft\\ oder\\ Ausgang\\ ist\\ unklar\\.\\ Erst\\ den\\ Auftrag\\ prüfen\\.$", []], ["runtime.stale_revision", "^Die\\ Liste\\ wurde\\ geändert\\.\\ Ansicht\\ aktualisieren\\.$", []], ["runtime.capacity", "^Maximal\\ neun\\ Geräteplätze\\.$", []], ["runtime.preview_expired", "^Vorschau\\ abgelaufen\\.\\ Rezept\\ erneut\\ prüfen\\.$", []], ["runtime.duplicate", "^Der\\ gekürzte\\ Gerätename\\ ist\\ bereits\\ in\\ der\\ Liste\\ vorhanden\\.$", []], ["runtime.bad_slot", "^Unbekannter\\ Listenplatz\\.$", []], ["runtime.bad_target", "^Ungültiger\\ Zielplatz\\.$", []], ["runtime.confirm", "^Aktuelle\\ Liste\\ prüfen\\ und\\ das\\ Ersetzen\\ aller\\ Geräteplätze\\ bestätigen\\.$", []], ["runtime.queue_count", "^Die\\ Upload\\-Liste\\ muss\\ 1\\ bis\\ 9\\ Rezepte\\ enthalten\\.$", []], ["runtime.not_ready", "^Gerät\\ nicht\\ bereit:\\ (.*?)$", ["reasons"]], ["runtime.no_receipt", "^Uploadantwort\\ enthält\\ keine\\ Auftrags\\-ID\\.$", []], ["runtime.bad_status", "^Ungültiger\\ Auftragsstatus\\.$", []], ["runtime.unknown_outcome", "^Uploadausgang\\ unklar\\.\\ Nicht\\ erneut\\ senden;\\ Gerät\\ und\\ Bridge\\ prüfen\\.$", []], ["runtime.release_check", "^Nur\\ nach\\ manueller\\ Prüfung\\ des\\ Geräts\\ und\\ eines\\ beendeten\\ Auftrags\\ freigeben\\.$", []], ["runtime.unknown_action", "^Unbekannte\\ HBAC\\-Aktion\\.$", []], ["runtime.no_job_id", "^Keine\\ Auftrags\\-ID\\ vorhanden\\.\\ Gerät\\ und\\ Bridge\\ manuell\\ prüfen\\.$", []], ["runtime.wrong_job", "^Unpassende\\ Bridge\\-Auftragsantwort\\.$", []], ["runtime.poll_failed", "^Auftragsstatus\\ derzeit\\ nicht\\ abrufbar\\.\\ Kein\\ erneuter\\ Upload;\\ Status\\ später\\ abfragen\\.$", []], ["runtime.entry", "^HBAC\\-Eintrag\\ fehlt\\ oder\\ ist\\ mehrdeutig\\.\\ entry_id\\ angeben\\.$", []], ["runtime.xml_size", "^BeerXML:\\ empty\\ file\\ or\\ file\\ larger\\ than\\ 512\\ KiB\\.$", []], ["runtime.xml_invalid", "^BeerXML:\\ invalid\\ or\\ unsafe\\ XML\\.$", []], ["runtime.xml_root", "^BeerXML:\\ expected\\ RECIPES\\ with\\ 1\\ to\\ 100\\ recipes\\.$", []], ["runtime.xml_field", "^BeerXML:\\ missing\\ or\\ duplicate\\ field\\ (.*?)\\.$", ["key"]], ["runtime.xml_number", "^BeerXML:\\ invalid\\ number\\ in\\ (.*?)\\.$", ["key"]], ["runtime.xml_version", "^BeerXML:\\ only\\ version\\ 1\\ is\\ supported\\.$", []], ["runtime.xml_folder", "^BeerXML:\\ import\\ folder\\ is\\ not\\ accessible\\.$", []], ["runtime.xml_selection", "^BeerXML:\\ invalid\\ file\\ selection\\.$", []], ["runtime.xml_file", "^BeerXML:\\ file\\ is\\ not\\ accessible\\.$", []], ["runtime.xml_expired", "^BeerXML:\\ selection\\ expired\\.\\ Load\\ the\\ file\\ again\\.$", []], ["runtime.source_missing", "^Recipe\\ source\\ is\\ not\\ configured\\.$", []], ["runtime.bf_rate", "^Brewer's\\ Friend:\\ rate\\ limit\\ reached\\.\\ Try\\ again\\ later\\.$", []], ["runtime.bf_auth", "^Brewer's\\ Friend:\\ invalid\\ API\\ key\\ or\\ missing\\ access\\.$", []], ["runtime.bf_http", "^Brewer's\\ Friend:\\ request\\ failed\\ \\(HTTP\\ (.*?)\\)\\.$", ["status"]], ["runtime.bf_size", "^Brewer's\\ Friend:\\ response\\ is\\ too\\ large\\.$", []], ["runtime.bf_invalid", "^Brewer's\\ Friend:\\ unavailable\\ or\\ invalid\\ response\\.$", []], ["runtime.bf_many", "^Brewer's\\ Friend:\\ too\\ many\\ recipes\\.\\ Use\\ a\\ recipe\\ ID\\.$", []], ["runtime.bf_id", "^Brewer's\\ Friend:\\ invalid\\ recipe\\ ID\\.$", []], ["runtime.integer", "^(.*?):\\ a\\ whole\\ number\\ from\\ (.*?)\\ to\\ (.*?)\\ is\\ required\\.$", ["field", "low", "high"]], ["runtime.bad_source", "^Invalid\\ Brewfather\\ record\\.$", []], ["runtime.no_batch_recipe", "^The\\ batch\\ does\\ not\\ contain\\ a\\ complete\\ recipe\\.$", []], ["runtime.no_name", "^Recipe\\ name\\ is\\ missing\\.$", []], ["runtime.bad_name", "^Recipe\\ name\\ has\\ no\\ characters\\ supported\\ by\\ the\\ device\\.$", []], ["runtime.name_changed", "^Device\\ name:\\ (.*?)\\ →\\ (.*?)$", ["original", "name"]], ["runtime.rest_count", "^The\\ device\\ requires\\ 1\\ to\\ 5\\ mash\\ rests\\.$", []], ["runtime.bad_rest", "^Rest\\ (.*?):\\ invalid\\ data\\.$", ["index"]], ["runtime.rest_type", "^Rest\\ (.*?):\\ type\\ (.*?)\\ is\\ not\\ supported\\.$", ["index", "type"]], ["runtime.rest_temp", "^Rest\\ (.*?),\\ temperature$", ["index"]], ["runtime.rest_minutes", "^Rest\\ (.*?),\\ minutes$", ["index"]], ["runtime.ramp", "^Rest\\ (.*?):\\ ramp\\ time\\ not\\ transferred;\\ the\\ device\\ controls\\ heating\\.$", ["index"]], ["runtime.end_temp", "^Rest\\ (.*?):\\ a\\ different\\ end\\ temperature\\ cannot\\ be\\ represented\\.$", ["index"]], ["runtime.infusion", "^Rest\\ (.*?):\\ infusion\\ water\\ amount\\ not\\ transferred\\.$", ["index"]], ["runtime.mash_default", "^Mash\\-in\\ suggested\\ from\\ the\\ first\\ rest;\\ adjust\\ in\\ HA\\ if\\ needed\\.$", []], ["runtime.mash_override", "^Mash\\-in\\ temperature\\ specified\\ in\\ HA\\.$", []], ["runtime.boil_duration", "^Boil\\ duration$", []], ["runtime.hops_list", "^Hop\\ additions\\ must\\ be\\ a\\ list\\.$", []], ["runtime.bad_hop", "^Invalid\\ hop\\ addition\\.$", []], ["runtime.hop_unit", "^(.*?):\\ boil\\ hop\\ time\\ must\\ be\\ in\\ minutes\\.$", ["label"]], ["runtime.flameout", "^(.*?):\\ flameout\\ addition\\ at\\ 0\\ minutes\\ not\\ transferred\\ as\\ a\\ device\\ alarm\\.$", ["label"]], ["runtime.remaining", "^(.*?),\\ remaining\\ boil\\ time$", ["label"]], ["runtime.hop_omitted", "^(.*?):\\ (.*?)\\ not\\ transferred\\ as\\ a\\ boil\\ hop\\ alarm\\.$", ["label", "use"]], ["runtime.unknown_hop", "^(.*?):\\ unknown\\ hop\\ use\\ (.*?)\\.$", ["label", "use"]], ["runtime.grouped", "^Simultaneous\\ boil\\ hop\\ additions\\ grouped\\ into\\ one\\ device\\ alarm\\.$", []], ["runtime.hop_count", "^More\\ than\\ six\\ distinct\\ boil\\ hop\\ times\\.$", []], ["runtime.boil_default", "^Boil\\ temperature\\ is\\ a\\ device\\ setting\\ \\(default\\ 103\\ °C\\),\\ editable\\ in\\ HA\\.$", []], ["runtime.mash_field", "^Mash\\-in\\ temperature$", []], ["runtime.boil_field", "^Boil\\ temperature$", []], ["runtime.ingredients", "^Ingredients\\ and\\ amounts$", []], ["runtime.water", "^Water\\ and\\ water\\ chemistry$", []], ["runtime.fermentation", "^Fermentation\\ and\\ packaging$", []], ["runtime.targets", "^Targets\\ and\\ measurements$", []], ["runtime.other_additions", "^Whirlpool,\\ dry\\ hops\\ and\\ other\\ ingredients$", []], ["runtime.unknown_source", "^Unknown\\ source\\.$", []], ["runtime.rate_limit", "^Brewfather\\ request\\ limit\\ reached\\.\\ Please\\ try\\ again\\ later\\.$", []], ["runtime.bad_id", "^Invalid\\ Brewfather\\ ID\\.$", []], ["runtime.auth", "^Brewfather\\ access\\ or\\ recipe/batch\\ read\\ permissions\\ are\\ missing\\.$", []], ["runtime.http", "^Brewfather\\ request\\ failed\\ \\(HTTP\\ (.*?)\\)\\.$", ["status"]], ["runtime.connection", "^Brewfather\\ unreachable\\ or\\ invalid\\ response\\.$", []], ["runtime.response", "^Unexpected\\ Brewfather\\ response\\ format\\.$", []], ["runtime.catalog_entry", "^Invalid\\ Brewfather\\ catalog\\ entry\\.$", []], ["runtime.pagination", "^Could\\ not\\ complete\\ Brewfather\\ pagination\\.$", []], ["runtime.bridge_missing", "^Bridge\\ actions\\ from\\ PR\\ \\#30\\ are\\ missing\\.\\ Update\\ the\\ HA\\ integration\\ and\\ Bridge\\.$", []], ["runtime.bridge_response", "^Invalid\\ Bridge\\ response\\.$", []], ["runtime.locked", "^Upload\\ running\\ or\\ outcome\\ unknown\\.\\ Check\\ the\\ job\\ first\\.$", []], ["runtime.stale_revision", "^The\\ list\\ has\\ changed\\.\\ Refresh\\ the\\ view\\.$", []], ["runtime.capacity", "^Maximum\\ nine\\ device\\ slots\\.$", []], ["runtime.preview_expired", "^Preview\\ expired\\.\\ Review\\ the\\ recipe\\ again\\.$", []], ["runtime.duplicate", "^The\\ shortened\\ device\\ name\\ is\\ already\\ in\\ the\\ list\\.$", []], ["runtime.bad_slot", "^Unknown\\ list\\ slot\\.$", []], ["runtime.bad_target", "^Invalid\\ target\\ slot\\.$", []], ["runtime.confirm", "^Review\\ the\\ current\\ list\\ and\\ confirm\\ replacing\\ all\\ device\\ slots\\.$", []], ["runtime.queue_count", "^The\\ upload\\ list\\ must\\ contain\\ 1\\ to\\ 9\\ recipes\\.$", []], ["runtime.not_ready", "^Device\\ not\\ ready:\\ (.*?)$", ["reasons"]], ["runtime.no_receipt", "^Upload\\ response\\ has\\ no\\ job\\ ID\\.$", []], ["runtime.bad_status", "^Invalid\\ job\\ status\\.$", []], ["runtime.unknown_outcome", "^Upload\\ outcome\\ unknown\\.\\ Do\\ not\\ resend;\\ check\\ the\\ device\\ and\\ Bridge\\.$", []], ["runtime.release_check", "^Unlock\\ only\\ after\\ manually\\ checking\\ the\\ device\\ and\\ confirming\\ the\\ job\\ has\\ ended\\.$", []], ["runtime.unknown_action", "^Unknown\\ HBAC\\ action\\.$", []], ["runtime.no_job_id", "^No\\ job\\ ID\\ available\\.\\ Check\\ the\\ device\\ and\\ Bridge\\ manually\\.$", []], ["runtime.wrong_job", "^Bridge\\ response\\ belongs\\ to\\ an\\ unexpected\\ job\\.$", []], ["runtime.poll_failed", "^Job\\ status\\ currently\\ unavailable\\.\\ Do\\ not\\ upload\\ again;\\ check\\ status\\ later\\.$", []], ["runtime.entry", "^HBAC\\ entry\\ missing\\ or\\ ambiguous\\.\\ Specify\\ entry_id\\.$", []], ["runtime.xml_size", "^BeerXML:\\ empty\\ file\\ or\\ file\\ larger\\ than\\ 512\\ KiB\\.$", []], ["runtime.xml_invalid", "^BeerXML:\\ invalid\\ or\\ unsafe\\ XML\\.$", []], ["runtime.xml_root", "^BeerXML:\\ expected\\ RECIPES\\ with\\ 1\\ to\\ 100\\ recipes\\.$", []], ["runtime.xml_field", "^BeerXML:\\ missing\\ or\\ duplicate\\ field\\ (.*?)\\.$", ["key"]], ["runtime.xml_number", "^BeerXML:\\ invalid\\ number\\ in\\ (.*?)\\.$", ["key"]], ["runtime.xml_version", "^BeerXML:\\ only\\ version\\ 1\\ is\\ supported\\.$", []], ["runtime.xml_folder", "^BeerXML:\\ import\\ folder\\ is\\ not\\ accessible\\.$", []], ["runtime.xml_selection", "^BeerXML:\\ invalid\\ file\\ selection\\.$", []], ["runtime.xml_file", "^BeerXML:\\ file\\ is\\ not\\ accessible\\.$", []], ["runtime.xml_expired", "^BeerXML:\\ selection\\ expired\\.\\ Load\\ the\\ file\\ again\\.$", []], ["runtime.source_missing", "^Recipe\\ source\\ is\\ not\\ configured\\.$", []], ["runtime.bf_rate", "^Brewer's\\ Friend:\\ rate\\ limit\\ reached\\.\\ Try\\ again\\ later\\.$", []], ["runtime.bf_auth", "^Brewer's\\ Friend:\\ invalid\\ API\\ key\\ or\\ missing\\ access\\.$", []], ["runtime.bf_http", "^Brewer's\\ Friend:\\ request\\ failed\\ \\(HTTP\\ (.*?)\\)\\.$", ["status"]], ["runtime.bf_size", "^Brewer's\\ Friend:\\ response\\ is\\ too\\ large\\.$", []], ["runtime.bf_invalid", "^Brewer's\\ Friend:\\ unavailable\\ or\\ invalid\\ response\\.$", []], ["runtime.bf_many", "^Brewer's\\ Friend:\\ too\\ many\\ recipes\\.\\ Use\\ a\\ recipe\\ ID\\.$", []], ["runtime.bf_id", "^Brewer's\\ Friend:\\ invalid\\ recipe\\ ID\\.$", []]];
// Embedded into hbac-card.js by scripts/build_frontend_i18n.py.
// Translation content is always rendered as text, never as HTML or executable code.
class HbacI18n {
  static cache = new Map();
  constructor() { this.strings = {...HBAC_EN_US}; this.language = "en-US"; }
  static normalize(value) {
    if (typeof value !== "string" || !/^[a-z]{2,3}(?:-[a-z0-9]{2,8})*$/i.test(value)) return "en-US";
    try { return Intl.getCanonicalLocales(value)[0]; } catch (_) { return "en-US"; }
  }
  static placeholders(value) { return [...value.matchAll(/\{(\w+)\}/g)].map(m => m[1]).sort().join(","); }
  static async read(url) {
    if (!this.cache.has(url)) this.cache.set(url, (async () => {
      try {
        const response = await fetch(url, {credentials: "same-origin", cache: "no-cache", signal: AbortSignal.timeout(5000)});
        if (!response.ok) return {};
        const data = await response.json();
        if (!data || Array.isArray(data) || typeof data !== "object") return {};
        return Object.fromEntries(Object.entries(data).filter(([key, value]) =>
          typeof value === "string" && value.trim() && key !== "__proto__" && key !== "constructor" &&
          (!HBAC_EN_US[key] || this.placeholders(value) === this.placeholders(HBAC_EN_US[key]))));
      } catch (_) { return {}; }
    })());
    return this.cache.get(url);
  }
  async load(value) {
    const language = HbacI18n.normalize(value);
    const base = language.split("-")[0];
    // Merge from least to most specific; exact regional variants override base language.
    const candidates = [...new Set(["en-US", base, language])];
    const urls = candidates.flatMap(locale => [
      `/hbac/locales/${locale}.json?v=${HBAC_VERSION}`,
      `/local/hbac/locales/${locale}.json?v=${HBAC_VERSION}`,
    ]);
    const dictionaries = await Promise.all(urls.map(url => HbacI18n.read(url)));
    this.strings = Object.assign({}, HBAC_EN_US, ...dictionaries);
    this.language = language;
  }
  t(key, params = {}) {
    const template = this.strings[key] || HBAC_EN_US[key] || key;
    return template.replace(/\{(\w+)\}/g, (match, name) => params[name] === undefined ? match : String(params[name]));
  }
  message(value, depth = 0) {
    if (value && typeof value === "object" && typeof value.key === "string") {
      return this.t(value.key, value.params || {});
    }
    const text = String(value ?? "");
    if (depth > 3) return text;
    // Keep Beta 1's persisted German warning strings readable in every language.
    for (const [key, pattern, names] of HBAC_MESSAGE_PATTERNS) {
      const match = text.match(new RegExp(pattern, "s"));
      if (!match) continue;
      const params = Object.fromEntries(names.map((name, i) => {
        let v = match[i + 1];
        if (name === "field") v = this.message(v, depth + 1);
        if (name === "use" && HBAC_EN_US[`hop.${v}`]) v = this.t(`hop.${v}`);
        if (name === "type" && HBAC_EN_US[`rest.${v}`]) v = this.t(`rest.${v}`);
        if (name === "reasons") v = v.split(", ").map(r => this.t(`reason.${r}`)).join(", ");
        // Recipe names and ingredient labels remain untouched.
        return [name, v];
      }));
      return this.t(key, params);
    }
    return text; // Errors originating outside HBAC remain diagnostic text.
  }
}
window.HbacI18n = HbacI18n;

/* END GENERATED I18N */
/* HBAC 0.4.0-beta.1. No third-party scripts; credentials stay in HA. */
class HbacCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
    this.i18n = this.i18n || new HbacI18n();
    this.kind = this.kind || "recipes";
    this.items = this.items || [];
    this.selected = this.selected || "";
    this.mash = this.mash || "";
    this.boil = this.boil || "103";
    if (!this.shadowRoot) this.attachShadow({mode: "open"});
    this.render();
    this.updateLanguage();
  }
  set hass(value) {
    this._hass = value;
    this.updateLanguage();
    if (!this.loaded && this.config && !this.busy) {
      this.loaded = true;
      this.run(async () => { this.state = await this.call("state"); });
    }
  }
  connectedCallback() {
    clearInterval(this.timer);
    this.timer = setInterval(async () => {
      if (!this._hass || this.busy || !this.loaded) return;
      try {
        const state = await this.call("state");
        if (this.state && state.revision !== this.state.revision) {
          this.state = state;
          this.confirmed = false;
          this.render();
        } else {
          this.state = state;
          this.renderStatus();
        }
      } catch (_) { /* Explicit actions surface connection errors. */ }
    }, 2000);
  }
  disconnectedCallback() { clearInterval(this.timer); }
  getCardSize() { return 10; }
  static getStubConfig() { return {}; }
  t(key, params) { return this.i18n.t(key, params); }
  message(value) { return this.i18n.message(value); }
  updateLanguage() {
    if (!this.i18n) return;
    const language = HbacI18n.normalize(this.config?.language || this._hass?.locale?.language || this._hass?.language || "en-US");
    if (language === this.requestedLanguage) return;
    this.requestedLanguage = language;
    this.localeReady = (async () => {
      const translator = new HbacI18n();
      await translator.load(language);
      if (this.requestedLanguage !== language) return;
      this.i18n = translator;
      // A language change never sends a service call or changes queue/consent state.
      this.render();
    })();
  }
  renderGuide(parent) {
    for (const section of ["fetch", "sources", "upload", "result", "setup"]) {
      const box = this.node("div", undefined, parent, "box");
      this.node("h3", this.t(`help.${section}.title`), box);
      this.node("p", this.t(`help.${section}.body`, {resource: `/hbac/hbac-card.js?v=${HBAC_VERSION}`}), box);
    }
  }
  async call(service, data = {}) {
    const result = await this._hass.callWS({type: "call_service", domain: "hbac", service,
      service_data: {...(this.config.entry_id ? {entry_id: this.config.entry_id} : {}), ...data},
      return_response: true});
    return result.response;
  }
  async run(fn) {
    if (this.busy) return;
    this.busy = true;
    this.error = "";
    for (const tag of ["button", "input", "select"]) this.shadowRoot.querySelectorAll(tag).forEach(b => b.disabled = true);
    try { await fn(); } catch (err) { this.error = err.message || String(err); }
    finally { this.busy = false; this.render(); }
  }
  node(tag, text, parent, cls) {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = text;
    if (cls) el.className = cls;
    if (parent) parent.append(el);
    return el;
  }
  button(parent, text, fn, disabled = false) {
    const b = this.node("button", text, parent);
    b.disabled = disabled || this.busy;
    b.onclick = () => this.run(fn);
    return b;
  }
  field(parent, label, value, oninput, type = "text") {
    const wrapper = this.node("label", label, parent);
    const input = this.node("input", undefined, wrapper);
    input.type = type;
    input.value = value;
    input.oninput = () => oninput(input.value);
    return input;
  }
  program(parent, preview) {
    const p = preview.program;
    this.node("strong", p.name, parent);
    this.node("p", this.t("ui.program", {mash: p.mash_in_temperature, minutes: p.boil_minutes, boil: p.boil_temperature}), parent);
    this.node("p", this.t("ui.rests", {rests: p.rests.map(r => `${r.temperature} °C / ${r.minutes} min`).join(" → ")}), parent);
    this.node("p", this.t("ui.hops", {times: p.hop_additions.join(", ") || this.t("ui.none")}), parent);
    const list = this.node("ul", undefined, parent);
    preview.warnings.forEach(w => this.node("li", this.message(w), list));
    this.node("p", this.t("ui.omitted", {items: preview.not_transferred.map(item => this.message(item)).join(", ")}), parent, "muted");
  }
  render() {
    if (!this.shadowRoot || !this.config) return;
    this.shadowRoot.replaceChildren();
    this.node("style", `
      :host {display:block} ha-card {padding:20px;color:var(--primary-text-color)}
      h2{margin:0 0 8px} h3{margin:24px 0 10px} p{line-height:1.5;margin:8px 0}
      label{display:block;margin:12px 0;font-size:14px} input,select{display:block;box-sizing:border-box;
      width:100%;padding:10px;margin-top:6px;border:1px solid var(--divider-color);border-radius:6px;
      color:var(--primary-text-color);background:var(--card-background-color)}
      button{padding:10px 14px;margin:4px 6px 4px 0;border:1px solid var(--divider-color);border-radius:6px;
      color:var(--primary-text-color);background:var(--secondary-background-color);cursor:pointer}
      button:disabled{opacity:.45;cursor:default} .box{border:1px solid var(--divider-color);border-radius:8px;padding:12px;margin:12px 0}
      .muted{color:var(--secondary-text-color);font-size:13px}.error{color:var(--error-color);white-space:pre-wrap}
      li{margin:5px 0} input[type=checkbox]{display:inline-block;width:auto;margin-right:8px}
      .check{display:flex;align-items:center} details{margin:8px 0} summary{cursor:pointer}
    `, this.shadowRoot);
    const card = this.node("ha-card", undefined, this.shadowRoot);
    this.node("h2", "HBAC", card);
    this.node("p", this.t("ui.subtitle"), card, "muted");
    const help = this.node("details", undefined, card);
    this.node("summary", this.t("ui.help"), help);
    this.renderGuide(help);
    if (this.error) this.node("p", this.message(this.error), card, "error");
    if (!this.state) {
      this.node("p", this.t("ui.loading"), card);
      this.button(card, this.t("ui.reconnect"), async () => { this.state = await this.call("state"); });
      return;
    }
    this.node("h3", this.t("ui.select_step"), card);
    const sourceLabel = this.node("label", this.t("ui.source"), card);
    const source = this.node("select", undefined, sourceLabel);
    const sources = this.state.sources || ["recipes", "batches"];
    if (!sources.includes(this.kind)) this.kind = sources[0];
    const labels = {recipes: `Brewfather · ${this.t("ui.recipes")}`, batches: `Brewfather · ${this.t("ui.batches")}`,
      brewersfriend: "Brewer's Friend", beerxml_folder: this.t("ui.folder"), beerxml_upload: this.t("ui.file_upload")};
    for (const v of sources) {
      const label = labels[v];
      const option = this.node("option", label, source); option.value = v;
    }
    source.value = this.kind;
    source.onchange = () => { this.kind = source.value; this.files = []; this.items = []; this.selected = ""; this.preview = null; this.mash = ""; this.render(); };
    if (this.kind === "beerxml_upload") {
      const fileLabel = this.node("label", this.t("ui.file_upload"), card);
      const file = this.node("input", undefined, fileLabel);
      file.type = "file"; file.accept = ".xml,application/xml,text/xml";
      file.disabled = this.busy;
      file.onchange = () => {
        const selectedFile = file.files?.[0];
        if (!selectedFile) return;
        this.run(async () => {
          this.preview = null; this.items = []; this.selected = "";
          if (selectedFile.size > 512 * 1024) throw new Error(this.t("runtime.xml_size"));
          const bytes = new Uint8Array(await selectedFile.arrayBuffer());
          let binary = "";
          for (const byte of bytes) binary += String.fromCharCode(byte);
          this.items = (await this.call("import_file", {content: btoa(binary)})).items;
          this.catalogLoaded = this.kind;
        });
      };
      this.node("p", this.t("ui.file_hint"), card, "muted");
    } else {
      this.button(card, this.t("ui.load_catalog"), async () => {
        const result = (await this.call("catalog", {kind: this.kind, refresh: true})).items;
        if (this.kind === "beerxml_folder") this.files = result;
        else this.items = result;
        this.catalogLoaded = this.kind;
      });
    }
    if (this.kind === "beerxml_folder") {
      this.node("p", this.t("ui.folder_hint"), card, "muted");
      const label = this.node("label", this.t("ui.file"), card);
      const files = this.node("select", undefined, label);
      const blank = this.node("option", this.t("ui.choose"), files); blank.value = "";
      for (const item of this.files || []) {
        const option = this.node("option", item.name, files); option.value = item.id;
      }
      files.value = this.filename || "";
      files.onchange = () => { this.filename = files.value; this.items = []; this.selected = ""; this.preview = null; this.render(); };
      this.button(card, this.t("ui.open_file"), async () => {
        this.preview = null; this.selected = ""; this.items = [];
        this.items = (await this.call("open_file", {filename: this.filename})).items;
      }, !this.filename);
    }
    if (this.items.length) {
      const listLabel = this.node("label", this.t("ui.selection"), card);
      const select = this.node("select", undefined, listLabel);
      const blank = this.node("option", this.t("ui.choose"), select); blank.value = "";
      this.items.forEach(item => {
        const option = this.node("option", `${item.batch_no != null ? "#" + item.batch_no + " · " : ""}${item.name}${item.status ? " · " + this.t(`batch.${item.status}`) : ""}`, select);
        option.value = item.id;
      });
      select.value = this.selected;
      select.onchange = () => { this.selected = select.value; this.preview = null; this.mash = ""; this.render(); };
    } else if (this.catalogLoaded === this.kind) this.node("p", this.t("ui.empty_catalog"), card);
    if (!["beerxml_upload", "beerxml_folder"].includes(this.kind)) this.field(card, this.t("ui.source_id"), this.selected, value => {
      this.selected = value.trim(); this.preview = null; this.mash = "";
      this.shadowRoot.querySelector("#preview-box")?.remove();
    });
    const mash = this.field(card, this.t("ui.mash_in"), this.mash, value => {
      this.mash = value; this.preview = null; this.shadowRoot.querySelector("#preview-box")?.remove();
    }, "number"); mash.min = 20; mash.max = 80; mash.step = 1;
    const boil = this.field(card, this.t("ui.boil_temperature"), this.boil, value => {
      this.boil = value; this.preview = null; this.shadowRoot.querySelector("#preview-box")?.remove();
    }, "number"); boil.min = 95; boil.max = 105; boil.step = 1;
    this.button(card, this.t("ui.preview"), async () => {
      if (!this.selected) throw new Error(this.t("ui.choose_error"));
      this.preview = await this.call("preview", {kind: this.kind, source_id: this.selected,
        ...(this.mash !== "" ? {mash_in: Number(this.mash)} : {}), boil_temperature: Number(this.boil)});
    });
    if (this.preview) {
      const box = this.node("div", undefined, card, "box"); box.id = "preview-box";
      this.node("h3", this.t("ui.review_step"), box);
      this.program(box, this.preview);
      this.button(box, this.t("ui.add"), async () => {
        this.state = await this.call("add", {preview_id: this.preview.preview_id, revision: this.state.revision});
        this.preview = null; this.confirmed = false;
      }, this.state.queue.length >= 9);
    }
    this.node("h3", this.t("ui.queue", {count: this.state.queue.length}), card);
    this.state.queue.forEach((item, index) => {
      const box = this.node("div", undefined, card, "box");
      this.node("strong", `${index + 1}. ${item.source.name}`, box);
      const detail = this.node("details", undefined, box);
      this.node("summary", this.t("ui.program_details"), detail); this.program(detail, item);
      const change = async (service, data) => {
        this.state = await this.call(service, {...data, revision: this.state.revision}); this.confirmed = false;
      };
      this.button(box, "↑", () => change("move", {index, target: index - 1}), index === 0).ariaLabel = this.t("ui.up");
      this.button(box, "↓", () => change("move", {index, target: index + 1}), index === this.state.queue.length - 1).ariaLabel = this.t("ui.down");
      this.button(box, this.t("ui.remove"), () => change("remove", {index}));
    });
    if (!this.state.queue.length) this.node("p", this.t("ui.empty_queue"), card, "muted");
    this.node("p", this.t("ui.replace_warning"), card);
    const checkLabel = this.node("label", undefined, card, "check");
    const check = this.node("input", undefined, checkLabel); check.type = "checkbox"; check.checked = !!this.confirmed;
    this.node("span", this.t("ui.consent"), checkLabel);
    check.onchange = () => { this.confirmed = check.checked; this.render(); };
    this.button(card, this.t("ui.readiness"), async () => { this.state = await this.call("readiness"); });
    this.button(card, this.t("ui.upload"), async () => {
      this.confirmed = false;
      this.state = await this.call("upload", {revision: this.state.revision, replace_all: true});
    }, !this.confirmed || !this.state.queue.length || ["queued", "sending", "submitting", "outcome_unknown"].includes(this.state.job?.result));
    this.statusBox = this.node("div", undefined, card, "box");
    this.renderStatus();
  }
  renderStatus() {
    const box = this.statusBox;
    if (!box || !this.state) return;
    box.replaceChildren();
    this.node("strong", this.t("ui.status_title"), box);
    const readiness = this.state.readiness;
    const reasons = {upload_disabled: this.t("reason.upload_disabled"), device_status_stale: this.t("reason.device_status_stale"),
      device_status_unreadable: this.t("reason.device_status_unreadable"), device_not_idle: this.t("reason.device_not_idle"), busy: this.t("reason.busy")};
    if (readiness) this.node("p", readiness.ready_for_upload ? this.t("ui.ready") :
      this.t("ui.not_ready", {reasons: (readiness.blocking_reasons || []).map(r => reasons[r] || r).join(", ")}), box);
    const job = this.state.job;
    if (job) {
      const labels = {queued: this.t("status.queued"), sending: this.t("status.sending"), submitting: this.t("status.submitting"),
        confirmed: this.t("status.confirmed"), state_changed: this.t("status.state_changed"),
        unconfirmed: this.t("status.unconfirmed"), outcome_unknown: this.t("status.outcome_unknown"),
        manually_released: this.t("status.manually_released")};
      this.node("p", labels[job.result] || job.result, box);
      if (job.job_id) this.node("p", this.t("ui.receipt", {id: job.job_id, written: job.written ?? "–"}), box, "muted");
      const verification = {matched: this.t("verify.matched"), mismatch: this.t("verify.mismatch"), not_available: this.t("verify.not_available")};
      this.node("p", verification[job.content_verification || "not_available"], box, job.content_verification === "mismatch" ? "error" : "muted");
      if (job.job_id) this.button(box, this.t("ui.refresh_status"), async () => { this.state = await this.call("status"); });
      if (["outcome_unknown", "queued", "sending"].includes(job.result)) {
        const details = this.node("details", undefined, box);
        this.node("summary", this.t("ui.recovery"), details);
        this.node("p", this.t("ui.recovery_warning"), details);
        this.button(details, this.t("ui.release"), async () => {
          if (!window.confirm(this.t("ui.release_confirm"))) return;
          this.state = await this.call("acknowledge_unknown", {device_checked: true}); this.confirmed = false;
        });
      }
    } else this.node("p", this.t("ui.no_job"), box, "muted");
    if (this.state.error) this.node("p", this.message(this.state.error), box, "error");
  }
}
if (!customElements.get("hbac-card")) customElements.define("hbac-card", HbacCard);
window.customCards = window.customCards || [];
window.customCards.push({type: "hbac-card", name: "HBAC", description: "Brewfather, Brewer's Friend and BeerXML recipes to Braumeister"});

class HbacHelpCard extends HbacCard {
  set hass(value) { this._hass = value; this.updateLanguage(); }
  connectedCallback() { /* Help only: no polling and no service calls. */ }
  getCardSize() { return 8; }
  render() {
    if (!this.shadowRoot || !this.i18n) return;
    this.shadowRoot.replaceChildren();
    this.node("style", "ha-card{padding:20px;color:var(--primary-text-color)}h2{margin-top:0}p{line-height:1.65}.box{margin:20px 0}h3{font-size:1.1em}", this.shadowRoot);
    const card = this.node("ha-card", undefined, this.shadowRoot);
    this.node("h2", this.t("ui.help"), card);
    this.renderGuide(card);
  }
}
if (!customElements.get("hbac-help-card")) customElements.define("hbac-help-card", HbacHelpCard);
window.customCards.push({type: "hbac-help-card", name: "HBAC · Help", description: "Localized HBAC instructions and test workflow"});
