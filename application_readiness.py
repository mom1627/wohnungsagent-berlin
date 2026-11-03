"""Fail-closed offer readiness checks before any application attempt.

Only publicly verified evidence can allow a live application. The function
does not claim WBS eligibility from a generic WBS mention.
"""
import re
from urllib.parse import urlsplit

SUPPORTED = {"www.gewobag.de"}
BLOCKED = re.compile(r"rollstuhl|barrierefrei nur|senioren|ab 60|wbs\s*(?:140|160|180|220)|wbs\s*für\s*(?:2|3|4)|dringlichkeit|sonderbedarf", re.I)

def evaluate(match, evidence, application_frame_present=False):
    url=match.get("url") or ""
    if urlsplit(url).scheme!="https" or urlsplit(url).hostname not in SUPPORTED:
        return False,"provider_not_supported"
    if not match.get("basic_criteria_match"):
        return False,"basic_criteria_unverified"
    if match.get("special_wbs_condition_detected"):
        return False,"special_wbs_condition"
    if evidence.get("status")!="readable_unverified" or evidence.get("http_status")!=200:
        return False,"offer_not_readable"
    mentions=evidence.get("evidence") or {}
    wbs=" ".join(mentions.get("wbs_mentions",[]))
    if BLOCKED.search(wbs):
        return False,"potentially_incompatible_eligibility"
    if match.get("wbs_mentioned_in_offer"):
        # WBS 100 alone does not prove eligibility for a particular listing.
        return False,"wbs_category_not_verified"
    if not application_frame_present:
        return False,"application_form_not_verified"
    return True,"ready"
