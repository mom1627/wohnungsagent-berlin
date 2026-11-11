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
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from provider_registry import canonical_offer

LEDGER = Path("application_ledger.json")
STATE_PATH = ".agent-state/application-ledger.json"
CONFIRMATION_PROOFS = frozenset({
    "provider_success_visible", "provider_reply_user_verified", "provider_receipt_email_verified",
})

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
        self.aliases = {}
        self.read()

    def api(self, method, payload=None, *, state_path=STATE_PATH):
        repo = os.environ.get("GITHUB_REPOSITORY","")
        token = os.environ.get("GH_STATE_TOKEN","")
        if not token or repo != "mom1627/wohnungsagent-berlin":
            raise RuntimeError("durable_ledger_credentials_missing")
        if state_path not in {STATE_PATH,".agent-state/candidate-watchlist.json",".agent-state/verified-offers.json"}:
            raise ValueError("unapproved_state_path")
        url = "https://api.github.com/repos/"+repo+"/contents/"+quote(state_path,safe="/")
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

    def register_aliases(self, url, aliases):
        self.aliases.setdefault(canonical(url), set()).update(canonical(alias) for alias in aliases)

    def contains(self,url):
        canonical_urls = {canonical(url), *self.aliases.get(canonical(url), ())}
        hashes = {key_for(alias) for alias in canonical_urls}
        if (canonical_urls | hashes) & self.entries.keys():
            return True
        return any(isinstance(entry, dict) and hashes.intersection(entry.get("alias_keys", []))
                   for entry in self.entries.values())

    def confirmed_on(self, day):
        count = 0
        for item in self.entries.values():
            if not isinstance(item,dict) or item.get("status") != "submitted_confirmed" or item.get("confirmation") not in CONFIRMATION_PROOFS:
                continue
            try:
                stamp=datetime.fromisoformat(item.get("confirmed_at_utc",item["at_utc"]))
                if stamp.tzinfo is None: continue
                if stamp.astimezone(ZoneInfo("Europe/Berlin")).date()==day: count+=1
            except (ValueError,TypeError,KeyError): continue
        return count

    def validated(self,adapter_version):
        return any(isinstance(x,dict) and x.get("status")=="submitted_confirmed" and
                   x.get("confirmation") in CONFIRMATION_PROOFS and
                   x.get("adapter_version")==adapter_version for x in self.entries.values())

    def adapter_uncertain(self,adapter_version):
        return any(isinstance(x,dict) and x.get("status") in {"submission_pending","submission_unverified"} and
                   x.get("adapter_version")==adapter_version for x in self.entries.values())

    def reserve(self,url,adapter_version=None):
        self.read()
        if self.contains(url): return False
        self.entries[key_for(url)] = {"status":"submission_pending","at_utc":datetime.now(timezone.utc).isoformat()}
        aliases = self.aliases.get(canonical(url), set()) - {canonical(url)}
        if aliases:
            self.entries[key_for(url)]["alias_keys"] = sorted(key_for(alias) for alias in aliases)
        if adapter_version:
            self.entries[key_for(url)]["adapter_version"] = adapter_version
        self.save()  # Failure must abort before any network submission.
        return True

    def finish(self,url,status,confirmation=None):
        from copy import deepcopy
        key = key_for(url)
        if key not in self.entries: raise ValueError("reservation_required")
        if status not in {"submitted_confirmed","submission_unverified"}: raise ValueError("invalid_submission_status")
        previous = deepcopy(self.entries[key])
        self.entries[key]["status"] = status
        if confirmation:
            # Store a fixed confirmation signal, never arbitrary server/form text.
            self.entries[key]["confirmation"] = "provider_success_visible"
            self.entries[key]["confirmed_at_utc"] = datetime.now(timezone.utc).isoformat()
        try:
            self.save()
        except Exception:
            self.entries[key] = previous
            raise

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

