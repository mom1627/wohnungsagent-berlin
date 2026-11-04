"""Public provider inspection. Sending remains gated by real adapter validation.

No CAPTCHA solving, unknown consents, account creation, field guesses or PII
logging. Probes never fill applicant fields or click a submission button.
"""
import re
from gewobag_adapter import visible_challenge
from urllib.parse import urlsplit
from provider_registry import provider_for, canonical_offer
from public_access import check_robots
from standard_form_adapters import open_howoge_form

CHALLENGE = "iframe[src*='recaptcha'],iframe[src*='hcaptcha'],[class*='g-recaptcha'],[class*='h-captcha'],textarea[id^='g-recaptcha-response'],script[src*='recaptcha'],[name='cf-turnstile-response']"
FIELD_JS = """els=>els.filter(e=>e.getClientRects().length).map(e=>({
 tag:e.tagName.toLowerCase(),type:e.type||'',id:e.id||'',name:e.name||'',
 label:[...(e.labels||[])].map(x=>x.innerText).join(' ').replace(/\\s+/g,' ').trim(),
 required:!!e.required||e.getAttribute('aria-required')==='true'||[...(e.labels||[])].some(x=>x.classList.contains('ant-form-item-required')||getComputedStyle(x,'::after').content.includes('*'))||!!e.closest('formly-field')?.querySelector('label.ant-form-item-required')
}))"""
# No production adapter has a confirmed end-to-end submission as of this revision.
# Adding a host here requires an actual matching property submission and visible
# confirmation, with its validation recorded in ADAPTER_STATUS.md.
VERIFIED_SENDERS = frozenset()

