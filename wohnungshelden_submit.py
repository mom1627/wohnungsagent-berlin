"""Conservative Wohnungshelden browser adapter.

Only submits when exact required fields can be identified and all required
checkboxes are ordinary privacy consents. Never bypass CAPTCHA or login.
No personal data is logged. Requires explicit ENABLE_LIVE_APPLICATIONS=1.
"""
import asyncio
import json
import os
import re
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from application_profile import load_profile

async def apply_gewobag(url):
    result={"url":url,"status":"not_submitted","confirmed":False}
    if os.getenv("ENABLE_LIVE_APPLICATIONS")!="1":
        result["reason"]="live_submission_disabled"
        return result
    profile=load_profile()
    if not profile.get("ready"):
        result["reason"]="missing_profile_secrets"
        return result
    if urlparse(url).hostname!="www.gewobag.de":
        result["reason"]="unsupported_provider"
        return result
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        context=await browser.new_context(locale="de-DE")
        page=await context.new_page()
        try:
            await page.goto(url,wait_until="domcontentloaded",timeout=35000)
            await page.wait_for_timeout(2500)
            frames=[f for f in page.frames if urlparse(f.url).hostname=="app.wohnungshelden.de"]
            if len(frames)!=1:
                result["reason"]="application_frame_missing_or_ambiguous"
                return result
            frame=frames[0]
            fields=await frame.locator("input,textarea,select").evaluate_all("""els=>els.map(e=>({
              tag:e.tagName.toLowerCase(),type:(e.getAttribute('type')||'').toLowerCase(),
              name:(e.getAttribute('name')||'').toLowerCase(),
              id:(e.id||'').toLowerCase(),
              placeholder:(e.getAttribute('placeholder')||'').toLowerCase(),
              required:!!e.required,disabled:!!e.disabled
            }))""")
            # Fail closed on unknown required fields or challenges.
            if await frame.locator("iframe[src*='recaptcha'],iframe[src*='hcaptcha'],input[type=file]").count():
                result["reason"]="manual_verification_or_document_required"
                return result
            targets={}
            for index,field in enumerate(fields):
                if field["disabled"] or field["type"] in ("hidden","submit","button"):
                    continue
                label=" ".join([field["name"],field["id"],field["placeholder"]])
                if field["type"] in ("checkbox","radio"):
                    if field["required"]:
                        result["reason"]="required_checkbox_requires_manual_review"
                        return result
                    continue
                key=None
                if re.search(r"e.?mail",label):key="email"
                elif re.search(r"telefon|phone|mobil",label):key="phone"
                elif re.search(r"nachricht|message|mitteilung|bemerkung",label):key="note"
                elif re.search(r"vorname|first.?name",label):key="first"
                elif re.search(r"nachname|last.?name|familienname",label):key="last"
                elif re.search(r"(^|\\W)name($|\\W)",label):key="name"
                if field["required"] and not key:
                    result["reason"]="unknown_required_field"
                    return result
                if key and key in targets:
                    result["reason"]="ambiguous_field_mapping"
                    return result
                if key:targets[key]=index
            if "email" not in targets or not (("first" in targets and "last" in targets) or "name" in targets):
                result["reason"]="essential_fields_not_identified"
                return result
            nameparts=profile["name"].strip().split(None,1)
            values={"email":profile["email"],"phone":profile["phone"],"note":profile["note"],
                    "name":profile["name"],"first":nameparts[0],"last":nameparts[1] if len(nameparts)>1 else ""}
            if "last" in targets and not values["last"]:
                result["reason"]="missing_last_name"
                return result
            for key,index in targets.items():
                await frame.locator("input,textarea,select").nth(index).fill(values[key])
            # Never send without explicit, observable submit button and exact success proof.
            submit=frame.get_by_role("button",name=re.compile(r"^(anfrage senden|bewerbung absenden|bewerben)$",re.I))
            if await submit.count()!=1:
                result["reason"]="submit_button_not_unique"
                return result
            await submit.click(timeout=10000)
            await frame.wait_for_timeout(2500)
            success=frame.get_by_text(re.compile(r"anfrage (wurde|ist) (erfolgreich )?(versendet|eingegangen)|vielen dank für ihre anfrage|bewerbung erfolgreich",re.I))
            if await success.count():
                result["status"]="submitted_confirmed"
                result["confirmed"]=True
            else:
                result["status"]="submission_unverified"
                result["reason"]="no_success_confirmation"
        except Exception as exc:
            result["reason"]="browser_error_"+type(exc).__name__
        finally:
            await browser.close()
    return result
