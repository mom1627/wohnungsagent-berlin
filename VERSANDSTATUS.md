# Weitere Anbieter und Übertragungskontrolle

4. November 2026: STADT UND LAND als vierter nativer Versandadapter implementiert. Das öffentliche Formular wurde ohne Bewerberdaten geprüft. Noch keine bestätigte Bewerbung und kein realer Versandtest für diesen Anbieter. Automatische Versuche bleiben gesperrt, bis der vom Nutzer festgelegte früheste Einzugstermin als `APPLICANT_EARLIEST_MOVE_IN` hinterlegt ist (`ASAP` oder `YYYY-MM-DD`). Das Datum wird nicht geraten. Einkommen wird ausschließlich aus dem geschützten Secret gelesen; die 35-Prozent-Frage wird rechnerisch wahrheitsgemäß beantwortet. Neue bedingte Fragen, zusätzliche Einwilligungen, Dokumente und sichtbare CAPTCHAs stoppen den Versand. Auch Mietpreis, Zimmer, WBS und Bezirk müssen am aktuellen Anbieterangebot eindeutig verifiziert sein.

Die gemeinsamen Versandadapter beobachten nach dem einmaligen normalen Formularbutton nur boolesche Übertragungsmerkmale und HTTP-Statuszahlen. Keine Request-/Response-Texte, URLs, Header, Formulardaten oder Tokens werden gespeichert. Ein POST oder HTTP 200 ist keine Bewerbungsbestätigung. Unklare Versuche bleiben dauerhaft gegen Wiederholung reserviert. Gewobag, HOWOGE und WBM bleiben für neue passende Angebote freigegeben; GESOBAU/Immomio bleibt bei sichtbarem CAPTCHA manuell.

96 lokale Regressionsprüfungen bestanden; vollständiger GitHub-Actions-Lauf folgt auf diesen Commit. Das Tagesziel von vier bestätigten Anfragen ist weiterhin nicht nachgewiesen.

---

# Aktueller Stand nach dem erweiterten Lauf

