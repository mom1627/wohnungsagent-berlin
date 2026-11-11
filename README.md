# Wohnungsagent Berlin

Der Agent durchsucht inBerlinWohnen sowie die Originalseiten von degewo,
GESOBAU, WBM und berlinovo dreimal täglich. Er prüft mögliche Treffer erneut
beim Anbieter und meldet die Ergebnisse und Ausfälle pro Quelle.

## Automatische Anfragen

Für Gewobag / Wohnungshelden ist der normale Browser-Formularweg implementiert.
Der Workflow ist für Versand konfiguriert. Er benötigt zusätzlich zu den drei
vorhandenen Kontakt-Secrets ein gültiges verschlüsseltes
APPLICANT_HOUSING_PROFILE. Ohne vollständiges geschütztes Profil wird nichts
gesendet. Einrichtung: HOUSING_PROFILE_SETUP.md.

Die erste tatsächlich passende Anfrage dient als echter Erfolgstest. Erst eine
neue ausdrückliche Bestätigung des Anbieters gilt als Versandnachweis und
validiert den Adapter für künftige Läufe. Der konkrete Versandstatus steht im
Laufbericht und in der dauerhaften Historie. Ein erfolgreicher Suchlauf allein
belegt keinen Versand.

Der Agent nutzt ausschließlich den regulären Formularbutton. Eine unsichtbare
reCAPTCHA-Einbindung wird nicht mit einer sichtbaren Sicherheitsaufgabe
verwechselt. Tatsächliche Challenges, unbekannte Pflichtfelder, zusätzliche
Verpflichtungen oder fehlende Bescheinigungen erfordern manuelle Klärung.

Gewobag, HOWOGE, WBM und STADT UND LAND besitzen implementierte Formularadapter.
Implementiert bedeutet noch nicht durch tatsächlichen Versand bestätigt. Für WBM
ist vor Nutzung eine gesonderte Freigabe der beobachteten Datenspeicherung nötig
(APPLICANT_WBM_DATA_CONSENT=1 als verschlüsseltes Secret). GESOBAU wird bis zum
Immomio-Bewerbungsweg geprüft und meldet CAPTCHA/Login als manuelle Voraussetzung.
Vier vollständig einsatzbereite und bestätigte Anbieter sind damit noch nicht erreicht.
Details: ADAPTER_STATUS.md.

## Kriterien

Alle zwölf Berliner Bezirke, bevorzugt ein Zimmer, auch zwei Zimmer,
maximal 550 Euro nachgewiesene Warmmiete.
WBS-Kategorie, erlaubte Fläche, Gültigkeit und besondere Bedingungen werden mit
dem geschützten Profil abgeglichen. Die Zahl der Bewohner wird nicht mit einer
ungeprüften Zimmerzahl gleichgesetzt. Fehlende Immatrikulation oder eine
notwendige nicht vorhandene Bescheinigung führen nicht zu falschen Antworten.
Eine Jobcenter-Zustimmung wird nicht behauptet.

## Dauerhafte Historie

Die personenbezugsfreie Historie liegt in .agent-state/application-ledger.json
im privaten Repository. Vor jedem Sendeversuch wird eine Reservierung atomar
gespeichert. Abgebrochene oder unklare Versuche werden nicht automatisch
wiederholt. Ein ungeklärter Vorgang sperrt dauerhaft dieses Angebot. Andere Wohnungen können
weiter angefragt werden. Nach einem neuen unklaren Versuch pausiert nur dieser
Anbieter für den Rest des aktuellen Laufs; der nächste Lauf darf andere Angebote prüfen.
Überlappende Produktionsläufe werden verhindert. Die Historie nicht zurücksetzen,
solange ein Sendevorgang ungeklärt ist.

## Zeitplan und Berichte

06:17, 11:17 und 16:17 UTC, aktuell im Winter 07:17, 12:17 und 17:17 Uhr Berlin.
GitHub kann Startzeiten verzögern. Laufberichte stehen als Actions-Zusammenfassung
und JSON-/Markdown-Artefakt bereit; Artefakte bleiben 14 Tage verfügbar.
Die Bewerbungshistorie und die erstmals beim Anbieter bestätigten Angebote
werden dauerhaft in getrennten Zustandsdateien gespeichert.

## Prüfung

Python 3.11: `python -m pip install lxml==6.1.1`, dann
`python -m unittest discover -s tests -v`.

Der Suchlauf verwendet Playwright 1.56.0 mit Chromium. Sicherheitsregressionen
prüfen unter anderem WBS-Gültigkeit, Flächenbegrenzung, dynamische Pflichtfelder,
sichtbare gegenüber unsichtbaren CAPTCHAs, Reservierung vor dem Button-Klick,
fehlgeschlagene Statusspeicherung und echte gegenüber bereits vorhandenen
Erfolgsnachrichten.

## Merkliste und Suchstörungen

Bereits gefundene Basis-Treffer werden ohne Bewerberdaten in .agent-state/candidate-watchlist.json gespeichert. Beim nächsten Lauf werden sie unabhängig von vorübergehenden Suchstörungen erneut auf der tatsächlichen Anbieterseite geprüft. Eine alte Quellenaufnahme ist niemals ein Versandnachweis oder ein Ersatz für aktuelle Angebotsbedingungen. Preis-/Zimmerabweichungen und unbekannte Voraussetzungen blockieren weiterhin. Ein unvollständiger Suchlauf bleibt im Bericht und im Actions-Ergebnis als Fehler sichtbar, auch wenn eine unabhängig geprüfte Anfrage möglich war.

## Tagesziel und Vertragsprüfung

Ziel sind mindestens vier tatsächlich bestätigte Anfragen pro Berliner Kalendertag. Alle neuen passenden Angebote werden bearbeitet; es werden keine unpassenden Wohnungen oder Doppelanfragen zum Auffüllen versendet. Die dauerhafte Historie zählt nur echte Bestätigungen. Ein nicht erreichtes Tagesziel wird ausdrücklich im Laufbericht ausgewiesen.

HOWOGE: Die erste Besichtigungsanfrage wird von der späteren Einkommens-/Vertragsprüfung getrennt. Das beobachtete erste Formular enthält nur Vorname, Nachname und E-Mail. Die drei vorangestellten Hinweise werden lediglich zur Kenntnis genommen. Fehlendes Einkommen in dreifacher Miethöhe blockiert die Kontaktanfrage nicht automatisch; es bleibt als notwendige Nachprüfung vor einem Mietvertrag sichtbar. Eine Mietübernahmeerklärung oder ausreichendes Einkommen werden niemals behauptet. Quelle: https://www.howoge.de/immobiliensuche/mietbedingungen.html
