"""Strict, explainable screening using explicit property labels, never navigation."""
import re
from decimal import Decimal, InvalidOperation

TARGETS = {"reinickendorf","wedding","mitte","pankow"}
SPECIAL = re.compile(r"besonder\w*\s+wohnbedarf|dringlichkeit|rollstuhlfahrer|nur.{0,25}senior|mindestens\s*(?:60|65)|wbs\s*(?:für|mit)\s*(?:2|3|4|zwei|drei|vier)\s*(?:räum|zimmer)|§\s*9",re.I)

def money(value):
    try:
        return Decimal(value.replace(".","").replace(",","."))
    except InvalidOperation:
        return None

def screen(text, *, provider_verified=False):
    text = " ".join(text.split())
    amount = re.search(r"(?:Bruttowarmmiete|Warmmiete|Gesamtmiete)\s*:?\s*([\d.]+,\d{2})\s*(?:€|Euro)",text,re.I)
    rooms = re.search(r"(?:Zimmeranzahl|Anzahl Zimmer|Zimmer)\s*:?\s*(\d+(?:[,.]\d+)?)(?![\d.,])",text,re.I)
    district = re.search(r"Bezirk/Ortsteil\s*:?\s*(Reinickendorf|Wedding|Mitte|Pankow)\s*(?:/|$)",text,re.I)
    if not district:
        district = re.search(r"(?:Adresse|Anschrift)\s*:?\s*[^:]{0,170}\b\d{5}\s*,?\s*(?:Berlin\s*,?\s*)?(Reinickendorf|Wedding|Mitte|Pankow)\b",text,re.I)
    rent = money(amount.group(1)) if amount else None
    count = Decimal(rooms.group(1).replace(",",".")) if rooms else None
    area = district.group(1).lower() if district else None
    reasons = []
    if rent is None: reasons.append("warm_rent_unverified")
    elif rent > 550: reasons.append("warm_rent_above_550")
    if count is None: reasons.append("rooms_unverified")
    elif count != 1: reasons.append("not_one_room")
    if area not in TARGETS: reasons.append("target_district_unverified")
    basics = not reasons
    # WBS references in the actual property content only.
    no_wbs = bool(re.search(r"(?:WBS|Wohnberechtigungsschein)\s*:?\s*(?:nicht erforderlich|nein|nicht notwendig)|(?:kein|ohne)\s+(?:WBS|Wohnberechtigungsschein)",text,re.I))
    categories = set(re.findall(r"\bWBS\s*[-:]?\s*(100|140|160|180|220)\b",text,re.I))
    generic = bool(re.search(r"\bWBS\b|Wohnberechtigungsschein",text,re.I))
    wbs = "not_required" if no_wbs and not categories else "100" if categories == {"100"} else "unknown" if generic else "not_stated"
    if wbs not in {"not_required","100"}: reasons.append("wbs_category_unverified")
    if SPECIAL.search(text): reasons.append("special_eligibility_requires_review")
    if re.search(r"Genossenschaftsanteil|Mitgliedsbeitrag|Pflichtanteil|Eintrittsgeld",text,re.I):
        reasons.append("cooperative_cost_requires_review")
    if re.search(r"nicht mehr verfügbar|bereits vermietet|Angebot.{0,20}beendet|keine.{0,15}Anfragen",text,re.I):
        reasons.append("offer_closed")
    availability = re.search(r"(?:Frei ab|Bezugsfrei(?: ab)?|Bezugsfertig ab|Verfügbar ab)\s*:?\s*(ab sofort|sofort|nach Vereinbarung|\d{2}\.\d{2}\.\d{4})",text,re.I)
    if not availability: reasons.append("availability_unverified")
    if not provider_verified: reasons.append("provider_details_not_rechecked")
    return {"basic_criteria_match":basics,"total_rent_eur":str(rent) if rent is not None else None,
            "rooms":str(count) if count is not None else None,"district":area,"wbs":wbs,
            "available_from":availability.group(1) if availability else None,
            "eligible":not reasons,"reasons":reasons,
            "jobcenter_approval":"not_asserted; separate rental-cost approval may be necessary"}
