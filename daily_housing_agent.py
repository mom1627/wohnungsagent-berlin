"""Discover every public results page, recheck matches and report exact blockers."""
import asyncio
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from collect_all_pages import collect_async
from eligibility import screen
from application_ledger import Ledger
from application_profile import load_profile
from provider_adapters import inspect_provider, VERIFIED_SENDERS

async def run():
    report = {"checked_at_utc":datetime.now(timezone.utc).isoformat(),
              "submission_requested":os.getenv("ENABLE_LIVE_APPLICATIONS")=="1",
              "submission_enabled":False,"validated_senders":sorted(VERIFIED_SENDERS),
              "discovered":0,"basic_matches":0,"applications_submitted":0,
              "applications":[],"offers":[],"errors":[]}
    try:
        discovery = await collect_async(max_pages=200)
        report["discovery"] = {k:v for k,v in discovery.items() if k!="listings"}
        report["discovered"] = discovery["count"]
        report["providers"] = dict(Counter(x["provider"] for x in discovery["listings"]))
        print("Discovery result:",discovery["count"],discovery["pages_checked"],discovery["stop_reason"],flush=True)
        candidates = []
        for item in discovery["listings"]:
            decision = screen(item["source_text"])
            decision.update({k:item[k] for k in ("url","provider","source_page")})
            report["offers"].append(decision)
            if decision["basic_criteria_match"]:
                candidates.append(item)
        report["basic_matches"] = len(candidates)
        profile = load_profile()
        report["profile_ready"] = profile["ready"]  # Boolean only; never profile data.
        ledger = Ledger()
        if ledger.remote and ledger.sha is None:
            ledger.save()
            ledger.read()
        report["durable_ledger_ready"] = ledger.remote
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(locale="de-DE")
            page = await context.new_page()
            robots = {}
            try:
                for item in candidates:
                    if ledger.contains(item["url"]):
                        report["applications"].append({"url":item["url"],"status":"skipped","reason":"already_reserved_or_submitted"})
                        continue
                    current = await inspect_provider(page,item["url"],robots)
                    source = screen(item["source_text"])
                    detail = screen(current.pop("text",""),provider_verified=current["detail_verified"])
                    # Source and current provider must agree; never fall back to stale source values.
                    mismatch = source["district"] != detail["district"] or any(
                        source[k] is None or detail[k] is None or Decimal(source[k]) != Decimal(detail[k])
                        for k in ("total_rent_eur","rooms"))
                    reasons = list(detail["reasons"])
                    if mismatch: reasons.append("source_provider_disagree")
                    if not discovery["complete"]: reasons.append("discovery_incomplete")
                    if not profile["ready"]: reasons.append("missing_profile_secrets")
                    reasons.append(current["reason"])
                    report["applications"].append({
                        "url":item["url"],"provider":item["provider"],"status":"not_submitted",
                        "reason":current["reason"],"blockers":sorted(set(reasons)),
                        "current_offer":detail,"form_present":current["form_present"],
                        "required_fields":[{"id":f["id"],"label":f["label"],"type":f["type"]}
                                           for f in current.get("fields",[]) if f["required"]]})
                    # No provider has a verified sender. Do not call an untested
                    # adapter merely because ENABLE_LIVE_APPLICATIONS was set.
            finally:
                await browser.close()
    except Exception as exc:
        report["errors"].append({"stage":"pipeline","error":type(exc).__name__})
    return report

def main():
    report = asyncio.run(run())
    Path("daily_housing_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines = ["# Wohnungsagent – Laufbericht","",
             f"Gefunden: {report['discovered']} · Basis-Treffer: {report['basic_matches']} · Bestätigt versendet: {report['applications_submitted']}",
             f"Automatischer Versand aktiv: {report['submission_enabled']}",""]
    for item in report["applications"]:
        lines.append("- "+item["url"]+" — "+item["status"]+": "+item["reason"])
    if report["errors"]: lines.append("\nPipeline-Fehler: "+str(len(report["errors"])))
    Path("daily_housing_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as f: f.write("\n".join(lines)+"\n")
    print(json.dumps({k:report[k] for k in ("discovered","basic_matches","applications_submitted","submission_enabled")}))
    return 1 if report["errors"] or not report.get("discovery",{}).get("complete") else 0

if __name__ == "__main__":
    sys.exit(main())

