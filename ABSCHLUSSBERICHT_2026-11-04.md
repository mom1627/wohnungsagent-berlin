# Wohnungsagent Berlin – Abschlussbericht vom 4. November 2026

**Ergebnis: Die automatische Suche funktioniert. Der automatische Bewerbungsversand ist nicht freigeschaltet und noch nicht vollständig implementiert bzw. validiert. Es wurden keine Bewerbungen versendet.**

Geprüfter Datenstand: 04.11.2026, 01:42 Uhr Berlin. Code: `9f538b0924e828ceb75f62613fad8ec77cec9fc3`.

[Erfolgreicher vollständiger Actions-Lauf](https://github.com/mom1627/wohnungsagent-berlin/actions/runs/41748738069) · [Erfolgreiche CI-Prüfung](https://github.com/mom1627/wohnungsagent-berlin/actions/runs/41748737983)

## Tatsächlich geprüft

| Prüfung | Ergebnis |
| --- | --- |
| Ergebnisseiten | 52, bis zur letzten Seite |
| Angebotsverweise | 511 |
| Eindeutige Wohnungen | 510; ein doppelter Verweis entfernt |
| Basis-Treffer bei Bezirk, Zimmerzahl und Warmmiete | 10 |
| Automatisch versendet / bestätigt | 0 / 0 |
| Lokale und GitHub-Tests | 41 bestanden |
| Bewerber-Secrets | alle drei vorhanden; Werte nicht in Dateien oder Logs ausgegeben |
| Dauerhafte Historie | erfolgreich angelegt und aus erneutem Actions-Lauf gelesen |
| Quellabfrage | vollständig und ohne Pipelinefehler |

## Abdeckung der Anbieter

| Anbieter | Eindeutige Angebote |
| --- | ---: |
| Gewobag | 77 |
| HOWOGE | 158 |
| degewo | 99 |
| STADT UND LAND | 41 |
| WBM | 14 |
| GESOBAU | 21 |
| berlinovo | 100 |

## Nicht versendete Basis-Treffer

Die folgenden Mieten stammen aus der Suchquelle. Ein Basis-Treffer ist noch keine vollständige Eignungs- oder Bewerbungsfreigabe. Alle zehn Angebote wurden vor einem Versand gesperrt.

| Angebot | Warmmiete laut Quelle | Konkreter Grund |
| --- | ---: | --- |
| [Ella-Kay-Straße 20, 10405, Pankow](https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/1000-00264-0102-0246) | 471,83 € | reCAPTCHA; WBS-Kategorie nicht vollständig bestätigt; Antwort zur §9-WoFG-Bescheinigung fehlt |
| [Schwedter Straße 31, 10435, Pankow](https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/1000-00160-0202-0067) | 548,78 € | reCAPTCHA; WBS-Kategorie nicht vollständig bestätigt |
| [Senftenberger Ring 12, 13439, Reinickendorf](https://www.gesobau.de/?immo_ref=10-00922-00001-0197-df320820-f8e7-4aef-aacb-72c65ba4b38d) | 456,64 € | Anbieterdetails nicht abrufbar; Quelle nennt zusätzlich eine Altersgrenze ab 50 Jahren |
| [Roedernallee 118C, 13437, Reinickendorf](https://www.gesobau.de/?immo_ref=10-00983-00005-1090-8aabe420-3a3e-4909-8c52-2a306159a03b) | 442,32 € | WG-Zimmer für Studierende/Azubis; Immomio-Konto/Profil und WBS-Prüfung erforderlich |
| [Bremer Straße 11, 10551, Mitte](https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/7100-76801-0101-0021) | 463,71 € | reCAPTCHA; WBS-Kategorie nicht vollständig bestätigt; Immatrikulationsstatus ungeklärt |
| [Amrumer Straße 36, 13353, Mitte](https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/0100-02132-0101-0109) | 368,66 € | reCAPTCHA; WBS-Kategorie nicht vollständig bestätigt; Immatrikulationsstatus ungeklärt |
| [Eichhorster Weg 44, 13435, Reinickendorf](https://www.gesobau.de/?immo_ref=10-00913-00001-0317-20d3bd65-2998-4e98-aea7-d48cde39f60d) | 488,31 € | Anbieterdetails nicht abrufbar; Quelle nennt zusätzlich eine Altersgrenze ab 50 Jahren |
| [Wilhelmsruher Damm 148, 13439, Reinickendorf](https://www.gesobau.de/?immo_ref=10-00920-00001-1322-f3b90427-6302-4ec2-bb38-1776df0a8005) | 496,93 € | Angebot ab 60 Jahren; Immomio-Konto/Profil erforderlich |
| [Wolfgang-Heinz-Straße 40, 13125, Pankow](https://www.howoge.de/wohnungen-gewerbe/wohnungssuche/detail/1770-24015-305.html?t=ibw) | 422,52 € | Anbieter meldet Angebot nicht mehr verfügbar; Bewerbungsweg geschlossen |
| [Wilhelmsruher Damm 148, 13439, Reinickendorf](https://www.gesobau.de/?immo_ref=10-00920-00001-1605-a05d1369-f056-49f8-9ac2-e899d7cd00b4) | 527,51 € | Angebot ab 60 Jahren; Immomio-Konto/Profil erforderlich; ausdrücklich ohne WBS-Anspruch |

## Umgesetzte Änderungen

- Echte Livewire-Seitennavigation statt unbestätigter `?page=`-Abfragen; notwendige Cookie-Auswahl wird gespeichert. Unvollständige und wiederholte Seiten werden als Fehler gemeldet.
- Alle sieben Anbieter werden erkannt. Objektkennungen in URL-Parametern bleiben erhalten. GESOBAU-Objekte behalten ihre Identität auch bei geänderter UUID.
- Aktuelle Anbieterdaten werden erneut geprüft. Warmmiete, Zimmerzahl, Bezirk, Verfügbarkeit und WBS werden nicht aus bloßen Schlagworten abgeleitet. Kaltmiete wird nicht als Warmmiete behandelt.
- Alters-, Studien-, WG-, Sonder-WBS- und Genossenschaftsbedingungen werden gemeldet. Eine Jobcenter-Zustimmung wird nicht behauptet.
- Die Formularprüfung wird tatsächlich durchgeführt; ein fest übergebenes `application_frame_present=False` blockiert nicht mehr pauschal den Ablauf.
- Dauerhafte, personenbezugsfreie Historie unter `.agent-state/application-ledger.json`; atomare GitHub-Schreibvorgänge mit SHA-Prüfung, Reservierung vor einem künftigen Sendevorgang und Sperre unklarer Versuche. Überlappende Produktionsläufe werden verhindert.
- JSON- und Markdown-Bericht samt Actions-Zusammenfassung, ohne Bewerberwerte. Der alte unvalidierte Wohnungshelden-Sender ist deaktiviert.

## Noch offen – deshalb kein automatischer Versand

1. Gewobag/Wohnungshelden enthält reCAPTCHA. Zusätzlich fehlen bei einzelnen Angeboten verbindlich bekannte Antworten zu Pflichtfragen, beispielsweise §9-WoFG-Bescheinigung oder Immatrikulation. Es wurden keine Antworten geraten und keine Schutzmaßnahmen umgangen.
2. HOWOGE hat einen mehrstufigen Prozess mit Einkommens- und Bonitätshinweisen. Der aktuelle Basis-Treffer ist bereits geschlossen; ein zulässiger Versand- und Erfolgstest war damit nicht möglich.
3. GESOBAU verwendet Immomio mit Konto und Profil. Die aktuellen Basis-Treffer enthalten zudem Alters- oder WG-Bedingungen. Es wurde kein Konto angelegt oder eine neue Vereinbarung akzeptiert.
4. Für degewo, WBM, STADT UND LAND und berlinovo liegt weiterhin kein verifizierter Versandadapter vor. Im geprüften Lauf gab es dort keinen Basis-Treffer für die angegebenen Kriterien.
5. Kein Anbieter hat bisher einen vollständigen zulässigen Sende- und Bestätigungstest bestanden. `ENABLE_LIVE_APPLICATIONS` bleibt deshalb `0`; die Liste verifizierter Sender bleibt leer. Eine grüne Suchpipeline belegt keinen erfolgreichen Bewerbungsversand.

## Laufender Betrieb

Die Suche läuft dreimal täglich: 06:17, 11:17 und 16:17 UTC, aktuell 07:17, 12:17 und 17:17 Uhr Berlin. GitHub kann Startzeiten verzögern. Der tägliche Bericht liegt als Actions-Artefakt vor und bleibt 14 Tage verfügbar; die Dublettenhistorie wird unabhängig davon dauerhaft im privaten Repository gespeichert.

## GitHub-Schreibzugriff

Die zusammengehörigen Änderungen wurden erfolgreich direkt auf `main` gespeichert. Die früher erwähnten Sicherheitsblockaden traten bei diesen Schreibvorgängen nicht auf; ihre damalige genaue Ursache ist damit nicht nachgewiesen.

**Gesamtziel noch nicht erreicht:** Ein Agent, der ohne tägliche Mithilfe automatisch rechtmäßige Anfragen abschickt, ist noch nicht einsatzbereit. Suche, Filterberichte und dauerhafte Historie sind eingerichtet und getestet. Der Versand bleibt aus den oben belegten Gründen offen.
