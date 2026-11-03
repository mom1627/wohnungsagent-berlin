"""One daily orchestration entry point: discover, inspect, screen, queue.

Submission is fail-closed until provider-specific form automation is verified.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from collect_inberlinwohnen import collect
from inspect_offer_details import inspect_url
from rank_evidence import extract

def main():
    result={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
            "source":"https://www.inberlinwohnen.de/wohnungsfinder",
            "discovered":0,"inspected":0,"basic_matches":0,
            "applications_submitted":0,"submission_enabled":False,"matches":[],"errors":[]}
    try:
        listing_data=collect()
        listings=listing_data["listings"]
        result["discovered"]=len(listings)
        robots_cache={}
        for item in listings:
            try:
                # Only run verified, supported inspection functions; never guess eligibility.
                evidence=inspect_url(item["url"], robots_cache)
                result["inspected"]+=1
                rank=extract(evidence)
                if rank["basic_criteria_match"] and not rank["special_wbs_condition_detected"]:
                    result["matches"].append(rank)
            except Exception as exc:
                result["errors"].append({"url":item["url"],"error":type(exc).__name__})
        result["basic_matches"]=len(result["matches"])
    except Exception as exc:
        result["errors"].append({"stage":"discovery","error":type(exc).__name__})
    Path("daily_housing_report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("matches","errors")},ensure_ascii=False))
    if result["errors"]:
        print("Non-sensitive error count:",len(result["errors"]))
    print("No applications sent: provider submission adapters not yet verified.")
    return 1 if result["discovered"]==0 and result["errors"] else 0

if __name__=="__main__":
    sys.exit(main())
