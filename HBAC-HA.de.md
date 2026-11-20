# HBAC 0.5.0-beta.3 – Rezeptquellen in Home Assistant

Neu: Die gesamte Bedienkarte und Anleitung sind in acht Sprachen verfügbar:
Englisch (en-US), Deutsch, Französisch, Spanisch, Italienisch, Portugiesisch,
Polnisch und Niederländisch. Die Karte folgt der HA-Benutzersprache;
fehlende Texte fallen auf en-US zurück. [Weitere Sprachen hinzufügen](I18N.md).

## Update von 0.4.0

1. Im Marketplace die Vorabversion **v0.5.0-beta.3** installieren und HA neu starten.
2. Die vorhandene Dashboard-Ressource auf
   `/hbac/hbac-card.js?v=0.5.0-beta.3` ändern (nicht doppelt hinzufügen).
3. Den Browser neu laden. Bedienkarte und eingeklappte Anleitung sind automatisch
   lokalisiert; die gespeicherte Upload-Liste und der Auftrag bleiben erhalten.
4. Für die separate Hilfeansicht die bisherigen deutschen Markdown-Karten durch
   `type: custom:hbac-help-card` ersetzen. Ein vollständiges Dashboard liegt unter
   [dashboard/hbac-test.yaml](dashboard/hbac-test.yaml).

Optional pro Bedien- oder Hilfekarte `language: nl` setzen, um die Profil-Sprache
zu übersteuern. Eigene JSON-Dateien unter `/config/www/hbac/locales/` ergänzen;
Details stehen in [I18N.md](I18N.md).

Neue eigene HA-Integration mit Dashboard-Karte: Rezepte oder angepasste Batch-Rezepte
aus Brewfather abrufen, Geräteprogramm prüfen, bis zu neun Plätze zusammenstellen,
über die Braumeister-Bridge hochladen und den zugehörigen Auftrag verfolgen.
Die bisherigen HBAC-CLI-Exporte bleiben verfügbar.

## Neue Quellen in 0.5.0

In der HBAC-Integration **Neu konfigurieren** öffnen, um den optionalen
Brewer’s-Friend-API-Schlüssel zu ergänzen. Brewfather-Zugangsdaten können bestehen
bleiben. Ohne Cloud-Zugangsdaten ist ein reiner BeerXML-Betrieb möglich.

- **Brewer’s Friend:** Quelle wählen, Liste laden oder numerische Rezept-ID eingeben.
- **BeerXML · Datei hochladen:** XML-Datei auf dem Rechner auswählen, enthaltenes
  Rezept wählen, Vorschau prüfen und zur Upload-Liste hinzufügen.
- **BeerXML · HA-Ordner:** `/config/hbac/import` in HA anlegen und XML-Dateien ablegen.
  Alternativ bei der Neukonfiguration einen anderen absoluten HA-Pfad einstellen.
  Quellenliste laden, Datei wählen und einlesen, danach Rezept auswählen.

Der Ordner wird nicht automatisch überwacht. Dateien werden weder verändert noch
entfernt. Kein Import startet automatisch einen Geräteupload. Bis zu 100 Rezepte
pro Datei (512 KiB), weiterhin maximal neun geprüfte Rezepte pro Upload-Liste.
Weitere Details und Testdateien: [SOURCES.md](SOURCES.md).

## Quellschritte prüfen

Nach dem Abruf je Schritt **Maischerast am Gerät** oder **Manueller Nachguss** wählen.
Bei Schritten namens Sparge/Nachguss ist eine ausdrückliche Auswahl erforderlich.
Dann **Programmvorschau erstellen** drücken. Temperaturen werden auf ganze °C
kaufmännisch gerundet und jede Änderung wird angezeigt. Manuell markierte Schritte
werden mit Hinweis ausgelassen; sie müssen separat ausgeführt werden. Änderungen
an der Auswahl verwerfen die Vorschau, nicht die schon gespeicherte Upload-Liste.

## Voraussetzungen

