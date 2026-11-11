"""Observed STADT UND LAND Wohnungshelden form, using normal UI controls only.

No request is sent without a user-supplied move-in date, truthful income answer,
fresh offer eligibility and the shared durable reservation/confirmation process.
New conditional questions are blocked, not answered with invented values.
"""
import os
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from housing_profile import today
from gewobag_adapter import norm, visible_challenge

VERSION = "stadtundland_browser_v1"
INCOME_LABEL = "Beträgt die monatliche Warmmiete höchstens 35 % Ihres monatlichen Netto-Haushaltseinkommens?"
WBS_LABEL = "Haben Sie einen Wohnberechtigungsschein (WBS) 140 oder 100?"
REFERRAL_LABEL = "Wie sind Sie auf uns aufmerksam geworden?"
DATE_LABEL = "Ab wann können Sie die Wohnung anmieten?"
PRIVACY = ("Ihre Angaben werden verschlüsselt übertragen und wir garantieren die Einhaltung der Datenschutzbestimmungen. "
           "Unsere aktuelle Datenschutzerklärung können Sie über den folgenden Link einsehen: "
           "https://www.stadtundland.de/Datenschutz.php.")
CONTACT_LABELS = {"Vorname","Nachname","E-Mail-Adresse","Telefonnummer","Straße","Nr.","PLZ","Ort","Adresszusatz","Anmerkungen"}
FORM_JS = """es=>es.filter(e=>e.getClientRects().length).map(e=>({
 id:e.id||'',type:e.type||'',tag:e.tagName.toLowerCase(),
 label:([...(e.labels||[])].map(l=>l.textContent).join(' ')||e.closest('mat-form-field')?.querySelector('label')?.textContent||'').replace(/\\s+/g,' ').trim(),
 required:!!e.required||e.getAttribute('aria-required')==='true',
 group:e.closest('[role=radiogroup]')?.getAttribute('aria-label')||''
}))"""

def income():
    try:
        value = Decimal(os.getenv("APPLICANT_MONTHLY_NET_INCOME","").replace(",","."))
        return value if value.is_finite() and 0 <= value <= 100000 else None
    except InvalidOperation:
        return None

def requested_date():
    value = os.getenv("APPLICANT_EARLIEST_MOVE_IN","").strip()
    if value == "ASAP": return today()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",value): return None
    try:
        parsed = date.fromisoformat(value)
        return max(parsed,today()) if abs((parsed-today()).days) <= 730 else None
    except ValueError:
        return None

def readiness_blocker():
    if requested_date() is None: return "stadtundland_user_move_in_date_required"
    if income() is None: return "stadtundland_income_answer_unverified"
    return None

def income_answer(rent):
    try:
        amount = Decimal(rent)
        net = income()
        if net is None or not amount.is_finite() or amount < 0: return None
        return "Ja" if amount <= net * Decimal("0.35") else "Nein"
    except (InvalidOperation, TypeError):
        return None

def known_control(field):
    label = norm(field["label"]).removesuffix(" *")
    tag, kind, identity = field["tag"],field["type"],field["id"]
    if tag == "mat-select":
        return label in {"Anrede",REFERRAL_LABEL}
    if re.fullmatch(r"mat-input-\d+",identity):
        return label in CONTACT_LABELS and kind in {"text","textarea"}
    if kind == "radio":
        radio_fields = {
            INCOME_LABEL: "stadt_und_land_monatliche_warmmiete_hoechstens_35%_monatliches_netto_haushaltseinkommen",
            WBS_LABEL: "$$_wbs_available_$$",
        }
        token = radio_fields.get(field["group"])
        return label in {"Ja","Nein"} and token is not None and token in identity
    if kind == "checkbox":
        return "stadt_und_land_bestaetigung_datenschutzhinweis" in identity and label == PRIVACY
    mapping = {"stadt_und_land_anzahl_einziehende_personen":("number","Anzahl der einziehenden Personen"),
               "stadt_und_land_anzahl_kinder":("number","Davon Kinder"),
               "stadt_und_land_ab_wann_kann_wohnung_angemietet_werden":("text",DATE_LABEL)}
    return any(token in identity and (kind,label) == expected for token,expected in mapping.items())

async def inspect_controls(frame):
    return await frame.locator("input,textarea,select,mat-select").evaluate_all(FORM_JS)

