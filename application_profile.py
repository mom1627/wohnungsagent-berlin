"""Application contact profile loaded only from GitHub Actions secrets.

Never store real applicant contact details in the repository or job logs.
"""
import os

NOTE = ("Guten Tag, ich interessiere mich sehr für die angebotene Wohnung. "
        "Ich werde demnächst mein Studium beginnen und suche dringend eine passende Wohnung. "
        "Über eine Rückmeldung und die Möglichkeit einer Besichtigung würde ich mich sehr freuen.")

def load_profile():
    fields = {"name": "APPLICANT_NAME", "email": "APPLICANT_EMAIL", "phone": "APPLICANT_PHONE"}
    missing = [secret for secret in fields.values() if not os.getenv(secret, "").strip()]
    if missing:
        return {"ready": False, "missing_secrets": missing}
    return {"ready": True, "name": os.environ[fields["name"]],
            "email": os.environ[fields["email"]],
            "phone": os.environ[fields["phone"]], "note": NOTE}
