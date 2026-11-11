"""Public listing snapshots only; every offer is rechecked before any request."""
import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from eligibility import screen
from provider_registry import provider_for, canonical_offer

STATE_PATH=".agent-state/candidate-watchlist.json"

def load_watchlist(path=STATE_PATH):
    try:
        data=json.loads(Path(path).read_text())
    except (OSError,ValueError): return []
    if not isinstance(data,dict) or not isinstance(data.get("offers"),list): return []
    result=[]
    for item in data["offers"][:100]:
        if not isinstance(item,dict): continue
        url,text=item.get("url"),item.get("source_text")
        if not isinstance(url,str) or not isinstance(text,str) or len(text)>10000: continue
        try: provider=provider_for(url)
        except ValueError: continue
        if provider!=item.get("provider") or provider is None: continue
        if not screen(text)["basic_criteria_match"]: continue
        result.append({"url":url,"provider":provider,"source_text":text,"source_page":0,
            "candidate_origin":"watchlist","source":item.get("source"),"source_snapshot_utc":item.get("source_snapshot_utc",data.get("updated_at_utc"))})
    return result

def merge_candidates(discovered,cached):
    result=[]
    seen=set()
    for item in [*discovered, *cached]:
        key=canonical_offer(item["url"])
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result

def save_watchlist(candidates,ledger):
    if not ledger.remote: return
    # Allowlist fields, never applicant values or form/server responses.
    now=datetime.now(timezone.utc).isoformat()
    items=[{**{k:x[k] for k in ("url","provider","source_text")},
        "source":x.get("source"), "source_snapshot_utc":x.get("source_snapshot_utc",now)} for x in candidates[:100]]
    try:
        current=ledger.api("GET",state_path=STATE_PATH)
    except HTTPError as exc:
        if exc.code!=404: raise
        current={}
    data={"updated_at_utc":datetime.now(timezone.utc).isoformat(),"offers":items}
    payload={"message":"Update public candidate watchlist [skip ci]","branch":"main",
        "content":base64.b64encode((json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode()).decode()}
    if current.get("sha"): payload["sha"]=current["sha"]
    ledger.api("PUT",payload,state_path=STATE_PATH)
