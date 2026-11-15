# HBAC 0.3.0 – Braumeister Bridge JSON und HA-Upload

## Direkter Upload mit der neuen generischen HA-Schnittstelle

Voraussetzung: die zugehörige Bridge-/HA-Erweiterung mit den Aktionen
`recipe_upload_readiness`, `start_recipe_upload` und `recipe_upload_status`.
Diese ist als separater Upstream-PR-Vorschlag vorbereitet und noch nicht als
offiziell veröffentlichte Schnittstelle vorauszusetzen.

Nach `pip install -e .` und Setzen des HA-Zugriffstokens in der Umgebungsvariable
`HA_TOKEN` zunächst nur prüfen:

```powershell
homebrew-bridge-upload recipes/lebkuchen-zauber/recipe.yaml --ha-url https://DEIN-HA
```

Mit zusätzlichem `--replace-all` wird die vollständige Geräterezeptliste ersetzt.
Bei mehreren Geräten `--config-entry-id ID` angeben. Der Client speichert die
Auftrags-ID in `bridge-upload-job.json` und fragt den Fortschritt ab.
Ein bestehender Auftrag lässt sich ohne erneuten Upload prüfen:

```powershell
homebrew-bridge-upload --ha-url https://DEIN-HA --status AUFTRAGS-ID
```

`confirmed` bestätigt die Rezeptanzahl. `content_verification: matched` bestätigt
zusätzlich einen danach empfangenen Inhaltsvergleich. Bei `not_available` steht
dieser Vergleich noch aus; später erneut Status abfragen. Bei verlorener
POST-Antwort niemals automatisch erneut senden. Ein Geräteupload wurde im Rahmen
der Implementierung nicht durchgeführt.

Diese Version ergänzt die bestehenden Exporte um einen lokalen JSON-Export.
Sie basiert auf der lokalen HBAC-Kopie vom 26.10.2026. Das Original unter
`C:\dev\Homebrew-as-Code` bleibt erhalten.

Installation und Export im Projektverzeichnis:

```powershell
pip install -e .
homebrew-bridge recipes/lebkuchen-zauber/recipe.yaml --output examples/braumeister.bridge.json
```

Alternativ ohne Installation bei gesetztem `PYTHONPATH=src`:

```powershell
python -m homebrew_as_code.bridge_export recipes/lebkuchen-zauber/recipe.yaml -o examples/braumeister.bridge.json
```

Bis zu neun YAML-Dateien können vor `--output` angegeben werden. Ihre Reihenfolge
bestimmt die Geräteplätze. Die Ausgabe enthält ausschließlich `{"recipes": [...]}`
als Aktionsdaten für Home Assistant. Es wird keine Verbindung aufgebaut.
Die separate `.report.json` beschreibt Namensänderungen und ausgelassene Daten.

## Upload über Home Assistant

1. Bridge mit Rezeptupload-Unterstützung installieren und `recipe_write_enabled: true`
   aktivieren. Für rein lokalen Betrieb `forward_to_cloud: false` setzen; andernfalls
   kann die Cloud die Rezeptliste später wieder überschreiben.
2. Braumeister ins Hauptmenü bringen; Pumpe und Heizung ausschalten.
3. Export und Bericht prüfen. **Der Upload ersetzt alle vorhandenen Geräterezeptplätze.**
4. In HA unter Entwicklerwerkzeuge → Aktionen `speidel_braumeister.upload_recipes`
   wählen. Die Liste aus dem JSON-Feld `recipes` als Feld `recipes` übernehmen.
   HA bietet hierbei keinen automatischen Dateiimport; JSON-Datei und Aktionsdaten
   sind dieselbe Datenstruktur. Bei mehreren Geräten zusätzlich `config_entry_id` setzen.

Beispiel im YAML-Modus (gekürzt auf ein Rezept):

```yaml
action: speidel_braumeister.upload_recipes
data:
  recipes:
    - name: Lebkuchen-Zaub
      mash_in_temperature: 60
      rests:
        - {temperature: 63, minutes: 20}
        - {temperature: 72, minutes: 45}
        - {temperature: 78, minutes: 10}
      boil_minutes: 60
      boil_temperature: 100
      hop_additions: [60]
```

## Grenzen und Zuordnung

Temperaturen und Zeiten müssen ganzzahlig sein: Einmaischen/Rasten 20–80 °C,
1–5 Rasten mit 1–180 Minuten, Kochen 1–180 Minuten bei 95–105 °C.
Ohne Quellwert für die Kochtemperatur gilt der Bridge-Standard 103 °C; der Bericht
weist darauf hin. Werte außerhalb des Geräteformats werden abgelehnt, nicht gerundet.

Hopfengaben werden wie im bestehenden HBAC-BeerJSON-Export am Feld
`alpha_acid_percent` erkannt. Bis zu sechs Gaben mit 1 bis Kochdauer Minuten Restzeit
sind möglich. Eine Gabe bei 0 Minuten wird abgelehnt. Andere Kochzutaten werden im
Bericht genannt und nicht als Hopfenalarme übertragen. Zutatenmengen, Wasser,
Gärung, Zielwerte und Nachkoch-Kontaktzeiten verbleiben im HBAC-Rezept.

Namen werden auf druckbares ASCII ohne Semikolon umgestellt (ä → ae usw.) und auf
14 Zeichen begrenzt. Der Bericht zeigt die Änderung. Für die direkte Bridge-HTTP-API
müsste zusätzlich `device_id` ergänzt werden; HA ermittelt diese selbst.

Ein abgebrochener Upload kann eine unvollständige Rezeptliste hinterlassen.
Nach Behebung des Fehlers die vollständige Liste erneut hochladen.
