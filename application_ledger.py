"""Persistent application idempotency ledger; never stores applicant PII."""
import json
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit

LEDGER=Path("application_ledger.json")
def canonical(url):
    u=urlsplit(url)
    return urlunsplit((u.scheme.lower(),u.netloc.lower(),u.path.rstrip("/"),"",""))
def load():
    if not LEDGER.exists(): return {}
    data=json.loads(LEDGER.read_text(encoding="utf-8"))
    if not isinstance(data,dict): raise ValueError("Invalid application ledger")
    return data
def should_attempt(url,ledger):
    # Unverified submissions are deliberately not retried automatically:
    # the server may have accepted the request.
    return canonical(url) not in ledger
def record(url,status,ledger):
    if status not in ("submitted_confirmed","submission_unverified"):
        return False
    key=canonical(url)
    if key in ledger: return False
    from datetime import datetime,timezone
    ledger[key]={"status":status,"at_utc":datetime.now(timezone.utc).isoformat()}
    LEDGER.write_text(json.dumps(ledger,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return True