- Home Assistant mit Custom-Integration-Unterstützung; Tests mit HA 2026.2.3.
- Speidel-Braumeister-Integration und Bridge mit den drei Aktionen aus
  [PR #30](https://github.com/omphteliba/ha-speidel-braumeister/pull/30):
  `recipe_upload_readiness`, `start_recipe_upload`, `recipe_upload_status`.
  PR #30 ist inzwischen in Upstream-main enthalten. Installierte Integration und
  Bridge müssen diese Aktionen unterstützen; ein Merge allein aktualisiert HA nicht.
- Bridge mit `recipe_write_enabled: true`. Für rein lokalen Betrieb
  `forward_to_cloud: false`; sonst kann die Cloud Rezepte später überschreiben.
- Optionaler Brewfather API-Zugang: User-ID und ein Key mit **recipes.read** und **batches.read**.
  Es werden ausschließlich GET-Anfragen an Brewfather gesendet.

## Installation

### Über HACS (Beta)

In HACS über das Drei-Punkte-Menü **Benutzerdefinierte Repositories** öffnen:
`https://github.com/DanielP-1337/Homebrew-as-Code` hinzufügen, Typ **Integration**.
**HBAC – Recipes to Braumeister** öffnen, Beta-/Vorabversionen anzeigen lassen
und **v0.5.0-beta.3** herunterladen. Bei einem Update HA neu starten; bei einer
Erstinstallation im Marketplace auf HA 2026.11+ nur, wenn HA dazu auffordert. Mit Schritt 3 unten
fortfahren. Die Dashboard-Ressource wird separat wie in Schritt 4 eingerichtet.

### Manuelle ZIP-Installation

1. Das Installations-ZIP im HA-Konfigurationsverzeichnis entpacken. Danach muss
   `/config/custom_components/hbac/manifest.json` existieren.
2. Home Assistant neu starten.
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen → HBAC** öffnen.
   Brewfather-Zugang eingeben und den bereits eingerichteten Braumeister auswählen.
4. Unter **Einstellungen → Dashboards → Ressourcen** folgende JavaScript-Modul-Ressource
   hinzufügen (ggf. erweiterten Modus im Benutzerprofil einschalten):
   `/hbac/hbac-card.js?v=0.5.0-beta.3`
5. Dashboard bearbeiten, manuelle Karte hinzufügen:

```yaml
type: custom:hbac-card
```

Bei mehreren HBAC-Einträgen die gewünschte HBAC-Konfigurations-ID angeben:

```yaml
type: custom:hbac-card
entry_id: DEINE_HBAC_KONFIGURATIONS_ID
```

Diese ID steht auch im Attribut `entry_id` des HBAC-Upload-Sensors.
Sie ist **nicht** die Konfigurations-ID der Speidel-Integration.
Zugangsdaten können über das Drei-Punkte-Menü der Integration neu konfiguriert werden.
Die Karte benötigt weder Brewfather-Key noch HA-Zugriffstoken.

## Bedienung

1. Quelle **Rezepte** oder **Batches** wählen und Liste laden. Alternativ eine
   bekannte Brewfather-ID direkt eingeben. Der Katalog lädt alle Seiten (50 Einträge
   pro Anfrage). Kein regelmäßiges Brewfather-Polling; der Katalog wird fünf Minuten
   zwischengespeichert, der Laden-Knopf aktualisiert ihn ausdrücklich.
2. Einmaischtemperatur leer lassen, um die erste Rast zu verwenden, oder einen
   eigenen ganzzahligen Wert von 20–80 °C eingeben. Kochtemperatur: Geräteparameter
   mit Vorgabe 103 °C, änderbar zwischen 95–103 °C.
   Das gilt auch für Brewer's Friend und BeerXML: Die Kochtemperatur ist eine
   separate Geräteeinstellung. 104/105 °C werden abgelehnt, nicht automatisch
   gekürzt. Bereits vorgemerkte Rezepte mit solchen Werten bitte entfernen und
   mit höchstens 103 °C neu zur Uploadliste hinzufügen.
3. **Abrufen und Vorschau erstellen**. Die Einzelabfrage holt das vollständige
   Rezept; bei Batches wird ausschließlich `batch.recipe` verwendet. Messwerte
   wie `measuredBoilTime` überschreiben keine geplanten Rezeptparameter.
4. Geräteprogramm und Hinweise prüfen, dann zur Liste hinzufügen. Bis zu neun
   Programme können hinzugefügt, entfernt und umgeordnet werden. Gleichnamige
   Gerätenamen nach Kürzung werden abgelehnt. Den Quellnamen ggf. in Brewfather ändern.
5. Braumeister ins Hauptmenü bringen, Pumpe/Heizung aus. Bereitschaft prüfen,
   Ersetzen aller Plätze bestätigen und Upload auslösen.
6. Auftragsstatus verfolgen. Die Integration fragt den konkreten Auftrag alle
   zwei Sekunden für bis zu drei Minuten ab. Anschließend ist die manuelle
   Statusabfrage weiterhin möglich.

**Jeder Upload ersetzt die komplette Geräterezeptliste.** Die Liste kann mit
weniger als neun Rezepten hochgeladen werden; übrige alte Rezepte bleiben nicht erhalten.
Kein Brauprogramm wird automatisch gestartet.

## Konvertierung

- API-Werte sind metrisch: °C und Minuten; Anzeigeeinheiten werden ignoriert.
- 1–5 Rasten, jeweils 20–80 °C und 1–180 Minuten; Kochdauer 1–180 Minuten.
  Ungültige, fehlende, nicht endliche oder gebrochene Gerätewerte werden abgelehnt.
- Temperatur-/Infusionsrasten werden als Temperaturrasten übertragen. Infusionsmengen
  und Rampenzeiten werden ausdrücklich als nicht übertragen ausgewiesen.
  Dekoktion oder abweichende Rast-Endtemperaturen werden abgelehnt.
- Kochhopfen (`use: Boil`) liefert Alarme in Minuten Restkochzeit. Gleiche Zeitpunkte
  werden zusammengefasst, maximal sechs verschiedene Zeitpunkte sind möglich.
- Flameout bei 0 Minuten, Whirlpool/Aroma, Maischehopfen, Vorderwürze und Stopfhopfen
  werden mit einem Hinweis nicht als Kochhopfenalarme übertragen. Diese Arbeitsschritte
  müssen außerhalb des Geräteprogramms beachtet werden.
- Zutatenmengen, Wasser, Gärung, Abfüllung und Mess-/Zielwerte sind keine Gerätefelder.
- Gerätenamen werden auf druckbares ASCII ohne Semikolon und maximal 14 Zeichen
  umgestellt. Die Vorschau zeigt die Änderung.
- Die geprüfte Vorschau wird unverändert übernommen; der Upload lädt das Quellrezept
  nicht erneut. Für Änderungen in Brewfather das Rezept erneut abrufen und prüfen.

## Status und Wiederherstellung

`confirmed` bestätigt nur die **Rezeptanzahl**. Erst `content_verification: matched`
bestätigt den Inhalt anhand einer nachfolgenden Geräte-Rezeptliste. `not_available`
bedeutet, dass diese Inhaltsprüfung noch nicht vorliegt; `mismatch` ist eine Abweichung.

Liste, Quellen-Snapshot und Auftrags-ID liegen persistent in HA `.storage/hbac.*`.
Zugangsdaten liegen im HA-Konfigurationseintrag. HA-Backups entsprechend schützen.
Ein Neustart löst **keinen neuen Upload** aus. Bekannte Aufträge lassen sich erneut
abfragen; die Bridge verliert ihre Auftragshistorie bei Neustart bzw. nach Verdrängung
aus den letzten 32 Aufträgen.

Bei verlorener Startantwort bleibt der Ausgang unbekannt und weiteres Senden gesperrt.
Bei fehlendem Status bleibt der letzte Zustand sichtbar mit Fehlermeldung. Niemals
einen Upload blind wiederholen. Gerät und Bridge prüfen; nur wenn kein Auftrag mehr
läuft, unter **Manuelle Wiederherstellung** die Sperre ausdrücklich aufheben.
Ein unterbrochener Upload kann eine unvollständige Liste hinterlassen. Nach Prüfung
kann die komplette Liste bewusst erneut hochgeladen werden; es gibt kein Rollback.

## HA-Aktionen und Automationen

Alle Aktionen unter `hbac` sind in **Entwicklerwerkzeuge → Aktionen** beschrieben und
unterstützen `response_variable`. Bei mehreren Einträgen `entry_id` angeben.
`preview` liefert `preview_id`; `add`, `remove`, `move`, `clear` und `upload` benötigen
die aktuelle `revision` aus `hbac.state`. Damit kann eine veraltete Ansicht keine
zwischenzeitlich geänderte Liste bestätigen. Indizes bei `move`/`remove`: 0–8.

```yaml
sequence:
  - action: hbac.preview
    data:
      kind: batches
      source_id: DEINE_BATCH_ID
    response_variable: vorschau
  # Vorschau zuerst prüfen. Nicht direkt automatisch zum Gerät senden.
```

Sensor: aktuelles Upload-Ergebnis sowie `job_id`, `written`, `content_verification`
und Anzahl vorgemerkter Rezepte. Vollständige Rezepte und API-Key werden nicht als
Sensorattribute in den Recorder geschrieben.

## Entwicklung und Quellen

- Integration: `custom_components/hbac/`; eigenständiger Konverter ohne HA-Abhängigkeit.
- Vorhandene HBAC-CLI: `src/homebrew_as_code/`; weiterhin separat installierbar.
- Tests: `pytest -c tests_ha/pytest.ini tests_ha` in Linux mit
  `requirements_test_ha.txt` und Python 3.13; Kartentest: `node tests_frontend/card.test.cjs`.
- Die Tests verwenden synthetische Rezepte und simulierte API-/Bridge-Antworten.
  Diese neue HA-Bedienoberfläche wurde noch nicht an deinem realen Gerät abgenommen.
- [Brewfather REST API](https://docs.brewfather.app/api)
- [Brewfather Datenfelder](https://docs.brewfather.app/api/types)
- [HA-Aktionen](https://developers.home-assistant.io/docs/dev_101_services/)

Eine Installation in deinem laufenden HA oder ein Geräteupload ist nicht Teil der
lokalen Erstellung des Installationspakets.
