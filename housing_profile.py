"""Typed eligibility profile from one encrypted Actions secret, never log values."""
import json
import os
from datetime import datetime, date
from zoneinfo import ZoneInfo

SECRET = "APPLICANT_HOUSING_PROFILE"
KEYS = {"salutation","household_size","apply_for_self","wbs_type","wbs_valid_until",
        "wbs_max_area_sqm","wbs_special_need","wofg9_certificate","enrolled","immomio_account"}

def today():
    return datetime.now(ZoneInfo("Europe/Berlin")).date()

def load_housing_profile():
    raw = os.getenv(SECRET,"")
    if not raw:
        return {"ready":False,"reason":"missing_protected_housing_profile"}
    try:
        p = json.loads(raw)
        if not isinstance(p,dict) or set(p) != KEYS:
            raise ValueError()
        if p["salutation"] not in {"Herr","Frau","Keine"}:
            raise ValueError()
        if type(p["household_size"]) is not int or not 1 <= p["household_size"] <= 10:
            raise ValueError()
        if type(p["wbs_max_area_sqm"]) not in {int,float} or not 1 <= p["wbs_max_area_sqm"] <= 200:
            raise ValueError()
        if p["wbs_type"] not in {"100","140","160","180","220"}:
            raise ValueError()
        for key in ("apply_for_self","wbs_special_need","wofg9_certificate","enrolled","immomio_account"):
            if type(p[key]) is not bool: raise ValueError()
        expiry = date.fromisoformat(p["wbs_valid_until"])
        if expiry < today():
            return {"ready":False,"reason":"housing_profile_wbs_expired"}
        return {"ready":True,**p}
    except (ValueError,TypeError,KeyError):
        return {"ready":False,"reason":"invalid_protected_housing_profile"}
