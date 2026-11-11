"""Normal browser-based requests with strict field mapping and durable reservation.

No CAPTCHA solving, token manipulation, direct submission endpoints or retries.
Applicant values live in memory only. A visible challenge requires manual work.
"""
import re
from datetime import date
from decimal import Decimal
from urllib.parse import urlsplit
from housing_profile import today

VERSION = "gewobag_browser_v2"
LAST_STAGE = "initial"
PRIVACY_ACK = ("Hiermit bestätigen Sie, dass die von Ihnen gemachten Angaben den Tatsachen entsprechen und dass Sie die "
               "Datenschutzbestimmungen der Gewobag zur Kenntnis genommen haben.")
SUCCESS = re.compile(r"(?:ihre\s+)?(?:anfrage|bewerbung)\s+(?:(?:wurde|ist)\s+)?(?:erfolgreich\s+)?(?:versendet|gesendet|eingegangen|übermittelt)|(?:anfrage|bewerbung)\s+erfolgreich\s+(?:abgeschickt|abgesendet)|vielen\s+dank\s+für\s+ihre\s+(?:anfrage|bewerbung)",re.I)

def norm(text): return " ".join(text.split())

def known_field(field):
    key = field["id"]
    if key in {"salutation","firstName","lastName","email","phone-number","applicant-message"}:
        return True
    return any(part in key for part in (
        "gesamtzahl_der_einziehenden_personen_erwachsene_und_kinder",
        "$$_wbs_available_$$_", "$$_wbs_valid_until_$$_", "gewobag_art_bezeichnung_des_wbs",
        "$$_wbs_max_number_rooms_$$_", "gewobag_fuer_wen_wird_die_wohnungsanfrage_gestellt",
        "gewobag_paragraph_9_bescheinigung_vorhanden", "gewobag_immatrikulationsbescheinigung_vorhanden",
        "$$_telephone_number_$$_", "gewobag_datenschutzhinweis_bestaetigt"))

def offer_blockers(decision, housing):
    if not housing.get("ready"):
        return [housing.get("reason","missing_protected_housing_profile")]
    reasons = list(decision["reasons"])
    if decision["wbs"] == "required_unspecified" and housing["wbs_type"] == "100":
        reasons = [r for r in reasons if r != "wbs_category_unverified"]
    # Berlin Senate, Drucksache 19/23545, pp. 2 and 4: ordinary stock belongs
    # to the income group up to 140, rather than a minimum income of 140.
    # Scope this inference to WBM's explicitly old stock, without an exclusive
    # category, new-build/funding-model notice or lower income bound. The
    # native inquiry asks only whether a WBS is held, not possession of WBS 140.
    ordinary_wbm_ceiling = (decision.get("provider")=="wbm" and decision["wbs"]=="140" and
        housing["wbs_type"]=="100" and isinstance(decision.get("building_year"),int) and
        decision["building_year"]<=2001 and not decision.get("specific_wbs_binding_requires_review",True))
    if ordinary_wbm_ceiling:
        reasons = [r for r in reasons if r != "wbs_category_unverified"]
    requires_wbs = decision["wbs"] in {"100","required_unspecified"} or ordinary_wbm_ceiling
    if requires_wbs:
        if housing["wbs_type"] != "100": reasons.append("wbs_type_not_validated")
        size = decision.get("area_sqm")
        if size is None: reasons.append("wbs_offer_area_unverified")
        elif Decimal(size) > min(Decimal(50), Decimal(str(housing["wbs_max_area_sqm"]))):
            reasons.append("offer_exceeds_wbs_area")
        if date.fromisoformat(housing["wbs_valid_until"]) < today(): reasons.append("wbs_expired")
        available = decision.get("available_from","")
        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}",available or ""):
            d,m,y = available.split(".")
            try:
                if date(int(y),int(m),int(d)) > date.fromisoformat(housing["wbs_valid_until"]):
                    reasons.append("wbs_expires_before_availability")
            except ValueError:
                reasons.append("availability_unverified")
    # The implemented form contract covers the applicant acting for themself.
    if housing.get("household_size", 1) != 1: reasons.append("household_size_profile_mismatch")
    if not housing["apply_for_self"]: reasons.append("third_party_application_not_supported")
    return sorted(set(reasons))