async def select_material(frame,label,value):
    control = frame.get_by_role("combobox",name=label,exact=True)
    if await control.count() != 1: raise ValueError("material_select_missing_or_ambiguous")
    await control.click(timeout=8000)
    option = frame.get_by_role("option",name=value,exact=True)
    if await option.count() != 1: raise ValueError("material_option_missing_or_ambiguous")
    await option.click(timeout=8000)
    if norm(await control.inner_text()) != value:
        raise ValueError("material_selection_not_verified")

async def prepare_stadtundland(page,frame,contact,housing,decision,*,referral="Inberlinwohnen.de"):
    # Check protected missing inputs before any profile values enter a form.
    blocker = readiness_blocker()
    if blocker: return False,blocker
    if referral not in {"Homepage","Inberlinwohnen.de"}:
        return False,"stadtundland_referral_unverified"
    if await visible_challenge(page): return False,"visible_captcha_requires_manual_action"
    current = await inspect_controls(frame)
    if not current or any(not known_control(f) for f in current):
        return False,"stadtundland_unknown_form_field_or_notice"
    if housing.get("household_size") != 1 or not housing.get("apply_for_self"):
        return False,"stadtundland_household_mapping_unverified"
    answer = income_answer(decision.get("total_rent_eur"))
    if answer is None: return False,"stadtundland_income_answer_unverified"
    group = frame.get_by_role("radiogroup",name=INCOME_LABEL,exact=True)
    if await group.count() != 1: return False,"stadtundland_income_question_changed"
    await group.get_by_role("radio",name=answer,exact=True).check(timeout=8000)
    # An answer can reveal a new question about Jobcenter coverage or documents.
    current = await inspect_controls(frame)
    if any(not known_control(f) for f in current):
        return False,"stadtundland_new_conditional_question_requires_review"
    wbs = frame.get_by_role("radiogroup",name=WBS_LABEL,exact=True)
    if await wbs.count():
        if await wbs.count() != 1 or housing.get("wbs_type") != "100":
            return False,"stadtundland_wbs_confirmation_unverified"
        await wbs.get_by_role("radio",name="Ja",exact=True).check(timeout=8000)
        if any(not known_control(f) for f in await inspect_controls(frame)):
            return False,"stadtundland_new_conditional_question_requires_review"
    names = contact["name"].strip().split(None,1)
    if len(names) != 2: return False,"structured_applicant_name_required"
    await select_material(frame,"Anrede",housing["salutation"])
    await select_material(frame,REFERRAL_LABEL,referral)
    move_in = requested_date()
    available = decision.get("available_from") or ""
    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}",available):
        move_in = max(move_in, date.fromisoformat("-".join(reversed(available.split(".")))))
    values = {"Vorname":names[0],"Nachname":names[1],"E-Mail-Adresse":contact["email"],
              "Telefonnummer":contact["phone"],"Anmerkungen":contact["note"]}
    for label,value in values.items():
        control = frame.get_by_label(label,exact=True)
        if await control.count() != 1: return False,"stadtundland_control_missing_or_ambiguous"
        await control.fill(value,timeout=8000)
    for token,value in {"stadt_und_land_anzahl_einziehende_personen":"1",
                        "stadt_und_land_anzahl_kinder":"0",
                        "stadt_und_land_ab_wann_kann_wohnung_angemietet_werden":move_in.strftime("%d.%m.%Y")}.items():
        control = frame.locator("input[id*='"+token+"']")
        if await control.count()!=1: return False,"stadtundland_control_missing_or_ambiguous"
        await control.fill(value,timeout=8000)
    await frame.get_by_role("checkbox",name=PRIVACY,exact=True).check(timeout=8000)
    current = await inspect_controls(frame)
    if any(not known_control(f) for f in current): return False,"stadtundland_new_conditional_question_requires_review"
    invalid = frame.locator("input:visible,textarea:visible,select:visible")
    if await invalid.evaluate_all("es=>es.some(e=>!e.checkValidity())"):
        return False,"stadtundland_form_validation_incomplete"
    if await frame.locator("mat-select.ng-invalid:visible").count():
        return False,"stadtundland_form_validation_incomplete"
    if await visible_challenge(page): return False,"visible_captcha_requires_manual_action"
    return True,"form_ready"
