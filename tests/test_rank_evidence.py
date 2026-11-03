import unittest
from rank_evidence import extract

class RankEvidenceTests(unittest.TestCase):
    def test_basic_match_without_false_wbs_confirmation(self):
        row = extract({"url":"https://example.com/1","evidence":{
            "rent_mentions":["Gesamtmiete 471,83 Euro Kaution 929,49"],
            "district_mentions":["Bezirk/Ortsteil Pankow / Prenzlauer Berg Anzahl Zimmer 1"],
            "wbs_mentions":["Für die Anmietung ist ein bereits vorhandener WBS Voraussetzung."]}})
        self.assertTrue(row["basic_criteria_match"])
        self.assertEqual(row["total_rent_eur"], "471.83")
        self.assertFalse(row["wbs_100_verified"])
    def test_reject_high_rent(self):
        row = extract({"evidence":{"rent_mentions":["Gesamtmiete 863,17 Euro"],
            "district_mentions":["Bezirk/Ortsteil Pankow / Prenzlauer Berg Anzahl Zimmer 3"]}})
        self.assertFalse(row["basic_criteria_match"])
if __name__ == "__main__":
    unittest.main()
