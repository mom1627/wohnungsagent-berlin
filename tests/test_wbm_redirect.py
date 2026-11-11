import unittest
from provider_adapters import wbm_heading_district
from eligibility import screen
from gewobag_adapter import offer_blockers
from test_automatic_dispatch import FIXTURE

class WbmRedirectDistrict(unittest.TestCase):
    def test_current_property_heading_survives_readable_url_redirect(self):
        district=wbm_heading_district("1-Zimmer-Wohnung in Mitte")
        self.assertEqual(district,"Mitte")
        current=screen("Warmmiete 420,86 EUR Anzahl der Zimmer: 1 Größe: ca. 32.87 m² Bezugsfertig ab: sofort WBS erforderlich: Ja WBS 140\nBezirk/Ortsteil: "+district+" / aktuelle Anbieterüberschrift",provider_verified=True)
        self.assertEqual(current["district"],"mitte")
        self.assertNotIn("target_district_unverified",current["reasons"])
        # Correct location must not silently assert possession of another WBS.
        self.assertIn("wbs_category_unverified",current["reasons"])

    def test_general_marketing_is_not_property_evidence(self):
        self.assertEqual(wbm_heading_district("1-Zimmer-Wohnung in Spandau"),"Spandau")
        for title in ("WBM in Mitte","Unsere Wohnungen in Mitte",
                      "1-Zimmer-Wohnung in Mitte oder Pankow","Wohnungen und Gewerbe"):
            self.assertIsNone(wbm_heading_district(title))

    def test_ordinary_wbm_income_ceiling_is_not_a_minimum_income(self):
        text="Warmmiete 420,86 EUR Anzahl der Zimmer: 1 Größe: ca. 32.87 m² Bezugsfertig ab: sofort WBS erforderlich: Ja Die Anmietung erfolgt mit einem gültigen WBS 140. Baujahr: 1985 Bezirk/Ortsteil: Mitte / aktuelle Anbieterüberschrift"
        decision={**screen(text,provider_verified=True),"provider":"wbm"}
        self.assertEqual(decision["wbs"],"140")
        self.assertEqual(offer_blockers(decision,{"ready":True,**FIXTURE}),[])
        for changed in (text.replace("1985","2025"),text.replace("Baujahr: 1985",""),
                        text.replace("WBS 140","WBS 160"),text+" Neubau nach besonderem Fördermodell",
                        text+" ausschließlich mit WBS 140"):
            d={**screen(changed,provider_verified=True),"provider":"wbm"}
            self.assertIn("wbs_category_unverified",offer_blockers(d,{"ready":True,**FIXTURE}))
        self.assertIn("wbs_category_unverified",offer_blockers({**decision,"provider":"gewobag"},{"ready":True,**FIXTURE}))

    def test_compatible_ceiling_does_not_waive_area_or_special_need(self):
        base="Warmmiete 420,86 EUR Anzahl der Zimmer: 1 Wohnfläche: 50,01 m² Bezugsfertig ab: sofort WBS 140 Baujahr 1985 Bezirk/Ortsteil: Mitte / Anbieter"
        d={**screen(base,provider_verified=True),"provider":"wbm"}
        self.assertIn("offer_exceeds_wbs_area",offer_blockers(d,{"ready":True,**FIXTURE}))
        d={**screen(base.replace("50,01","32,87")+" Nur mit besonderem Wohnbedarf",provider_verified=True),"provider":"wbm"}
        self.assertIn("special_eligibility_requires_review",offer_blockers(d,{"ready":True,**FIXTURE}))
