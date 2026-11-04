# Bewerbungsadapter

Stand: 4. November 2026, nach Lauf 41808132504. Vier Anbieter werden ausdrücklich ausgewiesen; vier vollständig aktive und durch echte Bestätigungen validierte Sender sind **nicht erreicht**.

| Anbieter | Implementierung | Tatsächlich bestätigt | Offene Voraussetzung |
| --- | --- | --- | --- |
| Gewobag | Geschütztes Profil, Wohnungshelden-Formular, dauerhafte Reservierung | Nein; zwei verschiedene Wohnungen einmal versucht und unbestätigt | Status klären; keine Wiederholung dieser Angebote |
| HOWOGE | Exakt geprüfte Kenntnisnahme-Hinweise, Kontaktformular Vorname/Nachname/E-Mail | Nein | Einkommensbetrag im Secret vorhanden; dreifache tatsächliche Warmmiete muss pro Angebot erfüllt sein |
| WBM | Eigenes Formular; optionale unbekannte Adresse leer, Honeypot unberührt | Nein | Freigabe im Secret vorhanden; passendes Angebot und echte Versandbestätigung stehen aus |
| GESOBAU | Öffentliche Immomio-Weiterleitung und CAPTCHA-Sperren geprüft | Nein; Versandadapter nicht fertig | Sichtbares Friendly-Captcha, danach Kontozugang/Profil prüfen |

## Geschützte Angaben eingerichtet

- `APPLICANT_MONTHLY_NET_INCOME` ist eingerichtet. Es enthält das bestätigte verfügbares monatliches Haushaltsnettoeinkommen, Dezimalbetrag ohne Währungszeichen. Fehlende/ungültige Werte und unterschrittene Grenze blockieren HOWOGE. Eine Ausnahme wegen Jobcenter-Bezug wird nicht erfunden.
- `APPLICANT_WBM_DATA_CONSENT` ist nach ausdrücklicher Nutzerfreigabe eingerichtet. Der geprüfte Einwilligungstext umfasst elektronische Verarbeitung für geeignete Wohnungsangebote, Widerrufsmöglichkeit und Löschung nach sechs Monaten. Geänderter Text blockiert vor Eingabe persönlicher Daten.

Alle Bewerberangaben bleiben ausschließlich in Actions-Secrets und im flüchtigen Formularspeicher. Keine Werte in Dateien oder Logs.

Eine erforderliche Ja-/Nein-Frage verlangt keine unwahre Ja-Antwort. Fehlende §9-Bescheinigung wird wahrheitsgemäß mit der vorhandenen Nein-Option beantwortet. Ein ausdrücklich im Angebot genannter §9-Bedarf blockiert weiter. Keine Immatrikulation, ausreichende Bonität oder Jobcenter-Zustimmung wird behauptet.

Unklare Ergebnisse sperren dieselbe Wohnung dauerhaft. Andere Wohnungen bleiben möglich; nach einem neuen unklaren Versuch pausiert dieser Anbieter für den Rest des Laufs. Keine automatische Wiederholung reservierter Angebote.

Nur reguläre Formularbuttons; keine CAPTCHA-Lösung, keine direkten Absende-Endpunkte, kein Umgehen von Login. Nur neue ausdrückliche Bestätigung auf freigegebener Anbieter-/Wohnungshelden-Seite zählt. Bereits bestehende Erfolgsnachrichten zählen nicht. Ergebnisdiagnostik speichert ausschließlich feste Wahrheitswerte, keine ungeprüften Servertexte oder Formulardaten.
