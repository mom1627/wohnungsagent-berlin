# Bewerbungsadapter

Stand: 4. November 2026, mit erweiterten Suchregeln (1 oder 2 Zimmer, bis 550 EUR warm). Fünf Anbieter werden ausdrücklich ausgewiesen; vier vollständig aktive und durch echte Bestätigungen validierte Sender sind **nicht erreicht**.

| Anbieter | Implementierung | Tatsächlich bestätigt | Offene Voraussetzung |
| --- | --- | --- | --- |
| Gewobag | Geschütztes Profil, Wohnungshelden-Formular, dauerhafte Reservierung | Nein; zwei verschiedene Wohnungen einmal versucht und unbestätigt | Status klären; keine Wiederholung dieser Angebote |
| HOWOGE | Exakt geprüfte Kenntnisnahme-Hinweise, Kontaktformular Vorname/Nachname/E-Mail | Nein | Erste Kontaktanfrage freigegeben; Einkommensnachweise/Jobcenter-Mietübernahme bleiben Voraussetzung der späteren Vertragsprüfung |
| WBM | Eigenes Formular; optionale unbekannte Adresse leer, Honeypot unberührt | Nein | Freigabe im Secret vorhanden; passendes Angebot und echte Versandbestätigung stehen aus |
| STADT UND LAND | Beobachtetes Material-Formular über Wohnungshelden; gemeinsamer dauerhafter Reservierungs- und Bestätigungsweg | Nein; noch kein realer Versandtest | Nutzer muss frühesten Einzugstermin als geschütztes Secret festlegen; aktuelle Bedingungen und Bezirk müssen am Anbieterangebot eindeutig sein |
| GESOBAU | Öffentliche Immomio-Weiterleitung und CAPTCHA-Sperren geprüft | Nein; Versandadapter nicht fertig | Sichtbares Friendly-Captcha, danach Kontozugang/Profil prüfen |

## Geschützte Angaben eingerichtet

- `APPLICANT_MONTHLY_NET_INCOME` ist eingerichtet. Es enthält das bestätigte verfügbares monatliches Haushaltsnettoeinkommen, Dezimalbetrag ohne Währungszeichen. Fehlende/ungültige Werte und unterschrittene Grenze markieren eine offene Vertragsprüfung, blockieren aber nicht die erste reine Besichtigungsanfrage. Eine Ausnahme wegen Jobcenter-Bezug wird nicht erfunden.
- `APPLICANT_WBM_DATA_CONSENT` ist nach ausdrücklicher Nutzerfreigabe eingerichtet. Der geprüfte Einwilligungstext umfasst elektronische Verarbeitung für geeignete Wohnungsangebote, Widerrufsmöglichkeit und Löschung nach sechs Monaten. Geänderter Text blockiert vor Eingabe persönlicher Daten.

Alle Bewerberangaben bleiben ausschließlich in Actions-Secrets und im flüchtigen Formularspeicher. Keine Werte in Dateien oder Logs.

Eine erforderliche Ja-/Nein-Frage verlangt keine unwahre Ja-Antwort. Fehlende §9-Bescheinigung wird wahrheitsgemäß mit der vorhandenen Nein-Option beantwortet. Ein ausdrücklich im Angebot genannter §9-Bedarf blockiert weiter. Keine Immatrikulation, ausreichende Bonität oder Jobcenter-Zustimmung wird behauptet.

Unklare Ergebnisse sperren dieselbe Wohnung dauerhaft. Andere Wohnungen bleiben möglich; nach einem neuen unklaren Versuch pausiert dieser Anbieter für den Rest des Laufs. Keine automatische Wiederholung reservierter Angebote.

Nur reguläre Formularbuttons; keine CAPTCHA-Lösung, keine direkten Absende-Endpunkte, kein Umgehen von Login. Nur neue ausdrückliche Bestätigung auf freigegebener Anbieter-/Wohnungshelden-Seite zählt. Bereits bestehende Erfolgsnachrichten zählen nicht. Ergebnisdiagnostik speichert ausschließlich feste Wahrheitswerte, keine ungeprüften Servertexte oder Formulardaten.

## Phasengerechte Prüfung

Die frühere automatische Sperre der ersten HOWOGE-Anfrage wegen einer Vertrags-Einkommensgrenze wurde korrigiert. Die offizielle Seite trennt Angaben zur Besichtigungsanfrage von Unterlagen für den Vertragsabschluss: https://www.howoge.de/immobiliensuche/mietbedingungen.html. Für Leistungsbeziehende nennt sie die Mietübernahmeerklärung des Jobcenters/Amts. Der Agent behauptet deren Vorliegen nicht und schließt keine Mietverträge. Der geprüfte Formularweg übermittelt nur Name und E-Mail, keine erfundene Einkommensangabe.

## STADT UND LAND und Übertragungsdiagnostik

`APPLICANT_EARLIEST_MOVE_IN` ist noch nicht eingerichtet: akzeptiert werden ausschließlich ein vom Nutzer bestätigtes `ASAP` oder ein ISO-Datum. Ohne diesen Wert werden keine Formulardaten eingegeben. Die 35-Prozent-Einkommensfrage wird aus geschütztem Einkommen und konkreter Warmmiete mit Ja oder Nein beantwortet. Eine Jobcenter-Kostenübernahme wird nicht behauptet. Neue bedingte Fragen stoppen vor weiteren Angaben; unbekannte Felder oder geänderte Datenschutzhinweise sind gesperrt. Die tatsächlichen öffentlichen Herkunftsoptionen wurden geprüft, darunter `Inberlinwohnen.de`.

Die passive Diagnose zählt ausschließlich POSTs aus dem vertrauenswürdigen Formular an den Anbieter/Formulardienst, HTTP-Statuszahlen und ein Fehlermerkmal. Request-/Response-Inhalte, URLs und Header werden nie aufgezeichnet. Auch HTTP 200 zählt ohne sichtbare Anbieterbestätigung nicht als versendete Bewerbung. Damit lassen sich künftig Fehler vor und nach der Übertragung unterscheiden, ohne Erfolg zu erfinden.
