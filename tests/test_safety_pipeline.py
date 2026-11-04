import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from eligibility import screen
from application_ledger import Ledger
from provider_registry import canonical_offer, provider_for

OFFER = "Adresse: Beispielstraße 1, 13347, Wedding Zimmeranzahl: 1,0 Gesamtmiete: 499,00 € WBS: nicht erforderlich Bezugsfertig ab: 05.11.2026"

class EligibilityTests(unittest.TestCase):
    def test_explicit_match(self):
        self.assertTrue(screen(OFFER,provider_verified=True)["eligible"])
    def test_cold_rent_is_not_warm(self):
        self.assertIn("warm_rent_unverified",screen(OFFER.replace("Gesamtmiete","Kaltmiete"))["reasons"])
    def test_generic_wbs_is_unknown(self):
        self.assertIn("wbs_category_unverified",screen(OFFER.replace("nicht erforderlich","erforderlich"),provider_verified=True)["reasons"])
    def test_wbs100_and_special_need(self):
        text = OFFER.replace("nicht erforderlich","WBS 100")
        self.assertTrue(screen(text,provider_verified=True)["eligible"])
        self.assertFalse(screen(text+" nur mit besonderem Wohnbedarf",provider_verified=True)["eligible"])
    def test_boundaries(self):
        self.assertFalse(screen(OFFER.replace("499,00","550,01"),provider_verified=True)["eligible"])
        self.assertFalse(screen(OFFER.replace("1,0","1,5"),provider_verified=True)["eligible"])
        self.assertFalse(screen(OFFER.replace("Wedding","Lichtenberg"),provider_verified=True)["eligible"])
    def test_unknown_availability_and_closed(self):
        self.assertFalse(screen(OFFER.split("Bezugsfertig")[0],provider_verified=True)["eligible"])
        self.assertFalse(screen(OFFER+" Angebot beendet",provider_verified=True)["eligible"])
    def test_cooperative_cost(self):
        self.assertFalse(screen(OFFER+" Genossenschaftsanteil 1500 Euro",provider_verified=True)["eligible"])
    def test_area_after_room_count_is_not_rooms(self):
        value = screen("1 Zimmer 34,08 m² Anzahl Zimmer: 1,00")
        self.assertEqual(value["rooms"],"1.00")
    def test_heating_must_be_part_of_total(self):
        text = "1 Zimmer 34,08 m² Kaltmiete: 408,96 € Betriebskosten: 85,19 € Heizkosten: 33,36 € Miete inkl. NK: 527,51 €"
        self.assertEqual(screen(text)["total_rent_eur"],"527.51")
        self.assertIsNone(screen(text.replace("527,51","494,15"))["total_rent_eur"])
    def test_age_and_student_restrictions(self):
        self.assertIn("age_restriction_requires_review",screen(OFFER+" Für Menschen ab 50 Jahren")["reasons"])
        self.assertIn("student_status_requires_review",screen(OFFER+" Studentenapartment")["reasons"])
        self.assertIn("shared_accommodation_requires_review",screen(OFFER+" Zimmer in 2er-WG")["reasons"])

class LedgerTests(unittest.TestCase):
    def test_crash_after_reservation_is_never_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"state.json"
            ledger = Ledger(remote=False,path=path)
            self.assertTrue(ledger.reserve("https://www.howoge.de/wohnungen-gewerbe/a?t=ibw"))
            again = Ledger(remote=False,path=path)
            self.assertFalse(again.reserve("https://howoge.de/immobiliensuche/a"))
            again.finish("https://howoge.de/immobiliensuche/a","submitted_confirmed",True)
            self.assertEqual(next(iter(json.loads(path.read_text()).values()))["status"],"submitted_confirmed")
            self.assertNotIn("http",path.read_text())
    def test_identity_queries_are_preserved(self):
        self.assertNotEqual(canonical_offer("https://wbm.de/offer?id=1"),canonical_offer("https://wbm.de/offer?id=2"))
    def test_gesobau_uuid_changes_keep_the_same_unit(self):
        old = "https://www.gesobau.de/?immo_ref=10-00920-00001-1605-a05d1369-f056-49f8-9ac2-e899d7cd00b4"
        new = "https://www.gesobau.de/mieten/wohnungssuche/detailseite/wilhelmsruher-damm-10-00920-00001-1605-eeb16c89-3a16-471a-ae51-f8e9017883b3/"
        self.assertEqual(canonical_offer(old),canonical_offer(new))
    def test_ledger_corruption_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"state.json"
            path.write_text("[]")
            with self.assertRaises(ValueError): Ledger(remote=False,path=path)
    def test_remote_write_failure_blocks(self):
        with patch.object(Ledger,"read"), patch.object(Ledger,"api",side_effect=HTTPError("x",409,"conflict",{},None)):
            ledger = Ledger(remote=True)
            with self.assertRaises(RuntimeError): ledger.reserve("https://gewobag.de/example")
    def test_all_providers_and_untrusted_hosts(self):
        for host in ("gewobag","howoge","gesobau","degewo","wbm","stadtundland","berlinovo"):
            self.assertIsNotNone(provider_for("https://www."+host+".de/example"))
        self.assertIsNone(provider_for("https://howoge.de.attacker.example/"))
        self.assertIsNone(provider_for("https://person@howoge.de/"))
        self.assertIsNone(provider_for("http://howoge.de/"))

if __name__ == "__main__":
    unittest.main()
