"""Observed native HOWOGE/WBM forms; no invented profile values or consent.

The HOWOGE preliminary boxes acknowledge notices only, not an income or credit
attestation. WBM's wider data-processing consent requires separate user approval.
GESOBAU/Immomio remains an explicitly reported CAPTCHA/login handoff.
"""
import os
from decimal import Decimal, InvalidOperation
from gewobag_adapter import fields, norm, one, visible_challenge, submit_prepared

SENDER_VERSIONS = {"gewobag":"gewobag_browser_v2", "howoge":"howoge_browser_v1",
                   "wbm":"wbm_browser_v1", "gesobau":"gesobau_immomio_v1"}
IMPLEMENTED_SENDERS = frozenset({"gewobag","howoge","wbm"})

def attempt_blocker(provider,url,ledger,uncertain_this_run):
    if ledger.contains(url): return "already_reserved_or_submitted"
    if provider in uncertain_this_run: return "provider_uncertain_submission_this_run"
    if provider not in IMPLEMENTED_SENDERS: return "provider_sender_not_implemented"
    return None

def monthly_net_income():
    try:
        value=Decimal(os.getenv("APPLICANT_MONTHLY_NET_INCOME","").replace(",","."))
        return value if value.is_finite() and 0 <= value <= 100000 else None
    except InvalidOperation: return None

def howoge_income_blocker(decision):
    income=monthly_net_income()
    if income is None: return "howoge_three_times_rent_income_unverified"
    rent=decision.get("total_rent_eur")
    if rent is None: return "warm_rent_unverified"
    if income < Decimal(rent)*3: return "howoge_three_times_rent_income_not_met"
    return None

HOWOGE_NOTICES = (
    ("checkbox--wbs","Ja, ich habe die Hinweise zum WBS zur Kenntnis genommen.",
     "Bitte beachten Sie, dass zur Anmietung einer WBS-gebundenen Wohnung der WBS zum Mietvertragsabschluss vorliegen muss. Ein gestellter WBS-Antrag ist nicht ausreichend."),
    ("checkbox--net-income","Ja, ich habe den Hinweis zum Haushaltsnettoeinkommen zur Kenntnis genommen.",
     "Wenn Sie einen Mietvertrag für Wohnungen bei der HOWOGE abschließen möchten, muss das insgesamt verfügbare Haushaltsnettoeinkommen mindestens dreimal so hoch sein wie die Gesamtmiete."),
    ("checkbox--schufa","Ja, ich habe den Hinweis zur Bonitätsauskunft zur Kenntnis genommen.",
     "Um Ihre Kreditwürdigkeit zu überprüfen informiert sich die HOWOGE über Ihre Bonität."),
)
WBM_CONSENT = ("Hiermit bestätige ich, dass ich die Hinweise zum Datenschutz gelesen habe. "
    "Ich bin damit einverstanden, dass meine personenbezogenen Daten elektronisch gespeichert und verarbeitet werden, "
    "damit die WBM GmbH mir geeignete Wohnungsangebote anbieten kann. Mein hiermit abgegebenes Einverständnis kann "
    "ich jederzeit per E-Mail an info@wbm.de oder per Post an WBM GmbH, Dircksenstraße 38, 10178 Berlin widerrufen. "
    "Die gespeicherten Daten werden nach sechs Monaten gelöscht.")
HOWOGE_IDS = {"immo-form-firstname","immo-form-lastname","immo-form-email"}
WBM_IDS = {"powermail_field_wbsvorhanden_1","powermail_field_wbsvorhanden_2",
    "powermail_field_anrede","powermail_field_name","powermail_field_vorname",
    "powermail_field_strasse","powermail_field_plz","powermail_field_ort",
    "powermail_field_e_mail","powermail_field_telefon","powermail_field_datenschutzhinweis_1","powermail_hp_2"}

