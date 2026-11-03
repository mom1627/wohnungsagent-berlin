import unittest
from review_offer_evidence import review

class ReviewTests(unittest.TestCase):
    def test_keywords_do_not_confirm_match(self):
        rows = review([{"url":"https://www.gewobag.de/x", "status":"readable_unverified",
                        "evidence":{"rent_mentions":["Warmmiete 400 Euro"],
                                    "wbs_mentions":["WBS 100"]}}])
        self.assertFalse(rows[0]["confirmed_match"])
        self.assertIsNone(rows[0]["fields"]["warm_rent_eur"])
        self.assertEqual(rows[0]["decision"], "manual_verification_required")

if __name__ == "__main__":
    unittest.main()
