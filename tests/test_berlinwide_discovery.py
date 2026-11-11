import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from application_ledger import Ledger
from berlin_location import DISTRICTS
from daily_housing_agent import compatible_source, discovery_candidate
from direct_sources import SOURCES, card_record, public_url
from eligibility import screen
from protego import Protego
from public_access import check_robots
from stadtundland_adapter import WBS_LABEL, known_control


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
        card = {"candidate_origin": "direct_provider", "source_text": "2 Zimmer"}
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
        source = next(source for source in SOURCES if source.provider == "degewo")
        url = "https://www.degewo.de/immosuche/details/test"
        card = card_record(source, {"url": url, "text": "549,00 € Warmmiete 1 Zimmer"}, 1)
        self.assertEqual(screen(card["source_text"])["total_rent_eur"], "549.00")
        self.assertFalse(public_url(source, url.replace("degewo.de", "degewo.de.example"), detail=True))
        self.assertFalse(public_url(source, "https://www.degewo.de/immosuche", detail=True))

    def test_howoge_robots_wildcard_blocks_application_queries(self):
        rules = Protego.parse("User-agent: *\nAllow: /\nDisallow: /*cHash")
        cache = {"www.howoge.de": rules}
        base = "https://www.howoge.de/immobiliensuche/wohnungssuche/"
        check_robots(base, cache)
        with self.assertRaisesRegex(PermissionError, "robots_disallowed"):
            check_robots(base + "bewerbungsprozess.html?controller=Immoobject&cHash=123", cache)

    def test_exact_stadtundland_wbs_100_prompt(self):
        field = {"tag": "input", "type": "radio", "label": "Ja", "group": WBS_LABEL,
                 "id": "formly_21_radio_$$_wbs_available_$$_0_0-input"}
        self.assertTrue(known_control(field))
        self.assertFalse(known_control({**field, "group": "Haben Sie einen WBS 160?"}))

    def test_age_and_move_in_wording_observed_at_stadtundland(self):
        match = screen("Seniorenwohnung, ab 63 Jahren. Einzug ab sofort möglich. Warmmiete 403,8 €")
        self.assertEqual(match["total_rent_eur"], "403.8")
        self.assertEqual(match["available_from"], "ab sofort")
        self.assertIn("age_restriction_requires_review", match["reasons"])

    def test_area_after_stadtundland_room_count_is_never_room_count(self):
        text = ("Elsa-Ledetsch-Weg 1, 12683 Berlin 1 Zimmer 45,36 m² Quadratmeter "
                "– Singlewohnung mit WBS sucht Nachmieter! Gesamtmiete 478,98 €")
        self.assertEqual(screen(text)["rooms"], "1")
        self.assertTrue(screen(text)["basic_criteria_match"])
        self.assertEqual(screen("Adresse: Luzinstr. 8, 12619 Berlin Zimmer 1,0 Etage 1")["rooms"], "1.0")

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
