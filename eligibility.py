"""Strict, explainable screening using explicit property labels, never navigation."""
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from housing_profile import today

from berlin_location import property_location

SPECIAL = re.compile(r"besonder\w*\s+wohnbedarf|dringlichkeit|rollstuhlfahrer|nur.{0,25}senior|mindestens\s*(?:60|65)|wbs\s*(?:für|mit)\s*(?:2|3|4|zwei|drei|vier)\s*(?:räum|zimmer)|§\s*9",re.I)

def money(value):
    try:
        return Decimal(value.replace(".","").replace(",","."))
    except InvalidOperation:
        return None

def screen(text, *, provider_verified=False):
    text = " ".join(text.split())
    amount = re.search(r"\b(?:Bruttowarmmiete|Warmmiete|Gesamtmiete)\s*:?\s*([\d.]+(?:,\d{1,2})?)\s*(?:€|Euro|EUR)",text,re.I)
    # Prefer explicit labels; '1 Zimmer 34,08 m²' must never become 34 rooms.
    rooms = None
    for pattern in (r"(?:Zimmeranzahl|Anzahl (?:der )?Zimmer)\s*:?\s*(\d+(?:[,.]\d+)?)(?![\d.,])",
                    r"\bZimmer\s*:?\s*(\d{1,2}(?:[,.]\d+)?)(?![\d.,])",
                    r"\b(\d+(?:[,.]\d+)?)\s*-?\s*Zimmer(?:wohnung|\b)"):
        rooms = re.search(pattern,text,re.I)
        if rooms: break
    rent = money(amount.group(1)) if amount else None
    if rent is None:
        reversed_amount = re.search(r"([\d.]+,\d{2})\s*(?:€|Euro|EUR)\s*Warmmiete\b",text,re.I)
        if reversed_amount:
            rent = money(reversed_amount[1])
    if rent is None:
        # GESOBAU: accept 'Miete inkl. NK' only when all three explicit cost
        # components, including heating, add up to that exact total.
        total = re.search(r"Miete inkl\.\s*NK\s*:\s*([\d.]+,\d{2})\s*€",text,re.I)
        parts = [re.search(label+r"\s*:\s*([\d.]+,\d{2})\s*€",text,re.I)
                 for label in ("Kaltmiete","Betriebskosten","Heizkosten")]
        if total and all(parts):
            values = [money(x.group(1)) for x in parts]
            if all(x is not None for x in values) and sum(values) == money(total.group(1)):
                rent = money(total.group(1))
    count = Decimal(rooms.group(1).replace(",",".")) if rooms else None
    area_match = re.search(r"(?:Wohnfläche(?:\s*/\s*Nutzfläche)?|Fläche in m[²2]|Größe)\s*:?\s*(?:ca\.\s*)?(\d+(?:[,.]\d+)?)\s*(?:m²|Quadratmeter)",text,re.I)
    square_metres = Decimal(area_match.group(1).replace(',','.')) if area_match else None
    area = property_location(text)
    reasons = []
    if rent is None: reasons.append("warm_rent_unverified")
    elif rent <= 0: reasons.append("warm_rent_unverified")
    elif rent > 550: reasons.append("warm_rent_above_550")
    if count is None: reasons.append("rooms_unverified")
    elif count not in {Decimal(1),Decimal(2)}: reasons.append("rooms_not_one_or_two")
    if area is None: reasons.append("target_district_unverified")
    basics = not reasons
    # WBS references in the actual property content only.
    no_wbs = bool(re.search(r"(?:WBS|Wohnberechtigungsschein)\s*:?\s*(?:nicht erforderlich|nein|nicht notwendig)|WBS erforderlich\s*:\s*Nein|(?:kein|ohne)\s+(?:WBS|Wohnberechtigungsschein)",text,re.I))
    categories = set(re.findall(r"\bWBS(?:[- ]Berechtigung)?\s*[-:]?\s*(100|140|160|180|220)\b",text,re.I))
    generic = bool(re.search(r"\bWBS\b|Wohnberechtigungsschein",text,re.I))
    required_wbs = not no_wbs and bool(re.search(r"\bWBS\s*:\s*erforderlich|(?:vorhandener|vorhandenen)\s+WBS\s+Voraussetzung|\bmit\s+WBS\b|WBS\s+(?:ist\s+)?(?:Voraussetzung|erforderlich)",text,re.I))
    wbs = next(iter(categories)) if len(categories)==1 else "unknown" if categories else "required_unspecified" if required_wbs else "not_required" if no_wbs else "unknown" if generic else "not_stated"
    if wbs not in {"not_required","100"}: reasons.append("wbs_category_unverified")
    if SPECIAL.search(text): reasons.append("special_eligibility_requires_review")
    if re.search(r"Senioren(?:residenz|wohnung|wohnhaus)|Seniorengerecht\s*:?\s*Ja|Wohnen.{0,25}(?:für Senioren|\d{2}\s*(?:plus|\+))|(?:Menschen|Personen)\s+ab\s+\d{2}|ab\s*\d{2}\b\s*(?:Jahr|\+)",text,re.I):
        reasons.append("age_restriction_requires_review")
    if re.search(r"Studentenapartment|Wohnplatz für Studis|(?:nur|für|ausschließlich).{0,25}(?:Studierende|Auszubildende)|Immatrikulations",text,re.I):
        reasons.append("student_status_requires_review")
    if re.search(r"\bWG\b|\d+er-WG|Wohngemeinschaft",text,re.I):
        reasons.append("shared_accommodation_requires_review")
    if re.search(r"ohne\s+WBS[- ]Anspruch|kein(?:en)?\s+WBS[- ]Anspruch",text,re.I):
        reasons.append("excludes_wbs_entitlement")
    if re.search(r"Genossenschaftsanteil|Mitgliedsbeitrag|Pflichtanteil|Eintrittsgeld",text,re.I):
        reasons.append("cooperative_cost_requires_review")
    if re.search(r"nicht mehr verfügbar|bereits vermietet|Angebot.{0,20}beendet|keine.{0,15}Anfragen",text,re.I):
        reasons.append("offer_closed")
    availability = re.search(r"(?:Frei ab|Bezugsfrei(?: ab)?|Bezugsfertig ab|Verfügbar ab|Verfügbarkeit|Bezugsdatum|Bezug|Einzug)\s*:?\s*(ab sofort|sofort|nächstmöglich|nach Vereinbarung|\d{2}\.\d{2}\.\d{4})",text,re.I)
    if not availability: reasons.append("availability_unverified")
    deadline = re.search(r"(?:Bewerbungsfrist(?: bis)?|Bewerbungen bis)\s*:?\s*(\d{2})\.(\d{2})\.(\d{4})",text,re.I)
    if deadline:
        try:
            day, month, year = map(int, deadline.groups())
            if date(year, month, day) < today():
                reasons.append("offer_closed")
        except ValueError:
            reasons.append("application_deadline_unverified")
    if re.search(r"Renovierungsarbeiten.{0,150}erforderlich|Arbeiten selbst auszuführen|Mieter werben Mieter|nur für Bestandsmieter",text,re.I):
        reasons.append("special_eligibility_requires_review")
    if re.search(r"(?:mindestens|nur für)\s*(?:zwei|drei|vier|[2-9])\s*Personen|(?:Haushalt(?:sgröße)?|Personenzahl)\s*:?\s*(?:mind\.\s*)?(?:zwei|drei|vier|[2-9])\b",text,re.I):
        reasons.append("household_size_restriction")
    if re.search(r"Heizkosten.{0,40}(?:nicht enthalten|separat)|(?:ohne|zuzüglich)\s+(?:der\s+)?Heizkosten",text,re.I):
        reasons.append("heating_not_included")
    if not provider_verified: reasons.append("provider_details_not_rechecked")
    year = re.search(r"\bBaujahr\s*:?\s*((?:18|19|20)\d{2})\b",text,re.I)
    # Preserve any explicit restriction that is narrower than an ordinary
    # income ceiling; do not reinterpret one as a general maximum.
    restricted_wbs = bool(re.search(r"(?:nur|ausschließlich)\s+(?:mit\s+)?(?:gültige\w*\s+)?WBS\s*140|(?:Einkommen|WBS).{0,12}(?:über|mindestens|ab)\s*1(?:00|40)|Erstbezug|Neubau|Fördermodell|Förderweg",text,re.I))
    return {"basic_criteria_match":basics,"total_rent_eur":str(rent) if rent is not None else None,
            "rooms":str(count) if count is not None else None,"district":area,"wbs":wbs,
            "area_sqm":str(square_metres) if square_metres is not None else None,
            "available_from":availability.group(1) if availability else None,
            "building_year":int(year.group(1)) if year else None,
            "specific_wbs_binding_requires_review":restricted_wbs,
            "eligible":not reasons,"reasons":reasons,
            "jobcenter_approval":"not_asserted; separate rental-cost approval may be necessary"}
