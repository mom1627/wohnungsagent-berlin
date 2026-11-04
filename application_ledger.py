"""Durable compare-and-swap ledger. Reservation precedes ANY submit click.

GitHub contents are authoritative in Actions. A crashed/ambiguous submission is
never retried automatically. No applicant values, form contents or tokens stored.
"""
import base64
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from provider_registry import canonical_offer

LEDGER = Path("application_ledger.json")
STATE_PATH = ".agent-state/application-ledger.json"

def canonical(url):
    return canonical_offer(url)

def key_for(url):
    return hashlib.sha256(canonical(url).encode()).hexdigest()

class Ledger:
    def __init__(self, remote=None, path=LEDGER):
        self.remote = bool(os.getenv("GITHUB_ACTIONS") == "true") if remote is None else remote
        self.path = Path(path)
        self.sha = None
        self.entries = {}
        self.read()

    def api(self, method, payload=None):
        repo = os.environ.get("GITHUB_REPOSITORY","")
        token = os.environ.get("GH_STATE_TOKEN","")
        if not token or repo != "mom1627/wohnungsagent-berlin":
            raise RuntimeError("durable_ledger_credentials_missing")
        url = "https://api.github.com/repos/"+repo+"/contents/"+quote(STATE_PATH,safe="/")
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(url,data=data,method=method,headers={
            "Authorization":"Bearer "+token,"Accept":"application/vnd.github+json",
            "X-GitHub-Api-Version":"2022-11-28","Content-Type":"application/json"})
        with urlopen(request,timeout=30) as response:
            return json.load(response)

    def read(self):
        if self.remote:
            try:
                data = self.api("GET")
            except HTTPError as exc:
                if exc.code != 404: raise RuntimeError("durable_ledger_read_failed") from None
                self.entries, self.sha = {}, None
                return
            self.sha = data["sha"]
            self.entries = json.loads(base64.b64decode(data["content"]))
        elif self.path.exists():
            self.entries = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(self.entries,dict):
            raise ValueError("invalid_application_ledger")

    def save(self):
        content = json.dumps(self.entries,sort_keys=True,indent=2)+"\n"
        if self.remote:
            payload = {"message":"Persist application reservation/status [skip ci]",
                       "content":base64.b64encode(content.encode()).decode(),"branch":"main"}
            if self.sha: payload["sha"] = self.sha
            try:
                saved = self.api("PUT",payload)
            except Exception:
                raise RuntimeError("durable_ledger_write_failed_no_submission_allowed") from None
            self.sha = saved["content"]["sha"]
        else:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w",dir=self.path.parent,delete=False,encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
                temp = f.name
            os.replace(temp,self.path)

    def contains(self,url):
        return key_for(url) in self.entries or canonical(url) in self.entries

    def reserve(self,url):
        self.read()
        if self.contains(url): return False
        self.entries[key_for(url)] = {"status":"submission_pending","at_utc":datetime.now(timezone.utc).isoformat()}
        self.save()  # Failure must abort before any network submission.
        return True

    def finish(self,url,status,confirmation=None):
        key = key_for(url)
        if key not in self.entries: raise ValueError("reservation_required")
        if status not in {"submitted_confirmed","submission_unverified"}: raise ValueError("invalid_submission_status")
        self.entries[key]["status"] = status
        if confirmation:
            # Store a fixed confirmation signal, never arbitrary server/form text.
            self.entries[key]["confirmation"] = "provider_success_visible"
        self.save()

# Legacy read-only API retained for the older inspection commands.
def load():
    return Ledger(remote=False).entries

def should_attempt(url,ledger):
    return key_for(url) not in ledger and canonical(url) not in ledger

def record(url,status,ledger):
    if status not in {"submitted_confirmed","submission_unverified"} or not should_attempt(url,ledger):
        return False
    obj = Ledger(remote=False)
    obj.entries = ledger
    obj.reserve(url)
    obj.finish(url,status)
    ledger.update(obj.entries)
    return True