4. November 2026: [Lauf 41813066484](https://github.com/mom1627/wohnungsagent-berlin/actions/runs/41813066484) erfolgreich; 86 Tests bestanden.

Suche und automatische Anfrageversuche sind dreimal täglich für Gewobag, HOWOGE und WBM freigegeben. Kriterien: 1 oder 2 Zimmer, maximal 550 EUR warm, günstigere Wohnungen eingeschlossen, bisherige Zielbezirke; WBS-Flächenlimit 50 m². HOWOGE-Kontaktanfragen werden nicht mehr durch die spätere Einkommens-/Vertragsprüfung gesperrt. Einkommen oder vorhandene Jobcenter-Mietübernahme werden nicht erfunden.

511 Angebote auf 52 vollständig durchlaufenen Ergebnisseiten, 11 Basis-Treffer. Keine neue Anfrage: zwei Wohnungen bereits reserviert, drei Studierendenangebote, fünf GESOBAU-Angebote mit besonderen Bedingungen bzw. fehlenden aktuellen Daten und ein geschlossener HOWOGE-Kontaktweg. Das günstigste erkannte 2-Zimmer-Angebot in den Zielbezirken lag im Lauf bei 686,30 EUR warm, oberhalb der bestätigten Grenze.

**Heute tatsächlich bestätigt: 0 von angestrebten 4.** Die zwei früheren Gewobag-Versuche bleiben unbestätigt und werden nicht wiederholt. GESOBAU hat noch keinen vollständigen Versandadapter; das sichtbare Immomio-CAPTCHA erfordert manuelle Aktion. Die separat geprüfte GESOBAU-Suche unter 550 EUR zeigte ein Studierenden-/Azubi-WG-Zimmer und zwei Seniorenangebote.

Vier bestätigte Bewerbungen täglich können ohne vier neue passende Angebote nicht garantiert werden. Ein verlässlich bestätigter Versand und vier vollständig aktive Anbieter sind noch nicht nachgewiesen.

## Frühere Läufe und Änderungen

# Versandstatus – 4. November 2026

Vollständiger Actions-Lauf: [41808132504](https://github.com/mom1627/wohnungsagent-berlin/actions/runs/41808132504), erfolgreich. **0 bestätigte Bewerbungen.** Ein grüner Suchlauf ist kein Versandnachweis.

| Wohnung | Tatsächliche Versuche | Ergebnis |
| --- | ---: | --- |
| Schwedter Straße 31, Gewobag 1000-00160-0202-0067 | 1 früherer Versuch | Unbestätigt, dauerhaft reserviert |
| Ella-Kay-Straße 20, Gewobag 1000-00264-0102-0246 | 1 neuer Versuch | Normale Formularaktion ausgeführt; keine ausdrückliche Erfolgsbestätigung innerhalb der damaligen Nachbeobachtung erfasst. `submission_unverified`, dauerhaft reserviert |

Im verbundenen Gmail wurde nach dem neuen Versuch keine passende Bestätigung gefunden. Beide Wohnungen werden nicht erneut angefragt. Andere geeignete Angebote können weiter angefragt werden; nach einem neuen unklaren Versuch pausiert nur der betreffende Anbieter für den Rest des Laufs.

## Suche

51 öffentlich erreichte Ergebnisseiten bis zur letzten Seite; 504 Angebotsverknüpfungen, 3 Dubletten, 501 unterschiedliche Angebote aller sieben Anbieter. 10 Basis-Treffer: eine neue unbestätigte Anfrage, eine alte Reservierung übersprungen, acht nicht gesendet (Senioren-/WG-/Studierendenbedingungen, fehlende aktuelle Daten, geschlossener HOWOGE-Kontaktweg, Immomio-CAPTCHA/Anmeldung).

Die zwischenzeitlichen Navigationsfehler wurden behoben: Der Agent übernimmt die öffentliche Adresse aus dem normalen Weiter-Button in eine neue Seite im selben Browserkontext. Bereits gefundene öffentliche Treffer werden zusätzlich dauerhaft als Merkliste gesichert. Eine Merkliste ersetzt niemals die aktuelle Anbieterprüfung.

## Vier gewünschte Anbieter

| Anbieter | Stand |
| --- | --- |
| Gewobag | Formularadapter aktiv für andere passende Wohnungen; bisher kein bestätigter Versand |
| HOWOGE | Eigener Formularadapter implementiert; bestätigtes Haushaltsnettoeinkommen ist geschützt hinterlegt; das Dreifache der jeweiligen Warmmiete wird weiterhin geprüft; letzter Basis-Treffer geschlossen |
| WBM | Eigener Formularadapter implementiert; ausdrückliche Freigabe zur sechsmonatigen Datenspeicherung für geeignete Angebote ist geschützt hinterlegt; kein aktueller Basis-Treffer |
| GESOBAU | Öffentlicher Immomio-Weg geprüft; sichtbares Friendly-Captcha erfordert manuelle Aktion. Vollständiger Versandadapter nicht fertig |

**Vier vollständig aktive, tatsächlich validierte Anbieter sind noch nicht erreicht.**

Nach dem genannten Lauf erweitert: Erfolgsprüfung der übergeordneten Anbieter-Seite und neuer Bestätigungsfenster auf freigegebenen Domains, bis zu 45 Sekunden Nachbeobachtung, ausschließlich feste Rückmeldesignale als Wahrheitswerte. Das rekonstruiert keine verlorene Bestätigung. Der neueste Actions-Bericht und die dauerhafte Historie bleiben maßgeblich.

## Erweiterung auf Wunsch des Nutzers

Ab dieser Revision gelten 1 oder 2 Zimmer und weiterhin maximal 550 EUR Warmmiete, einschließlich günstigerer Wohnungen. Die WBS-Flächenbegrenzung bleibt bestehen. Vier tatsächlich bestätigte Anfragen pro Berliner Kalendertag sind ein überwacht ausgewiesenes Ziel, keine garantierte Verfügbarkeit. Die HOWOGE-Einkommensprüfung wird für die erste reine Kontaktanfrage nicht mehr vorgezogen; sie bleibt als offene Voraussetzung vor Vertragsabschluss markiert. Die obigen Suchzahlen stammen aus dem genannten früheren Lauf mit den damaligen Zimmerkriterien. Aktuelle Ergebnisse siehe Actions.
