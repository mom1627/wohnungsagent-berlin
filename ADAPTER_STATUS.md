# Bewerbungsadapter

Stand: 4. November 2026, Revision mit vier ausdrücklich ausgewiesenen Anbieterwegen.

| Anbieter | Implementierung | Tatsächlich bestätigt | Offene Voraussetzung |
| --- | --- | --- | --- |
| Gewobag | Wohnungshelden-Formular mit geschütztem Profil, nativen Auswahlfeldern und reserviertem Absendeversuch | Noch kein Nachweis | Nächste andere geeignete Wohnung; unbestätigte alte Anfrage bleibt gesperrt |
| HOWOGE | Eigener Adapter für drei exakt geprüfte Kenntnisnahme-Hinweise und Kontaktformular mit Vorname, Nachname, E-Mail | Noch kein Nachweis | Aktuelles geeignetes Angebot und Erfolgstest |
| WBM | Eigener Formularadapter; optionale unbekannte Adresse bleibt leer; sichtbares Honeypot-Feld bleibt unberührt | Noch kein Nachweis | Gesonderte Zustimmung zur sechsmonatigen Datenspeicherung für geeignete Wohnungsangebote; aktuelles passendes Angebot |
| GESOBAU | Eigene Prüfung der öffentlichen Immomio-Weiterleitung und sichtbarer CAPTCHA-Sperren | Kein Versandadapter abgeschlossen | Sichtbares Friendly-Captcha vor Jetzt bewerben; danach Kontozugang/Profil prüfen |

Das Vier-Anbieter-Ziel ist noch nicht erreicht. Der Bericht trennt implementierte, freigegebene und tatsächlich bestätigte Anbieter.

Ungeklärte Ergebnisse sperren ausschließlich dieselbe Wohnung dauerhaft. Nach einem neuen ungeklärten Versuch pausiert der jeweilige Anbieter für den Rest des Laufs, andere Anbieter werden weiter geprüft. Es gibt niemals einen automatischen erneuten Versand für reservierte Wohnungen.

HOWOGE: Es werden ausschließlich die beobachteten Hinweise zur Kenntnis genommen. Keine Angabe zu Einkommenshöhe, ausreichender Bonität, Bürgschaft oder Jobcenter-Zustimmung wird ergänzt. Geänderte Hinweise und zusätzliche Felder stoppen den Adapter.

WBM: Die gesonderte Zustimmung wird nicht vorausgesetzt. Erst nach ausdrücklicher Freigabe das Actions-Secret APPLICANT_WBM_DATA_CONSENT auf 1 setzen. Der exakte Zustimmungstext ist in standard_form_adapters.py hinterlegt und wird vor Eingabe persönlicher Daten geprüft. Eine abweichende Erklärung erfordert neue Prüfung.

Gewobag: Eine Pflichtfrage zum Vorhandensein der §9-Bescheinigung ist keine Aufforderung, Ja anzugeben. Bei fehlender Bescheinigung wird die angebotene Option Nein gewählt. Ein im Angebot ausdrücklich genannter §9-Bedarf blockiert weiterhin die Eignung. Fehlende Immatrikulation wird nicht als vorhandener Status ausgegeben.

Keine CAPTCHA-Lösung, keine direkten Absende-Endpunkte, keine Zugangsdaten in Dateien/Logs. Alle Sender verwenden das gemeinsame dauerhafte Reservierungs- und Bestätigungsverfahren. Eine Reservierung oder ein grüner Actions-Lauf gilt nicht als Versandbestätigung.
