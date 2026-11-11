"""Persist verified public listings and their first verification across runs."""
import base64
import json
from datetime import datetime, timezone
from urllib.error import HTTPError

from provider_registry import canonical_offer

PATH = ".agent-state/verified-offers.json"


class OfferHistory:
    def __init__(self, ledger):
        self.ledger = ledger
        self.entries = {}
        self.sha = None
        self.changed = False
        if ledger.remote:
            try:
                result = ledger.api("GET", state_path=PATH)
            except HTTPError as exc:
                if exc.code != 404:
                    raise
            else:
                self.sha = result["sha"]
                self.entries = json.loads(base64.b64decode(result["content"]))
                if not isinstance(self.entries, dict):
                    raise ValueError("invalid_verified_offer_history")

    def observe(self, listing, detail, provider, source_record):
        url = provider.get("offer_url") or listing["url"]
        key = canonical_offer(url)
        previous = self.entries.get(key) or self.entries.get(canonical_offer(listing["url"]))
        stamp = datetime.now(timezone.utc).isoformat()
        self.entries[key] = {
            "url": url, "provider": listing["provider"], "first_verified_utc": (previous or {}).get("first_verified_utc", stamp),
            "last_verified_utc": stamp, "warm_rent_eur": detail["total_rent_eur"],
            "rooms": detail["rooms"], "address": provider.get("address") or source_record["address"],
            "available_from": detail["available_from"],
        }
        self.changed = True
        return previous is None

    def save(self):
        if not self.changed or not self.ledger.remote:
            return
        content = json.dumps(self.entries, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        payload = {"message": "Record verified public offers [skip ci]", "branch": "main",
                   "content": base64.b64encode(content.encode()).decode()}
        if self.sha:
            payload["sha"] = self.sha
        saved = self.ledger.api("PUT", payload, state_path=PATH)
        self.sha = saved["content"]["sha"]
        self.changed = False
