"""Compatibility entry point; the old unvalidated sender is retired.

The actual public form contains reCAPTCHA and unknown mandatory answers.
No request is sent until a provider adapter has a verified end-to-end result.
"""
async def apply_gewobag(url):
    return {"url":url,"status":"not_submitted","confirmed":False,
            "reason":"adapter_not_validated_captcha_and_required_answers"}
