"""Discover every public results page, recheck matches and report exact blockers."""
import asyncio
import gewobag_adapter
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from collect_all_pages import collect_async
from eligibility import screen
from application_ledger import Ledger
from housing_profile import today
from application_profile import load_profile
from housing_profile import load_housing_profile
from gewobag_adapter import VERSION, offer_blockers, prepare, submit_prepared
from provider_adapters import inspect_provider
from candidate_watchlist import load_watchlist, merge_candidates, save_watchlist
from standard_form_adapters import (SENDER_VERSIONS, IMPLEMENTED_SENDERS,
    provider_statuses, prepare_native, submit_native, attempt_blocker, howoge_income_blocker)

async def run():
    report = {"checked_at_utc":datetime.now(timezone.utc).isoformat(),
              "submission_requested":os.getenv("ENABLE_LIVE_APPLICATIONS")=="1",
              "submission_enabled":False,"validated_senders":[],
              "daily_confirmed_application_goal":4,"confirmed_today":0,"daily_goal_met":False,
              "discovered":0,"basic_matches":0,"applications_submitted":0,
              "applications":[],"offers":[],"errors":[]}
    try:
        discovery = await collect_async(max_pages=200)
        report["discovery"] = {k:v for k,v in discovery.items() if k!="listings"}
        report["discovered"] = discovery["count"]
        report["providers"] = dict(Counter(x["provider"] for x in discovery["listings"]))
        print("Discovery result:",discovery["count"],discovery["pages_checked"],discovery["stop_reason"],flush=True)
        candidates = []
        all_listings=merge_candidates(discovery["listings"],load_watchlist())
        report["watchlist_candidates"] = sum(x.get("candidate_origin")=="watchlist" for x in all_listings)
        for item in all_listings:
            decision = screen(item["source_text"])
            decision.update({k:item[k] for k in ("url","provider","source_page")})
            decision["title"] = item["source_text"].split("Alle Details",1)[0].strip()
            decision["candidate_origin"] = item.get("candidate_origin","current_discovery")
            address = re.search(r"Adresse:\s*(.*?)\s*Zimmeranzahl:",item["source_text"])
            decision["address"] = address.group(1) if address else None
            report["offers"].append(decision)
            if decision["basic_criteria_match"]:
                candidates.append(item)
        report["basic_matches"] = len(candidates)
        profile = load_profile()
        housing = load_housing_profile()
        report["profile_ready"] = profile["ready"]  # Boolean only; never profile data.
        report["housing_profile_ready"] = housing["ready"]
        ledger = Ledger()
        if ledger.remote and ledger.sha is None:
            ledger.save()
            ledger.read()
        report["durable_ledger_ready"] = ledger.remote
        try:
            save_watchlist(candidates,ledger)
        except Exception:
            report["watchlist_error"] = "public_candidate_cache_write_failed"
        live_ready = report["submission_requested"] and profile["ready"] and housing["ready"] and ledger.remote
        report["provider_status"] = provider_statuses(ledger,live_ready)
        report["validated_senders"] = [p for p,v in SENDER_VERSIONS.items() if ledger.validated(v)]
        report["submission_enabled"] = any(x["automatic_attempts_enabled"] for x in report["provider_status"].values())
        report["minimum_required_providers"] = 4
        report["minimum_provider_goal_met"] = len(report["validated_senders"]) >= 4
        # Unknown outcomes remain reserved for that apartment. They do not
        # permanently disable requests for other properties. Stop that provider
        # for the rest of this run after one new uncertain result.
        uncertain_this_run = set()
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
                    frame = current.pop("_frame",None)
                    source = screen(item["source_text"])
                    source_record = next(x for x in report["offers"] if x["url"]==item["url"])
                    detail = screen(current.pop("text",""),provider_verified=current["detail_verified"])
                    # Source and current provider must agree; never fall back to stale source values.
                    mismatch = source["district"] != detail["district"] or any(
                        source[k] is None or detail[k] is None or Decimal(source[k]) != Decimal(detail[k])
                        for k in ("total_rent_eur","rooms"))
                    reasons = offer_blockers(detail,housing)+[r for r in source["reasons"] if r in {
                        "age_restriction_requires_review","student_status_requires_review",
                        "shared_accommodation_requires_review","special_eligibility_requires_review",
                        "excludes_wbs_entitlement","cooperative_cost_requires_review"}]
                    if mismatch: reasons.append("source_provider_disagree")
                    if item["provider"]=="howoge":
                        # HOWOGE distinguishes the initial viewing inquiry (name,
                        # contact, WBS) from the later contract/document check.
                        # Official: /immobiliensuche/mietbedingungen.html
                        # Never attest income sufficiency or Jobcenter approval.
                        detail["contract_follow_up"] = howoge_income_blocker(detail)
                        detail["contract_requirements_verified"] = False
                    # A pagination failure is reported as a search error. It
                    # does not invalidate an independently rechecked apartment.
                    if not profile["ready"]: reasons.append("missing_profile_secrets")
                    detail["profile_eligibility_passed"] = not reasons
                    outcome = {"url":item["url"],"status":"not_submitted","confirmed":False}
                    if frame is None:
                        reasons.append(current["reason"])
                    elif not reasons:
                        if not report["submission_requested"]:
                            reasons.append("live_submission_disabled")
                        elif not ledger.remote:
                            reasons.append("durable_remote_ledger_required")
                        elif attempt_blocker(item["provider"],item["url"],ledger,uncertain_this_run):
                            reasons.append(attempt_blocker(item["provider"],item["url"],ledger,uncertain_this_run))
                        else:
                            try:
                                if item["provider"] == "gewobag":
                                    ready,why = await prepare(page,frame,profile,housing)
                                else:
                                    ready,why = await prepare_native(item["provider"],page,profile,housing)
                                if not ready:
                                    reasons.append(why)
                                else:
                                    # This first real, authorized matching inquiry validates
                                    # the adapter; later runs reuse its durable success proof.
                                    if item["provider"] == "gewobag":
                                        outcome = await submit_prepared(page,frame,item["url"],ledger,enabled=True)
                                    else:
                                        outcome = await submit_native(item["provider"],page,item["url"],ledger)
                                    if outcome["status"] == "submission_unverified":
                                        uncertain_this_run.add(item["provider"])
                                    if not outcome["confirmed"]: reasons.append(outcome["reason"])
                            except Exception as exc:
                                reasons.append("form_processing_error_"+type(exc).__name__+"_"+gewobag_adapter.LAST_STAGE)
                    if outcome["confirmed"]:
                        report["applications_submitted"] += 1
                    report["applications"].append({
                        "url":item["url"],"provider":item["provider"],"status":"not_submitted",
                        **outcome,
                        "reason":outcome.get("reason") or (reasons[0] if reasons else current["reason"]),"blockers":sorted(set(reasons)),
                        "title":source_record["title"],"address":source_record["address"],
                        "candidate_origin":source_record["candidate_origin"],
                        "source_warm_rent_eur":source["total_rent_eur"],
                        "current_offer":detail,"form_present":current["form_present"],
                        "required_fields":[{"id":f["id"],"label":f["label"],"type":f["type"]}
                                           for f in current.get("fields",[]) if f["required"]]})
                    report["validated_senders"] = [p for p,v in SENDER_VERSIONS.items() if ledger.validated(v)]
                    report["provider_status"] = provider_statuses(ledger,live_ready)
                    report["minimum_provider_goal_met"] = len(report["validated_senders"]) >= 4
            finally:
                await browser.close()
        report["confirmed_today"] = ledger.confirmed_on(today())
        report["daily_goal_met"] = report["confirmed_today"] >= report["daily_confirmed_application_goal"]
    except Exception as exc:
        report["errors"].append({"stage":"pipeline","error":type(exc).__name__})
    return report

