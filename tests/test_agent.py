import tempfile
import unittest
from pathlib import Path
from agent import eligible, run

BASE = {"url": "https://example.org/expose/123?tracking=1",
        "warm_rent_eur": 499, "rooms": 1, "district": "Berlin-Wedding",
        "wbs_100_eligible": True, "application_open": True}

class AgentTests(unittest.TestCase):
    def test_eligible(self):
        self.assertTrue(eligible(BASE))
    def test_no_unverified_listing(self):
        self.assertFalse(eligible({**BASE, "application_open": None}))
        self.assertFalse(eligible({**BASE, "wbs_100_eligible": False}))
        self.assertFalse(eligible({**BASE, "warm_rent_eur": 551}))
    def test_dedup_tracking_parameters(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "seen.db"
            self.assertEqual(len(run([BASE], db)), 1)
            self.assertEqual(len(run([{**BASE, "url": "https://example.org/expose/123?x=2"}], db)), 0)

if __name__ == "__main__":
    unittest.main()
