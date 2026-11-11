"""Conservative review queue for housing offers.

Evidence snippets are NOT reliable structured rental fields. Never auto-approve
a candidate from mere keyword matches.
"""
import json
from pathlib import Path

from berlin_location import DISTRICTS

TARGET = {"max_warm_rent_eur": 550, "rooms": [1, 2], "wbs": "WBS 100",
          "districts": list(DISTRICTS)}

def review(items):
    output = []
    for item in items:
        evidence = item.get("evidence") or {}
        fields = {
            "warm_rent_eur": None, "rooms": None, "district": None,
            "wbs_100_eligible": None, "application_open": None,
        }
        missing = list(fields)
        output.append({
            "url": item.get("url"),
            "page_status": item.get("status"),
            "decision": "manual_verification_required",
            "confirmed_match": False,
            "fields": fields,
            "missing_verification": missing,
            "evidence_hints": {k: v[:3] for k, v in evidence.items() if v},
            "note": "Keyword snippets are not sufficient to verify listing eligibility.",
        })
    return output

def main():
    raw = json.loads(Path("inberlinwohnen_offer_evidence.json").read_text(encoding="utf-8"))
    results = review(raw)
    report = {"criteria": TARGET, "confirmed_matches": 0,
              "requires_verification": len(results), "offers": results}
    Path("inberlinwohnen_review_queue.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"total": len(results), "confirmed_matches": 0,
                      "manual_verification_required": len(results),
                      "output": "inberlinwohnen_review_queue.json"}, ensure_ascii=False))
if __name__ == "__main__":
    main()
