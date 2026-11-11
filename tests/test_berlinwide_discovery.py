import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from application_ledger import Ledger
from berlin_location import DISTRICTS
from daily_housing_agent import compatible_source, discovery_candidate
from direct_sources import SOURCES, card_record, public_url
from eligibility import screen


class BerlinwideDiscoveryTests(unittest.TestCase):
    def test_all_twelve_districts_and_their_localities(self):
        self.assertEqual(len(DISTRICTS), 12)
        for district, localities in DISTRICTS.items():
            for name in (district, *localities.split("|")):
                with self.subTest(locality=name):
                    result = screen(f"Bezirk/Ortsteil: {name} / Berlin 2 Zimmer Warmmiete: 545,00 €")
                    self.assertEqual(result["district"], district.casefold())
                    self.assertTrue(result["basic_criteria_match"])

    def test_original_must_establish_missing_source_values(self):
        card = {"candidate_origin": "direct_provider"}
        candidate = screen("2 Zimmer")
        self.assertTrue(discovery_candidate(card, candidate))
        original = screen("2 Zimmer 12555 Berlin Warmmiete: 545,00 €", provider_verified=True)
        self.assertTrue(compatible_source(candidate, original))
        self.assertFalse(compatible_source(screen("2 Zimmer Warmmiete 540,00 €"), original))
        self.assertFalse(original["eligible"])

    def test_explicit_household_and_heating_restrictions(self):
        result = screen("2 Zimmer Warmmiete 540,00 € Heizkosten sind separat. Mindestens 2 Personen.")
        self.assertIn("household_size_restriction", result["reasons"])
        self.assertIn("heating_not_included", result["reasons"])

    def test_degewo_public_card_only(self):
        source = SOURCES[0]
        url = "https://www.degewo.de/immosuche/details/test"
        card = card_record(source, {"url": url, "text": "549,00 € Warmmiete 1 Zimmer"}, 1)
        self.assertEqual(screen(card["source_text"])["total_rent_eur"], "549.00")
        self.assertFalse(public_url(source, url.replace("degewo.de", "degewo.de.example"), detail=True))
        self.assertFalse(public_url(source, "https://www.degewo.de/immosuche", detail=True))

    def test_old_reservation_is_found_via_current_redirect(self):
        old = "https://www.wbm.de/wohnungen-berlin/angebote/details/?id=42"
        new = "https://www.wbm.de/wohnungen-berlin/angebote/details/wohnungsname/"
        with TemporaryDirectory() as directory:
            ledger = Ledger(remote=False, path=Path(directory) / "history.json")
            self.assertTrue(ledger.reserve(old))
            ledger.register_aliases(new, [old])
            self.assertFalse(ledger.reserve(new))
            self.assertTrue(ledger.contains(old))

    def test_new_alias_is_persisted_for_restarted_agent(self):
        old = "https://www.wbm.de/wohnungen-berlin/angebote/details/?id=42"
        new = "https://www.wbm.de/wohnungen-berlin/angebote/details/wohnungsname/"
        with TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            ledger = Ledger(remote=False, path=path)
            ledger.register_aliases(old, [new])
            self.assertTrue(ledger.reserve(old))
            self.assertFalse(Ledger(remote=False, path=path).reserve(new))
