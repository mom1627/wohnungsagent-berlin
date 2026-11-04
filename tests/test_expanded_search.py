import tempfile
import unittest
from datetime import date
from pathlib import Path
from application_ledger import Ledger
from eligibility import screen
from gewobag_adapter import offer_blockers

def offer(rooms, area="49,00"):
    return f"Adresse: Beispiel 1, 10405, Pankow Zimmeranzahl: {rooms} Wohnfläche: {area} m² Gesamtmiete: 549,99 € WBS: nicht erforderlich Bezugsfertig ab: 05.11.2026"

class ExpandedSearchTests(unittest.TestCase):
    def test_one_and_two_rooms_match_but_intermediate_or_three_do_not(self):
        for rooms in ("1","2","2,0"):
            self.assertTrue(screen(offer(rooms),provider_verified=True)["eligible"])
        for rooms in ("1,5","2,5","3"):
            self.assertFalse(screen(offer(rooms),provider_verified=True)["eligible"])
    def test_cheaper_offers_are_included_and_warm_limit_stays_550(self):
        self.assertTrue(screen(offer(2).replace("549,99","450,00"),provider_verified=True)["eligible"])
        self.assertFalse(screen(offer(2).replace("549,99","550,01"),provider_verified=True)["eligible"])
    def test_two_rooms_do_not_override_wbs_area(self):
        profile={"ready":True,"wbs_type":"100","wbs_max_area_sqm":50,
                 "wbs_valid_until":"2099-12-31","apply_for_self":True}
        valid=screen(offer(2).replace("WBS: nicht erforderlich","mit WBS"),provider_verified=True)
        self.assertEqual(offer_blockers(valid,profile),[])
        invalid=screen(offer(2,"50,01").replace("WBS: nicht erforderlich","mit WBS"),provider_verified=True)
        self.assertIn("offer_exceeds_wbs_area",offer_blockers(invalid,profile))
    def test_daily_total_uses_confirmations_and_berlin_day_across_runs(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=Ledger(remote=False,path=Path(d)/"state.json")
            ledger.entries={
                "a":{"status":"submitted_confirmed","confirmation":"provider_success_visible","at_utc":"2026-11-03T23:30:00+00:00"},
                "b":{"status":"submission_unverified","at_utc":"2026-11-04T01:00:00+00:00"},
                "c":{"status":"submitted_confirmed","confirmation":"provider_success_visible","at_utc":"2026-11-04T23:30:00+00:00"},
                "d":{"status":"submitted_confirmed","at_utc":"2026-11-04T01:00:00+00:00"}}
            ledger.save()
            restarted=Ledger(remote=False,path=ledger.path)
            self.assertEqual(restarted.confirmed_on(date(2026,11,4)),1)
            self.assertEqual(restarted.confirmed_on(date(2026,11,5)),1)

if __name__=="__main__": unittest.main()