async def visible_challenge(page):
    """An invisible badge/script is not itself a human-verification task."""
    for frame in page.frames:
        if frame.is_detached(): continue
        parsed = urlsplit(frame.url)
        host = parsed.hostname or ""
        if host in {"www.google.com","www.recaptcha.net","www.google.com.au","google.com","recaptcha.net"} and "/recaptcha/" in parsed.path:
            try:
                owner = await frame.frame_element()
            except Exception:
                if frame.is_detached(): continue
                raise
            if not await owner.is_visible(): continue
            if "/bframe" in parsed.path:
                box = await owner.bounding_box()
                if box and box["height"] > 40 and box["width"] > 100: return True
            if "/anchor" in parsed.path and "size=invisible" not in parsed.query:
                checkbox = frame.get_by_role("checkbox")
                if await checkbox.count() and await checkbox.first.is_visible(): return True
        if host == "hcaptcha.com" or host.endswith(".hcaptcha.com") or host in {"challenges.cloudflare.com","eu.frcapi.com","global.frcapi.com"}:
            owner = await frame.frame_element()
            if await owner.is_visible(): return True
    return False

def browser_error_code(exc):
    # Never persist raw exception messages: they can contain form values or tokens.
    message = str(exc).lower()
    if "detach" in message: return "frame_detached"
    if "execution context" in message: return "navigation_context_changed"
    if "closed" in message: return "browser_target_closed"
    if "timeout" in message or isinstance(exc, TimeoutError): return "browser_timeout"
    return "browser_error"

CONFIRMATION_HOSTS = {"app.wohnungshelden.de","www.gewobag.de","gewobag.de",
                      "www.howoge.de","howoge.de","www.wbm.de","wbm.de",
                      "stadtundland.de","www.stadtundland.de"}

class SubmissionTransport:
    """Passive diagnostics only. A POST or HTTP 200 is never success proof.

    No URLs, payloads, response text, headers or tokens are retained. Only POSTs
    from a trusted application frame to its provider/vendor are counted.
    """
    def __init__(self, page):
        self.page = page
        self.posts = 0
        self.statuses = set()
        self.failed = False

    def accepts(self, request):
        try:
            if request.method != "POST" or request.resource_type not in {"xhr","fetch","document"}:
                return False
            origin = urlsplit(request.frame.url)
            destination = urlsplit(request.url)
            if origin.scheme != "https" or origin.hostname not in CONFIRMATION_HOSTS:
                return False
            host = destination.hostname or ""
            return destination.scheme == "https" and (
                host == origin.hostname or
                origin.hostname == "app.wohnungshelden.de" and
                (host == "wohnungshelden.de" or host.endswith(".wohnungshelden.de")))
        except Exception:
            return False

    def request(self, request):
        if self.accepts(request): self.posts += 1

    def response(self, response):
        if self.accepts(response.request):
            status = response.status
            if isinstance(status, int) and 100 <= status <= 599:
                self.statuses.add(status)

    def requestfailed(self, request):
        if self.accepts(request): self.failed = True

    def start(self):
        for event in ("request","response","requestfailed"):
            self.page.on(event, getattr(self,event))

    def stop(self):
        for event in ("request","response","requestfailed"):
            self.page.remove_listener(event, getattr(self,event))

    def report(self):
        return {"provider_post_observed":self.posts > 0,
                "provider_post_count":self.posts,
                "provider_http_statuses":sorted(self.statuses),
                "provider_request_failed":self.failed}