def main():
    report = asyncio.run(run())
    Path("daily_housing_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines = ["# Wohnungsagent – Laufbericht","",
             f"Gefunden: {report['discovered']} · Basis-Treffer: {report['basic_matches']} · Bestätigt versendet: {report['applications_submitted']}",
             f"Automatische Anfrageversuche freigegeben: {report['submission_enabled']}",
             f"Heute bestätigt: {report['confirmed_today']} · Tagesziel: {report['daily_confirmed_application_goal']} · Erreicht: {report['daily_goal_met']}",
             f"Anbieter mit tatsächlicher Versandbestätigung: {', '.join(report['validated_senders']) or 'keiner'}",""]
    lines += ["| Anbieter | Versand implementiert | Tatsächlich bestätigt | Manuelle Voraussetzung |",
              "| --- | --- | --- | --- |"]
    for provider,status in report.get("provider_status",{}).items():
        lines.append(f"| {provider} | {status['sender_implemented']} | {status['submission_confirmed']} | {status['manual_requirement'] or '—'} |")
    lines.append("")
    discovery = report.get("discovery",{})
    lines += [f"Ergebnisseiten: {discovery.get('pages_checked',0)} · Vollständig durchlaufen: {discovery.get('complete',False)}",
              f"Zusätzliche Treffer aus Merkliste (Anbieter neu geprüft): {report.get('watchlist_candidates',0)}",
              f"Bewerber-Secrets verfügbar: {report.get('profile_ready',False)} · Dauerhafte Historie erreichbar: {report.get('durable_ledger_ready',False)}","",
              "| Angebot | Warmmiete laut Quelle | Ergebnis |", "| --- | ---: | --- |"]
    for item in report["applications"]:
        label = (item.get("address") or item.get("title") or item["url"]).replace("|","/")
        reasons = ", ".join(item.get("blockers",[item["reason"]]))
        lines.append("| ["+label+"]("+item["url"]+") | "+str(item.get("source_warm_rent_eur","—"))+" € | "+item["status"]+": "+reasons+" |")
    if report["errors"]: lines.append("\nPipeline-Fehler: "+str(len(report["errors"])))
    Path("daily_housing_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as f: f.write("\n".join(lines)+"\n")
    print(json.dumps({k:report[k] for k in ("discovered","basic_matches","applications_submitted","submission_enabled")}))
    return 1 if report["errors"] or not report.get("discovery",{}).get("complete") else 0

if __name__ == "__main__":
    sys.exit(main())