async def inspect_provider(page, url, robots_cache):
    provider = provider_for(url)
    result = {"url":url,"provider":provider,"detail_verified":False,"form_present":False,
              "can_submit":False,"reason":"provider_adapter_not_validated"}
    if not provider:
        result["reason"] = "unapproved_provider"
        return result
    try:
        check_robots(url,robots_cache)
        wbm_district = None
        if provider == "wbm":
            # WBM labels the district on the corresponding list-card image,
            # while its detail address contains only the Berlin postcode.
            listing_url = "https://www.wbm.de/wohnungen-berlin/angebote/"
            check_robots(listing_url,robots_cache)
            listing_response = await page.goto(listing_url,wait_until="domcontentloaded",timeout=35000)
            if listing_response and listing_response.status==200:
                cards = await page.locator("a.immo-button-cta").evaluate_all("""es=>es.map(e=>({
                    url:e.href,district:e.closest('.immo-col')?.previousElementSibling?.querySelector('.area')?.innerText?.trim()
                }))""")
                matches = [c for c in cards if canonical_offer(c["url"])==canonical_offer(url)]
                if len(matches)==1 and matches[0].get("district") in {"Mitte","Wedding","Reinickendorf","Pankow"}:
                    wbm_district = matches[0]["district"]
        response = await page.goto(url,wait_until="domcontentloaded",timeout=40000)
        if not response or response.status != 200:
            result["reason"] = "provider_http_error"
            return result
        if provider_for(page.url) != provider:
            result["reason"] = "unexpected_provider_redirect"
            return result
        main = page.locator("main,#content,.site-content").first
        if not await main.count(): main = page.locator("body")
        # Visible detail text, not script/style strings or JSON-LD navigation.
        text = await main.inner_text()
        if wbm_district:
            text += "\nBezirk/Ortsteil: "+wbm_district+" / Anbieter-Angebotskarte"
            result["provider_district_evidence"] = "matching_wbm_list_card"
        result["text"] = text
        result["detail_verified"] = True
        if re.search(r"verify you are human|checking your browser|automated traffic",text,re.I):
            result["reason"] = "manual_security_check"
            return result
        if provider == "gewobag":
            # Dismiss only the ordinary cookie choice, then reveal the request tab.
            save = page.get_by_role("button",name="Speichern wie ausgewählt",exact=True)
            if await save.count() and await save.is_visible():
                await save.click()
            request = page.get_by_role("button",name="Anfrage senden",exact=True).first
            if await request.count():
                await request.click()
            iframe = page.locator("iframe[src*='app.wohnungshelden.de/public/listings/']")
            if await iframe.count() != 1:
                result["reason"] = "application_frame_missing_or_ambiguous"
                return result
            src = await iframe.get_attribute("src")
            if urlsplit(src).hostname != "app.wohnungshelden.de":
                result["reason"] = "unapproved_application_host"
                return result
            frame = await iframe.element_handle()
            frame = await frame.content_frame()
            await frame.locator("#firstName").wait_for(state="visible",timeout=20000)
            result["form_present"] = True
            result["fields"] = await frame.locator("input,textarea,select").evaluate_all(FIELD_JS)
            if await visible_challenge(page):
                result["reason"] = "visible_captcha_requires_manual_action"
            elif await frame.locator("input[type='file']").count():
                result["reason"] = "document_upload_requires_manual_action"
            else:
                result["reason"] = "form_profile_mapping_required"
                result["_frame"] = frame
        elif provider == "howoge":
            link = page.get_by_role("link",name=re.compile("Besichtigung vereinbaren")).first
            if not await link.count():
                result["reason"] = "application_link_missing_or_closed"
                return result
            href = await link.get_attribute("href")
            from urllib.parse import urljoin
            href = urljoin(page.url,href)
            if provider_for(href) != provider:
                result["reason"] = "unapproved_application_host"
                return result
            check_robots(href,robots_cache)
            await page.goto(href,wait_until="domcontentloaded",timeout=35000)
            ready,why = await open_howoge_form(page)
            result["form_present"] = ready
            result["reason"] = why
            if ready:
                form = page.locator("form").filter(has=page.locator("#immo-form-firstname"))
                result["fields"] = await form.locator("input,select,textarea").evaluate_all(FIELD_JS)
                result["_frame"] = page.main_frame
        elif provider == "wbm":
            reject = page.get_by_role("button",name="Ablehnen",exact=True)
            if await reject.count()==1 and await reject.is_visible():
                await reject.click()
            form = page.locator("form").filter(has=page.locator("#powermail_field_vorname"))
            if await form.count() != 1:
                result["reason"] = "wbm_application_form_missing_or_ambiguous"
                return result
            result["form_present"] = True
            result["fields"] = await form.locator("input,textarea,select").evaluate_all(FIELD_JS)
            result["reason"] = "form_profile_mapping_required"
            result["_frame"] = page.main_frame
        elif provider == "stadtundland":
            reject = page.get_by_role("button",name="Alle ablehnen",exact=True)
            if await reject.count()==1 and await reject.is_visible(): await reject.click()
            iframe = page.locator("iframe#contactForm")
            if await iframe.count()!=1:
                result["reason"] = "stadtundland_application_frame_missing_or_ambiguous"
                return result
            src = urlsplit(await iframe.get_attribute("src") or "")
            if src.scheme!="https" or src.hostname!="app.wohnungshelden.de" or not src.path.startswith("/public/listings/"):
                result["reason"] = "unapproved_application_host"
                return result
            handle = await iframe.element_handle()
            frame = await handle.content_frame()
            await frame.get_by_label("Vorname",exact=True).wait_for(state="visible",timeout=25000)
            # Only the provider's embedded application URL is followed.
            if urlsplit(frame.url).hostname!="app.wohnungshelden.de":
                result["reason"] = "unexpected_application_redirect"
                return result
            result["form_present"] = True
            result["fields"] = await frame.locator("input,textarea,select").evaluate_all(FIELD_JS)
            if await visible_challenge(page):
                result["reason"] = "visible_captcha_requires_manual_action"
            else:
                result["reason"] = "form_profile_mapping_required"
                result["_frame"] = frame
        else:
            links = await main.locator("a[href]").evaluate_all("""es=>es.map(e=>({text:e.innerText,href:e.href}))""")
            applications = [x for x in links if re.search(r"jetzt bewerben|wohnung anfragen|besichtigung",x["text"],re.I)]
            if any(urlsplit(x["href"]).hostname == "tenant.immomio.com" for x in applications):
                result["reason"] = "immomio_account_and_profile_required"
                if provider == "gesobau":
                    href = next(x["href"] for x in applications if urlsplit(x["href"]).hostname == "tenant.immomio.com")
                    parsed = urlsplit(href)
                    if parsed.scheme != "https" or not re.fullmatch(r"/(?:de/)?apply/[a-f0-9-]{36}",parsed.path):
                        result["reason"] = "unapproved_application_link"
                        return result
                    check_robots(href,robots_cache)
                    await page.goto(href,wait_until="domcontentloaded",timeout=35000)
                    # No automated CAPTCHA interaction or credential entry.
                    await page.get_by_role("button",name="Jetzt bewerben",exact=True).wait_for(state="visible",timeout=15000)
                    result["form_present"] = True
                    if await visible_challenge(page):
                        result["reason"] = "immomio_visible_captcha_requires_manual_action"
            else:
                result["reason"] = "provider_adapter_not_validated"
    except Exception as exc:
        # No exception messages, request bodies, screenshots or HTML containing PII.
        result["reason"] = "inspection_error_"+type(exc).__name__
    return result