async def confirmation_visible(page, original, existing_frames, existing_pages=()):
    candidates = [original]
    if page.main_frame is not original and urlsplit(page.url).hostname in CONFIRMATION_HOSTS:
        candidates.append(page.main_frame)
    for candidate in page.frames:
        if candidate is original or candidate in existing_frames: continue
        # Only a newly created frame on the actual application origin can replace it.
        if urlsplit(candidate.url).hostname == "app.wohnungshelden.de":
            candidates.append(candidate)
    for popup in page.context.pages:
        if popup is page or popup in existing_pages: continue
        if urlsplit(popup.url).hostname in CONFIRMATION_HOSTS:
            candidates.append(popup.main_frame)
    for candidate in candidates:
        if candidate.is_detached(): continue
        if not isinstance(candidate.url,str) or urlsplit(candidate.url).hostname not in CONFIRMATION_HOSTS:
            continue
        try:
            body = await candidate.locator("body").inner_text(timeout=1500)
            if SUCCESS.search(body): return True
        except Exception:
            # A form can navigate between enumeration and reading; try next poll.
            continue
    return False

async def feedback_signals(page,frame):
    """Fixed booleans only; never persist server text or applicant values."""
    signals={"application_frame_attached":not frame.is_detached()}
    if frame.is_detached(): return signals
    try:
        body=await frame.locator("body").inner_text(timeout=1500)
        for key,pattern in {
            "email_verification_required":r"(?:E-Mail|Email).{0,70}bestätigen|bestätigen.{0,70}(?:E-Mail|Email)",
            "duplicate_notice":r"bereits.{0,40}(?:beworben|angefragt|Anfrage)",
            "provider_error_visible":r"(?:Fehler|fehlgeschlagen|nicht gesendet|nicht versendet|nicht übermittelt)",
            "form_still_visible":r"Anfrage versenden|Anfrage absenden|Vorname"}.items():
            signals[key]=bool(re.search(pattern,body,re.I))
    except Exception:
        signals["feedback_unavailable"]=True
    return signals

FIELD_JS = """es=>es.filter(e=>e.getClientRects().length).map(e=>({
 id:e.id||'',type:e.type||'',tag:e.tagName.toLowerCase(),
 label:[...(e.labels||[])].map(l=>l.textContent).join(' ').replace(/\\s+/g,' ').trim(),
 required:!!e.required||e.getAttribute('aria-required')==='true'||[...(e.labels||[])].some(l=>l.classList.contains('ant-form-item-required'))||!!e.closest('formly-field')?.querySelector('label.ant-form-item-required')
}))"""


def phone_formats(raw):
    value = raw.strip().strip("'\"")
    value = re.sub(r"[\s()/.\-\u200b\u200e\u200f]", "", value)
    if not re.fullmatch(r"(?:\+|00)?[0-9]{7,15}",value):
        return []
    if value.startswith("00"): value = "+"+value[2:]
    if value.startswith("+490"): value = "+49"+value[4:]
    options = [value]
    if value.startswith("+49"): options.append("0"+value[3:])
    elif re.fullmatch(r"01[567][0-9]{7,11}",value): options.append("+49"+value[1:])
    return list(dict.fromkeys(options))


async def fields(frame):
    return await frame.locator("input,textarea,select").evaluate_all(FIELD_JS)

async def one(frame,selector):
    control = frame.locator(selector)
    if await control.count() != 1 or not await control.is_visible():
        raise ValueError("form_control_missing_or_ambiguous")
    return control

async def choose(frame,selector,label):
    global LAST_STAGE
    LAST_STAGE = "dropdown_open_"+selector
    control = await one(frame,selector)
    await control.press("ArrowDown",timeout=8000)
    await control.fill(label,timeout=8000)
    option = frame.get_by_role("option",name=label,exact=True)
    if await option.count() != 1: raise ValueError("dropdown_option_missing_or_ambiguous")
    LAST_STAGE = "dropdown_option_"+selector
    await control.press("Enter",timeout=8000)
    selected = await control.evaluate("e=>e.closest('ng-select')?.querySelector('.ng-value-label')?.textContent?.trim()")
    if selected != label: raise ValueError("dropdown_choice_not_verified")

