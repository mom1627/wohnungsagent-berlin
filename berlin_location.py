"""Recognize Berlin from an explicit property location."""
import re

# Official district names and their constituent localities.
# https://denkmaldatenbank.berlin.de/liste_ortsteil.php
DISTRICTS = {
    "Mitte": "Mitte|Moabit|Hansaviertel|Tiergarten|Wedding|Gesundbrunnen",
    "Friedrichshain-Kreuzberg": "Friedrichshain|Kreuzberg",
    "Pankow": "Pankow|Prenzlauer Berg|Weißensee|Blankenburg|Heinersdorf|Karow|Stadtrandsiedlung Malchow|Buch|Französisch Buchholz|Niederschönhausen|Rosenthal|Wilhelmsruh|Blankenfelde",
    "Charlottenburg-Wilmersdorf": "Charlottenburg|Wilmersdorf|Schmargendorf|Grunewald|Westend|Charlottenburg-Nord|Halensee",
    "Spandau": "Spandau|Haselhorst|Siemensstadt|Staaken|Gatow|Kladow|Hakenfelde|Falkenhagener Feld|Wilhelmstadt",
    "Steglitz-Zehlendorf": "Steglitz|Lichterfelde|Lankwitz|Zehlendorf|Dahlem|Nikolassee|Wannsee|Schlachtensee",
    "Tempelhof-Schöneberg": "Tempelhof|Schöneberg|Friedenau|Mariendorf|Marienfelde|Lichtenrade",
    "Neukölln": "Neukölln|Britz|Buckow|Rudow|Gropiusstadt",
    "Treptow-Köpenick": "Alt-Treptow|Treptow|Plänterwald|Baumschulenweg|Johannisthal|Niederschöneweide|Altglienicke|Adlershof|Bohnsdorf|Oberschöneweide|Köpenick|Friedrichshagen|Rahnsdorf|Grünau|Müggelheim|Schmöckwitz",
    "Marzahn-Hellersdorf": "Marzahn|Biesdorf|Kaulsdorf|Mahlsdorf|Hellersdorf",
    "Lichtenberg": "Lichtenberg|Friedrichsfelde|Karlshorst|Rummelsburg|Fennpfuhl|Alt-Hohenschönhausen|Neu-Hohenschönhausen|Hohenschönhausen|Malchow|Wartenberg|Falkenberg",
    "Reinickendorf": "Reinickendorf|Tegel|Konradshöhe|Heiligensee|Frohnau|Hermsdorf|Waidmannslust|Lübars|Wittenau|Märkisches Viertel|Borsigwalde",
}
LOCALITIES = {name.casefold(): district.casefold()
              for district, areas in DISTRICTS.items() for name in [district, *areas.split("|")]}
LOCALITY_PATTERN = "|".join(map(re.escape, sorted(LOCALITIES, key=len, reverse=True)))
LABELLED = re.compile(r"(?:Bezirk(?:\s*/\s*Ortsteil)?|Ortsteil)\s*:?\s*(" + LOCALITY_PATTERN + r")(?=\s*/|\s*$|\s*(?:Adresse|Zimmer))", re.I)
POSTCODE = re.compile(r"\b(1\d{4})\s*,?\s*(?:Berlin\b[ ,–-]*)?(" + LOCALITY_PATTERN + r")(?![\w-])", re.I)
BERLIN_ADDRESS = re.compile(r"\b(1\d{4})\s*,?\s*Berlin\b", re.I)


def berlin_postcode(code):
    return 10115 <= int(code) <= 14199 and code != "12529"


def district_name(value):
    return LOCALITIES.get(re.sub(r"^berlin[\s-]+", "", value.strip(), flags=re.I).casefold())


def property_location(text):
    text = text.casefold()
    labelled = LABELLED.search(text)
    postcode = POSTCODE.search(text)
    berlin = BERLIN_ADDRESS.search(text)
    if berlin and not berlin_postcode(berlin[1]) or postcode and not berlin_postcode(postcode[1]):
        return None
    if labelled:
        return district_name(labelled[1])
    if postcode:
        return district_name(postcode[2])
    if berlin:
        return "berlin"
    return None
