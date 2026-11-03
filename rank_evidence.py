"""Rank housing offers from explicit evidence snippets, not generic keyword hits.

Read-only. A candidate is never marked eligible to apply without verifying
WBS type, offer status, and landlord conditions.
"""
import json
import re
from decimal import Decimal
from pathlib import Path

TARGET_DISTRICTS = {"Pankow", "Reinickendorf", "Mitte", "Wedding"}
RENT_LIMIT = Decimal("550.00")

def extract(item):
    evidence = item.get("evidence") or {}
    rent_text = " ".join(evidence.get("rent_mentions", []))
    district_text = " ".join(evidence.get("district_mentions", []))
    room_text = " ".join(evidence.get("room_mentions", []) + evidence.get("district_mentions", []))
    wbs_text = " ".join(evidence.get("wbs_mentions", []))
    rent_match = re.search(r"Gesamtmiete\s+([\d.]+,\d{2})\s*(?:Euro|€)", rent_text, re.I)
    district_match = re.search(r"Bezirk/Ortsteil\s+(Pankow|Reinickendorf|Mitte|Wedding)\s*/", district_text, re.I)
    room_match = re.search(r"Anzahl Zimmer\s+(\d+(?:[,.]\d+)?)", room_text, re.I)
    if not room_match:
        room_match = re.search(r"\b(\d+(?:[,.]\d+)?)\s*Zimmer(?:wohnung|\b)", room_text, re.I)
    rent = Decimal(rent_match.group(1).replace(".", "").replace(",", ".")) if rent_match else None
    rooms = Decimal(room_match.group(1).replace(",", ".")) if room_match else None
    district = district_match.group(1).capitalize() if district_match else None
    wbs_mentioned = bool(re.search(r"Für die Anmietung.{0,90}\bWBS\b", wbs_text, re.I))
    special_wbs = bool(re.search(r"WBS für drei Räumen|Wohnberechtigungsschein für Rollstuhlfahrer", wbs_text, re.I))
    matches_basic = rent is not None and rooms is not None and district is not None and rent <= RENT_LIMIT and rooms == 1 and district in TARGET_DISTRICTS
    return {
        "url": item.get("url"),
        "total_rent_eur": str(rent) if rent is not None else None,
        "rooms": str(rooms) if rooms is not None else None,
        "district": district,
        "wbs_mentioned_in_offer": wbs_mentioned,
        "special_wbs_condition_detected": special_wbs,
        "basic_criteria_match": matches_basic,
        "wbs_100_verified": False,
        "application_open_verified": False,
        "application_submitted": False,
        "decision": "review_now" if matches_basic and not special_wbs else "not_confirmed",
    }

def main():
    evidence = json.loads(Path("inberlinwohnen_offer_evidence.json").read_text(encoding="utf-8"))
    offers = [extract(x) for x in evidence]
    offers.sort(key=lambda x: (x["decision"] != "review_now", Decimal(x["total_rent_eur"]) if x["total_rent_eur"] else Decimal("999999")))
    report = {"basic_matches": sum(x["basic_criteria_match"] for x in offers),
              "fully_verified_matches": 0, "applications_submitted": 0, "offers": offers}
    Path("inberlinwohnen_ranked.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"basic_matches": report["basic_matches"], "fully_verified_matches": 0,
                      "review_now": [x["url"] for x in offers if x["decision"] == "review_now"]}, ensure_ascii=False))
if __name__ == "__main__":
    main()
