# Wohnungsagent Berlin

Status am 4. November 2026: automatische Suche und Berichte aktiv;
automatischer Bewerbungsversand **nicht aktiv**.

Der geprüfte GitHub-Actions-Lauf 41747957456 hat alle 52 öffentlichen
Ergebnisseiten durchlaufen: 510 eindeutige Angebote aus allen sieben
Gesellschaften, zehn Basis-Treffer, null versendete Bewerbungen.
Die drei Bewerber-Secrets sind vorhanden. Persönliche Werte werden weder in
Dateien noch in Berichten ausgegeben.

## Zeitplan und Berichte

Der Workflow läuft um 06:17, 11:17 und 16:17 UTC (im Winter 07:17, 12:17 und
17:17 Uhr Berlin) sowie nach relevanten Codeänderungen und manuell.
GitHub kann geplante Läufe verzögern. Zusammenfassung im Actions-Lauf;
vollständiger JSON- und Markdown-Bericht im Artefakt daily-housing-report.

## Kriterien und Sicherheitsgrenzen

Ein Zimmer, höchstens 550 Euro Warmmiete, Reinickendorf/Wedding/Mitte/Pankow,
WBS 100 oder ausdrücklich kein WBS erforderlich. Unbekannte WBS-Kategorie,
besondere Wohnbedarfe, Alters- oder Studierendenbedingungen, WG-Zimmer,
Genossenschaftskosten und widersprüchliche Daten werden zur Prüfung gemeldet.
Eine Jobcenter-Zustimmung oder ein bereits begonnenes Studium wird nicht
behauptet. Aktuelle Anbieterdaten müssen die Quellendaten bestätigen.

Die Suche folgt den echten Livewire-Schaltflächen bis zur letzten Seite. Sie
erkennt wiederholte Seiten, unvollständige Läufe und unbekannte Anbieterlinks.
Identitätsparameter wie GESOBAU immo_ref und WBM-Objektkennungen bleiben
erhalten; wechselnde GESOBAU-UUIDs derselben Wohneinheit werden zusammengeführt.

Die dauerhafte Historie liegt unter .agent-state/application-ledger.json in
diesem privaten Repository. Reservierungen werden atomar vor dem Absenden
gespeichert; unklare oder unterbrochene Versuche werden nicht wiederholt.
Historie niemals zurücksetzen, solange ein Versandstatus ungeklärt ist.

## Offene Versandblocker

Gewobag/Wohnungshelden: reCAPTCHA und zusätzliche unbekannte Pflichtantworten,
unter anderem zur §9-WoFG-Bescheinigung. HOWOGE: mehrstufige Bedingungen zu
Einkommen und Bonität; das derzeit passende Beispiel war bereits geschlossen.
GESOBAU: Immomio-Konto/Profil erforderlich; aktuelle Treffer enthalten zudem
Alters- oder WG-Bedingungen. Die übrigen Anbieter haben noch keinen verifizierten
Versandadapter. Details: ADAPTER_STATUS.md.

Keine Schutzmaßnahmen umgehen und keinen Versand allein durch Umschalten von
ENABLE_LIVE_APPLICATIONS erzwingen. Ein gültiger Formular- und Erfolgstest steht
weiterhin aus. Die vorherige unvalidierte Sendefunktion ist deaktiviert.

## Lokale Tests

Python 3.11: python -m unittest discover -s tests -v
Für den öffentlichen Suchlauf zusätzlich Playwright 1.56.0 und Chromium
installieren. Ein fehlgeschlagener oder unvollständiger Suchlauf beendet den
Workflow mit Fehlerstatus und hinterlegt trotzdem einen Bericht.