async def radio(frame,token,answer):
    control = await one(frame,"input[type='radio'][id*='"+token+"'][id$='-"+answer+"']")
    global LAST_STAGE
    LAST_STAGE = "radio_"+token
    if not await control.is_checked():
        await control.press("Space",timeout=8000)
    if not await control.is_checked(): raise ValueError("radio_choice_not_verified")

async def prepare(page,frame,contact,housing):
    current = await fields(frame)
    if await visible_challenge(page): return False,"visible_captcha_requires_manual_action"
    if any(f["required"] and not known_field(f) for f in current): return False,"unknown_required_field"
    if any(f["type"] == "file" for f in current): return False,"document_upload_requires_manual_action"
    # A required yes/no question is not a requirement to answer yes. Public offer
    # eligibility is checked separately; never claim possession of a certificate.
    if any("immatrikulationsbescheinigung" in f["id"] for f in current) and not housing["enrolled"]:
        return False,"required_enrollment_certificate_not_available"
    names = contact["name"].strip().split(None,1)
    if len(names) != 2: return False,"structured_applicant_name_required"
    await choose(frame,"#salutation",housing["salutation"])
    # Form changes are inspected after every answer that reveals further fields.
    if any("$$_wbs_available_$$_" in f["id"] for f in current):
        await radio(frame,"wbs_available","Ja")
        date_field = await one(frame,"input[id*='wbs_valid_until']")
        await date_field.fill(date.fromisoformat(housing["wbs_valid_until"]).strftime("%d.%m.%Y"))
        await choose(frame,"input[id*='gewobag_art_bezeichnung_des_wbs']","WBS "+housing["wbs_type"])
        if housing["household_size"] != 1 or housing["wbs_max_area_sqm"] != 50:
            return False,"wbs_room_cluster_not_validated"
        await choose(frame,"input[id*='wbs_max_number_rooms']","1 Raum oder 1 1/2 und 2 Räume bis zu 50qm")
    await choose(frame,"input[id*='gewobag_fuer_wen_wird_die_wohnungsanfrage_gestellt']","Für mich selbst")
    await (await one(frame,"input[id*='gesamtzahl_der_einziehenden_personen']")).fill(str(housing["household_size"]))
    refreshed = await fields(frame)
    for token,answer in (("paragraph_9_bescheinigung",housing["wofg9_certificate"]),("immatrikulationsbescheinigung",housing["enrolled"])):
        if any(token in f["id"] for f in refreshed): await radio(frame,token,"Ja" if answer else "Nein")
    if any(f["required"] and not known_field(f) for f in refreshed): return False,"new_unknown_required_field"
    values = {"firstName":names[0],"lastName":names[1],"email":contact["email"],"phone-number":contact["phone"],"applicant-message":contact["note"]}
    for identity,value in values.items():
        control = frame.locator("[id='"+identity+"']")
        if await control.count() and await control.is_visible(): await control.fill(value)
    mobile = frame.locator("input[id*='telephone_number']:visible")
    if await mobile.count() != 1: return False,"visible_mobile_field_missing_or_ambiguous"
    formats = phone_formats(contact["phone"])
    if not formats: return False,"phone_secret_has_no_valid_number_format"
    mobile_valid = False
    for formatted in formats:
        await mobile.fill(formatted)
        await mobile.press("Tab")
        if (await mobile.input_value()).strip() != formatted: return False,"mobile_value_not_transferred"
        if "ng-invalid" not in (await mobile.get_attribute("class") or ""):
            mobile_valid = True
            break
    if not mobile_valid: return False,"mobile_format_rejected_by_provider"
    acknowledgement = await one(frame,"input[type='checkbox'][id*='gewobag_datenschutzhinweis_bestaetigt']")
    ack_text = await acknowledgement.evaluate("e=>[...(e.labels||[])].map(l=>l.textContent).join(' ')")
    if norm(ack_text) != PRIVACY_ACK: return False,"privacy_acknowledgement_changed"
    global LAST_STAGE
    LAST_STAGE = "privacy_acknowledgement"
    if not await acknowledgement.is_checked():
        await acknowledgement.press("Space",timeout=8000)
    if not await acknowledgement.is_checked(): return False,"privacy_acknowledgement_not_checked"
    final_fields = await fields(frame)
    if any(f["required"] and not known_field(f) for f in final_fields): return False,"new_unknown_required_field"
    invalid = frame.locator("input.ng-invalid:visible,textarea.ng-invalid:visible,ng-select.ng-invalid:visible")
    if await invalid.count():
        ids = await invalid.evaluate_all("es=>es.map(e=>e.id||e.tagName).join(',')")
        return False,"form_validation_incomplete_"+ids
    if await visible_challenge(page): return False,"visible_captcha_requires_manual_action"
    return True,"form_ready"

