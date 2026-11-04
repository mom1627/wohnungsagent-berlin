import unittest
from provider_adapters import wbm_heading_district
from eligibility import screen

class WbmRedirectDistrict(unittest.TestCase):
    def test_current_property_heading_survives_readable_url_redirect(self):
        district=wbm_heading_district("1-Zimmer-Wohnung in Mitte")
        self.assertEqual(district,"Mitte")
        current=screen("Warmmiete 420,86 EUR Anzahl der Zimmer: 1 Größe: ca. 32.87 m² Bezugsfertig ab: sofort WBS erforderlich: Ja WBS 140\nBezirk/Ortsteil: "+district+" / aktuelle Anbieterüberschrift",provider_verified=True)
        self.assertEqual(current["district"],"mitte")
        self.assertNotIn("target_district_unverified",current["reasons"])
        # Correct location must not silently assert possession of another WBS.
        self.assertIn("wbs_category_unverified",current["reasons"])

    def test_general_marketing_or_other_district_is_not_property_evidence(self):
        for title in ("WBM in Mitte","Unsere Wohnungen in Mitte","1-Zimmer-Wohnung in Spandau",
                      "1-Zimmer-Wohnung in Mitte oder Pankow","Wohnungen und Gewerbe"):
            self.assertIsNone(wbm_heading_district(title))
