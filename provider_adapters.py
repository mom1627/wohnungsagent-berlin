"""Public provider inspection. Sending remains gated by real adapter validation.

No CAPTCHA solving, unknown consents, account creation, field guesses or PII
logging. Probes never fill applicant fields or click a submission button.
"""
import re
from urllib.parse import urlsplit
from provider_registry import provider_for
from public_access import check_robots

CHALLENGE = "iframe[src*='recaptcha'],iframe[src*='hcaptcha'],[class*='g-recaptcha'],[class*='h-captcha'],[name='cf-turnstile-response']"
FIELD_JS = """els=>els.filter(e=>e.getClientRects().length).map(e=>({
 tag:e.tagName.toLowerCase(),type:e.type||'',id:e.id||'',name:e.name||'',
 label:[...(e.labels||[])].map(x=>x.innerText).join(' ').replace(/\\s+/g,' ').trim(),
 required:!!e.required||e.getAttribute('aria-required')==='true'
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
            await frame.locator("input").first.wait_for(state="attached",timeout=20000)
            result["form_present"] = True
            result["fields"] = await frame.locator("input,textarea,select").evaluate_all(FIELD_JS)
            if await frame.locator(CHALLENGE).count():
                result["reason"] = "captcha_requires_manual_action"
            elif await frame.locator("input[type='file']").count():
                result["reason"] = "document_upload_requires_manual_action"
            else:
                result["reason"] = "additional_required_answers_or_consents"
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
            result["form_present"] = True
            result["reason"] = "income_credit_notices_and_form_require_manual_review"
        else:
            result["reason"] = "provider_adapter_not_validated"
    except Exception as exc:
        # No exception messages, request bodies, screenshots or HTML containing PII.
        result["reason"] = "inspection_error_"+type(exc).__name__
    return result
