# Wohnungsagent Berlin

Der Agent durchsucht inBerlinWohnen automatisch dreimal täglich und prüft neue
Basis-Treffer erneut auf der Anbieterseite. Der vollständige Suchlauf wurde über
alle 52 Ergebnisseiten und alle sieben Gesellschaften erfolgreich geprüft.

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

Gewobag, HOWOGE und WBM besitzen eigene implementierte Formularadapter.
Implementiert bedeutet noch nicht durch tatsächlichen Versand bestätigt. Für WBM
ist vor Nutzung eine gesonderte Freigabe der beobachteten Datenspeicherung nötig
(APPLICANT_WBM_DATA_CONSENT=1 als verschlüsseltes Secret). GESOBAU wird bis zum
Immomio-Bewerbungsweg geprüft und meldet CAPTCHA/Login als manuelle Voraussetzung.
Vier vollständig einsatzbereite und bestätigte Anbieter sind damit noch nicht erreicht.
Details: ADAPTER_STATUS.md.

## Kriterien

Ein Zimmer, maximal 550 Euro Warmmiete, Reinickendorf/Wedding/Mitte/Pankow.
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
Die Historie wird unabhängig davon dauerhaft gespeichert.

## Prüfung

Python 3.11: python -m unittest discover -s tests -v

Der Suchlauf verwendet Playwright 1.56.0 mit Chromium. Sicherheitsregressionen
prüfen unter anderem WBS-Gültigkeit, Flächenbegrenzung, dynamische Pflichtfelder,
sichtbare gegenüber unsichtbaren CAPTCHAs, Reservierung vor dem Button-Klick,
fehlgeschlagene Statusspeicherung und echte gegenüber bereits vorhandenen
Erfolgsnachrichten.
