import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from candidate_watchlist import load_watchlist, merge_candidates, save_watchlist

TEXT="Adresse: Beispiel 1, 10405, Pankow Zimmeranzahl: 1 Gesamtmiete: 500,00 € WBS: nicht erforderlich Bezugsfertig ab: 05.11.2026"
ITEM={"url":"https://www.gewobag.de/offer/1","provider":"gewobag","source_text":TEXT,"source_page":2}

class WatchlistTests(unittest.TestCase):
    def test_cached_matches_can_be_rechecked_after_empty_discovery(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"cache.json"
            p.write_text(json.dumps({"updated_at_utc":"2026-01-01","offers":[ITEM]}))
            candidates=merge_candidates([],load_watchlist(p))
        self.assertEqual(candidates[0]["candidate_origin"],"watchlist")
        self.assertEqual(candidates[0]["source_snapshot_utc"],"2026-01-01")
        # It remains source evidence, never a provider-verified eligibility result.
        self.assertNotIn("eligible",candidates[0])
    def test_current_discovery_replaces_cached_snapshot_and_alias_is_not_duplicated(self):
        cached={**ITEM,"url":"https://gewobag.de/offer/1/","source_text":"old"}
        self.assertEqual(merge_candidates([ITEM],[cached]),[ITEM])
    def test_untrusted_hosts_or_nonmatching_cache_are_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"cache.json"
            items=[{**ITEM,"url":"https://gewobag.de.evil.example/offer/1"},
                   {**ITEM,"source_text":TEXT.replace("500,00","900,00")}]
            p.write_text(json.dumps({"offers":items}))
            self.assertEqual(load_watchlist(p),[])
    def test_only_allowlisted_public_fields_are_persisted(self):
        ledger=Mock(remote=True)
        ledger.api.return_value={"sha":"lease"}
        save_watchlist([{**ITEM,"source_snapshot_utc":"2026-01-01","email":"private-test-value","name":"private-test-value"}],ledger)
        payload=ledger.api.call_args.args[1]
        decoded=base64.b64decode(payload["content"]).decode()
        self.assertNotIn("private-test-value",decoded)
        self.assertEqual(json.loads(decoded)["offers"][0]["source_snapshot_utc"],"2026-01-01")
        self.assertEqual(payload["sha"],"lease")

if __name__=="__main__": unittest.main()