async def submit_prepared(page,frame,url,ledger,*,enabled,adapter_version=VERSION,submit_button=None):
    result = {"url":url,"status":"not_submitted","confirmed":False}
    if not enabled:
        return {**result,"reason":"live_submission_disabled"}
    if not ledger.remote:
        return {**result,"reason":"durable_remote_ledger_required"}
    if await visible_challenge(page):
        return {**result,"reason":"visible_captcha_requires_manual_action"}
    button = submit_button if submit_button is not None else frame.get_by_role("button",name="Anfrage versenden",exact=True)
    if await button.count() != 1 or not await button.is_enabled():
        return {**result,"reason":"submit_control_not_ready"}
    initial = await frame.locator("body").inner_text()
    if SUCCESS.search(initial): return {**result,"reason":"preexisting_success_message"}
    if page.main_frame is not frame and urlsplit(page.url).hostname in CONFIRMATION_HOSTS:
        parent_initial=await page.main_frame.locator("body").inner_text()
        if SUCCESS.search(parent_initial): return {**result,"reason":"preexisting_parent_success_message"}
    # Remote reservation is made before the request button can transmit anything.
    if not ledger.reserve(url,adapter_version=adapter_version):
        return {**result,"status":"skipped","reason":"already_reserved_or_submitted"}
    result["status"] = "submission_unverified"
    result["reason"] = "no_success_confirmation"
    existing_frames = list(page.frames)
    existing_pages = list(page.context.pages)
    transport = SubmissionTransport(page)
    transport.start()
    try:
        await button.press("Enter",timeout=10000)
    except Exception as exc:
        # The action may already have transmitted before a frame/navigation error.
        # Observe only: never press the button again.
        result["reason"] = "submit_action_"+browser_error_code(exc)
    try:
        # Let the website perform its own ordinary invisible verification.
        # Never call grecaptcha, inject a token, solve a challenge or POST directly.
        for _ in range(90):
            if await visible_challenge(page):
                result["reason"] = "visible_captcha_after_submit_requires_manual_action"
                break
            if await confirmation_visible(page,frame,existing_frames,existing_pages):
                result.update(status="submitted_confirmed",confirmed=True,reason="provider_success_visible")
                break
            await page.wait_for_timeout(500)
    except Exception as exc:
        result["reason"] = "confirmation_observer_"+browser_error_code(exc)
    finally:
        transport.stop()
    result["transport_diagnostics"] = transport.report()
    if not result["confirmed"]:
        result["provider_feedback"] = await feedback_signals(page,frame)
    # An error here leaves a durable pending reservation, so no retry is possible.
    try:
        ledger.finish(url,result["status"],confirmation=result["confirmed"])
    except Exception:
        result["ledger_update_failed"] = True
        result["reason"] = ("provider_success_visible_ledger_update_failed" if result["confirmed"]
                            else "submission_unverified_ledger_update_failed")
    return result
