# Suchquellen und Bewerbungswege in Berlin

Der Produktionslauf durchsucht inBerlinWohnen und sechs Anbieter unabhängig
voneinander. Ein Ausfall bleibt mit Grund und Seitenzahl sichtbar. Mögliche
Treffer werden anhand des aktuellen Originalangebots und des Bewerbungswegs
geprüft.

| Quelle | Suche | Bewerbungsweg |
| --- | --- | --- |
| inBerlinWohnen | Öffentliche Angebotskarten und sichtbare Seitennavigation | Weiterleitung zum Anbieter |
| Gewobag | Offizielle öffentliche Ergebnisliste mit Seitenlinks | Vorhandener Browseradapter für Wohnungshelden |
| STADT UND LAND | Öffentliche Angebotsliste und „Mehr Ergebnisse laden“ | Vorhandener Browseradapter, mit geschütztem Einkommen und Einzugstermin |
| GESOBAU | Öffentliche Angebotsliste mit Seitenlinks | Immomio über Anbieterlink, manuelle Anmeldung und ggf. Sicherheitsprüfung |
| degewo | Öffentliche Angebotsliste mit Seitenlinks | Anbieterformular mit Friendly Captcha, manuelle Bearbeitung |
| WBM | Öffentliche Angebotsliste | Vorhandener Formularadapter mit zusätzlicher hinterlegter Einwilligung |
| berlinovo | Öffentliche Angebotsliste mit Seitenlinks und HTTPS-Exposé | Öffentlich verlinkter Wohnungshelden-Weg wird auf Verfügbarkeit geprüft |
| HOWOGE | Angebotskarten über inBerlinWohnen | Die direkte Ergebnisliste lädt über einen in robots.txt ausgeschlossenen JSON-Endpunkt. Die aktuellen Bewerbungslinks mit cHash sind ebenfalls von der automatisierten Abfrage ausgeschlossen und bleiben manuell. |

## Weitere geprüfte Quellen

| Quelle | Ergebnis |
| --- | --- |
| Immomio | Die Nutzungsbedingungen erfordern eine ausdrückliche Freigabe für automatisierten Zugriff und Versand in angemeldeten Bereichen. Anbieterlinks bleiben für die manuelle Bewerbung sichtbar. [Nutzungsbedingungen](https://www.immomio.com/nutzungsbedingungen/) |
| Kleinanzeigen | Automatisiertes Sammeln erfordert eine schriftliche Einwilligung des Betreibers. [Nutzungsbedingungen](https://themen.kleinanzeigen.de/nutzungsbedingungen/) |
| ImmoScout24 | Die dokumentierte Such-API ist für Content-Partner. [Such-API](https://api.immobilienscout24.de/api-docs/search/introduction/) |
| immowelt | Die dokumentierte API setzt einen aktiven Anbietervertrag voraus und liefert eigene Inserate. [API-Bedingungen](https://www.immowelt.de/meineimmowelt/apinutzungsbedingungen.aspx) |
| Waitly | Die Plattform arbeitet mit Interessen- und Wartelisten. Für diesen Agenten wurde kein freigegebener Such- oder Bewerbungszugang verifiziert. [Waitly](https://waitly.eu/de) |
| EverReal | Für diesen Agenten wurde kein öffentlicher Berlin-Feed verifiziert. Einzelne Bewerbungswege sind erst am konkreten Inserat prüfbar. [EverReal](https://de.everreal.co/) |
| Märkische Scholle und Märkische Baugenossenschaft | Beide Angebotsseiten meldeten bei der Prüfung keine Angebote. Ein etwaiger späterer Beitritt setzt überprüfbare Eintrittskosten voraus. [Märkische Scholle](https://maerkische-scholle.de/wohnungsangebote.html) · [Märkische Baugenossenschaft](https://mb-eg.de/wohnungssuche) |

Die Suche umfasst alle zwölf Bezirke. Sie priorisiert Einzimmerwohnungen und
berücksichtigt Zweizimmerwohnungen. Die Warmmiete muss am Originalangebot mit
höchstens 550 Euro belegt sein. WBS, Wohnfläche, Haushaltsgröße und
Sonderbedingungen müssen zum geschützten Profil passen.

Die Bewerbungshistorie reserviert ein Angebot vor dem Versand und speichert
URL-Aliase, soweit sie über die öffentliche Weiterleitung verifiziert wurden.
Der Lauf zählt ausschließlich ausdrückliche Bestätigungen. Ungeklärte Versuche
bleiben gesperrt. Eine manuelle Prüfung ist bei CAPTCHA, fehlenden Angaben,
nicht validierten Formularen oder notwendigen Einwilligungen im Bericht sichtbar.