def provider_statuses(ledger, live_ready):
    return {provider:{"sender_implemented":provider in IMPLEMENTED_SENDERS,
            "submission_confirmed":ledger.validated(version),
            "automatic_attempts_enabled":bool(live_ready and provider in IMPLEMENTED_SENDERS and
                (provider != "wbm" or os.getenv("APPLICANT_WBM_DATA_CONSENT")=="1")),
            "manual_requirement":("immomio_captcha_and_authenticated_session" if provider=="gesobau"
                else "wbm_data_processing_consent" if provider=="wbm" and os.getenv("APPLICANT_WBM_DATA_CONSENT")!="1"
                else "income_or_jobcenter_documents_before_rental_contract" if provider=="howoge" else None)}
            for provider,version in SENDER_VERSIONS.items()}

async def open_howoge_form(page):
    """Advance only the three exact non-binding notices, without applicant data."""
    for identity,label,notice in HOWOGE_NOTICES:
        main = page.locator("main")
        if notice not in norm(await main.inner_text()):
            return False,"howoge_notice_changed_requires_review"
        control = await one(page,"#"+identity+":visible")
        actual = await control.evaluate("e=>[...(e.labels||[])].map(l=>l.textContent).join(' ')")
        if norm(actual) != label: return False,"howoge_notice_label_changed"
        await control.check()
        await page.get_by_role("button",name="Weiter",exact=True).click(timeout=10000)
    await page.locator("#immo-form-firstname").wait_for(state="visible",timeout=15000)
    return True,"form_profile_mapping_required"

async def prepare_native(provider,page,contact,housing):
    if await visible_challenge(page): return False,"visible_captcha_requires_manual_action"
    if provider=="wbm" and os.getenv("APPLICANT_WBM_DATA_CONSENT")!="1":
        return False,"wbm_additional_data_processing_consent_required"
    names=contact["name"].strip().split(None,1)
    if len(names)!=2: return False,"structured_applicant_name_required"
    scope=page.locator("form").filter(has=page.locator("#immo-form-firstname" if provider=="howoge" else "#powermail_field_vorname"))
    if await scope.count()!=1: return False,"form_missing_or_ambiguous"
    observed=await fields(scope)
    allowed=HOWOGE_IDS if provider=="howoge" else WBM_IDS
    if any(f["type"]=="file" for f in observed): return False,"document_upload_requires_manual_action"
    # Refuse new controls even if optional: they can introduce consent or a new step.
    if any(f["id"] not in allowed for f in observed): return False,"unknown_native_form_field"
    if provider=="howoge":
        values={"immo-form-firstname":names[0],"immo-form-lastname":names[1],"immo-form-email":contact["email"]}
    elif provider=="wbm":
        consent=await one(scope,"#powermail_field_datenschutzhinweis_1")
        actual=await consent.evaluate("e=>[...(e.labels||[])].map(l=>l.textContent).join(' ')")
        if norm(actual)!=WBM_CONSENT: return False,"wbm_data_consent_changed"
        await (await one(scope,"#powermail_field_anrede")).select_option(label=housing["salutation"])
        await (await one(scope,"#powermail_field_wbsvorhanden_1")).check()
        await consent.check()
        values={"powermail_field_vorname":names[0],"powermail_field_name":names[1],
                "powermail_field_e_mail":contact["email"],"powermail_field_telefon":contact["phone"]}
        # Address is optional and unknown. Honeypot remains untouched.
    else:
        return False,"unsupported_native_form"
    for identity,value in values.items():
        await (await one(scope,"#"+identity)).fill(value)
    invalid=await scope.locator("input:visible,select:visible,textarea:visible").evaluate_all(
        "es=>es.some(e=>!e.checkValidity())")
    if invalid: return False,"native_form_validation_incomplete"
    if await visible_challenge(page): return False,"visible_captcha_requires_manual_action"
    return True,"form_ready"

async def submit_native(provider,page,url,ledger):
    identity="immo-form-firstname" if provider=="howoge" else "powermail_field_vorname"
    form=page.locator("form").filter(has=page.locator("#"+identity))
    label="Anfrage senden" if provider=="howoge" else "Anfrage absenden"
    return await submit_prepared(page,page.main_frame,url,ledger,enabled=True,
        adapter_version=SENDER_VERSIONS[provider],submit_button=form.get_by_role("button",name=label,exact=True))
