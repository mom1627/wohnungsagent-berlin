import tempfile
import unittest
from datetime import date
from pathlib import Path
from application_ledger import Ledger, key_for

class ProviderReplyReceipt(unittest.TestCase):
    def ledger(self, directory, proof="provider_reply_user_verified"):
        ledger=Ledger(remote=False,path=Path(directory)/"ledger.json")
        ledger.entries[key_for("https://www.wbm.de/example") ]={
            "status":"submitted_confirmed","adapter_version":"wbm_browser_v1",
            "at_utc":"2026-11-04T17:44:00+00:00","confirmed_at_utc":"2026-11-04T18:50:00+00:00",
            "confirmation":proof,"application_outcome":"not_selected_for_viewing"}
        return ledger

    def test_provider_rejection_confirms_receipt_without_counting_as_viewing(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=self.ledger(d)
            self.assertEqual(ledger.confirmed_on(date(2026,11,4)),1)
            self.assertTrue(ledger.validated("wbm_browser_v1"))
            self.assertFalse(ledger.validated("other_adapter"))
            self.assertEqual(next(iter(ledger.entries.values()))["application_outcome"],"not_selected_for_viewing")

    def test_reply_and_rejection_do_not_release_property_for_repeat_requests(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=self.ledger(d)
            ledger.save()
            restarted=Ledger(remote=False,path=ledger.path)
            self.assertTrue(restarted.contains("https://www.wbm.de/example"))
            self.assertFalse(restarted.reserve("https://www.wbm.de/example",adapter_version="wbm_browser_v1"))

    def test_authenticated_email_receipt_counts_as_confirmation(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = self.ledger(d, "provider_receipt_email_verified")
            self.assertEqual(ledger.confirmed_on(date(2026, 11, 4)), 1)
            self.assertTrue(ledger.validated("wbm_browser_v1"))
            self.assertTrue(ledger.contains("https://www.wbm.de/example"))

    def test_status_without_known_receipt_proof_cannot_validate_or_inflate_goal(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=self.ledger(d,"http_200_only")
            self.assertEqual(ledger.confirmed_on(date(2026,11,4)),0)
            self.assertFalse(ledger.validated("wbm_browser_v1"))
