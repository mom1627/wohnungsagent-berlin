# Letzte Verifikation – 4. November 2026

Aktueller Versandcode: Commit 862e98b8a9e88f4e68ccb6f0fc9ce223272c286c. **100 lokale Tests bestanden. Der neue vollständige Actions-Lauf [41879180233](https://github.com/mom1627/wohnungsagent-berlin/actions/runs/41879180233/job/126747311167) ist ausgelöst, zeigt bei der letzten Kontrolle aber noch `queued` / `Starting job`; deshalb ist die neue WBM-Anfrage noch nicht ausgeführt oder bestätigt.** Der vorherige Job 126738169210 hat bereits alle Schritte erfolgreich protokolliert und ein vollständiges Artefakt geliefert (96 damalige Tests, 532 Angebote, 54 Seiten, 16 Basis-Treffer, 0 neue Anfrage). Seine äußere Laufstatus-Anzeige blieb widersprüchlich `in_progress`; ein Abbruchversuch wurde von GitHub mit `Cannot cancel a workflow run that is not in progress` zurückgewiesen. Kein belegter allgemeiner Actions-Ausfall; die offizielle Status-API meldete Actions operational. Ein überholter Zwischenlauf wurde zum Abbruch angefordert. Kein erneutes Absenden einer reservierten Wohnung.

Gewobag, HOWOGE und WBM bleiben im Produktionsworkflow für neue passende Anfragen freigegeben. Das WBM-Angebot Rathausstraße 17 (420,86 EUR warm, 1 Zimmer, 32,87 m², sofort, Baujahr 1985) war beim letzten direkten Öffnen noch vorhanden. Technische Bezirkszuordnung und begrenzte Einkommensobergrenzenprüfung sind korrigiert, ohne eine andere Bescheinigung oder Jobcenter-Zusage zu behaupten. Sichtbare CAPTCHA-/Login-Hürden werden nicht umgangen.

STADT UND LAND ist als vierter Sender implementiert, aber **vor jeglicher Dateneingabe gesperrt**, solange der Nutzer seinen frühesten Einzugstermin nicht angegeben hat. Dafür ist `APPLICANT_EARLIEST_MOVE_IN` vorgesehen; keine Annahme und kein Secret-Wert wurden erfunden. GESOBAU/Immomio bleibt ohne vollständigen Sender und bei sichtbarem CAPTCHA manuell.

**Tatsächlich bestätigt: weiterhin 0 Bewerbungen. Vier tägliche Bestätigungen oder vier erfolgreich validierte Anbieter sind nicht erreicht.** Die Automatik ist freigegeben und geplant; ihre tatsächliche Ausführung hängt von GitHubs Start des Jobs und passenden, regulär anfragbaren Angeboten ab. Der neue Lauf zählt nur sichtbare tatsächliche Anbieterbestätigungen. Kontaktdaten und geschützte Profilwerte bleiben ausschließlich Secrets / flüchtiger Formularspeicher.

---

# Korrektur der WBM-Bestandsprüfung

4. November 2026: Der technische Bezirksfehler bei WBM-Weiterleitungen ist behoben. Zusätzlich wurde eine zu strenge WBS-Sperre für alte WBM-Bestandsangebote eingegrenzt korrigiert: Der Berliner Senat ordnet Bestandswohnungen der Einkommensgruppe **bis 140** zu (Drucksache 19/23545, Antwort 1 und 1b, https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-23545.pdf). Daraus wird für die erste unverbindliche Anfrage abgeleitet, dass ein gültiger WBS der unteren Einkommensgruppe die Obergrenze erfüllt. Diese Auslegung gilt im Code ausschließlich für WBM, explizites Baujahr bis 2001 und eine normale WBS-140-Angabe ohne exklusive Kategorie, Untergrenze, Neubau-/Fördermodell-Hinweis. Andere Kategorien, besondere Bedingungen, Flächenlimit und Gültigkeit werden nicht freigegeben. Im geprüften WBM-Formular wird ausschließlich wahrheitsgemäß das Vorhandensein eines WBS bestätigt, keine Bescheinigung eines anderen Typs erfunden. Endgültige Dokumenten-/Vertragsprüfung bleibt beim Anbieter. 100 lokale Tests bestanden. Der neue Actions-Lauf prüft den tatsächlichen normalen Versandweg, falls das Angebot noch verfügbar ist. Eine Versandbestätigung liegt zum Commit-Zeitpunkt weiterhin nicht vor.

# Aktueller Versandstatus – 4. November 2026

[GitHub-Actions-Job 126738169210 / Lauf 41876774829](https://github.com/mom1627/wohnungsagent-berlin/actions/runs/41876774829/job/126738169210): alle Job-Schritte erfolgreich, 96 Tests bestanden. 532 unterschiedliche Angebote auf 54 bis zur letzten Seite durchlaufenen Ergebnisseiten; 16 Basis-Treffer einschließlich öffentlicher Merkliste, jeweils vor einer möglichen Anfrage neu geprüft. Keine Pipeline-Fehler. **Keine neue Anfrage und weiterhin 0 tatsächlich bestätigte Bewerbungen; Tagesziel 4 nicht erreicht.** Im verbundenen Gmail-Postfach wurde bei erneuter Suche keine zuordenbare Bestätigung gefunden; es ist nicht nachgewiesen, dass dieses Postfach mit dem Bewerbungs-Secret übereinstimmt.

| Anbieter | Versandcode | Automatische neue Versuche | Tatsächliche Bestätigung |
| --- | --- | --- | --- |
| Gewobag | Implementiert | Freigegeben für passende neue Angebote | Keine; zwei frühere unterschiedliche Wohnungen dauerhaft reserviert |
| HOWOGE | Implementiert | Freigegeben; spätere Vertragsunterlagen werden nicht erfunden | Keine |
| WBM | Implementiert | Freigegeben bei nachgewiesenen Angebotsbedingungen und bestätigter Datenschutzeinwilligung | Keine |
| STADT UND LAND | Neu implementiert; öffentliches Formular ohne Bewerberdaten geprüft | Gesperrt: vom Nutzer festzulegender frühester Einzugstermin fehlt | Noch kein realer Versandtest |
| GESOBAU | Öffentliche Immomio-Prüfung, noch kein vollständiger Sender | Gesperrt bei sichtbarem CAPTCHA / nicht verfügbarem Kontozugang | Keine |

## Gründe der 16 Treffer im vollständigen Job

- Zwei bereits reservierte Gewobag-Wohnungen: keine Wiederholung trotz fehlender Bestätigung.
- Vier weitere Gewobag-Angebote: zusätzliche besondere Berechtigung bzw. Studierendenanforderungen; keine Immatrikulationsbescheinigung behauptet.
- Acht GESOBAU-Angebote: Senioren-/WG-/Studierendenbedingungen, ausgeschlossener WBS-Anspruch oder nicht mehr verifizierbare Anbieterdetails; kein vollständig geprüfter automatischer Immomio-Versandweg.
- Ein HOWOGE-Angebot: der aktuelle Anbieter-Kontaktweg ist geschlossen.
- WBM, Rathausstraße 17: 420,86 EUR warm, 1 Zimmer, 32,87 m², sofort. Die aktuelle Anbieterseite verlangt ausdrücklich WBS 140. Der vorherige Lauf blockierte hier wegen der engen Kategorienprüfung; siehe die oben dokumentierte, begrenzte Bestandskorrektur. Ein Zuordnungsfehler bei der Weiterleitung von Objekt-ID auf lesbaren URL-Pfad wurde anschließend behoben: Der eindeutige aktuelle Angebotstitel nennt Mitte und wird nun als Anbieterbeleg erkannt. Allgemeine Werbung und widersprüchliche Bezirksbelege bleiben ausgeschlossen. 98 lokale Tests bestanden nach dieser Korrektur; vollständiger Nachlauf wird mit dem Commit gestartet. Ein weiteres recherchiertes WBM-Angebot mit ausdrücklich WBS 100/140 war beim aktuellen Öffnen nicht mehr vorhanden (404).

Der Berliner Mietratgeber erläutert Einkommensobergrenzen und verlangt einen gültigen passenden WBS; daraus wird keine erfundene Bescheinigung oder anbieterspezifische Zusage abgeleitet: https://www.berlin.de/sen/wohnen/wissen-fuer-mieter/berliner-mietratgeber/wohnberechtigungsschein/.

## Neu umgesetzt

STADT UND LAND nutzt seinen tatsächlich eingebetteten Wohnungshelden-Formularweg. Einzugstermin ausschließlich aus `APPLICANT_EARLIEST_MOVE_IN` (`ASAP` oder `YYYY-MM-DD` nach Nutzerangabe), Einkommensantwort aus dem geschützten Secret. Keine Standardannahme, Jobcenter-Zusage, neue Einwilligung oder unbekannte bedingte Pflichtangabe. Aktuelle Miet-, Zimmer-, Bezirks- und WBS-Bedingungen werden vor einem Versuch erneut geprüft. Der fehlende Termin beeinflusst die bisherigen drei Anbieter nicht.

Die gemeinsame passive Versanddiagnostik speichert ausschließlich feste Übertragungsmerkmale, POST-Anzahl und HTTP-Statuszahlen, niemals Request-/Response-Texte, URLs, Header, Tokens oder Bewerberdaten. HTTP 200 ist keine Versandbestätigung. Nur eine neue sichtbare Anbieterbestätigung zählt. Schutz vor Doppelbewerbungen bleibt dauerhaft im privaten Repository gespeichert.

Die Produktion bleibt dreimal täglich freigegeben; Kriterien bleiben 1 oder 2 Zimmer, höchstens 550 EUR warm einschließlich günstigerer Angebote, bisherige Zielbezirke und WBS-Flächenlimit. Vier tägliche bestätigte Bewerbungen und vier erfolgreich validierte Anbieter sind weiterhin nicht nachgewiesen. Für tatsächlichen Versand müssen neue passende Angebote und ein vollständig bedienbarer regulärer Formularweg vorliegen.

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
